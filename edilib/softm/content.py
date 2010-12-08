#!/usr/bin/env python
# encoding: utf-8
"""
convert SoftM INVOICE to VerySimpleInvoiceProtocol.

Leider wird die EDI-Invoice Schnittstelle von SoftM nur unvollständig versorgt. So fehlen bei Aufträgen mit
abweichender Lieferadresse nicht nur die Lieferadresse, sondern auch die Auftragsnummer und das
Leistungsdatum.

Created by Maximillian Dornseif on 2008-10-31.
Copyright (c) 2008, 2010 HUDORA. All rights reserved.
"""

from decimal import Decimal
import codecs
import datetime
import edilib.softm.structure
import os
import os.path
import shutil
import husoftm.tools
import sys


class SoftMConverter(object):
#     """Base class for the various SoftM files"""
#     pass
#class SoftMInvoiceConverter(SoftMConverter):
    """Converts SoftM INVOICE files to very Simple Invoice Protocol."""

    def __init__(self):
        # super(self, SoftMInvoiceConverter).__init__()
        self.interchangeheader = {}
        self.invoicelistfooter = {}
        self.invoices = []
        self.softm_record_list = None # whole set of records from SoftM

    def _convert_invoice_head(self, invoice_records):
        """Converts SoftM F1 and varius others."""

        # needed entries from SoftM
        fa = invoice_records['FA']
        f1 = invoice_records['F1']
        f3 = invoice_records['F3']
        f9 = invoice_records['F9']

        # erfasst_von - Name der Person oder des Prozesses, der den Auftrag in das System eingespeist hat.
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


# <gesamtbetrag: Decimal('-53.550')>,
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
# <mehrwertsteuer: Decimal('-8.550')>,
# <kopfrabatt2: Decimal('0.000')>,
# <TxtSlKopfrabatt1: ''>,
# <TxtSlKopfrabatt2: ''>,
# <KopfrabattUSt1: Decimal('0.000')>>

        kundennr = str(f1.rechnungsempfaenger)
        if not kundennr.startswith('SC'):
            kundennr = 'SC%s' % kundennr

        rechnungsnr=str(f1.rechnungsnr)
        if not rechnungsnr.startswith('RG'):
            rechnungsnr = 'RG%s' % rechnungsnr
        self.guid = rechnungsnr

        auftragsnr = str(f1.auftragsnr)
        if auftragsnr and not auftragsnr.startswith('SO'):
            auftragsnr = 'SO%s' % auftragsnr.lstrip('SO')

        kopf = dict(
            # absenderadresse
            # erfasst_von
            guid=self.guid,
            kundennr=kundennr,
            name1=fa.rechnung_name1,
            name2=fa.rechnung_name2,
            name3=fa.rechnung_name3,
            strasse=fa.rechnung_strasse,
            land=husoftm.tools.land2iso(fa.rechnung_land),
            plz=fa.rechnung_plz,
            ort=fa.rechnung_ort,
            rechnungsnr=rechnungsnr,
            auftragsnr=auftragsnr,
            kundenauftragsnr=f1.kundenbestellnummer,
            # <kundenbestelldatum: datetime.date(2008, 12, 16)>
            auftragsdatum=f1.auftragsdatum,
            rechnungsdatum=f1.rechnungsdatum,
            leistungsdatum=f1.liefertermin,
            infotext_kunde=' '.join([str(x) for x in (#f1.eigene_iln_beim_kunden.strip(),
                                                      f1.lieferantennummer.strip(),
                                                      ) if x]),
            versandkosten = int(f9.versandkosten1*100),
            warenwert = int(abs(f9.warenwert)*100), # in cent

            # summe_zuschlaege=f9.summe_zuschlaege,
            # rechnungsbetrag='?5', - Rechnungsbetrag ohne Steuer und Abzüge als String mit zwei Nachkommastellen. Entspricht warenwert - Abschlag
            rechnung_steuranteil=int(f9.mehrwertsteuer*100),
            steuer_prozent="19",
            # Der Betrag, denn der Kund eZahlen muss - es sei denn, er zieht Skonto
            zu_zahlen=int(f9.gesamtbetrag*100), # in cent
            # Rechnungsbetrag ohne Steuer und Abz<C3><BC>ge als String mit zwei Nachkommastellen.
            # Entspricht warenwert - abschlag oder zu_zahlen - rechnung_steuranteil
            rechnungsbetrag=int((f9.gesamtbetrag-f9.mehrwertsteuer)*100),

            zahlungstage=f1.nettotage,
            #skontofaehig=int(abs(f9.skontofaehig)*100),  # TODO: in cent?
            #steuerpflichtig1=int(abs(f9.steuerpflichtig1)*100), # TODO: in cent?
            #skontoabzug=f9.skontoabzug,
            )

        kopf['hint'] = dict(
            zahlungsdatum=f1.nettodatum,
            # rechnungsbetrag_bei_skonto=, # excl. skonto
            # debug
            #skontofaehig_ust1=f1.skontofaehig_ust1,
            #skonto1=f1.skonto1,
            #skontobetrag1_ust1=f1.skontobetrag1_ust1,
            steuernr_kunde=str(f1.ustdid_rechnungsempfaenger or f1.steuernummer),
            steuernr_lieferant=str(f1.ustdid_absender),
        )

        if f1.valutatage:
            kopf['valutatage'] = f1.valutatage,
            kopf['valutadatum'] = f1.valutadatum

        if f9.summe_rabatte:
            text1 = f9.kopfrabatt1_text.strip()
            if text1 and f9.kopfrabatt1_prozent:
                text1 = "%s (%s %%)" % (text1, f9.kopfrabatt1_prozent)
            text2 = f9.kopfrabatt2_text.strip()
            if text2 and f9.kopfrabatt2_prozent:
                text2 = "%s (%s %%)" % (text2, f9.kopfrabatt2_prozent)
            kopf['abschlag_text'] = ', '.join([x for x in [text1, text2] if x])
            kopf['abschlag'] = int(f9.summe_rabatte*100) # = f9.kopfrabatt1 + f9.kopfrabatt2, in cent
            kopf['hint']['abschlag_prozent'] = "%.2f" % float(str(f9.kopfrabatt1_prozent+f9.kopfrabatt2_prozent))
            # 'kopfrabatt1_vorzeichen', fieldclass=FixedField, default='+'),
            # 'kopfrabatt2_vorzeichen', fieldclass=FixedField, default='+'),

        if f1.skontotage1:
            kopf['skontotage'] = f1.skontotage1
            kopf['skonto_prozent'] = f1.skonto1
            # in cent
            kopf['zu_zahlen_bei_skonto'] = int((f9.gesamtbetrag-f1.skontobetrag1_ust1)*100)
            kopf['hint']['skontodatum'] = f1.skontodatum1
            kopf['hint']['skontobetrag'] = int(abs(f9.skontoabzug)*100)
            kopf['hint']['steueranteil_bei_skonto'] = kopf['zu_zahlen_bei_skonto']-int(kopf['zu_zahlen_bei_skonto']/1.19)

        if 'F2' in invoice_records:
            # manchmal wird KEINE Lieferadresse mitgegeben
            f2 = invoice_records['F2']

            warenempfaenger = str(f2.warenempfaenger)
            if not warenempfaenger.startswith('SC'):
                warenempfaenger = 'SC%s' % warenempfaenger
            
            kopf['lieferadresse'] = dict(
                kundennr=warenempfaenger,
                name1=f2.liefer_name1,
                name2=f2.liefer_name2,
                name3=f2.liefer_name3,
                strasse=f2.liefer_strasse,
                plz=f2.liefer_plz,
                ort=f2.liefer_ort,
                land=husoftm.tools.land2iso(f2.liefer_land),  # fixup to iso country code
                #rec119_lieferaddr.internepartnerid = f2.warenempfaenger
            )
            
            if f2.liefer_iln and f2.liefer_iln != '0':
                kopf['lieferadresse']['iln'] = str(f2.liefer_iln)
            elif f2.iln_warenempfaenger and f2.iln_warenempfaenger != '0':
                kopf['lieferadresse']['iln'] = str(f2.iln_warenempfaenger)
            elif f2.besteller_iln and f2.besteller_iln != '0':
                kopf['lieferadresse']['iln'] = str(f2.besteller_iln)

        if f1.iln_rechnungsempfaenger and f1.iln_rechnungsempfaenger != '0':
            kopf['iln'] = str(f1.iln_rechnungsempfaenger)

        # Gutschrift oder Rechnung?
        if f1.belegart.lstrip('0') in ['380', '84']:
            kopf['transaktionsart'] = 'Rechnung'
        elif f1.belegart.lstrip('0') in ['381', '83']:
            kopf['transaktionsart'] = 'Gutschrift'
        else:
            raise ValueError("%s: Belegart %s unbekannt" % (rechnungsnr, f1.belegart.lstrip('0')))

        if f1.lieferscheinnr and int(f1.lieferscheinnr):
            kopf['lieferscheinnr'] = str(f1.lieferscheinnr)

        #rec900.steuerpflichtiger_betrag = abs(f9.steuerpflichtig1)
        #rec900.mwst_gesamtbetrag = abs(f9.mehrwertsteuer)
        #rec900.skontofaehiger_betrag = abs(f9.skontofaehig)

        # FK = versandbedingungen und so
        # FX = kopfrabatt
        # FE = lieferbedingungen
        zeilen = []
        for k in ['FK', 'FE', 'FX', 'FV', 'FL', 'FN']:
            if k in invoice_records:
                zeile = []
                for i in range(1, 9):
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

        # ungenutzte Felder entfernen
        for k in kopf.keys():
            if kopf[k] == '':
                del kopf[k]
        # ungenutzte Felder entfernen
        for k in kopf['hint'].keys():
            if kopf['hint'][k] == '':
                del kopf['hint'][k]
        kopf['_parsed_at'] = datetime.datetime.now()
        return kopf

    def _convert_invoice_position(self, position_records):
        """Converts SoftM F3 & F4 records to orderline"""

        f3 = position_records['F3']
        f4 = position_records['F4'] # Positionsrabatte

        line = dict(
            guid="%s-%s" % (self.guid, f3.positionsnr),
            menge=int(f3.menge),
            artnr=f3.artnr,
            kundenartnr=f3.artnr_kunde,
            name=f3.artikelbezeichnung.strip(),
            infotext_kunde=[f3.artikelbezeichnung_kunde],
            einzelpreis=int(f3.verkaufspreis*100),
            warenwert=int(f3.wert_netto*100),
            zu_zahlen=int(f3.wert_brutto*100),
            abschlag=-1*int(f4.positionsrabatt_gesamt*100)
        )

        if f3.ean and int(f3.ean):
            line['ean']=f3.ean

        if f4.textschluessel3:
            raise ValueError("%s hat mehr als 2 Positionsrabatte - das ist nicht unterstützt" % (rechnungsnr))

        rabattep = {} # %
        rabatteb = {} # Betraege
        rabattet = {} # Texte
        abschlagtext = []
        # FR = positionsrabatttext
        for i in range(1,9):
            if 'FR' in position_records.keys():
                rabattet[i] = getattr(position_records['FR'], 'textzeile%d' % i).strip()
            if getattr(f4, 'rabattkennzeichen%d' % i) == '0':
                rabattep[i] = getattr(f4, 'positionsrabatt%dp' % i)
                if rabattep[i]:
                     abschlagtext.append("%s: %s %%" % (rabattet[i], rabattep[i]))
            elif getattr(f4, 'rabattkennzeichen%d' % i) == '1':
                rabatteb[i] = getattr(f4, 'rabattbetrag%d' % i)
                if rabatteb[i]:
                    abschlagtext.append("%s: %.2f Euro" % (rabattet[i], -1 * float(str(rabatteb[i]))))
            else:
                raise ValueError("%s hat nicht unterstütztes Rabattkennzeichen" % (rechnungsnr))
        line['abschlagtext'] = ', '.join(abschlagtext)

        # FP = positionstext
        for k in [u'FP']:
            if k in position_records.keys():
                zeile = []
                for i in range(1, 9):
                    text = getattr(position_records[k], 'textzeile%d' % i).strip()
                    if text:
                        zeile.append(text)
                if zeile:
                    line['infotext_kunde'].append(' '.join(zeile).strip())

        line['infotext_kunde'] = ', '.join([x for x in line['infotext_kunde'] if x])

        # ungenutzte Felder entfernen
        for k in line.keys():
            if line[k] == '':
                del line[k]
        return line

    def _convert_invoice(self, softm_record_slice):
        """Handles a SoftM invoice. Works on a slice of an INVOICE list, which
        contains the relavant stuff for the actual invoice."""

        softm_records = dict(softm_record_slice)
        kopf = self._convert_invoice_head(softm_records)

        # the now we have to extract the per invoice records from softm_record_list
        # every position starts with a F3 record
        record_iter = iter(softm_record_slice)

        # remove everything until we hit the first F3
        for key, val in record_iter:
            if key == 'F3':
                break
        if key != 'F3':
            raise RuntimeError('Invalid invoice data')

        # process positions
        kopf['orderlines'] = []
        while record_iter and key == "F3":

            # slice of segment until the next F3
            position = [(key, val)]
            for key, val in record_iter:
                if key == 'F3':
                    break
                position.append((key, val))

            # process position
            kopf['orderlines'].append(self._convert_invoice_position(dict(position)))
        return kopf

    def _convert_invoices(self):
        """Handles the invoices of a SoftM invoice list."""

        # now we have to extract the per invoice records from self.softm_record_list
        # every position starts with a F1 record
        record_iter = iter(self.softm_record_list)

        # remove everything until we hit the first F1
        for key, val in record_iter:
            if key == 'F1':
                break

        # create sub-part of whole invoice (list) that represents one single invoice
        if key != 'F1':
            raise RuntimeError('Invalid invoice data: no F1 record')

        invoices = []
        while record_iter and key == "F1":
            # slice of segment until the next F1
            invoice = [(key, val)]
            for key, val in record_iter:
                if key == 'F1':
                    break
                invoice.append((key, val))


            # process invoice
            invoices.append(self._convert_invoice(invoice))
        return invoices

    def _convert_interchangehead(self):
        """Handles file header information."""

        xh = None
        for key, entry in self.softm_record_list:
            if 'XH' == key:
                xh = entry
                break

        if not xh:
            raise RuntimeError('Missing file header (XH) in data.')

        return dict(
            technischer_rechnungsempfaenger=xh.dfue_partner,
            erstellungsdatum=xh.erstellungs_datum,
            erstellungszeit=xh.erstellungs_zeit[:4], # remove seconds
            anwendungsreferenz=xh.umgebung,
            testkennzeichen=xh.testkennzeichen)


    def _convert_invoicelistfooter(self):
        """Handle R1, R2, R3 entries of invoice lists.

        R1   Rechnungsliste-Verbandsdaten                 1-mal pro Verband
        R2   Rechnungsliste-Position (= Rechnungssumme)   1-mal pro Rechnung
        R3   Rechnungsliste-Summe                         1-mal pro Kopfdaten (R1)
        """

        softm_record_dict = dict(self.softm_record_list)
        r1 = softm_record_dict.get('R1', None)
        r3 = softm_record_dict.get('R3', None)
        r2 = [x[1] for x in self.softm_record_list if x[0] == 'R2']

        if not all((r1, r2, r3)):
            if any((r1, r2, r3)):
                raise RuntimeError("Data seems to be a invoice list with missing information.")
            return {}

        return dict(
            rechnungslistennr=r2[-1].listennr,
            rechnungslistendatum=r2[-1].listendatum,
            empfaenger_iln=r1.verband_iln,
            lieferantennr=r1.lieferantennr_verband,
            rechnungslistenendbetrag=r3.summe,
            mwst=sum([rec.mwst for rec in r2]),
            steuerpflichtiger_betrag=sum([rec.warenwert for rec in r2]))
    
    def convert(self, data):
        """Parse INVOICE file and save result in workfile."""

        # If we handle a collection of single invoices here, we have to split them into pieces and
        # provide a header for them.

        # call init to clean this instance of SoftMConverter if this function is used multiple times
        self.__init__()

        # parse invoice(list)
        self.softm_record_list = edilib.softm.structure.parse_to_objects(data.split('\n'))
        self.interchangeheader = self._convert_interchangehead()
        self.invoices = self._convert_invoices()
        self.invoicelistfooter = self._convert_invoicelistfooter()

        # for invoice lists, add the invoice recipient to every single invoice
        if self.invoicelistfooter:
            for invoice in self.invoices:
                invoice['rechnungsadresse'] = {'iln': self.interchangeheader['technischer_rechnungsempfaenger']}

        return self.invoices


class SoftMABConverter(SoftMConverter):
    
    def convert_header(self, records):
        """Auftragskopf konvertieren"""
        
        a1 = records['A1']
        a2 = records['A2']
        
        kundennr = str(a1.rechnungsempfaenger)
        if not kundennr.startswith('SC'):
            tmp = kundennr.split()
            kundennr = 'SC%s' % int(tmp[-1])

        auftragsnr = str(a1.auftragsnr)
        if auftragsnr and not auftragsnr.startswith('SO'):
            auftragsnr = 'SO%d' % int(auftragsnr)
        
        self.guid = auftragsnr
        
        kopf = dict(
            # absenderadresse
            # erfasst_von
            guid=self.guid,
            iln=a1.iln_rechnungsempfaenger,
            kundennr=kundennr,
            name1=a2.name1,
            name2=a2.name2,
            name3=a2.name3,
            strasse=a2.strasse,
            land=husoftm.tools.land2iso(a2.land),
            plz=a2.plz,
            ort=a2.ort,
            auftragsnr=auftragsnr,
        )
                
        kopf['_parsed_at'] = datetime.datetime.now()
        return kopf
    
    def convert_position(self, records):
        """Konvertiere Auftragsposition"""
        a3 = records['A3']
        pos = dict(guid='%s-%s' % (self.guid, a3.position),
                   posnr=int(a3.position),
                   artnr=a3.artnr,
                   ean=a3.ean,
                   infotext_kunde=a3.bezeichnung,
                   menge=int(a3.menge) / 1000)
        
        # TODO
        if 'A4' in records:
            pass
        if 'AP' in records:
            pass
        
        return pos        
        
    def convert(self, data):
        """Parse ORDRSP file."""

        records, positions = {}, []
        position = None
        record_list = edilib.softm.structure.parse_to_objects(data.split('\n'))        
        for key, record in record_list:
            if key in ('XH', 'A1', 'A2', 'A8', 'A9'):
                records[key] = record
            elif key in ('AV', 'AL', 'AN', 'AK'):
                pass
            elif key == 'A3':
                if position:
                    positions.append(position)
                position = {'A3': record}
            else:
                position[key] = record
        
        if position:
            positions.append(position)

        # For legacy code from base class
        self.softm_record_list = record_list
        self.interchangeheader = self._convert_interchangehead()

        # Auftrags(-bestaetigungs)kopfs
        ab = self.convert_header(records)
        ab['positions'] = [self.convert_position(position) for position in positions]
        return ab


def main():
    converter = SoftMABConverter()
    converter.convert(open('../workdir/archive/INVOIC/AB00049_ORIGINAL.txt').read())
    
    # converter = SoftMABConverter()
    # converter.convert(open('RG01490.TXT').read())
    
    #for f in sorted(os.listdir('/Users/md/code2/git/DeadTrees/workdir/backup/INVOIC/'), reverse=True):
    #    if not f.startswith('RG'):
    #        continue
    #    # print f, os.path.join('/Users/md/code2/git/DeadTrees/workdir/backup/INVOIC/', f)
    #    converter = SoftMConverter()
    #    converter.convert(os.path.join('/Users/md/code2/git/DeadTrees/workdir/backup/INVOIC/', f))

# RG821130 ist nen tolles Beispiel für ne Gutschrift

if __name__ == '__main__':
    main()
