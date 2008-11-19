#!/usr/bin/env python
# encoding: utf-8
""" Functionality for basic generation of StratEDI INVOIC data.

Created by Maximillian Dornseif on 2008-10-29.
Copyright (c) 2008 HUDORA. All rights reserved.
"""

import datetime
from edilib.recordbased import generate_field_datensatz_class, FixedField, DecimalField, IntegerField
from edilib.recordbased import DateField, TimeField, EanField


INTERCHANGEHEADER000 = [
    dict(length=3, startpos=1, endpos=3, name='satzart', fieldclass=FixedField, default="000"),
    dict(length=35, startpos=4, endpos=38, name='sender_iln'),
    dict(length=35, startpos=39, endpos=73, name='empfaenger_iln'),
    dict(length=8, startpos=74, endpos=81, name='erstellungsdatum',
         fieldclass=DateField, default=datetime.datetime.now),
    dict(length=4, startpos=82, endpos=85, name='erstellungszeit',
         fieldclass=TimeField, default=datetime.datetime.now),
    dict(length=14, startpos=86, endpos=99, name='datenaustauschreferenz', fieldclass=IntegerField,
         doc='Fortlaufende achtstellige Sendenummer.'),
    dict(length=14, startpos=100, endpos=113, name='referenznummer', fieldclass=IntegerField),
    dict(length=14, startpos=114, endpos=127, name='anwendungsreferenz'),
    # This has to be changed to 0 for production data
    dict(length=1, startpos=128, endpos=128, name='testkennzeichen'),
    dict(length=5, startpos=129, endpos=133, name='schnittstellenversion',
         fieldclass=FixedField, default='4.5  '),
    dict(length=467, startpos=134, endpos=600, name='filler', fieldclass=FixedField, default=' '* 467),
]
# fix since this is not in python notation fix "off by one" errors
for feld in INTERCHANGEHEADER000:
    feld['startpos'] -= 1
interchangeheader000 = generate_field_datensatz_class(INTERCHANGEHEADER000, name='interchangeheader',
                                                      length=600)

TRANSAKTIONSKOPF100 = [
    dict(startpos=1, endpos=3, length=3, name='satzart', fieldclass=FixedField, default="100"),
    dict(startpos=4, endpos=17, length=14, name='referenz', fieldclass=IntegerField,
        doc='Eindeutige Nachrichtenreferenz des Absenders; laufende Nummer der Nachrichten im Datenaustausch;'
            + ' beginnt mit "1" und wird für jede Rechnung/Gutschrift innerhalb einer Übertragungsdatei'
            + ' um 1 erhöht.'),
    dict(startpos=18, endpos=23, length=6, name='typ', fieldclass=FixedField, default="INVOIC",
        doc="UNH-0065"),
    dict(startpos=24, endpos=26, length=3, name='version', fieldclass=FixedField, default="D  ",
        doc="UNH-0052"),
    dict(startpos=27, endpos=29, length=3, name='release', fieldclass=FixedField, default='96A',
        doc="UNH-0054"),
    dict(startpos=30, endpos=31, length=2, name='organisation1', fieldclass=FixedField, default="UN",
        doc="UNH-0051"),
    dict(startpos=32, endpos=37, length=6, name='organisation2', fieldclass=FixedField, default='EAN008',
        doc="UNH-0057"),
    dict(startpos=38, endpos=40, length=3, name='transaktionsart', fieldclass=FixedField, default='380',
        doc='"380" = Rechnung, "381" = Gutschrift (Waren und Dienstleistungen) '),
    dict(startpos=41, endpos=43, length=3, name='transaktionsfunktion', fieldclass=FixedField, default='   ',
        doc="BGM-1225"),
    dict(startpos=44, endpos=78, length=35, name='belegnr', fieldclass=IntegerField,
        doc="BGM-1004"),
    dict(startpos=79, endpos=86, length=8, name='belegdatum', fieldclass=DateField,
        doc="DTM-2380"),
    dict(startpos=87, endpos=89, length=3, name='antwortart',
        doc="BGM-4343"),
    dict(startpos=90, endpos=90, length=1, name='selbstabholung', fieldclass=FixedField, default='N',
        doc="TOD-4055"),
    dict(startpos=91, endpos=125, length=35, name='dokumentanname',
        doc="BGM-1000"),
    dict(startpos=126, endpos=512, length=387, name='filler', fieldclass=FixedField, default=' '*387),
    ]
# fix since this is not in python notation fix "off by one" errors
for feld in TRANSAKTIONSKOPF100:
    feld['startpos'] -= 1
transaktionskopf100 = generate_field_datensatz_class(TRANSAKTIONSKOPF100, name='transaktionskopf', length=600)

TRANSAKTINSREFERENZ111 = [
    dict(startpos=1, endpos=3, length=3, name='satzart', fieldclass=FixedField, default="111"),
    # 111-02 Angebots-Nummer K an 35 4 38 
    # 111-03 Angebots-Datum K an 8 39 46 YYYYMMDD 
    # 111-04 Werbe- oder Aktionsnummer K an 35 47 81 
    # 111-05 Nummer der Preisliste K an 35 82 116 
    dict(length=35, startpos=117, endpos=151, name='auftragsnr'),
    dict(length=8, startpos=152, endpos=159, name='auftragsdatum', fieldclass=DateField),
    # 111-08 Interne Auftragsnummer K an 35 160 194 
    # 111-09 Internes Auftragsdatum K an 8 195 202 YYYYMMDD 
    dict(length=8, startpos=203, endpos=210, name='lieferdatum', fieldclass=DateField),
    dict(length=35, startpos=211, endpos=245, name='lieferscheinnr'),
    dict(length=8, startpos=246, endpos=253, name='lieferscheindatum', fieldclass=DateField),
    dict(length=35, startpos=254, endpos=288, name='rechnungslistennr'),
    dict(length=8, startpos=289, endpos=296, name='rechnungslistendatum', fieldclass=DateField),
    dict(length=35, startpos=297, endpos=331, name='abkommensnr'),
    # 111-16 Kontonummer K an 35 332 366 
    # 111-17 Leistungszeitraum bis D an 8 367 374 YYYYMMDD 
    # 111-18 Rechnungs-/Referenznummer (bei Gutschrift) K an 35 375 409 
    # 111-19 Rechnungs-/Referenzdatum (bei Gutschrift) K an 8 410 417 YYYYMMDD 
    # 111-20 Retourennummer (bei Gutschrift) K an 35 418 452 
    # 111-21 Retourendatum (bei Gutschrift) K an 8 453 460 YYYYMMDD 
    dict(length=140, startpos=461, endpos=600, name='filler', fieldclass=FixedField, default=' '*140),
]

# fix since this is not in python notation fix "off by one" errors
for feld in TRANSAKTINSREFERENZ111:
    feld['startpos'] -= 1
transaktionsreferenz111 = generate_field_datensatz_class(TRANSAKTINSREFERENZ111,
                                                         name='transaktionsreferenz', length=600)


# Satzart 119: ID + Adressen der beteiligten Partner (1 x pro Transaktion und Partner)
ADDRESSEN119 = [
    dict(startpos=1, endpos=3, length=3, name='satzart', fieldclass=FixedField, default="119"),
    dict(startpos=4, endpos=6, length=3, name='partnerart',
        choices=('BY', 'IV', 'DP', 'SU'),
        doc="""Entspricht NAD-3035 Party function code qualifier
               BY Buyer: Party to whom merchandise and/or service is sold.
               DP Delivery party: Party to which goods should be delivered, if not identical with consignee.
               IV Invoicee: Party to whom an invoice is issued.
               SU Supplier: Party who supplies goods and/or services."""),
    dict(startpos=7, endpos=19, length=13, name='iln',
        doc="NAD-3039"),
    dict(startpos=20, endpos=54, length=35, name='name1',
        doc="NAD-3036"),                                 
    dict(startpos=55, endpos=89, length=35, name='name2',
        doc="NAD-3036"),                                 
    dict(startpos=90, endpos=124, length=35, name='name3',
        doc="NAD-3036"),
    dict(startpos=125, endpos=159, length=35, name='strasse1',
        doc="NAD-3042"),
    dict(startpos=160, endpos=194, length=35, name='strasse2',
        doc="NAD-3042"),
    dict(startpos=195, endpos=229, length=35, name='strasse3',
        doc="NAD-3042"),
    dict(startpos=230, endpos=238, length=9, name='plz',
        doc="NAD-3251"),
    dict(startpos=239, endpos=273, length=35, name='ort',
        doc="NAD-3164"),
    dict(startpos=274, endpos=276, length=3, name='land',
        doc="NAD-3207 - contrary to documentation ISO 3166-1 alpha-2 is NOT always used here."),
    dict(startpos=277, endpos=311, length=35, name='internepartnerid',
        doc="RFF-1154"),
    dict(startpos=312, endpos=346, length=35, name='gegebenepartnerid',
        doc="RFF-1154"),
    dict(startpos=347, endpos=381, length=35, name='ustdid',
        doc="RFF-1154"),
    dict(startpos=382, endpos=416, length=35, name='partnerabteilung',
        doc="CTA-3412"),           
    dict(startpos=417, endpos=451, length=35, name='steuernr',
        doc="RFF-1154 - Muss für Lieferant/Zahlungsleistender"),
    dict(startpos=452, endpos=471, length=20, name='ansprechpartner',
        doc="CTA-3412"),           
    dict(startpos=472, endpos=491, length=20, name='tel',
        doc="COM-3148"),           
    dict(startpos=492, endpos=511, length=20, name='fax',
        doc="COM-3148"),           
    dict(startpos=512, endpos=514, length=3, name='weeekennzeichen', fieldclass=FixedField, default='XA ',
        doc='"XA" = WEEE-Reg.-Nr.'),
    dict(startpos=515, endpos=549, length=35, name='weeenr',
         default='DE 70323035', doc='Muss für Lieferant/Zahlungsleistender, wenn WEEE-Reg.-Nr. existiert'),
    dict(startpos=550, endpos=600, length=51, name='filler', fieldclass=FixedField, default=' '*51),
    ]

# fix since this is not in python notation fix "off by one" errors
for feld in ADDRESSEN119:
    feld['startpos'] -= 1
addressen119 = generate_field_datensatz_class(ADDRESSEN119, name='adressatz', length=600)

ZAHLUNGSBEDINGUNGEN120 = [
    dict(startpos=1, endpos=3, length=3, name='satzart', fieldclass=FixedField, default="120"),
    dict(startpos=4, endpos=6, length=3, name='waehrung', fieldclass=FixedField, default='EUR',
        doc="CUX-6345"),
    dict(startpos=7, endpos=11, length=5, name='mwstsatz', fieldclass=DecimalField, precision=2,
        doc="TAX-5278"),
    dict(startpos=12, endpos=14, length=3, name='zahlungsziel', fieldclass=FixedField, default=' ' * 3,
        doc="PAT8-2152"),
    dict(startpos=15, endpos=22, length=8, name='valutadatum', fieldclass=FixedField, default=' ' * 8,
        doc="DTM8-2380"),
    dict(startpos=23, endpos=30, length=8, name='faelligkeitsdatum', fieldclass=FixedField, default=' ' * 8,
        doc="DTM8-2380"),
    dict(startpos=31, endpos=33, length=3, name='incoterms', choices=['DDP'], doc="TOD-4053"),
    dict(startpos=34, endpos=36, length=3, name='valutatage', fieldclass=FixedField, default=' ' * 3,
        doc="PAT8-2152"),
    dict(startpos=37, endpos=71, length=35, name='frei', fieldclass=FixedField, default=' ' * 35,
        doc="RFF1-1154"),
    dict(startpos=72, endpos=74, length=3, name='konditionssperre', fieldclass=FixedField, default=' ' * 3,
        doc="ALI-4183"),
    dict(startpos=75, endpos=77, length=3, name='steuerbefreit', fieldclass=FixedField, default=' ' * 3,
        doc="TAX6-5305"),
    dict(startpos=78, endpos=112, length=35, name='lieferbedingung', fieldclass=FixedField, default=' ' * 35,
        doc="TOD-4052"),
    dict(startpos=113, endpos=512, length=400, name='filler', fieldclass=FixedField, default=' ' * 400),
]
# fix since this is not in python notation fix "off by one" errors
for feld in ZAHLUNGSBEDINGUNGEN120:
    feld['startpos'] -= 1
zahlungsbedingungen120 = generate_field_datensatz_class(ZAHLUNGSBEDINGUNGEN120, name='zahlungsbedingungen',
                                                        length=600)


texte130 = [
    dict(startpos=1, endpos=3, length=3, name='satzart', fieldclass=FixedField, default="130"),
    dict(startpos=4, endpos=6, length=3, name='textzuordnung', choices=['AAI'],
         doc="""FTX-4451: Text subject code qualifier
                AAI General information: The text contains general information"""),
    dict(startpos=7, endpos=356, length=350, name='text',
        doc="FTX-4440"),
    dict(startpos=357, endpos=512, length=156, name='filler', fieldclass=FixedField, default=' ' * 156),
]
# fix since this is not in python notation fix "off by one" errors
for feld in texte130:
    feld['startpos'] -= 1
    

zusatzkosten140 = [
    dict(startpos=1, endpos=3, length=3, name='satzart', fieldclass=FixedField, default="140"),
    dict(startpos=4, endpos=8, length=5, name='mwstsatz',
         doc="TAX20-5278"),
    dict(startpos=9, endpos=16, length=8, name='skontoprozent', fieldclass=DecimalField,
        doc="PCD17-5482"),
    dict(startpos=17, endpos=34, length=18, name='skontobetrag', fieldclass=FixedField, default=' ' * 18,
        doc="MOA20-5004"),
    dict(startpos=35, endpos=52, length=18, name='frachtbetrag', fieldclass=FixedField, default=' ' * 18,
        doc="MOA20-5004"),
    dict(startpos=53, endpos=70, length=18, name='verpackungsbetrag', fieldclass=FixedField,
         default=' ' * 18, doc="MOA20-5004"),
    dict(startpos=71, endpos=88, length=18, name='versicherungsbetrag', fieldclass=FixedField,
         default=' ' * 18, doc="MOA20-5004"),
    dict(startpos=89, endpos=91, length=3, name='skontotage',
        doc="PAT8-2152"),
    dict(startpos=92, endpos=99, length=8, name='skontodatum', fieldclass=FixedField, default=' ' * 8,
        doc="PAT8-2152"),
    dict(startpos=100, endpos=512, length=413, name='filler', fieldclass=FixedField, default=' ' * 413),
]


# fix since this is not in python notation fix "off by one" errors
for feld in zusatzkosten140:
    feld['startpos'] -= 1

RECHNUNGSPOSITION500 = [
    dict(startpos=1, endpos=3, length=3, name='satzart', fieldclass=FixedField, default="500"),
    dict(startpos=4, endpos=9, length=6, name='positionsnummer', fieldclass=IntegerField,
         doc="LIN-1082"),
    dict(startpos=10, endpos=12, length=3, name='aktivitaetsart', fieldclass=FixedField,
        default='   ', doc="LIN-1229"),
    dict(startpos=13, endpos=25, length=13, name='ean', fieldclass=EanField,
        doc="LIN-7140"),
    dict(startpos=26, endpos=60, length=35, name='artnr_lieferant',
        doc="PIA-7140"),
    dict(startpos=61, endpos=95, length=35, name='artnr_kunde',
        doc="PIA-7140"),
    dict(startpos=96, endpos=130, length=35, name='warengruppe', fieldclass=FixedField,
        default=' ' * 35, doc="RFF-1154"),
    dict(startpos=131, endpos=165, length=35, name='artikelbezeichnung1',
        doc="IMD-7008"),
    dict(startpos=166, endpos=200, length=35, name='artikelbezeichnung2',
        doc="IMD-7008"),
    dict(startpos=201, endpos=235, length=35, name='artikelgroesse', fieldclass=FixedField,
        default=' ' * 35, doc="IMD-7008"),
    dict(startpos=236, endpos=270, length=35, name='artikelfarbe', fieldclass=FixedField,
        default=' ' * 35, doc="IMD-7008"),
    dict(startpos=271, endpos=285, length=15, name='berechnete_menge', fieldclass=DecimalField,
        precision=2, doc="QTY-6060"),
    dict(startpos=286, endpos=300, length=15, name='menge_ohne_berechnung', fieldclass=FixedField,
        default = '               ', doc="QTY-6060"),
    dict(startpos=301, endpos=303, length=3, name='waehrung', fieldclass=FixedField, default='EUR',
        doc="CUX-6345"),
    dict(startpos=304, endpos=308, length=5, name='mwstsatz', fieldclass=DecimalField,
        precision=2, doc="TAX-5278"),
    dict(startpos=309, endpos=323, length=15, name='nettostueckpreis', fieldclass=DecimalField,
        precision=4, doc="PRI-5118"),
    dict(startpos=324, endpos=338, length=15, name='bruttostueckpreis', fieldclass=DecimalField, precision=2,
         doc="PRI-5118 existieren Artikelzu-/abschläge, ist Brutto-Stückpreis zu füllen"),
    dict(startpos=339, endpos=353, length=15, name='verkaufspreis', fieldclass=FixedField,
        default=' ' * 15, doc="PRI-5118"),
    dict(startpos=354, endpos=368, length=15, name='aktionspreis', fieldclass=FixedField,
        default=' ' * 15, doc="PRI-5118"),
    dict(startpos=369, endpos=383, length=15, name='listenpreis', fieldclass=FixedField,
        default=' ' * 15, doc="PRI-5118"),
    dict(startpos=384, endpos=392, length=9, name='preisbasis', fieldclass=FixedField,
        default=' ' * 9, doc="PRI-5284"),
    dict(startpos=393, endpos=395, length=3, name='mengeneinheit', choices=['PCE'],
        doc='PRI-6411 "PCE" = Stück; "KGM" = Kilogramm'),
    dict(startpos=396, endpos=413, length=18, name='nettowarenwert', fieldclass=DecimalField, precision=2,
         doc='''MOA-5004 Nettowarenwert = Menge x Bruttopreis ./. Artikelrabatte bzw. Menge x Nettopreis
        (Rabatte sind im Preis eingerechnet) 
        Bei Gutschriftspositionen ist der Nettowarenwert negativ einzustellen.'''),
    dict(startpos=414, endpos=431, length=18, name='bruttowarenwert', fieldclass=DecimalField, precision=2,
         doc="MOA-5004 Bruttowarenwert = Menge x Bruttopreis ohne MWSt., vor Abzug der Artikelrabatte"),
    dict(startpos=432, endpos=449, length=18, name='summeabschlaege', fieldclass=FixedField,
        default=' ' * 18, doc='''MOA-5004 Summe aller Zu- und Abschläge aus Satzart(en) 513 mit
                              vorzeichengerechter Darstellung'''),
    dict(startpos=450, endpos=456, length=7, name='verpackungsart', choices=['CT'],
        doc="PAC-7065"),
    dict(startpos=457, endpos=463, length=7, name='verpackungszahl', fieldclass=IntegerField,
        doc="PAC-7065"),
    dict(startpos=464, endpos=464, length=1, name='gebinde', fieldclass=IntegerField,
        default=' ', doc='''PIA-7143 handelt es sich bei der Fakturiereinheit um ein Gebinde, ist hier ein
         "G" einzustellen; handelt es sich bei der Fakturiereinheit um ein Display/Sortiment, ist hier ein
         "D" einzustellen; wird eine Verbrauchereinheit fakturiert, ist hier ein "V" einzustellen. 
         "P" = Pfandartikel (Mehrweg); "E" = Einweg'''),
    dict(startpos=465, endpos=479, length=15, name='bestellte_vs_gelieferte_menge', fieldclass=FixedField,
        default=' ' * 15, doc="QTY-6060"),
    dict(startpos=480, endpos=494, length=15, name='aktionsvariante', fieldclass=FixedField,
        default='               ', doc="PIA-7143"),
    dict(startpos=495, endpos=497, length=3, name='steuerbefreit', fieldclass=FixedField,
        default='   ', doc='TAX-5305, Mußfeld (Inhalt=Y), wenn die Artikelposition keiner MwSt. unterliegt'),
    dict(startpos=498, endpos=507, length=10, name='kennzeichen', fieldclass=FixedField,
        default='          ', doc="?"),
    dict(startpos=508, endpos=508, length=1, name='nachlieferung_erfolgt', fieldclass=FixedField,
        default=' ', doc="?"),
    dict(startpos=509, endpos=511, length=3, name='grund_abweichung', fieldclass=FixedField,
        default='   ', doc="?"),
    dict(startpos=512, endpos=600, length=89, name='filler', fieldclass=FixedField, default=' ' * 89),
]
# fix since this is not in python notation fix "off by one" errors
for feld in RECHNUNGSPOSITION500:
    feld['startpos'] -= 1
rechnungsposition500 = generate_field_datensatz_class(RECHNUNGSPOSITION500, name='positionssatz', length=600)


artikeltexte530 = [
    dict(startpos=1, endpos=3, length=3, name='satzart', fieldclass=FixedField, default="530"),
    dict(startpos=4, endpos=6, length=3, name='textzuordnung', choices=['AAI'],
         doc="""FTX-4451: Text subject code qualifier
                AAI General information: The text contains general information"""),
    dict(startpos=7, endpos=356, length=350, name='text',
        doc="FTX-4440"),
    dict(startpos=357, endpos=512, length=156, name='filler', fieldclass=FixedField, default=' ' * 156),
]
# fix since this is not in python notation fix "off by one" errors
for feld in artikeltexte530:
    feld['startpos'] -= 1

BELEGSUMMEN900 = [
    dict(startpos=1, endpos=3, length=3, name='satzart', fieldclass=FixedField, default="900"),
    dict(startpos=4, endpos=21, length=18, name='rechnungsendbetrag', fieldclass=DecimalField,
         precision=2, doc="MOA-5004"),
    dict(startpos=22, endpos=39, length=18, name='mwst_gesammtbetrag',
         fieldclass=DecimalField, precision=2, doc="MOA-5004"),
    dict(startpos=40, endpos=57, length=18, name='nettowarenwert_gesammt',
         fieldclass=DecimalField, precision=2),
    dict(startpos=58, endpos=75, length=18, name='steuerpflichtiger_betrag',
         fieldclass=DecimalField, precision=2),
    dict(startpos=76, endpos=93, length=18, name='skontofaehiger_betrag',
         fieldclass=DecimalField, precision=2),
    dict(startpos=94, endpos=111, length=18, name='zu_und_abschlage',
         fieldclass=DecimalField, precision=2),
    dict(startpos=112, endpos=129, length=18, name='gesammt_verkaufswert',
         fieldclass=DecimalField, precision=2),
    dict(startpos=130, endpos=600, length=471, name='filler', fieldclass=FixedField, default=' ' * 471),
]

# fix since this is not in python notation fix "off by one" errors
for feld in BELEGSUMMEN900:
    feld['startpos'] -= 1
belegsummen900 = generate_field_datensatz_class(BELEGSUMMEN900, name='belegsummen', length=600)

# Satzart 901: MWSt.-Angaben (1 x pro Transaktion und MWSt.-Satz)

# Satzart 913: Zu- / Abschläge auf Belegebene (max. 1 x pro Abschlagsart / -stufe und MWSt.-Satz) 
# (Belegzuschläge bzw. Belegrabatte werden auf den Beleg gewährt. Es handelt sich ausdrücklich nicht um Summen
#  von Artikelzu-/abschlägen. 
BELEGABSCHLAEGE913 = [
    dict(length=3, startpos=1, endpos=3, name='satzart', fieldclass=FixedField, default="913"),
    dict(length=3, startpos=4, endpos=6, name='kennzeichen', fieldclass=FixedField, default='A  ',
         doc='913-02 Kennzeichen Zu-/Abschlag, "C" = Zuschlag, "A" = Abschlag/Rabatt'),
    dict(length=3, startpos=7, endpos=9, name='art', fieldclass=FixedField, default='   '),
    dict(length=3, startpos=10, endpos=12, name='kalkulationsfolgeanzeige', fieldclass=FixedField,
         default='001', doc='''913-04 Kalkulationsfolgeanzeige. Die Kalkulationsstufe gibt darüber Auskunft,
         ob sich ein Rabatt auf einen bereits reduzierten (rabattierten) Betrag bezieht oder nicht.
         Existiert nur ein Rabatt, ist der Inhalt immer "1".
         Mussfeld, wenn mehrere Belegzu-/-abschläge existieren.'''),
    dict(length=5, startpos=13, endpos=17, name='mwst_abschlag', fieldclass=DecimalField, precision=2,
         doc='913-05 MWSt.-Satz des Zu-/Abschlages (2 NK-St.)'),
    dict(length=8, startpos=18, endpos=25, name='abschlag_prozent',
         fieldclass=DecimalField, precision=2, doc='Zu-/Abschlag in Prozent (2 NK-St.)'),
    dict(length=18, startpos=26, endpos=43, name='abschlag',
         fieldclass=DecimalField, precision=2, doc='Zu-/Abschlag als Betrag (2 NK-St.)'),
    dict(length=15, startpos=44, endpos=58, name='menge_naturalrabatt', fieldclass=IntegerField, default=1,
         doc='913-08 Menge Naturalrabatt / Mengenzuschlag K n 15 44 58 (2 NK-St.)'),
    # 913-09 Zu-/Abschlag je Einheit D n 15 59 73 (2 NK-St.) 
    # 913-10 Zu-/Abschlagbasis D n 18 74 91 (2 NK-St.) 
    dict(length=35, startpos=92, endpos=126, name='text',
         doc='913-11 Art des Zu-/Abschlages, Text'),
    dict(length=474, startpos=127, endpos=600, name='filler', fieldclass=FixedField, default=' '*474,
         doc='913-12 Filler K(Blank)'),
]

# fix since this is not in python notation fix "off by one" errors
for feld in BELEGABSCHLAEGE913:
    feld['startpos'] -= 1
belegabschlaege913 = generate_field_datensatz_class(BELEGABSCHLAEGE913, name='belegabschlaege', length=600)



RECHNUNGSLISTE990 = [
    dict(length=3, startpos=1, endpos=3, name='satzart', fieldclass=FixedField, default="990"),
    dict(length=3, startpos=4, endpos=6, name='art'),
    dict(length=35, startpos=7, endpos=41, name='rechnungslistennr'),
    dict(length=8, startpos=42, endpos=49, name='rechnungslistendatum', fieldclass=DateField),
    dict(length=35, startpos=50, endpos=84, name='abkommen'),
    dict(length=13, startpos=85, endpos=97, name='hudora_iln',
         fieldclass=FixedField, default="4005998000007"),
    #dict(length=35, startpos=98, endpos=132, name='lieferantennr'),
    dict(length=13, startpos=133, endpos=145, name='empfaenger_iln'),
    dict(length=13, startpos=146, endpos=158, name='hudora_iln2',
         fieldclass=FixedField, default="4005998000007"),
    dict(length=13, startpos=159, endpos=171, name='zahlungsleistender_iln', fieldclass=EanField),
    dict(length=3, startpos=172, endpos=174, name='waehrungskennzeichen',
         fieldclass=FixedField, default="EUR"),
    #dict(length=8, startpos=175, endpos=182, name='valutadatum', fieldclass=DateField),
    #990-13 Fälligkeitsdatum (Rechnungsdatum ist Referenzdatum) (12) D an 8 183 190 YYYYMMDD 
    dict(length=18, startpos=191, endpos=208, name='rechnungslistenendbetrag',
         fieldclass=DecimalField, precision=2),
    dict(length=18, startpos=209, endpos=226, name='mwst', fieldclass=DecimalField, precision=2),
    dict(length=18, startpos=227, endpos=244, name='nettowarenwert', fieldclass=DecimalField, precision=2),
    dict(length=18, startpos=245, endpos=262, name='steuerpflichtiger_betrag',
         fieldclass=DecimalField, precision=2, doc='990-17 ReLi-Steuerpflichtiger Betrag, gesamt'),
    #990-18 ReLi-Skontofähiger Betrag, gesamt D n 18 263 280 (2 NK-Stellen) 
    #990-19 ReLi-Belegzu- / Abschläge, gesamt (Vorzeichen !!!) D n 18 281 298 (2 NK-Stellen) 
    #990-20 MWSt.-Satz D n 5 299 303 (2 NK-Stellen) 
    #990-21 Abrechnungszeitraum - Beginn D an 8 304 311 YYYYMMDD 
    #990-22 Abrechnungszeitraum - Ende D an 8 312 319 YYYYMMDD 
    dict(length=281, startpos=320, endpos=600, name='Filler', fieldclass=FixedField, default=" " * 281),
]

# fix since this is not in python notation fix "off by one" errors
for feld in RECHNUNGSLISTE990:
    feld['startpos'] -= 1
rechnungsliste990 = generate_field_datensatz_class(RECHNUNGSLISTE990, name='rechnungsliste', length=600)
