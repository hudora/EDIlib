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

import datetime
import edilib.softm.structure
import huTools.monetary
import husoftm.tools
import logging
import os


def get_text(records, separator=' '):
    """Konkateniet Textzeilen aus SoftM-Textsatz und gib eine Liste von Texten zurück."""
    # Manchmal ist `record` eine Liste und manchmal direkt eine
    # `edilib.softm.structure.Struct` - wir müssen hier mit beidem umgehen können.
    if not isinstance(records, list):
        records = [records]
    ret = []
    for record in records:
        text = separator.join(getattr(record, 'textzeile%d' % (i + 1)) for i in range(8))
        ret.append(text.strip())
    return ret


class SoftMConverter(object):
    """Base class for the various SoftM filetypes"""

    file_records = ['XH']
    position_prefix = ''

    def get_recordname(self, recordtype):
        """Convenience Method for resolving record name"""
        return '%s%s' % (self.position_prefix, recordtype)

    @property
    def position_key(self):
        """Name des Records für Positionen"""
        return self.get_recordname('3')

    def parse(self, data):
        """Parse input data into records

        Returns a list of (dict of records and a list of position)
        """

        def add(parent, key, record):
            """
            Füge Record in dict ein

            Wenn der Schlüssel schon exisitert,
            werden die Records als Liste gespeichert.
            """

            if key in parent:
                if isinstance(parent[key], list):
                    parent[key].append(record)
                else:
                    parent[key] = [parent[key], record]
            else:
                parent[key] = record

        # Datensätze, die einmal pro Übertragungsdatei auftreten
        # diese werden in alle Dateien kopiert
        file_records = {}

        # übertragene Datensätze
        files = []

        # rohe Datensätze aus der Eingagsdatei
        record_list = edilib.softm.structure.parse_to_objects(data.split('\n'))

        records, position = None, None
        positions = []
        for key, record in record_list:
            if key in self.file_records:
                add(file_records, key, record)
            elif key == self.get_recordname('1'):
                # Beginn neuer Datei: Lege neue Datei an und kopiere file_records
                if position:
                    positions.append(position)
                if records:
                    files.append((records, positions))
                positions = []
                position = None
                records = dict(file_records)
                records[key] = record
            elif key in self.header_records:  # Datensatz, der ein- oder n-mal pro Header auftritt
                add(records, key, record)
            elif key == self.position_key:  # Beginn neuer Position
                if position:
                    positions.append(position)
                position = {key: record}
            elif key in self.position_records:
                if not position:
                    raise RuntimeError(u'Record %s without %s Record' % (key, self.position_key))
                add(position, key, record)
            else:
                raise RuntimeError(u'Unknown record: %s' % key)

        if position:
            positions.append(position)

        files.append((records, positions))
        return files

    def convert_interchangeheader(self, records):
        """Convert file interchange header information."""

        if not 'XH' in records:
            raise RuntimeError('Missing file header (XH) in data.')
        record = records['XH']
        return dict(technischer_rechnungsempfaenger=record.dfue_partner,
                    erstellungsdatum=record.erstellungs_datum,
                    erstellungszeit=record.erstellungs_zeit[:4],  # remove seconds
                    anwendungsreferenz=record.umgebung,
                    testkennzeichen=record.testkennzeichen)

    def convert_position(self, guid, position_records):
        """Converts SoftM position record to orderline"""

        position = position_records[self.position_key]
        rabatt = position_records[self.get_recordname('4')]

        line = dict(
            guid="%s-%s" % (guid, position.positionsnr),
            menge=int(position.menge),
            artnr=position.artnr,
            kundenartnr=position.artnr_kunde,
            name=position.artikelbezeichnung.strip(),
            infotext_kunde=[position.artikelbezeichnung_kunde],
            einzelpreis=huTools.monetary.euro_to_cent(position.verkaufspreis),
            warenwert=huTools.monetary.euro_to_cent(position.wert_netto),
            zu_zahlen=huTools.monetary.euro_to_cent(position.wert_brutto),
            abschlag=huTools.monetary.euro_to_cent(-1 * rabatt.positionsrabatt_gesamt),
            ursprungsland=position.ursprungsland,
            #steuersatz=position.steuersatz,
            #steuerbetrag=position.steuerbetrag,
        )

        # Füge EAN ein, wenn nicht leerer String oder nur aus '0' bestehend
        if position.ean and int(position.ean):
            line['ean'] = position.ean

        # Den Liefertermin pro Position gibt es (noch) in Auftragsbestätigungen, aber nicht in Rechnungen
        if hasattr(position, 'liefertermin'):
            line['liefertermin'] = position.liefertermin

        # Komponentenbezogene Daten gibt es in Auftragsbestätigungen, aber nicht in Rechnungen
        if hasattr(position, 'anzahl_komponenten'):
            line['anzahl_komponenten'] = position.anzahl_komponenten
        if hasattr(position, 'komponentenaufloesung'):
            line['komponentenaufloesung'] = position.komponentenaufloesung

        if rabatt.textschluessel3:
            raise RuntimeError(u"%s hat mehr als 2 Positionsrabatte" % line['guid'])

        rabattep = {}  # Rabatte in %
        rabatteb = {}  # Rabattbeträge
        rabattet = {}  # Rabatttexte

        abschlagtext = []

        # Bearbeite die Positionsrabatte
        # Es kann bis zu acht Rabatte geben - unterstützt werden aber nur zwei!
        # Record '?R' ist der Positionsrabatttext (den es wohl nur bei Rechnungen gibt)
        key = self.get_recordname('R')
        for i in range(1, 9):
            # Speichere Rabatt-Text aus Positionsrabatttext-Record
            if key in position_records.keys():
                rabattet[i] = getattr(position_records[key], 'textzeile%d' % i).strip()

            # Wenn Rabattkennzeichen gesetzt ist, füge Rabatt-Text ein, falls vorhanden
            # Es werden nur die Rabattkennzeichen '0' und '1' unterstützt
            rabattkennzeichen = getattr(rabatt, 'rabattkennzeichen%d' % i)

            if rabattkennzeichen == '0':  # '0' ist "Rabatt in Prozent"
                rabattep[i] = getattr(rabatt, 'positionsrabatt%dp' % i)
                if rabattep[i]:
                    abschlagtext.append("%s: %s %%" % (rabattet.get(i, '*unknown*'), rabattep[i]))
            elif rabattkennzeichen == '1':  # '1' ist Rabatt als Betrag
                rabatteb[i] = getattr(rabatt, 'rabattbetrag%d' % i)
                if rabatteb[i]:
                    abschlagtext.append("%s: %.2f Euro" % (rabattet.get(i, '*unknown'), -1 * float(str(rabatteb[i]))))
            else:
                raise ValueError(u"%s: nicht unterstütztes Rabattkennzeichen: %r" % (line['guid'], rabattkennzeichen))

        line['abschlagtext'] = ', '.join(abschlagtext)

        # Füge Positionstexte an 'infotext_kunde'
        # Record '?P' ist der Positionstext
        key = self.get_recordname('P')
        if key in position_records.keys():
            line['infotext_kunde'].extend(get_text(position_records[key]))

        # die restlichen Felder hinzufügen, d.h. alle außer ?3, ?4 und ?P (und ?R)
        # Positionszuschläge: 'A5'
        # Set-Komponenten: 'A6'

        if self.get_recordname('5') in position_records:
            print 'HAS %s!' % self.get_recordname('5')

        # Texte für Set-Komponenten
        if self.get_recordname('6') in position_records:
            records = position_records[self.get_recordname('6')]
            if not isinstance(records, list):
                records = [records]
            for record in records:
                set_text = '%d x %s  -  %s' % (record.menge, record.artnr, record.bezeichnung)
                line['infotext_kunde'].append(set_text)

        line['infotext_kunde'] = '\n'.join([x for x in line['infotext_kunde'] if x])

        # ungenutzte Felder entfernen
        for k in line.keys():
            if line[k] == '':
                del line[k]
        return line


class SoftMInvoiceConverter(SoftMConverter):
    """Converts SoftM INVOICE files to very Simple Invoice Protocol."""

    position_prefix = 'F'
    file_records = ['XH', 'R1', 'R2', 'R3']
    header_records = ['F1', 'F2', 'FV', 'FL', 'FK', 'F8', 'F9', 'FX', 'FA', 'FE']
    position_records = ['F3', 'F4', 'FR', 'FP', 'F5', 'F6']

    def convert_header(self, invoice_records):
        """Converts SoftM F1 and varius others."""

        # needed entries from SoftM
        fa = invoice_records['FA']
        f1 = invoice_records['F1']
        f9 = invoice_records['F9']

        kundennr = str(f1.rechnungsempfaenger)
        if not kundennr.startswith('SC'):
            kundennr = 'SC%s' % kundennr

        rechnungsnr = str(f1.rechnungsnr)
        if not rechnungsnr.startswith('RG'):
            rechnungsnr = 'RG%s' % rechnungsnr
        guid = rechnungsnr

        auftragsnr = str(f1.auftragsnr)
        if auftragsnr and not auftragsnr.startswith('SO'):
            auftragsnr = 'SO%s' % auftragsnr.lstrip('SO')

        kopf = dict(
            # absenderadresse
            # erfasst_von
            guid=guid,
            waehrung=f1.waehrung,
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
            infotext_kunde=str(f1.lieferantennummer).strip(),

            versandkosten=huTools.monetary.euro_to_cent(f9.versandkosten1),
            warenwert=huTools.monetary.euro_to_cent(abs(f9.warenwert)),

            # summe_zuschlaege=f9.summe_zuschlaege,
            # Rechnungsbetrag ohne Steuer und Abzüge als String mit zwei Nachkommastellen.
            # Entspricht Warenwert - Abschlag
            # rechnungsbetrag='?5',
            rechnung_steueranteil=huTools.monetary.euro_to_cent(f9.mehrwertsteuer),
            steuer_prozent="19",
            # Der Betrag, denn der Kunde Zahlen muss - es sei denn, er zieht Skonto
            zu_zahlen=huTools.monetary.euro_to_cent(f9.gesamtbetrag),
            # Rechnungsbetrag ohne Steuer und Abz<C3><BC>ge als String mit zwei Nachkommastellen.
            # Entspricht warenwert - abschlag oder zu_zahlen - rechnung_steueranteil
            rechnungsbetrag=huTools.monetary.euro_to_cent((f9.gesamtbetrag - f9.mehrwertsteuer)),

            zahlungstage=f1.nettotage,
            #skontofaehig=huTools.monetary.euro_to_cent(abs(f9.skontofaehig)),
            #steuerpflichtig1=huTools.monetary.euro_to_cent(abs(f9.steuerpflichtig1)),
            #skontoabzug=f9.skontoabzug,
            )

        kopf['hint'] = dict(
            zahlungsdatum=f1.nettodatum,
            # rechnungsbetrag_bei_skonto=,  # excl. skonto
            # debug
            #skontofaehig_ust1=f1.skontofaehig_ust1,
            #skonto1=f1.skonto1,
            #skontobetrag1_ust1=f1.skontobetrag1_ust1,
            steuernr_kunde=str(f1.ustdid_rechnungsempfaenger),
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
            kopf['abschlag'] = huTools.monetary.euro_to_cent(f9.summe_rabatte)  # = f9.kopfrabatt1 + f9.kopfrabatt2
            kopf['hint']['abschlag_prozent'] = "%.2f" % float(str(f9.kopfrabatt1_prozent + f9.kopfrabatt2_prozent))
            # 'kopfrabatt1_vorzeichen', fieldclass=FixedField, default='+'),
            # 'kopfrabatt2_vorzeichen', fieldclass=FixedField, default='+'),

        if f1.skontotage1:
            kopf['skontotage'] = f1.skontotage1
            kopf['skonto_prozent'] = f1.skonto1
            kopf['zu_zahlen_bei_skonto'] = huTools.monetary.euro_to_cent(f9.gesamtbetrag - f1.skontobetrag1_ust1)
            kopf['hint']['skontodatum'] = f1.skontodatum1
            kopf['hint']['skontobetrag'] = huTools.monetary.euro_to_cent(abs(f9.skontoabzug))

            # huTools.monetary.tara
            tmp = kopf['zu_zahlen_bei_skonto'] - huTools.monetary.netto(kopf['zu_zahlen_bei_skonto'])
            kopf['hint']['steueranteil_bei_skonto'] = tmp

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

            if f2.verband:
                kopf['verbandsnr'] = "SC%s" % f2.verband

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
            kopf['lieferscheinnr'] = "SL%s" % f1.lieferscheinnr

        #rec900.steuerpflichtiger_betrag = abs(f9.steuerpflichtig1)
        #rec900.mwst_gesamtbetrag = abs(f9.mehrwertsteuer)
        #rec900.skontofaehiger_betrag = abs(f9.skontofaehig)

        # FK = Kopftexte
        # FE = Rechnungs-Endetexte
        # FX = Texte Kopfrabatt
        # FV = Texte Versandart
        # FL = Texte Lieferbedingung
        # FN = Texte Nebenkosten
        zeilen = []
        for k in ['FK', 'FE', 'FX', 'FV', 'FL', 'FN']:
            if k in invoice_records:
                zeilen.extend(get_text(invoice_records[k]))
        if zeilen:
            kopf['infotext_kunde'] = '\n'.join(zeilen).strip()

        if f1.ust2_fuer_skonto:
            logging.critical("2. Skontosatz: %s %r", f1.ust2_fuer_skonto, kopf)
            raise ValueError("%s hat einen zweiten Steuersatz - das ist nicht unterstützt" % (rechnungsnr))
        if f1.skontodatum2 or f1.skontotage2 or f1.skonto2:
            logging.critical("2. Skontosatz: %r", kopf)
            raise ValueError("%s hat 2. Skontosatz - das ist nicht unterstützt" % (rechnungsnr))
        if not f1.waehrung in ['EUR', 'USD']:
            logging.critical("Währungsproblem: %r", kopf)
            raise ValueError("%s ist nicht in EUR/USD - das ist nicht unterstützt" % (rechnungsnr))

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

    def convert_invoicelistfooter(self, records):
        """Handle R1, R2, R3 entries of invoice lists.

        R1   Rechnungsliste-Verbandsdaten                 1-mal pro Verband
        R2   Rechnungsliste-Position (= Rechnungssumme)   1-mal pro Rechnung
        R3   Rechnungsliste-Summe                         1-mal pro Kopfdaten (R1)
        """

        if not ('R1' in records and 'R2' in records and 'R3' in records):
            return

        r1 = records['R1']
        r3 = records['R3']
        r2 = records['R2']

        if not isinstance(r2, list):
            r2 = [r2]

        footer = dict(rechnungslistennr=r2[-1].listennr,
                      rechnungslistendatum=r2[-1].listendatum,
                      empfaenger_iln=r1.verband_iln,
                      lieferantennr=r1.lieferantennr_verband,
                      rechnungslistenendbetrag=r3.summe,
                      mwst=sum([rec.mwst for rec in r2]),
                      steuerpflichtiger_betrag=sum([rec.warenwert for rec in r2]))
        return footer

    def convert(self, data):
        """Parse INVOICE file and return result in Very Simple Invoice Format."""

        # If we handle a collection of single invoices here, we have to split them into pieces and
        # provide a header for them.

        footer = None
        interchangeheader = None
        invoices = []

        files = self.parse(data)
        for records, positions in files:
            if not interchangeheader:
                interchangeheader = self.convert_interchangeheader(records)

            if not positions:
                raise RuntimeError("Keien Auftragspositionen!")
            invoice = self.convert_header(records)
            invoice['orderlines'] = [self.convert_position(invoice['guid'], position) for position in positions]
            invoices.append(invoice)

            if 'R1' in records and not footer:
                footer = self.convert_invoicelistfooter(records)

        # call init to clean this instance of SoftMConverter if this function is used multiple times
        self.__init__()

        # for invoice lists, add the invoice recipient to every single invoice
        if footer:
            for invoice in self.invoices:
                invoice['rechnungsadresse'] = {'iln': interchangeheader['technischer_rechnungsempfaenger']}

        return invoices


class SoftMABConverter(SoftMConverter):
    """Converter for AB files"""

    position_prefix = 'A'

    # Datensätze, die genau einmal pro Auftrag auftreten und
    # Texte: Versandart, Lieferbedingungen, Nebenkosten, Kopftexte
    #        Texte Kopfrabatt, Endetexte
    # Treten 1 oder n mal pro Kopf auf
    header_records = ['A1', 'A2', 'A8', 'A9', 'AV', 'AL', 'AN', 'AK', 'AX', 'AE']

    # Records, die n mal pro Position auftreten
    position_records = ['A3', 'A4', 'A6', 'AP']

    def convert_header(self, records):
        """Auftragskopf konvertieren"""

        a1 = records['A1']
        a2 = records['A2']
        a9 = records['A9']

        kundennr = str(a1.rechnungsempfaenger)
        if not kundennr.startswith('SC'):
            tmp = kundennr.split()
            kundennr = 'SC%s' % int(tmp[-1])

        auftragsnr = str(a1.auftragsnr)
        if auftragsnr and not auftragsnr.startswith('SO'):
            auftragsnr = 'SO%d' % int(auftragsnr)

        guid = auftragsnr.replace('SO', 'SB')

        kopf = dict(
            guid=guid,
            iln=a1.iln_rechnungsempfaenger,
            kundennr=kundennr,
            auftragsnr=auftragsnr,
            auftragsdatum=a1.auftragsdatum,
            kundenauftragsnr=a1.kundenbestellnummer,

            # Daten aus A9-Record
            warenwert=huTools.monetary.euro_to_cent(abs(a9.nettowarenwert)),
            # Der Betrag, denn der Kunde zahlen muss - es sei denn, er zieht Skonto
            zu_zahlen=huTools.monetary.euro_to_cent(a9.gesamtbetrag),
            steueranteil=huTools.monetary.euro_to_cent(a9.mehrwertsteuer),
            versandkosten=huTools.monetary.euro_to_cent(a9.versandkosten1),

            rechnungsbetrag=huTools.monetary.euro_to_cent(a9.steuerpflichtig_ust1),
            skontofaehig=huTools.monetary.euro_to_cent(a9.skontofaehig),
            skontoabzug=huTools.monetary.euro_to_cent(a9.skontoabzug),
            steuer_prozent=a9.steuersatz1,

            # Wird bei Rechnung addiert! TODO
            # kopf['abschlag'] = huTools.monetary.euro_to_cent(f9.summe_rabatte)  # = f9.kopfrabatt1 + f9.kopfrabatt2
            summe_zuschlaege=huTools.monetary.euro_to_cent(a9.summe_zuschlaege),
            summe_rabatte=huTools.monetary.euro_to_cent(a9.summe_rabatte),

            kopfrabatt1=huTools.monetary.euro_to_cent(a9.kopfrabatt1),
            kopfrabatt1_pct=a9.kopfrabatt1_pct,
            textschluessel1=a9.textschluessel1,
            kopfrabatt2=huTools.monetary.euro_to_cent(a9.kopfrabatt2),
            kopfrabatt2pct=a9.kopfrabatt2_pct,
            textschluessel2=a9.textschluessel2,

            # verpackungskosten1=a9.verpackungskosten1,
            # nebenkosten1=a9.nebenkosten1,
            anzahl_positionen=a9.anzahl_positionen,
        )

        kopf['hint'] = dict(
            lieferantennr=a1.lieferantennr,
            steuernr_kunde=str(a1.ustdid_rechnungsempfaenger),
            steuernr_lieferant=str(a1.ustdid_absender),
        )

        if a1.skontotage1:
            kopf['skontotage'] = a1.skontotage1
            kopf['skonto_prozent'] = a1.skonto1
            kopf['zu_zahlen_bei_skonto'] = huTools.monetary.euro_to_cent(a9.gesamtbetrag - a1.skontobetrag1_ust1)
            kopf['hint']['skontobetrag'] = huTools.monetary.euro_to_cent(abs(a9.skontoabzug))

            # huTools.monetary.tara
            tmp = kopf['zu_zahlen_bei_skonto'] - huTools.monetary.netto(kopf['zu_zahlen_bei_skonto'])
            kopf['hint']['steueranteil_bei_skonto'] = tmp

        # Daten aus Satz A2 (Auftrags-Lieferdaten) einfügen
        warenempfaenger = str(a2.warenempfaenger)
        if not warenempfaenger.startswith('SC'):
            warenempfaenger = 'SC%s' % warenempfaenger

        kopf['lieferadresse'] = dict(
            kundennr=warenempfaenger,
            name1=a2.liefer_name1,
            name2=a2.liefer_name2,
            name3=a2.liefer_name3,
            strasse=a2.liefer_strasse,
            plz=a2.liefer_plz,
            ort=a2.liefer_ort,
            land=husoftm.tools.land2iso(a2.liefer_land),
        )

        if a2.liefer_iln and a2.liefer_iln != '0':
            kopf['lieferadresse']['iln'] = str(a2.liefer_iln)
        elif a2.iln_warenempfaenger and a2.iln_warenempfaenger != '0':
            kopf['lieferadresse']['iln'] = str(a2.iln_warenempfaenger)

        zeilen = []
        for key in ('AV', 'AL', 'AN', 'AK', 'AX', 'AE'):
            if key in records:
                zeilen.extend(get_text(records[key], separator='\n'))

        kopf['infotext_kunde'] = '\n'.join(zeilen).strip()
        kopf['_parsed_at'] = datetime.datetime.now()
        return kopf

    def convert(self, data):
        """Parse ORDRSP file."""

        files = self.parse(data)
        for records, positions in files:
            # Auftrags(-bestätigungs)kopf
            ab = self.convert_header(records)
            ab['positionen'] = [self.convert_position(ab['guid'], position) for position in positions]

            # Schreibe frühsten und spätesten Liefertermin der Positionen als
            # anliefertermin_ab und anliefertermin_bis in die Auftragsbestätigung
            liefertermine = [pos['liefertermin'] for pos in ab['positionen']]
            ab['anliefertermin_ab'] = min(liefertermine)
            ab['anliefertermin_bis'] = max(liefertermine)

        return ab


def main():
    """Main Entry Point.

    Perform basic tests. Expects testfiles located in directory testdata/formate/
    """

    # iterate over all files located in testfolder and try parsing
    testdir = os.path.join('testdata', 'formate')
    for filename in sorted(os.listdir(testdir), reverse=True):
        print filename, os.path.join(testdir, filename)

        # Parse INVOIC file
        if filename.startswith('softm-edi-rechnungsliste'):
            converter = SoftMInvoiceConverter()
            invoices = converter.convert(open(os.path.join(testdir, filename)).read())
            assert(invoices)
            for invoice in invoices:
                assert(len(invoice['orderlines']))

        # parse ORDRSP file
        elif filename.startswith('softm-edi-auftragsbestaetigung'):
            converter = SoftMABConverter()
            orderresponse = converter.convert(open(os.path.join('.', filename)).read())
            assert(orderresponse)
            assert(len(orderresponse['positionen']))

        # no parsable file
        else:
            print "skipped"


if __name__ == '__main__':
    main()
