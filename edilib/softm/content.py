#!/usr/bin/env python
# encoding: utf-8
"""
softm2cctop convert SoftM INVOICE to StratEDI INVOICE records.

Created by Maximillian Dornseif on 2008-10-31.
Copyright (c) 2008, 2010 HUDORA. All rights reserved.
"""

from decimal import Decimal
import edilib.softm.structure
import codecs
import copy
import os
import os.path
import shutil
import sys


class SoftMConverter(object):
    """Converts SoftM INVOICE files to very Simple Invoice Protocol."""

    def __init__(self):
        # Helper variables
        # TODO: check which of them are still needed
        self.is_credit = False
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


    def _convert_invoice_head(self, invoice_records):
        """Converts SoftM F1 & F2."""

        # needed entries from SoftM
        f1 = invoice_records['F1']
        f2 = invoice_records['F2']
        f3 = invoice_records['F3']
        f9 = invoice_records['F9']

        # erfasst_von - Name der Person oder des Prozesses (bei EDI), der den Auftrag in das System eingespeist hat.

        # dict(length=17, startpos=228, endpos=244, name='ustdid_absender'),

        rechnungsnr=str(f1.rechnungsnr)
        if not rechnungsnr.startswith('RG'):
            rechnungsnr = 'RG%s' % rechnungsnr
        
        kopf = dict(
            # guid - Eindeutiger ID des Vorgangs, darf niemals doppelt verwendet werden - kann als Rechnungsnummer verwendet werden
            infotext_kunde = ' '.join([f1.eigene_iln_beim_kunden, f1.lieferantennummer, f1.ustdid_rechnungsempfaenger, str(f1.kundenbestelldatum)]), # was ist mit auftragstexten?
            iln=f1.iln_rechnungsempfaenger,
            kundennr=f1.rechnungsempfaenger,
            rechnungsnr=str(f1.rechnungsnr),
            auftragsnr = f1.auftragsnr,
            kundenauftragsnr = f1.kundenbestellnummer,
            auftragsdatum = f1.auftragsdatum,
            rechnungsdatum=f1.rechnungsdatum,
            leistungsdatum = f1.liefertermin,
            lieferscheinnr = f1.lieferscheinnr,
            lieferscheindatum = f1.lieferscheindatum,
            versandkosten = f9.versandkosten1,
            skontotage = f1.skontotage1,
            skontobetrag = abs(f1.skontobetrag1_ust1),
            skonto_prozent = f1.skonto1,
            skontodatum = f1.skontodatum1,
            #rec900.steuerpflichtiger_betrag = abs(f9.steuerpflichtig1)
            #rec900.skontofaehiger_betrag = abs(f9.skontofaehig)
            rechnungsbetrag_brutto = abs(f9.gesamtbetrag),
            rechnungsbetrag_netto = abs(f9.warenwert),
            zahlungsziel=f1.nettotage,
            zahlungsdatum=f1.nettodatum,
            mwstbetrag = abs(f9.mehrwertsteuer),
            mwst_prozent=f9.mwstsatz,
            #rec120.waehrung = f1.waehrung
            skontofaehig=f9.skontofaehig,
            steuerpflichtig1=f9.steuerpflichtig1,
            skontoabzug=f9.skontoabzug,
            mehrwertsteuer=f9.mehrwertsteuer,
            steuerbetrag1=f9.steuerbetrag1,
            nettowarenwert1=f9.nettowarenwert1,
            abschlaege=f9.summe_rabatte, # = f9.kopfrabatt1 + f9.kopfrabatt2,
            abschlaege_prozent=f9.kopfrabatt1_prozent + f9.kopfrabatt2_prozent,
            # summe_zuschlaege=f9.summe_zuschlaege,
            )
        
        if f1.valutatage or f1.valutadatum:
            print kopf
            raise ValueError("%s hat Valuta - das ist nicht unterstützt" % (rechnungsnr))
        if f1.ust2_fuer_skonto:
            print f1.ust2_fuer_skonto, kopf
            raise ValueError("%s hat einen zweiten Stuerersatz - das ist nicht unterstützt" % (rechnungsnr))
        if f1.skontodatum2 or f1.skontotage2 or f1.skonto2:
            print kopf
            raise ValueError("%s hat 2. Skontosatz - das ist nicht unterstützt" % (rechnungsnr))
    
    
        # Gutschrift oder Rechnung?
        if f1.belegart.lstrip('0') in ['380', '84']:
            self.is_credit = 'Rechnung'
        elif f1.belegart.lstrip('0') in ['381', '83']:
            kopf['transaktionsart'] = 'Gutschrift'
        else:
            raise RuntimeError("Belegart %s unbekannt" % f1.belegart.lstrip('0'))
        
        # Lieferadresse / Warenempfänger
        # lieferadresse/... Felder des AddressProtocol (Zum Teil Pflichtfelder).
        # lieferadresse/kundennr Interne Kundennummer. Kann das AddressProtocol erweitern.
        kopf['lieferadresse'] = dict(
            iln=f2.liefer_iln,
            name1 = f2.liefer_name1,
            name2 = f2.liefer_name2,
            name3 = f2.liefer_name3,
            strasse1 = f2.liefer_strasse,
            plz = f2.liefer_plz,
            ort = f2.liefer_ort,
            land = f2.liefer_land, # fixup to iso country code
            #rec119_lieferaddr.internepartnerid = f2.warenempfaenger
        )
        if not kopf['lieferadresse']['iln']:
            kopf['lieferadresse']['iln'] = f2.iln_warenempfaenger
        if not kopf['lieferadresse']['iln']:
            kopf['lieferadresse']['iln'] = f2.f2.besteller_iln

        return kopf

    def _convert_invoice_position(self, position_records):
        """Converts SoftM F3 & F4 records to orderline"""

        f3 = position_records['F3']
        f4 = position_records['F4']

        line = dict(
            guid=f3.positionsnr, # needs fixing
            menge=f3.menge,
            artnr=f3.artnr,
            ean=f3.ean,
            infotext_kunde=' '.join([f3.artnr_kunde, f3.artikelbezeichnung]).strip(),
            #preis=
        )
        # Preisbasis ist die Menge, auf die sich der Stückpreis bezieht: bspw. preisbasis = 1000
        # heisst, dass der stückpreis entsprechend das tausendfache des Einzelpreises ist
        #rec500.preisbasis = 10**int(f3.preisdimension)

        # MOA-5004 Bruttowarenwert = Menge x Bruttopreis ohne MWSt., vor Abzug der Artikelrabatte
        #rec500.bruttostueckpreis = abs(f3.verkaufspreis)
        #rec500.bruttowarenwert = abs(f3.wert_brutto)

        # MOA-5004 Nettowarenwert = Menge x Bruttopreis ./. Artikelrabatte bzw. Menge x Nettopreis
        # (Rabatte sind im Preis eingerechnet)
        # Bei Gutschriftspositionen ist der Nettowarenwert negativ einzustellen.
        #rec500.nettostueckpreis = abs(f3.verkaufspreis)
        #rec500.nettowarenwert = abs(f3.wert_netto)

        # MOA-5004 Summe aller Zu- und Abschläge aus Satzart(en) 513 mit vorzeichengerechter Darstellung
        # rec500.summeabschlaege
        #self.stratedi_records.append(rec500)
        #return (rec500.nettowarenwert, rec500.bruttowarenwert)
        return line

    def _convert_invoice_footer(self, invoice_records):
        """Converts SoftM F9 record"""

        f9 = invoice_records['F9']
        f1 = invoice_records['F1']
        #rec900.nettowarenwert_gesamt = abs(f9.warenwert)
        #rec900.steuerpflichtiger_betrag = abs(f9.steuerpflichtig1)
        #rec900.rechnungsendbetrag = abs(f9.gesamtbetrag)
        #rec900.mwst_gesamtbetrag = abs(f9.mehrwertsteuer)
        #rec900.skontofaehiger_betrag = abs(f9.skontofaehig)
        
        # Ist das nur Zuschlaege oder Zuschlaege + Rabatte?
        # Dies ist "Vorzeichenbehaftet" - siehe http://cybernetics.hudora.biz/intern/fogbugz/default.php?4554
        # rec900.zu_und_abschlage = -1 * f9.summe_rabatte

        # Zuschlaege
        #rec900.zu_und_abschlage = f9.summe_zuschlaege - f9.summe_rabatte + f9.versandkosten1
        #if self.is_credit:
        #    rec900.zu_und_abschlage *= -1

        # Speichern der einzelrechnungssummen fuer Rechnungslistenendbetröge
        #self.zu_und_abschlage_total += rec900.zu_und_abschlage
        #self.steuerpflichtiger_betrag_total += rec900.steuerpflichtiger_betrag
        #self.mwst_gesamtbetrag_total += rec900.mwst_gesamtbetrag
        #self.rechnungsendbetrag_total += rec900.rechnungsendbetrag

        # Vorzeichen muss noch eingearbeitet werden.
        # f9.Vorzeichen Summe Zuschläge'),
        # rec900.gesamt_verkaufswert

    def _convert_invoice(self, softm_record_slice):
        """Handles a SoftM invoice. Works on a slice of an INVOICE list, which
        contains the relavant stuff for the actual invoice."""

        softm_records = dict(softm_record_slice)
        kopf = self._convert_invoice_head(softm_records)

        # the now we have to extract the per invoice records from softm_record_list
        # every position starts with a F3 record
        tmp_softm_record_list = copy.deepcopy(softm_record_slice)

        # remove everything until we hit the first F3
        while tmp_softm_record_list and tmp_softm_record_list[0] and tmp_softm_record_list[0][0] != 'F3':
            tmp_softm_record_list.pop(0)

        # process positions
        kopf['orderlines'] = []
        while tmp_softm_record_list:
            # slice of segment untill the next F3
            position = [tmp_softm_record_list.pop(0)]
            while tmp_softm_record_list and tmp_softm_record_list[0] and tmp_softm_record_list[0][0] != 'F3':
                position.append(tmp_softm_record_list.pop(0))

            # process position
            kopf['orderlines'].append(self._convert_invoice_position(dict(position)))

        # TODO: FK satz?
        # self._convert_invoice_footer(softm_records, nettosum, bruttosum)
        return kopf

    def _convert_invoices(self):
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
            from pprint import pprint
            invoice = self._convert_invoice(invoice)
            pprint(invoice)
            print '-' * 90


    def convert(self, filename):
        """Parse INVOICE file and save result in workfile."""

        # If we handle a collection of single invoices here, we have to split them into pieces and
        # provide a header for them.

        infile = codecs.open(filename, 'r', 'cp850')
        if not infile:
            raise RuntimeError("Datei %s nicht vorhanden" % infile)
        self.softm_record_list = edilib.softm.structure.parse_to_objects(infile)
        self._convert_invoices()


def main():
    for f in sorted(os.listdir('/Users/md/code2/git/DeadTrees/workdir/backup/INVOIC/'), reverse=False):
        if not f.startswith('RG'):
            continue
        print f
        converter = SoftMConverter()
        converter.convert(os.path.join('/Users/md/code2/git/DeadTrees/workdir/backup/INVOIC/', f))

if __name__ == '__main__':
    main()
