#!/usr/bin/env python
# encoding: utf-8
"""
softm2cctop convert SoftM INVOICE to StratEDI INVOICE records.

Created by Maximillian Dornseif on 2008-10-31.
Copyright (c) 2008. 2010 HUDORA. All rights reserved.
"""

from decimal import Decimal
from edilib.softm.structure import parse_to_objects
import codecs
import copy
import os
import os.path
import shutil
import sys


class SoftMConverter(object):
    """Converts SoftM INVOICE files to very Simple Invoice Protocol."""

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
        self.summe_fracht_leergut_verpackung = Decimal()
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
        self.archivdir = None

        # Paperlist
        if self.is_invoicelist:
            self.paperlistfile = workfile.lower().replace('txt', 'paper.txt')
            self.paperlist = Paperlist(self.paperlistfile)

    @property
    def is_invoicelist(self):
        """Checks by filename, if the file is an invoice list or a collection of invoices.

        TODO: Maybe this needs to be done by preparsing the file in future."""
        self._is_invoicelist = False
        return self._is_invoicelist

    def _set_transaktionsart(self, transaktionsart):
        """Checks transaktionsart and sets flag to credit or invoice."""
        if transaktionsart in ['380', '84']:
            self.is_credit = False
        elif transaktionsart in ['381', '83']:
            self.is_credit = True
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
            # dict(hudora_iln=rec000.sender_iln, empf_iln=''))
            self.paperlist.update_header_from_rec000(rec000)
        self.stratedi_records.extend([rec000])

    def _convert_invoice_head(self, invoice_records, sequence_no, config):
        """Converts SoftM F1 & F2 to StratEDI 100, 111, 119.BY, 119.SU, 119.DP, 119.IV & 120 records."""

        # needed entries from softm
        f1 = invoice_records['F1']
        f2 = invoice_records['F2']
        f3 = invoice_records['F3']
        f9 = invoice_records['F9']

        if self.is_invoicelist:
            r1 = invoice_records['R1']

        ret = dict(
            rechnungsnr=str(f1.rechnungsnr),
            auftragsnr = f1.auftragsnr,
            auftragsnr_kunde = f1.kundenbestellnummer,
            auftragsdatum = f1.auftragsdatum,
            rechnungsdatum=f1.rechnungsdatum,
            leistungsdatum = f1.liefertermin,
            lieferscheinnr = f1.lieferscheinnr,
            lieferscheindatum = f1.lieferscheindatum,
            versandkosten = f9.versandkosten1,
            # f1.nettotage'),
            # f1.='Nettodatum'),
            # f1.valutatage', fieldclass=IntegerField),
            # f1.='valutadatum', fieldclass=DateField),
            #rec120.mwstsatz = f3.mwstsatz # dies ist ein Zufälliger Rechnungspositionssatz
            #rec140.skontoprozent = f1.skonto1
            #rec140.skontobetrag = abs(f1.skontobetrag1_ust1)
            #rec140.skontodatum = f1.skontodatum1
            #rec140.skontotage = f1.skontotage1
            #verkaeuferaddr.gegebenepartnerid = f1.lieferantennummer
            ## Warenempfänger
            #rec119_lieferaddr.partnerart = 'DP'
            #rec119_lieferaddr.iln = f2.liefer_iln #iln_warenempfaenger
            #rec119_lieferaddr.name1 = f2.liefer_name1
            #rec119_lieferaddr.name2 = f2.liefer_name2
            #rec119_lieferaddr.name3 = f2.liefer_name3
            #rec119_lieferaddr.strasse1 = f2.liefer_strasse
            #rec119_lieferaddr.plz = f2.liefer_plz
            #rec119_lieferaddr.ort = f2.liefer_ort
            #rec119_lieferaddr.land = f2.liefer_land
            #rec119_lieferaddr.internepartnerid = f2.warenempfaenger
            ## Rechnungsempfänfger
            #rec119_rechnungsaddr.iln = f1.iln_rechnungsempfaenger
            #rec119_rechnungsaddr.internepartnerid = f1.rechnungsempfaenger
            #rec119_rechnungsaddr.gegebenepartnerid = f1.lieferantennummer
            #rec119_rechnungsaddr.ustdid = f1.ustdid_rechnungsempfaenger
            #rec120.waehrung = f1.waehrung
            #rec140.mwstsatz = f1.ust1_fuer_skonto
            )

        # Gutschrift oder Rechnung?
        rec100.transaktionsart = f1.belegart.lstrip('0')
        self._set_transaktionsart(rec100.transaktionsart)

        # Kaeufer
        rec119_kaeuferaddr.iln = f2.iln_warenempfaenger
        if f2.besteller_iln:
            rec119_kaeuferaddr.iln = f2.besteller_iln #Verband ILN ???



        # Nicht genutzte Felder aus SoftM
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
        return ret

    def _convert_invoice_position(self, position_records):
        """Converts SoftM F3 & F4 records to orderline"""

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

        # Preisbasis ist die Menge, auf die sich der Stückpreis bezieht: bspw. preisbasis = 1000
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
                raise RuntimeError("Netto-Warenwert unschlüssig: %r != %r" % (dbg_nettoval,
                                                                              dbg_nettowarenwert))

        dbg_bruttoval = rec500.bruttostueckpreis * rec500.berechnete_menge
        dbg_bruttoval /= rec500.preisbasis
        dbg_bruttoval = dbg_bruttoval.quantize(Decimal('.01'))#, rounding=ROUND_DOWN)
        dbg_bruttowarenwert = rec500.bruttowarenwert
        dbg_bruttowarenwert = dbg_bruttowarenwert.quantize(Decimal('.01'))#, rounding=ROUND_DOWN)
        if dbg_bruttoval != dbg_bruttowarenwert:
            if not (abs(dbg_bruttoval) == abs(dbg_bruttowarenwert) and self.is_credit):
                raise RuntimeError("Brutto-Warenwert unschlüssig: %r != %r" % (dbg_bruttoval,
                                                                               dbg_bruttowarenwert))

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
        rec900.zu_und_abschlage = f9.summe_zuschlaege - f9.summe_rabatte + f9.versandkosten1
        if self.is_credit:
            rec900.zu_und_abschlage *= -1

        paperlist_warenwert = rec900.steuerpflichtiger_betrag
        paperlist_skonto = abs(f1.skontobetrag1_ust1)

        # Speichern der einzelrechnungssummen fuer Rechnungslistenendbetröge
        self.zu_und_abschlage_total += rec900.zu_und_abschlage
        self.steuerpflichtiger_betrag_total += rec900.steuerpflichtiger_betrag
        self.mwst_gesamtbetrag_total += rec900.mwst_gesamtbetrag
        self.rechnungsendbetrag_total += rec900.rechnungsendbetrag

        # Vorzeichen muss noch eingearbeitet werden.
        # f9.Vorzeichen Summe Zuschläge'),
        # rec900.gesamt_verkaufswert

        # Rabatt 1
        if f9.kopfrabatt1 > 0:
            rec913a = belegabschlaege913()
            rec913a.abschlag_prozent = f9.kopfrabatt1_prozent
            rec913a.abschlag = f9.kopfrabatt1
            self.stratedi_records.append(rec913a)

        # Rabatt 2 - kaskadierender Rabatt (!?!)
        if f9.kopfrabatt2 > 0:
            rec913b = belegabschlaege913()
            # Rabatt auf rabattierten Endbetrag! FIXME: ist das immer so?
            rec913b.kalkulationsfolgeanzeige = '002'
            rec913b.abschlag_prozent = f9.kopfrabatt2_prozent
            rec913b.abschlag = f9.kopfrabatt2
            self.stratedi_records.append(rec913b)

    def _convert_invoice(self, softm_record_slice, config):
        """Handles a SoftM invoice. Works on a slice of an INVOICE list, which
        contains the relavant stuff for the actual invoice."""

        softm_records = dict(softm_record_slice)
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

        # TODO: FK satz?
        self._convert_invoice_footer(softm_records, nettosum, bruttosum)

    def _convert_invoices(self, config):
        """Handles the invoices of an SoftM invoice list."""

        softm_records = dict(self.softm_record_list)

        # now we have to extract the per invoice records from self.softm_record_list
        # every position starts with a F1 record
        tmp_softm_record_list = copy.deepcopy(self.softm_record_list)

        # remove everything until we hit the first F1
        while tmp_softm_record_list and tmp_softm_record_list[0] and tmp_softm_record_list[0][0] != 'F1':
            tmp_softm_record_list.pop(0)

        # create sub-part of whole invoice (list) that represents one single
        # invoice
        while tmp_softm_record_list:
            # slice of segment until the next F1
            invoice = [tmp_softm_record_list.pop(0)]
            while tmp_softm_record_list and tmp_softm_record_list[0] and tmp_softm_record_list[0][0] != 'F1':
                invoice.append(tmp_softm_record_list.pop(0))

            # process invoice
            self._convert_invoice(invoice, config)

    def _doconvert(self):
        """Convert a SoftM Transmission to SimpleInvoice Format.

        Expects a list of records already parsed by edilib.softmd written to self.softm_record_list."""

        config = dict(operatoriln='4005998000007',
                      operatorweeenr='DE 70323035',
                      operatorfax='+49 2191 60912-50',
                      operatortel='+49 2191 60912-0',
                      transmissionid=str(self.transmission.id))

        self._convert_interchangehead(get_list_id(), config)
        self._convert_invoices(config)

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
            # sollte nur fuer den letzten Marker zutreffen, vielleicht gibt es einen clevereren Ansatz
            if not inv:
                continue
            invout = rec000_serialized + inv.strip()
            outfilename, ext = os.path.splitext(self.workfile)
            outfilename = "%s_%03i%s" % (outfilename, index, ext)
            codecs.open(outfilename, 'w', 'iso-8859-1').write(invout + '\r\n')

    def convert(self):
        """Parse INVOICE file and save result in workfile."""

        # If we handle a collection of single invoices here, we have to split them into pieces and
        # provide a header for them.

        infile = codecs.open(self.infile, 'r', 'cp850')
        if not infile:
            raise RuntimeError("Datei %s nicht vorhanden" % infile)
        self.softm_record_list = parse_to_objects(infile)
        self._doconvert()
        self.convert_single_invoices()


def main():
    pass

if __name__ == '__main__':
    main()
