#!/usr/bin/env python
# encoding: utf-8
"""
softm2cctop convert SoftM INVOICE to StratEDI INVOICE records.

Created by Maximillian Dornseif on 2008-10-31.
Copyright (c) 2008 HUDORA. All rights reserved.
"""

import os
import os.path
import sys
import copy
import pprint
import codecs
from decimal import Decimal

# From http://superjared.com/entry/django-and-crontab-best-friends/
from django.core.management import setup_environ
import settings
setup_environ(settings)
from django.db import connection

#from django.db import transaction


from huTools.fs import makedirhier

from benedict.models import SoftMTransmission

from edilib.cctop.invoic import interchangeheader000, transaktionskopf100, transaktionsreferenz111
from edilib.cctop.invoic import addressen119, zahlungsbedingungen120, rechnungsposition500, zusatzkosten140
from edilib.cctop.invoic import belegsummen900, belegabschlaege913, rechnungsliste990
from edilib.softm import parse_to_objects

from benedict.models import log_action, ADDITION, CHANGE

from paperlist import Paperlist


def get_list_id():
    "Get next list id from database sequence"

    cursor = connection.cursor()
    cursor.execute("SELECT nextval('benedict_invoice_list_seq');")
    listid, = cursor.fetchone()
    return listid


class SoftMConverter(object):
    """Converts SoftM INVOICE files to Stratedi cctop INVOICE files."""

    # identification ILN for customers w/ special treatment
    EDEKA_ILNS = ['4311501000007'] # TODO automaticly generation of this list from SoftM?

    def __init__(self, infile, outfile, transmission):
        """Initialisation...

        infile is the file coming from SoftM

        outfile is the resulting file in cctop format that will be sent to
        stratedi

        transmission represents a SoftMTransmission object."""

        #logging.basicConfig(level=logging.DEBUG,
        #                    format='%(asctime)s %(levelname)s %(message)s',
        #                    filename=os.path.join(workdir, 'INVOIC_Log.txt'),
        #                    filemode='a+')
        #
        #logging.debug("Verarbeite %r nach %r. Logs in %r" % (inputdir, outputdir, workdir))

        # Helper variables # TODO: check which of them are still needed
        self._is_finished = False
        self._is_invoicelist = None
        self.is_credit = False
        self.referenced_invoices = []
        self.iln_rechnungsempfaenger = None
        self.skonto_total = 0
        self.last_mwst = None
        self.zu_und_abschlage_total = Decimal()
        self.steuerpflichtiger_betrag_total = Decimal()
        self.mwst_gesamtbetrag_total = Decimal()
        self.rechnungsendbetrag_total = Decimal()

        # Parsing variables
        self.softm_record_list = None # whole set of records from SoftM
        self.stratedi_records = [] # whole set of records for cctop
        self.infile = infile
        self.outfile = outfile
        self.transmission = transmission

        # Paperlist
        if self.is_invoicelist:
            fn = outfile.lower().replace('txt', 'paper.txt')
            print fn
            print 'x' * 30
            self.paperlist = Paperlist(fn)

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
        return self.iln_rechnungsempfaenger in SoftMConverter.EDEKA_ILNS

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
        if self.is_invoicelist:
            self.paperlist.update_header(rec000) #dict(hudora_iln=rec000.sender_iln, empf_iln=''))
        self.stratedi_records.extend([rec000])

    def _convert_transmissionhead(self, invoice_records, sequence_no, config):
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
        print "Rechnungsnummer: ", rechnr,

        rec100.belegnr = f1.rechnungsnr
        rec100.belegdatum = f1.rechnungsdatum

        if self.is_invoicelist:
            self.paperlist.collect_invoice_info(dict(rechn_nr=rec100.belegnr,
                                            rechn_datum=str(rec100.belegdatum)[:10]))

        # Gutschrift oder Rechnung?
        print "\tBELEGART: ", f1.belegart # 380 (Rechnung), 381 (Gutschrift),  83 (Wertgutschrift) oder 84 (Wertbelastung)
        # print "Skontobetrag: ", f1.skontobetrag1_ust1
        #print "USt fuer Skonto1:", f1.ust1_fuer_skonto
        #print "USt fuer Skonto2:", f1.ust2_fuer_skonto
        #print "Skonto%:", f1.skonto1

        rec100.transaktionsart = f1.belegart.lstrip('0')
        self._set_transaktionsart(rec100.transaktionsart)

        rec111.auftragsnr = f1.auftragsnr
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
        # TODO: was ist der Unterschied zwischen ustdid und steuernr?
        rec119_verkaeuferaddr.ustdid = f1.ustdid_absender
        rec119_verkaeuferaddr.steuernr = f1.steuernummer
        rec119_verkaeuferaddr.weeenr = config['operatorweeenr']
        rec119_verkaeuferaddr.tel = config['operatortel']
        rec119_verkaeuferaddr.fax = config['operatorfax']

        try:
            # R1 entries are related to invoice lists (Vorsicht gef. Halbwissen!). So if this is a
            # single invoice, we have to handle this here
            rec119_verkaeuferaddr.gegebenepartnerid = invoice_records['R1'].lieferantennr_verband
        except:
            pass

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
        # rec140.frachtbetrag = f1.xxx
        # rec140.verpackungsbetrag = f1.xxx
        # rec140.versicherungsbetrag = f1.xxx
        rec140.skontotage = f1.skontotage1
        rec140.skontodatum = f1.skontodatum1

        if self.is_invoicelist:
            self.paperlist.collect_invoice_info(dict(skonto=rec140.skontobetrag))

        # pprint.pprint(f1.__dict__)
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
        rec500.artikelbezeichnung1 = f3.artikelbezeichnung[:35]
        rec500.artikelbezeichnung2 = f3.artikelbezeichnung[35:70]
        rec500.mwstsatz = f3.mwstsatz
        if self.last_mwst and (self.last_mwst != f3.mwstsatz):
            raise RuntimeError("Wechsel im Steuersatz zwischen Auftragspositionen: %s | %s" %
                               (self.last_mwst, f3.mwstsatz))
        self.last_mwst = f3.mwstsatz

        if int(f3.preisdimension) != 0:
            raise RuntimeError("Preisdimension != 0 wird noch nicht unterstuetzt")

        # MOA-5004 Bruttowarenwert = Menge x Bruttopreis ohne MWSt., vor Abzug der Artikelrabatte
        rec500.bruttostueckpreis = abs(f3.verkaufspreis)
        rec500.bruttowarenwert = abs(f3.wert_brutto)

        # MOA-5004 Nettowarenwert = Menge x Bruttopreis ./. Artikelrabatte bzw. Menge x Nettopreis
        # (Rabatte sind im Preis eingerechnet)
        # Bei Gutschriftspositionen ist der Nettowarenwert negativ einzustellen.
        rec500.nettostueckpreis = abs(f3.verkaufspreis)
        rec500.nettowarenwert = abs(f3.wert_netto)

        # pruefen ob netto = menge x brutto ./. Artikelrabatt
        dbg_nettoval = rec500.nettostueckpreis * rec500.berechnete_menge - f4.positionsrabatt_gesamt
        if  dbg_nettoval != rec500.nettowarenwert:
            if not (dbg_nettoval == abs(rec500.nettowarenwert) and self.is_credit):
                raise RuntimeError("Netto-Warenwert unschlüssig: %r * %r != %r" %
                        (rec500.nettostueckpreis, rec500.berechnete_menge, rec500.nettowarenwert))

        if rec500.bruttostueckpreis * rec500.berechnete_menge != rec500.bruttowarenwert:
            if not (abs(rec500.bruttostueckpreis * rec500.berechnete_menge) == abs(rec500.bruttowarenwert)
                    and self.is_credit):
                raise RuntimeError("Brutto-Warenwert unschlüssig: %r * %r != %r" % (rec500.bruttostueckpreis,
                                   rec500.berechnete_menge, rec500.bruttowarenwert))

        # MOA-5004 Summe aller Zu- und Abschläge aus Satzart(en) 513 mit vorzeichengerechter Darstellung
        # rec500.summeabschlaege
        self.stratedi_records.append(rec500)
        return (rec500.nettowarenwert, rec500.bruttowarenwert)

    def _convert_invoice_footer(self, invoice_records, nettosum, bruttosum):
        """Converts SoftM F9 record to StratEDI 900 and optionally 913 records."""

        rec900 = belegsummen900()
        rec913 = belegabschlaege913()
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
        #print "Rabatt=8.50 2%", f9.kopfrabatt1, f9.kopfrabatt1_prozent
        #print "gesamtrabatt=8.49", f9.summe_rabatte
        # Dies ist "Vorzeichenbehaftet" - siehe http://cybernetics.hudora.biz/intern/fogbugz/default.php?4554
        # rec900.zu_und_abschlage = -1 * f9.summe_rabatte

        if self.is_edeka:
            # Skonto wird fuer Edeka als Rabatt eingetragen
            skonto = -f1.skontobetrag1_ust1
            rec900.zu_und_abschlage = skonto
            rec900.steuerpflichtiger_betrag = rec900.nettowarenwert_gesamt + skonto
            rec900.mwst_gesamtbetrag = rec900.steuerpflichtiger_betrag * self.last_mwst / Decimal('100.0')
            rec900.rechnungsendbetrag = rec900.steuerpflichtiger_betrag + rec900.mwst_gesamtbetrag
            pass
        else:
            # Zuschlaegen getreu ihrer Vorzeichen
            rec900.zu_und_abschlage = f9.summe_rabatte + f9.summe_zuschlaege

        # speichern der einzelrechnungssummen fuer Rechnungslistenendbetröge
        self.zu_und_abschlage_total += rec900.zu_und_abschlage
        self.steuerpflichtiger_betrag_total += rec900.steuerpflichtiger_betrag
        self.mwst_gesamtbetrag_total += rec900.mwst_gesamtbetrag
        self.rechnungsendbetrag_total += rec900.rechnungsendbetrag

        # Vorzeichen muss noch eingearbeitet werden.
        # f9.Vorzeichen Summe Zuschläge'),
        # rec900.gesamt_verkaufswert

        rec913.abschlag_prozent = f9.kopfrabatt1_prozent
        rec913.abschlag = f9.kopfrabatt1

        if self.is_invoicelist:
            self.paperlist.collect_invoice_info(dict(warenwert=rec900.nettowarenwert_gesamt,
                rechnungsendbetrag=rec900.rechnungsendbetrag, umsatzsteuer=rec900.mwst_gesamtbetrag))

        self.stratedi_records.append(rec900)
        if f9.kopfrabatt1 > 0:
            self.stratedi_records.append(rec913)

    def _convert_invoice(self, softm_record_slice, config):
        """Handles a SoftM invoce. Works on a slice of an INVOICE list, which

        contains the relavant stuff for the actual invoice."""

        # Skonto aus allen f1 eintraegen ermitteln f. Papierliste
        f1list = [x[1] for x in softm_record_slice if x[0] == 'F1']
        if f1list:
            skonto = sum([rec.skontobetrag1_ust1 for rec in f1list])
            self.skonto_total += skonto

        softm_records = dict(softm_record_slice)
        self._convert_transmissionhead(softm_records, get_list_id(), config)

        # the now we have to extract the per invoice records from softm_record_list
        # every position starts with a F3 record
        tmp_softm_record_list = copy.deepcopy(softm_record_slice)

        # remove everything until we hit the first F3
        while tmp_softm_record_list and tmp_softm_record_list[0] and tmp_softm_record_list[0][0] != 'F3':
            tmp_softm_record_list.pop(0)

        nettosum = 0
        bruttosum = 0
        while tmp_softm_record_list:
            # slice of segment untill the next F3
            position = [tmp_softm_record_list.pop(0)]
            while tmp_softm_record_list and tmp_softm_record_list[0] and tmp_softm_record_list[0][0] != 'F3':
                position.append(tmp_softm_record_list.pop(0))

            # process position
            netto, brutto = self._convert_invoice_position(dict(position))
            # print("netto: %f \t brutto: %f" % (netto, brutto)),
            nettosum += netto
            bruttosum += brutto
            # print("nettosum: %f \t bruttosum: %f" % (nettosum, bruttosum))

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

        # Footer information for paperlist
        self.paperlist.update_footer(dict(warenwert=abs(rec990.steuerpflichtiger_betrag),
                              umsatzsteuer=abs(rec990.mwst), skonto=abs(self.skonto_total),
                              rechnungsendbetrag=abs(rec990.rechnungslistenendbetrag)))
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
        """Parse INVOICE file and save result in outfile."""
        self.softm_record_list = parse_to_objects(codecs.open(self.infile, 'r', 'cp850'))
        self._doconvert(additionalconfig)
        out = '\r\n'.join([record.serialize() for record in self.stratedi_records])
        codecs.open(self.outfile, 'w', 'iso-8859-1').write(out + '\r\n')

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

        #tweet = "%d INVOIC Dateien nach cctop konvertiert" % count
        #TwitHTTP('edi', 'edi').sendTwitter(tweet)


def main():
    """Main function to be called by cron."""
    inputdir = "/usr/local/edi/transfer/softm/pull/new"
    workdir = "/usr/local/edi/transfer/softm/pull/test"
    outputdir = "/usr/local/edi/transfer/stratedi/push/new"

    makedirhier(workdir)

    # Process all files that are in django db right now
    # TODO: limit this to unparsed (status=new or failed) objects
    transmissions = SoftMTransmission.objects.all()
    for count, transmission in enumerate(transmissions.iterator()):
        transmission.status = "being parsed"
        filename = transmission.filename

        # TODO These are using other 'preisdimension', so skip them atm
        if filename.upper() in ['RL00614_UPDATED.txt'.upper(),
                                'RL00602_UPDATED.txt'.upper()]:
            continue

        if filename.upper() != 'RL00603_UPDATED.txt'.upper(): # sent to stratedi 19.03.2009
            pass # continue

        print filename
        msg = "softm2cctop: "
        workfilename = os.path.join(workdir, filename)
        converter = SoftMConverter(os.path.join(inputdir, filename), workfilename, transmission)

        # Try parsing. If something fails this should be reported and
        # transmission.status  should be set to parsing_error
        try:
            converter.convert()
        except:
            (klass, error_obj, tback) = sys.exc_info()
            msg = "failed w/ msg: %s" % error_obj.message
            converter.passed(False, msg)

            if not '--tryall' in sys.argv:
                raise
        else:
            converter.passed()

        finally:
            converter.finish()


if __name__ == '__main__':
    main()
