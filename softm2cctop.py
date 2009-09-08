#!/usr/bin/env python
# encoding: utf-8
"""
softm2cctop convert SoftM INVOICE to StratEDI INVOICE records.

Created by Maximillian Dornseif on 2008-10-31.
Copyright (c) 2008 HUDORA. All rights reserved.
"""

from decimal import Decimal
import codecs
import copy
import os
import os.path
import shutil
import sys

# From http://superjared.com/entry/django-and-crontab-best-friends/
if __name__ == '__main__':
    from django.core.management import setup_environ
    import settings
    setup_environ(settings)

from django.db import connection

from benedict import iln
from benedict.models import SoftMTransmission, EdiPartner
from benedict.models import log_action, ADDITION, CHANGE
from benedict.tools.paperlist import Paperlist
from edilib.cctop.invoic import addressen119, zahlungsbedingungen120, rechnungsposition500, zusatzkosten140
from edilib.cctop.invoic import belegsummen900, belegabschlaege913, rechnungsliste990
from edilib.cctop.invoic import interchangeheader000, transaktionskopf100, transaktionsreferenz111
from edilib.softm import parse_to_objects
from huTools.fs import makedirhier
from cs.zwitscher import zwitscher


def zwitscherwrapper(text, username):
    if os.environ.get('PYTHONUNITTEST', None):
        print("%s: '%s'" % (username, text))
    else:
        zwitscher(text=text, username=username)


class SplitMarker(object):
    """Helper class for marking a place inside of the collection of records."""
    TAG = "SPLIT HERE"
    def __init__(self):
        pass
    def serialize(self):
        return SplitMarker.TAG


def get_list_id():
    "Get next list id from database sequence"

    if os.environ.get('PYTHONUNITTEST', None):
        idstr = os.environ.get('xxxxyyyyyNumber', '5651')
        os.environ['xxxxyyyyyNumber'] = str(int(idstr)+1)
        return idstr

    if settings.DATABASE_ENGINE == 'sqlite3':
        idstr = os.environ.get('xxxxyyyyyNumber', '1')
        os.environ['xxxxyyyyyNumber'] = str(int(idstr)+1)
        return idstr
    else:
        cursor = connection.cursor()
        cursor.execute("SELECT nextval('benedict_invoice_list_seq');")
        listid, = cursor.fetchone()
        return listid


class SoftMConverter(object):
    """Converts SoftM INVOICE files to Stratedi cctop INVOICE files."""

    # identification ILN for customers w/ special treatment

    def __init__(self, infile, workfile, uploaddir, transmission):
        """Initialisation...

        infile is the file coming from SoftM

        workfile - as the name says

        uploaddir is the location in the filesystem where the resulting file(s) will be copied to and
        from where these are uploaded to stratedi.

        transmission represents a SoftMTransmission (django-model) instance."""

        # Helper variables # TODO: check which of them are still needed
        self._is_finished = False
        self._is_invoicelist = None
        self.is_credit = False
        self.referenced_invoices = []
        self.iln_rechnungsempfaenger = None
        self.skontonetto_total = Decimal()
        self.last_mwst = None
        self.zu_und_abschlage_total = Decimal()
        self.steuerpflichtiger_betrag_total = Decimal()
        self.mwst_gesamtbetrag_total = Decimal()
        self.rechnungsendbetrag_total = Decimal()
        self.transmissionlogmessage = ""

        # Parsing variables
        self.softm_record_list = None # whole set of records from SoftM
        self.stratedi_records = [] # whole set of records for cctop
        self.infile = infile
        self.workfile = workfile
        self.uploaddir = uploaddir
        self.transmission = transmission
        self.faildir = None
        self.archivdir =  None

        # Paperlist
        if self.is_invoicelist:
            self.paperlistfile = workfile.lower().replace('txt', 'paper.txt')
            self.paperlist = Paperlist(self.paperlistfile)

    @property
    def is_invoicelist(self):
        """Checks by filename, if the file is an invoice list or a collection of invoices.

        TODO: Maybe this needs to be done by preparsing the file in future."""
        if self._is_invoicelist == None:
            filename = os.path.basename(self.infile)
            if filename.upper().startswith('RG'):
                self._is_invoicelist = False
            elif filename.upper().startswith('RL'):
                self._is_invoicelist = True
            if (self._is_invoicelist == None):
                raise RuntimeError("Filenames not beginning with RG or RL are not supported: %s" % filename)
        return self._is_invoicelist

    @property
    def is_edeka(self):
        return iln.customer(self.iln_rechnungsempfaenger) == 'EDEKA'

    @property
    def is_toysrus(self):
        return iln.customer(self.iln_rechnungsempfaenger) == 'TRU'

    def _set_transaktionsart(self, transaktionsart):
        """Checks transaktionsart and sets flag to credit or invoice."""
        if transaktionsart in ['380', '84']:
            self.is_credit = False
        elif transaktionsart in ['381', '83']:
            self.is_credit = True
            if self.is_invoicelist:
                self.paperlist.comment('Gutschrift')
        else:
            raise RuntimeError("Belegart %s unbekannt" % transaktionsart)

    def _convert_interchangehead(self, sequence_no, config):
        """Converts a SoftM XH record to an StratEDI 000 record.

        sequence_no is a counter for each transmission"""
        transmission_records = dict(self.softm_record_list)
        xh = transmission_records['XH']
        rec000 = interchangeheader000()
        rec000.sender_iln = config['operatoriln']
        rec000.empfaenger_iln = xh.dfue_partner
        rec000.erstellungsdatum = xh.erstellungs_datum
        rec000.erstellungszeit = xh.erstellungs_zeit[:4] # remove seconds
        # Fortlaufende achtstellige Sendenummer
        rec000.datenaustauschreferenz = sequence_no # FIXME: is this needed for single invoices too?
        # rec000.referenznummer = xh.dateiname
        rec000.anwendungsreferenz = xh.umgebung
        rec000.testkennzeichen = xh.testkennzeichen

        self.iln_rechnungsempfaenger = rec000.empfaenger_iln
        self.transmission.destination_iln = self.iln_rechnungsempfaenger
        self.transmission.save()
        log_action(self.transmission, CHANGE, message='Set destination_iln from record 000')

        if self.is_invoicelist:
            self.paperlist.update_header_from_rec000(rec000) #dict(hudora_iln=rec000.sender_iln, empf_iln=''))
        self.stratedi_records.extend([rec000])

    def _convert_invoice_head(self, invoice_records, sequence_no, config):
        """Converts SoftM F1 & F2 to StratEDI 100, 111, 119.BY, 119.SU, 119.DP, 119.IV & 120 records."""

        # needed entries from softm
        f1 = invoice_records['F1']
        f2 = invoice_records['F2']
        f3 = invoice_records['F3']

        if self.is_invoicelist:
            r1 = invoice_records['R1']

        # records to write in cctop file
        rec100 = transaktionskopf100()
        rec111 = transaktionsreferenz111()
        rec119_lieferaddr = addressen119()
        rec119_rechnungsaddr = addressen119()
        rec119_verkaeuferaddr = addressen119()
        rec119_kaeuferaddr = addressen119()
        rec120 = zahlungsbedingungen120()
        rec140 = zusatzkosten140()

        # Eindeutige Nachrichtenreferenz des Absenders; laufende Nummer der Nachrichten im Datenaustausch
        # beginnt mit "1" und wird für jede Rechnung/Gutschrift innerhalb einer Übertragungsdatei
        # um 1 erhöht.
        rec100.referenz = sequence_no

        rechnr = str(f1.rechnungsnr)
        self.referenced_invoices.append(rechnr)

        rec100.belegnr = f1.rechnungsnr
        rec100.belegdatum = f1.rechnungsdatum

        if self.is_invoicelist:
            self.paperlist.collect_invoice_info(dict(rechn_nr=rec100.belegnr,
                                            rechn_datum=str(rec100.belegdatum)[:10]))

        # Gutschrift oder Rechnung?
        rec100.transaktionsart = f1.belegart.lstrip('0')
        self._set_transaktionsart(rec100.transaktionsart)

        # rec111.auftragsnr = f1.auftragsnr
        rec111.auftragsnr = f1.kundenbestellnummer # FIXME nur f. TRU oder auch EDEKA?
        rec111.auftragsdatum = f1.auftragsdatum
        rec111.lieferdatum = f1.liefertermin
        rec111.lieferscheinnr = f1.lieferscheinnr
        rec111.lieferscheindatum = f1.lieferscheindatum
        rec111.rechnungslistennr = f1.rechnungsliste
        rec111.rechnungslistendatum = f1.rechnungslistendatum

        # Specific for EDEKA
        if self.is_edeka:
            rec111.abkommensnr = '20'

        # Lieferant
        rec119_verkaeuferaddr.partnerart = 'SU'
        rec119_verkaeuferaddr.iln = f1.eigene_iln_beim_kunden
        rec119_verkaeuferaddr.ustdid = f1.ustdid_absender
        rec119_verkaeuferaddr.steuernr = f1.steuernummer
        rec119_verkaeuferaddr.weeenr = config['operatorweeenr']
        rec119_verkaeuferaddr.tel = config['operatortel']
        rec119_verkaeuferaddr.fax = config['operatorfax']

        if self.is_invoicelist:
            rec119_verkaeuferaddr.gegebenepartnerid = invoice_records['R1'].lieferantennr_verband
        else:
            rec119_verkaeuferaddr.gegebenepartnerid = f1.lieferantennummer

        # Warenempfänger
        rec119_lieferaddr.partnerart = 'DP'
        rec119_lieferaddr.iln = f2.liefer_iln #iln_warenempfaenger
        rec119_lieferaddr.name1 = f2.liefer_name1
        rec119_lieferaddr.name2 = f2.liefer_name2
        rec119_lieferaddr.name3 = f2.liefer_name3
        rec119_lieferaddr.strasse1 = f2.liefer_strasse
        rec119_lieferaddr.plz = f2.liefer_plz
        rec119_lieferaddr.ort = f2.liefer_ort
        rec119_lieferaddr.land = f2.liefer_land
        rec119_lieferaddr.internepartnerid = f2.warenempfaenger

        if self.is_invoicelist:
            self.paperlist.update_header(dict(steuernr=rec119_verkaeuferaddr.steuernr))
            self.paperlist.collect_invoice_info(dict(name_ort=rec119_lieferaddr.name1+', '+rec119_lieferaddr.ort,
                iln=rec119_lieferaddr.iln))

        # Kaeufer
        rec119_kaeuferaddr.partnerart = 'BY'
        if f2.besteller_iln:
            rec119_kaeuferaddr.iln = f2.besteller_iln #Verband ILN ???
        else:
            rec119_kaeuferaddr.iln = f2.iln_warenempfaenger
            # rec119_kaeuferaddr.iln = self.iln_rechnungsempfaenger

        # Rechnungsempfänfger
        rec119_rechnungsaddr.partnerart = 'IV'
        rec119_rechnungsaddr.iln = f1.iln_rechnungsempfaenger
        rec119_rechnungsaddr.internepartnerid = f1.rechnungsempfaenger
        rec119_rechnungsaddr.gegebenepartnerid = f1.lieferantennummer
        rec119_rechnungsaddr.ustdid = f1.ustdid_rechnungsempfaenger
        # rec119_rechnungsaddr.partnerabteilung

        rec120.mwstsatz = f3.mwstsatz # dies ist ein Zufälliger Rechnungspositionssatz
        rec120.waehrung = f1.waehrung

        rec140.mwstsatz = f1.ust1_fuer_skonto
        rec140.skontoprozent = f1.skonto1
        rec140.skontobetrag = abs(f1.skontobetrag1_ust1)
        if self.is_edeka: # TODO code duplication, substitute w/ function
            skonto_netto = rec140.skontobetrag
            skonto_netto *= 100
            skonto_netto /= 119
            skonto_netto = skonto_netto.quantize(Decimal('.01')) # FIXME: ich glaube so arbeiten Kaufmänner?!?
            rec140.skontobetrag = skonto_netto
        # rec140.frachtbetrag = f1.xxx
        # rec140.verpackungsbetrag = f1.xxx
        # rec140.versicherungsbetrag = f1.xxx
        rec140.skontotage = f1.skontotage1
        rec140.skontodatum = f1.skontodatum1

        # Nicht genutzte Felder aus SoftM
        # f1.
        # f1.ust1_fuer_skonto', fieldclass=DecimalFieldNoDot, precision=2),
        # f1.ust2_fuer_skonto', fieldclass=DecimalFieldNoDot, precision=2),
        # f1.'Skontofähig USt 1'),
        # f1.'Skontofähig USt 2'),
        # f1.Skontodatum 1'),
        # f1.Skontotage 1'),
        # f1.Skonto 1'),
        # f1.'Skontobetrag 1 USt 1'),
        # f1.'Skontobetrag 1 USt 2'),
        # f1.Skontodatum 2'),
        # f1.Skontotage 2'),
        # f1.Skonto 2'),
        # f1.'Skontobetrag 2 USt 1'),
        # f1.'Skontobetrag 2 USt 2'),
        # f1.='Nettodatum'),
        # f1.valutatage', fieldclass=IntegerField),
        # f1.='valutadatum', fieldclass=DateField),
        # f1.Firma'), # , fieldclass='FixedField', default='01'),
        # f1.Abteilung'),
        # f1.'Bibliothek'),
        # f1.nettotage'),
        # f1.e='iln_besteller', fieldclass=EanField),
        # f1.e='Reserve', fieldclass=FixedField, default=' ' *18),
        # f1.Status', fieldclass=FixedField, default=' '),
        # f2.'Lagerbezeichnung'),
        # f2.versandart'),
        # f2.lieferbedingung'),
        # f2.verband', fieldclass=IntegerField),
        # f2.verband_iln', fieldclass=EanField),

        self.stratedi_records.extend([rec100, rec111, rec119_lieferaddr, rec119_rechnungsaddr,
                                      rec119_kaeuferaddr, rec119_verkaeuferaddr, rec120, rec140])

    def _convert_invoice_position(self, position_records):
        """Converts SoftM F3 records to StratEDI 500 records."""

        f3 = position_records['F3']
        f4 = position_records['F4']

        rec500 = rechnungsposition500()
        rec500.positionsnummer = f3.positionsnr
        rec500.berechnete_menge = f3.menge
        rec500.ean = f3.ean
        rec500.artnr_lieferant = f3.artnr
        rec500.artnr_kunde = f3.artnr_kunde
        if self.is_toysrus:
            rec500.artnr_kunde = rec500.artnr_kunde.upper().replace('SKN', '').strip()
            assert(1 < int(rec500.artnr_kunde) < 999999)
        rec500.artikelbezeichnung1 = f3.artikelbezeichnung[:35]
        rec500.artikelbezeichnung2 = f3.artikelbezeichnung[35:70]
        rec500.mwstsatz = f3.mwstsatz
        if self.last_mwst and (self.last_mwst != f3.mwstsatz):
            raise RuntimeError("Wechsel im Steuersatz zwischen Auftragspositionen: %s | %s" %
                               (self.last_mwst, f3.mwstsatz))
        self.last_mwst = f3.mwstsatz

        # Preisbasis is die Menge, auf die sich der Stückpreis bezieht: bspw. preisbasis = 1000
        # heisst, dass der stückpreis entsprechend das tausendfache des Einzelpreises ist
        rec500.preisbasis = 10**int(f3.preisdimension)

        # MOA-5004 Bruttowarenwert = Menge x Bruttopreis ohne MWSt., vor Abzug der Artikelrabatte
        rec500.bruttostueckpreis = abs(f3.verkaufspreis)
        rec500.bruttowarenwert = abs(f3.wert_brutto)

        # MOA-5004 Nettowarenwert = Menge x Bruttopreis ./. Artikelrabatte bzw. Menge x Nettopreis
        # (Rabatte sind im Preis eingerechnet)
        # Bei Gutschriftspositionen ist der Nettowarenwert negativ einzustellen.
        rec500.nettostueckpreis = abs(f3.verkaufspreis)
        rec500.nettowarenwert = abs(f3.wert_netto)

        # pruefen ob netto = menge x brutto ./. Artikelrabatt
        dbg_nettoval = rec500.nettostueckpreis * rec500.berechnete_menge
        dbg_nettoval /= rec500.preisbasis
        dbg_nettoval -= f4.positionsrabatt_gesamt
        dbg_nettoval = dbg_nettoval.quantize(Decimal('.01'))#, rounding=ROUND_DOWN)
        dbg_nettowarenwert = rec500.nettowarenwert # * rec500.preisbasis
        dbg_nettowarenwert = dbg_nettowarenwert.quantize(Decimal('.01'))#, rounding=ROUND_DOWN)
        if  dbg_nettoval != dbg_nettowarenwert:
            if not (dbg_nettoval == abs(dbg_nettowarenwert) and self.is_credit):
                raise RuntimeError("Netto-Warenwert unschlüssig: %r != %r" % (dbg_nettoval, dbg_nettowarenwert))

        dbg_bruttoval =  rec500.bruttostueckpreis * rec500.berechnete_menge
        dbg_bruttoval /=  rec500.preisbasis
        dbg_bruttoval = dbg_bruttoval.quantize(Decimal('.01'))#, rounding=ROUND_DOWN)
        dbg_bruttowarenwert = rec500.bruttowarenwert
        dbg_bruttowarenwert = dbg_bruttowarenwert.quantize(Decimal('.01'))#, rounding=ROUND_DOWN)
        if dbg_bruttoval != dbg_bruttowarenwert:
            if not (abs(dbg_bruttoval) == abs(dbg_bruttowarenwert) and self.is_credit):
                raise RuntimeError("Brutto-Warenwert unschlüssig: %r != %r" % (dbg_bruttoval, dbg_bruttowarenwert))

        # MOA-5004 Summe aller Zu- und Abschläge aus Satzart(en) 513 mit vorzeichengerechter Darstellung
        # rec500.summeabschlaege
        self.stratedi_records.append(rec500)
        return (rec500.nettowarenwert, rec500.bruttowarenwert)

    def _convert_invoice_footer(self, invoice_records, nettosum, bruttosum):
        """Converts SoftM F9 record to StratEDI 900 and optionally 913 records."""

        rec900 = belegsummen900()
        f9 = invoice_records['F9']
        f1 = invoice_records['F1']

        if nettosum != f9.warenwert:
            if not (abs(nettosum) == abs(f9.warenwert) and self.is_credit):
                raise RuntimeError("Netto-Summe unschlüssig: %r != %r" % (nettosum, f9.warenwert))

        # FIXME das fliegt bei einigen Gutschriften raus. Macht es denn ueberhaupt sinn, dass die
        # bruttosumme gleich dem *Netto*warenwert ist? Bisher flog das nur nicht raus, weil netto meist
        # gleich brutto ist, dh. keine Positionsrabatte abgezogen wurden
        #if bruttosum != f9.nettowarenwert1:
        #    if not (abs(bruttosum) == abs(f9.nettowarenwert1) and self.is_credit):
        #        raise RuntimeError("Brutto-Summe unschlüssig: %r != %r" % (bruttosum, f9.nettowarenwert1))

        sum_kopfrabatte = f9.kopfrabatt1 + f9.kopfrabatt2
        if f9.summe_rabatte != sum_kopfrabatte:
            if not (abs(f9.summe_rabatte) == abs(sum_kopfrabatte) and self.is_credit):
                raise RuntimeError("Rabatte unschlüssig: %r != %r" % (f9.summe_rabatte, sum_kopfrabatte))

        rec900.nettowarenwert_gesamt = abs(f9.warenwert)
        rec900.steuerpflichtiger_betrag = abs(f9.steuerpflichtig1)
        rec900.rechnungsendbetrag = abs(f9.gesamtbetrag)
        rec900.mwst_gesamtbetrag = abs(f9.mehrwertsteuer)
        rec900.skontofaehiger_betrag = abs(f9.skontofaehig)

        # Ist das nur Zuschlaege oder Zuschlaege + Rabatte?
        # Dies ist "Vorzeichenbehaftet" - siehe http://cybernetics.hudora.biz/intern/fogbugz/default.php?4554
        # rec900.zu_und_abschlage = -1 * f9.summe_rabatte

        # Zuschlaege
        rec900.zu_und_abschlage =  f9.summe_zuschlaege - f9.summe_rabatte
        if self.is_credit:
            rec900.zu_und_abschlage *= -1

        paperlist_warenwert = rec900.steuerpflichtiger_betrag
        paperlist_skonto = abs(f1.skontobetrag1_ust1)
        if self.is_edeka:
            # Skonto wird fuer Edeka als Rabatt eingetragen, dazu erstmal auf Nettobetrag umrechnen
            skonto_netto = paperlist_skonto
            skonto_netto *= 100
            skonto_netto /= 119
            skonto_netto = skonto_netto.quantize(Decimal('.01')) # FIXME: ich glaube so arbeiten Kaufmänner?!?
            self.skontonetto_total += skonto_netto # Fuer Summe in Papierliste
            paperlist_skonto = skonto_netto

            # Skonto zu den Rabatten zurechnen
            rec900.zu_und_abschlage -= skonto_netto

            # Steuerplfichtiger Betrag, MwSt und Endbetrag wg. Skonto auf Nettobetrag anpassen
            rec900.steuerpflichtiger_betrag -= skonto_netto
            rec900.mwst_gesamtbetrag = rec900.steuerpflichtiger_betrag * self.last_mwst / Decimal('100.0')
            rec900.rechnungsendbetrag = rec900.steuerpflichtiger_betrag + rec900.mwst_gesamtbetrag
            pass

        # Speichern der einzelrechnungssummen fuer Rechnungslistenendbetröge
        self.zu_und_abschlage_total += rec900.zu_und_abschlage
        self.steuerpflichtiger_betrag_total += rec900.steuerpflichtiger_betrag
        self.mwst_gesamtbetrag_total += rec900.mwst_gesamtbetrag
        self.rechnungsendbetrag_total += rec900.rechnungsendbetrag

        # Vorzeichen muss noch eingearbeitet werden.
        # f9.Vorzeichen Summe Zuschläge'),
        # rec900.gesamt_verkaufswert


        if self.is_invoicelist:
            self.paperlist.collect_invoice_info(
                    dict(skonto=paperlist_skonto, warenwert=paperlist_warenwert,
                         rechnungsendbetrag=rec900.rechnungsendbetrag, umsatzsteuer=rec900.mwst_gesamtbetrag))
        self.stratedi_records.append(rec900)

        # Rabatt 1
        if f9.kopfrabatt1 > 0:
            rec913a = belegabschlaege913()
            rec913a.abschlag_prozent = f9.kopfrabatt1_prozent
            rec913a.abschlag = f9.kopfrabatt1
            self.stratedi_records.append(rec913a)

        # Rabatt 2 - kaskadierender Rabatt (!?!)
        if f9.kopfrabatt2 > 0:
            rec913b = belegabschlaege913()
            rec913b.kalkulationsfolgeanzeige = '002' # Rabatt auf rabattierten Endbetrag! FIXME: ist das immer so?
            rec913b.abschlag_prozent = f9.kopfrabatt2_prozent
            rec913b.abschlag = f9.kopfrabatt2
            self.stratedi_records.append(rec913b)

    def _convert_invoice(self, softm_record_slice, config):
        """Handles a SoftM invoice. Works on a slice of an INVOICE list, which

        contains the relavant stuff for the actual invoice."""

        softm_records = dict(softm_record_slice)
        # FIXME I think get_list_id() is wrong here. As i understand the doc, here we start from zero for every list
        self._convert_invoice_head(softm_records, get_list_id(), config)

        # the now we have to extract the per invoice records from softm_record_list
        # every position starts with a F3 record
        tmp_softm_record_list = copy.deepcopy(softm_record_slice)

        # remove everything until we hit the first F3
        while tmp_softm_record_list and tmp_softm_record_list[0] and tmp_softm_record_list[0][0] != 'F3':
            tmp_softm_record_list.pop(0)

        # process positions
        nettosum = 0
        bruttosum = 0
        while tmp_softm_record_list:
            # slice of segment untill the next F3
            position = [tmp_softm_record_list.pop(0)]
            while tmp_softm_record_list and tmp_softm_record_list[0] and tmp_softm_record_list[0][0] != 'F3':
                position.append(tmp_softm_record_list.pop(0))

            # process position
            netto, brutto = self._convert_invoice_position(dict(position))
            nettosum += netto
            bruttosum += brutto

        self._convert_invoice_footer(softm_records, nettosum, bruttosum)

        # TODO: FK satz?

    def _convert_invoicelist(self, config):
        """Handles the invoices of an SoftM invoice list."""

        softm_records = dict(self.softm_record_list)
        r1 = softm_records.get('R1', '')

        # the now we have to extract the per invoice records from self.softm_record_list
        # every position starts with a F1 record
        tmp_softm_record_list = copy.deepcopy(self.softm_record_list)

        # remove everything until we hit the first F1
        while tmp_softm_record_list and tmp_softm_record_list[0] and tmp_softm_record_list[0][0] != 'F1':
            tmp_softm_record_list.pop(0)


        # create sub-part of whole invoice (list) that represents one single
        # invoice
        while tmp_softm_record_list:
            # slice of segment untill the next F1
            invoice = [tmp_softm_record_list.pop(0)]
            while tmp_softm_record_list and tmp_softm_record_list[0] and tmp_softm_record_list[0][0] != 'F1':
                invoice.append(tmp_softm_record_list.pop(0))

            if self.is_invoicelist:
                # always also send the R1 records to the invoice processor
                invoice.append(('R1', r1))
                # tell paperlist module to create a new invoice entry
                self.paperlist.add_invoice()

            # process invoice
            self._convert_invoice(invoice, config)

            # add a mark for breaking up the list later
            if not self.is_invoicelist:
                self.stratedi_records.append(SplitMarker())

    def _convert_invoicelistfooter(self, config):
        """Converts SoftM R1, R2 & R3 records to a StratEDI 990 record."""

        softm_record_dict = dict(self.softm_record_list)
        r1 = softm_record_dict.get('R1', None)
        r3 = softm_record_dict.get('R3', None)

        r2list = [x[1] for x in self.softm_record_list if x[0] == 'R2']

        #990-15: MwSt-Betrag der Rechnungsliste: fehlt
        #990-17: Stpfl. Betrag der Rechnungsliste: fehlt
        rec990 = rechnungsliste990()

        if r2list:
            rec990.rechnungslistennr = r2list[-1].listennr
            rec990.rechnungslistendatum = r2list[-1].listendatum

        rec990.hudora_iln2 = rec990.hudora_iln = config['operatoriln']

        if r1:
            rec990.empfaenger_iln = r1.verband_iln
            rec990.lieferantennr = r1.lieferantennr_verband

        # rec990.zahlungsleistender_iln
        # rec990.valutadatum
        if r3:
            rec990.rechnungslistenendbetrag = r3.summe
        # rec990.nettowarenwert = r3.summe

        rec990.mwst = sum([rec.mwst for rec in r2list])
        rec990.steuerpflichtiger_betrag = sum([rec.warenwert for rec in r2list])

        # EDEKA specific
        if self.is_edeka:
            rec990.abkommen = '20'
            rec990.rechnungslistenendbetrag = self.rechnungsendbetrag_total
            rec990.steuerpflichtiger_betrag = self.steuerpflichtiger_betrag_total
            rec990.mwst = self.mwst_gesamtbetrag_total
            rec990.reli_zu_und_abschlaege = self.zu_und_abschlage_total
            # Vorzeichen rumdrehen, wenn es sich um eine Gutschrift handelt
            if self.is_credit:
                rec990.rechnungslistenendbetrag *= -1
                rec990.steuerpflichtiger_betrag *= -1
                rec990.mwst *= -1
                rec990.reli_zu_und_abschlaege *= -1

        # Footer information for paperlist
        self.paperlist.update_header(dict(rechnungslistennr=rec990.rechnungslistennr))
        self.paperlist.update_footer(dict(warenwert=abs(rec990.steuerpflichtiger_betrag+self.skontonetto_total),
                                          umsatzsteuer=abs(rec990.mwst), skonto = self.skontonetto_total,
                                          rechnungsendbetrag=abs(rec990.rechnungslistenendbetrag),
                                          rechnungslistennr=rec990.rechnungslistennr))
        self.stratedi_records.append(rec990)

    def _doconvert(self, additionalconfig=None):
        """Convert a SoftM Transmission to StratEDI Format.

        Expects a list of records already parsed by husoftm.dateexportschnittstelle and written to
        instance variable softm_record_list."""

        config = dict(operatoriln='4005998000007',
                      operatorweeenr='DE 70323035',
                      operatorfax='+49 2191 60912-50',
                      operatortel='+49 2191 60912-0',
                      transmissionid=str(self.transmission.id))

        if additionalconfig:
            config.update(additionalconfig)

        self._convert_interchangehead(get_list_id(), config)
        self._convert_invoicelist(config)
        if self.is_invoicelist:
            self._convert_invoicelistfooter(config)

    def convert(self, additionalconfig=None):
        """Parse INVOICE file and save result in workfile.

        If we handle a collection of single invoices here, we have to split them into pieces and
        provide a header for them."""

        infile = codecs.open(self.infile, 'r', 'cp850')
        if not infile:
            raise RuntimeError("Datei %s nicht vorhanden" % infile)
        self.softm_record_list = parse_to_objects(infile)
        self._doconvert(additionalconfig)
        if self.is_invoicelist:
            out = '\r\n'.join([record.serialize() for record in self.stratedi_records])
            codecs.open(self.workfile, 'w', 'iso-8859-1').write(out + '\r\n')
        else:
            self.convert_single_invoices()

    def convert_single_invoices(self):
        """Writes single invoices to seperate files.

        Needs to extract the rec000 (header-info) first, to provide it to all invoices."""
        # extract and serialize rec000 entry
        rec000 = self.stratedi_records.pop(0) # XXX sure ???
        assert(type(rec000) == interchangeheader000)
        rec000_serialized = rec000.serialize() + '\r\n'
        # seraialize rest of file, split invoices and write to seperate files
        out = '\r\n'.join([record.serialize() for record in self.stratedi_records])
        single_invoices = out.split(SplitMarker.TAG)
        for index, inv in enumerate(single_invoices):
            index += 1 # TODO: use enumerate(single_invoices, 1) when moving to py26 and upper
            if not inv: # sollte nur fuer den letzten Marker zutreffen, vielleicht gibt es einen clevereren Ansatz
                continue
            invout = rec000_serialized + inv.strip()
            outfilename, ext = os.path.splitext(self.workfile)
            outfilename = "%s_%03i%s" % (outfilename, index, ext)
            codecs.open(outfilename, 'w', 'iso-8859-1').write(invout + '\r\n')

    def passed(self, success=True, message='passed'):
        """Marks if parsing went well or not."""
        self.transmissionlogmessage = message
        if success:
            self.transmission.status = 'ok'
            if self.is_invoicelist:
                self.paperlist.valid = True
        else:
            self.transmission.status = 'parsing_failed'

    # FIXME: or using destructor for that purpose
    def finish(self):
        """Writes log messages, paperlists, etc. This method can only be called
        once."""
        if self._is_finished:
            raise RuntimeError("Parsing ist bereits beendet.")
        self._is_finished = True

        if self.is_invoicelist:
            self.paperlist.finish()

        self.transmission.references_invoices = '\n'.join(self.referenced_invoices)
        self.transmission.save()
        log_action(self.transmission, CHANGE, message=self.transmissionlogmessage)

        partner = EdiPartner.objects.get(destination_iln=self.iln_rechnungsempfaenger)
        if partner.invoic_live:
            # HACK only files w/ higher number than 627 (First non testing file that was sent to
            # stratedi)
            filename = os.path.basename(self.workfile)
            assert(filename.startswith('RL'))
            filename = filename.split('.')[0].split('_')[0]
            filename = filename[2:]
            if int(filename) > 637 or os.environ.get('PYTHONUNITTEST', None): # letzte an Stratedi geschickte Datei
                # TODO: Wenn mehrere Dateien erzeugt wurden (als Einzelrechnungen), dann hier Sclheife
                # einbauen...Sollte auber auch für TRU nicht notwendig sein, da Umstellung auf
                # Rechnungslisten.
                # if parsing succeeded, copy workfile to uploaddir and zwitscher
                self.paperlist.printlist()
                shutil.copy(self.workfile, self.uploaddir)
                msg = "#INVOICE %r copied to upload area." % os.path.basename(self.workfile)
                zwitscherwrapper(msg, username='edi')
                if self.transmission.status == 'ok':
                    # shutil.move(self.infile, os.path.join(self.archivdir, 'original'))
                    shutil.move(self.paperlist.filename, os.path.join(self.archivdir, 'paperlists'))
                    shutil.move(self.workfile, os.path.join(self.archivdir, 'processed'))
                    self.transmission.status = 'copied_to_uploaddir'
                    self.transmission.save()
                else:
                    # shutil.move(self.infile, os.path.join(self.faildir, 'original'))
                    shutil.move(self.paperlist.filename, os.path.join(self.faildir, 'paperlists'))
                    shutil.move(self.workfile, os.path.join(self.faildir, 'processed'))
        else:
            self.transmission.status = 'new'
            self.transmission.save()


def softm2cctop(infile, workfilename, outputdir, transmission, faildir, archivdir):
    """Calls the converter directly. Useful for testing purpose."""
    converter = SoftMConverter(infile, workfilename, outputdir, transmission)

    converter.faildir = faildir
    converter.archivdir = archivdir

    for dir in ['paperlists', 'processed']:
        makedirhier(os.path.join(archivdir, dir))
        makedirhier(os.path.join(faildir, dir))

    # Try parsing. If something fails this should be reported and
    # transmission.status  should be set to parsing_error
    try:
        converter.convert()
    except:
        (klass, error_obj, tback) = sys.exc_info()
        msg = "failed w/ msg: %s" % error_obj.message
        converter.passed(False, msg)
        raise
    else:
        converter.passed()
    finally:
        converter.finish()


def main():
    """Main function to be called by cron."""
    inputdir = "/usr/local/edi/transfer/softm/pull/new" # where original files are downloaded to
    workdir = "/usr/local/edi/transfer/softm/pull/tmp" # where  generated files lie temporary
    archivdir = "/usr/local/edi/transfer/softm/pull/archiv" # where files, paperlists and processed files will be archived
    faildir = "/usr/local/edi/transfer/softm/pull/fail" # where failded files will be archived
    outputdir = "/usr/local/edi/transfer/stratedi/push/new" # where processed files will be copied to be uploaded to stratedi

    #debug:
    #inputdir = "/tmp/benedict_tmp/new" # where original files are downloaded to
    #workdir = "/tmp/benedict_tmp/tmp" # where  generated files lie temporary
    #archivdir = "/tmp/benedict_tmp/archiv" # where files, paperlists and processed files will be archived
    #faildir = "/tmp/benedict_tmp/fail" # where failded files will be archived
    #outputdir = "/tmp/benedict_tmp/upload" # where processed files will be copied to be uploaded to stratedi

    for dir in [inputdir, archivdir, faildir, workdir, outputdir]:
        makedirhier(dir)

    for dir in ['paperlists', 'processed']:
        makedirhier(os.path.join(archivdir, dir))
        makedirhier(os.path.join(faildir, dir))

    transmissions = SoftMTransmission.objects.filter(status='new')
    #transmissions = SoftMTransmission.objects.filter(id='167')
    for count, transmission in enumerate(transmissions.iterator()):
        transmission.status = "being parsed"
        filename = transmission.filename
        if filename.upper().startswith('RG'):
            continue
        if not filename.upper().startswith('RL'):
            print 'Unbekannte SoftM - Rechnungsdatei ausgelassen:', filename
            transmission.status = u'unparsed'
            transmission.save()
            continue
        workfilename = os.path.join(workdir, filename)
        softm2cctop(os.path.join(inputdir, filename), workfilename, outputdir, transmission, faildir, archivdir)


if __name__ == '__main__':
    main()
