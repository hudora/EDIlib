#!/usr/bin/env python
# encoding: utf-8
"""
softm2cctop convert SoftM INVOICE to StratEDI INVOICE records.

Created by Maximillian Dornseif on 2008-10-31.
Copyright (c) 2008, 2010 HUDORA. All rights reserved.
"""

from decimal import Decimal
import codecs
import copy
import edilib.softm.structure
import os
import os.path
import shutil
import sys

class SoftMConverter(object):
    """Converts SoftM INVOICE files to very Simple Invoice Protocol."""

    def __init__(self):
        self.softm_record_list = None # whole set of records from SoftM

    def _convert_invoice_head(self, invoice_records):
        """Converts SoftM F1, F2 and varius others."""

        # needed entries from SoftM
        fa = invoice_records['FA']
        f1 = invoice_records['F1']
        f2 = invoice_records['F2']
        f3 = invoice_records['F3']
        f9 = invoice_records['F9']

        # erfasst_von - Name der Person oder des Prozesses (bei EDI), der den Auftrag in das System eingespeist hat.
        # F8 = Kontodaten


# <Bezogene Rechnungsnummer: 0>
# <verband: 0>,

# <Skontofähig USt 1: u'000000000053550'>, 
# <waehrung: 'EUR'>,
# <ust1_fuer_skonto: Decimal('19.00')>,
# <ust2_fuer_skonto: Decimal('0.00')>, 
# <eigene_iln_beim_kunden: u'4005998000007'>, 
# <nettodatum: datetime.date(2009, 4, 7)>, 
# <liefertermin: datetime.date(2009, 1, 21)>,
# <skonto1: Decimal('3.00')>, 
# <skontobetrag1_ust1: Decimal('-1.610')>,
# <steuernummer: u'12657370941'>, 

# <gesamtbetrag: Decimal('-53.550')>, 
# <warenwert: Decimal('-45.000')>, 
# <nettowarenwert1: Decimal('-45.000')>, 
# <summe_rabatte:Decimal('0.000')>, 
# <skontofaehig: Decimal('0.000')>, 
# <summe_zuschlaege: Decimal('0.000')>, 
# <steuerpflichtig1: Decimal('-45.000')>, 
# <kopfrabatt1_prozent: Decimal('0.000')>, 
# <steuerpflichtig USt 2: '000000000000000+'>,
# <kopfrabatt2_prozent: Decimal('0.000')>,
# <skontoabzug: Decimal('1.610')>,
# <kopfrabatt1_vorzeichen: '+'>, 
# <kopfrabatt2_vorzeichen: '+'>, 
# <kopfrabatt1: Decimal('0.000')>, 
# <versandkosten1: Decimal('0.000')>, 
# <mehrwertsteuer: Decimal('-8.550')>, 
# <kopfrabatt2: Decimal('0.000')>,
# <steuerbetrag1: Decimal('-8.550')>, 
# <TxtSlKopfrabatt1: ''>, 
# <TxtSlKopfrabatt2: ''>, 
# <KopfrabattUSt1: Decimal('0.000')>>

        rechnungsnr=str(f1.rechnungsnr)
        if not rechnungsnr.startswith('RG'):
            rechnungsnr = 'RG%s' % rechnungsnr
        self.guid = rechnungsnr
        
        kopf = dict(
            guid=self.guid,
            iln=f1.iln_rechnungsempfaenger,
            kundennr=f1.rechnungsempfaenger,
            name1=fa.rechnung_name1,
            name2=fa.rechnung_name2,
            name3=fa.rechnung_name3,
            strasse=fa.rechnung_strasse,
            land=fa.rechnung_land, 
            plz=fa.rechnung_plz, 
            ort=fa.rechnung_ort, 
            rechnungsnr=str(f1.rechnungsnr),
            auftragsnr=f1.auftragsnr,
            kundenauftragsnr=f1.kundenbestellnummer,
            # <kundenbestelldatum: datetime.date(2008, 12, 16)>
            auftragsdatum=f1.auftragsdatum,
            rechnungsdatum=f1.rechnungsdatum,
            leistungsdatum=f1.liefertermin,
            infotext_kunde=' '.join([f1.eigene_iln_beim_kunden.strip(), f1.lieferantennummer.strip(), f1.ustdid_rechnungsempfaenger.strip(), str(f1.kundenbestelldatum)]), # was ist mit auftragstexten?

            versandkosten = f9.versandkosten1,
            warenwert = abs(f9.warenwert),
            abschlag_prozent=f9.kopfrabatt1_prozent + f9.kopfrabatt2_prozent,
            # summe_zuschlaege=f9.summe_zuschlaege,
            rechnungsbetrag='?5',
            rechnung_steuranteil=f9.mehrwertsteuer,
            steuer_prozent='?4',
            zu_zahlen=abs(f9.gesamtbetrag),

            zahlungstage=f1.nettotage,
            zahlungsdatum='?3',

            skonto_prozent = f1.skonto1,
            skontotage = f1.skontotage1,
            
            zu_zahlen_bei_skonto=abs(f9.gesamtbetrag)-abs(f1.skontobetrag1_ust1),
            valutatage=f1.valutatage,
            valutadatum=f1.valutadatum,
            skontofaehig=f9.skontofaehig,
            steuerpflichtig1=f9.steuerpflichtig1,
            skontoabzug='?1',
            nettowarenwert1=f9.nettowarenwert1,
            )
        
        kopf['hint'] = dict(
            abschlag=f9.summe_rabatte, # = f9.kopfrabatt1 + f9.kopfrabatt2,
            zahlungsdatum=f1.nettodatum,
            skontodatum = f1.skontodatum1,
            skontobetrag = abs(f1.skontobetrag1_ust1),
            # rechnungsbetrag_bei_skonto=f9.skontoabzug, # excl. skonto
            rechung_steueranteil_bei_skonto='?6',
        )
        
        kopf['lieferadresse'] = dict(
            kundennr=f2.warenempfaenger,
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

        # Gutschrift oder Rechnung?
        if f1.belegart.lstrip('0') in ['380', '84']:
            kopf['transaktionsart'] = 'Rechnung'
        elif f1.belegart.lstrip('0') in ['381', '83']:
            kopf['transaktionsart'] = 'Gutschrift'
        else:
            raise ValueError("%s: Belegart %s unbekannt" % (rechnungsnr, f1.belegart.lstrip('0')))

        if f1.lieferscheinnr and int(f1.lieferscheinnr):
            kopf['lieferscheinnr'] = f1.lieferscheinnr

        #rec900.steuerpflichtiger_betrag = abs(f9.steuerpflichtig1)
        #rec900.mwst_gesamtbetrag = abs(f9.mehrwertsteuer)
        #rec900.skontofaehiger_betrag = abs(f9.skontofaehig)
        #rec900.zu_und_abschlage = -1 * f9.summe_rabatte
        #rec900.zu_und_abschlage = f9.summe_zuschlaege - f9.summe_rabatte + f9.versandkosten1
        #if self.is_credit:
        #    rec900.zu_und_abschlage *= -1
    


        # FK = versandbedingungen und so
        # FX = kopfrabatt
        # FE = lieferbedingungen
        zeilen = []
        for k in ['FK', 'FE', 'FX', 'FV', 'FL', 'FN']:
            if k in invoice_records:
                zeile = []
                for i in range(1,9):
                     text = getattr(invoice_records[k], 'textzeile%d' % i).strip()
                     if text:
                         zeile.append(text.strip())
                if zeile:
                    zeilen.append(' '.join(zeile))
        if zeilen:
            kopf['infotext_kunde'] = '\n'.join(zeilen).strip()

        if f1.ust2_fuer_skonto:
            print f1.ust2_fuer_skonto, kopf
            raise ValueError("%s hat einen zweiten Stuerersatz - das ist nicht unterstützt" % (rechnungsnr))
        if f1.skontodatum2 or f1.skontotage2 or f1.skonto2:
            print kopf
            raise ValueError("%s hat 2. Skontosatz - das ist nicht unterstützt" % (rechnungsnr))
        if f1.waehrung != 'EUR':
            print kopf
            raise ValueError("%s ist nicht in EURO - das ist nicht unterstützt" % (rechnungsnr))

        return kopf

    def _convert_invoice_position(self, position_records):
        """Converts SoftM F3 & F4 records to orderline"""

        f3 = position_records['F3']
        f4 = position_records['F4'] # Positionsrabatte

        line = dict(
            guid="%s-%s" % (self.guid, f3.positionsnr),
            menge=f3.menge,
            artnr=f3.artnr,
            kundenartnr=f3.artnr_kunde,
            name=f3.artikelbezeichnung.strip(),
            infotext_kunde=' '.join([f3.artnr_kunde.strip(),
                                     f3.artikelbezeichnung_kunde.strip()]).strip(),
            einzelpreis = abs(f3.verkaufspreis),
            positionswert = abs(f3.wert_netto), # - incl rabatte?
        )
        
        if f3.ean and int(f3.ean):
            line['ean']=f3.ean
        
        # FP = positionstext
        # FR = positionsrabatttext
        zeilen = []
        for k in [u'FP', u'FR']:
            if k in position_records.keys():
                zeile = []
                for i in range(1,9):
                    text = getattr(position_records[k], 'textzeile%d' % i).strip()
                    if text:
                        zeilen.append(text)
                if zeile:
                    zeilen.append(' '.join(zeile))
        if zeilen:
            line['infotext_kunde'] = ' '.join([line['infotext_kunde']] + zeilen).strip()

        if f3.wert_netto != f3.wert_brutto:
            print line
            raise ValueError("%s hat Positionsrabatt - das ist nicht unterstützt" % (rechnungsnr))
        return line

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

        # create sub-part of whole invoice (list) that represents one single invoice
        invoices = []
        while tmp_softm_record_list:
            # slice of segment until the next F1
            invoice = [tmp_softm_record_list.pop(0)]
            while tmp_softm_record_list and tmp_softm_record_list[0] and tmp_softm_record_list[0][0] != 'F1':
                invoice.append(tmp_softm_record_list.pop(0))

            # process invoice
            invoices.append(self._convert_invoice(invoice))
        return invoices

    def convert(self, data):
        """Parse INVOICE file and save result in workfile."""

        # If we handle a collection of single invoices here, we have to split them into pieces and
        # provide a header for them.

        self.softm_record_list = edilib.softm.structure.parse_to_objects(data.split('\n'))
        return self._convert_invoices()


def main():
    converter = SoftMConverter()
    converter.convert('/Users/md/code2/git/DeadTrees/workdir/backup/INVOIC/RG00994.TXT')
    for f in sorted(os.listdir('/Users/md/code2/git/DeadTrees/workdir/backup/INVOIC/'), reverse=True):
        if not f.startswith('RG'):
            continue
        # print f, os.path.join('/Users/md/code2/git/DeadTrees/workdir/backup/INVOIC/', f)
        converter = SoftMConverter()
        converter.convert(os.path.join('/Users/md/code2/git/DeadTrees/workdir/backup/INVOIC/', f))

# RG821130 ist nen tolles Beispiel für ne gutschrift

if __name__ == '__main__':
    main()
