#!/usr/bin/env python
# encoding: utf-8
"""
datenexportschnittstelle.py - Read the SoftM EDI Datenexportschnittstelle (INVOIC/DESADV)

Based on trunk/web/MoftS/lib/pySoftM/EDI.py

Created by Maximillian Dornseif on 2007-05-07.
Copyright (c) 2007, 2008, 2010 HUDORA GmbH. All rights reserved.
"""


import datetime
from edilib.recordbased import generate_field_datensatz_class, DateField, TimeField, BooleanField
from edilib.recordbased import IntegerField, DecimalFieldNoDot, DecimalFieldNoDotSigned, FixedField, EanField


doctext = """Diese Satzart enthält allgemeine Angaben zur empfangenen EDIFACT-Nachricht und kennzeichnet
jeweils den Beginn einer neuen Übertragung."""
FELDERXH = [
 # dict(length=35, startpos=1, endpos=35, name='uebertragungs_id'),
 dict(length=8, startpos=36, endpos=43, name='uebertragungs_datum', fieldclass=DateField,
      default=datetime.datetime.today, doc='000-04 bei StratEDI'),
 dict(length=4, startpos=44, endpos=47, name='uebertragungs_zeit', fieldclass=TimeField,
      default=datetime.datetime.now, doc='000-05 bei StratEDI'),
 dict(length=8, startpos=48, endpos=55, name='empfangsdatum', fieldclass=DateField,
      default=datetime.datetime.today),
 dict(length=4, startpos=56, endpos=59, name='empfangszeit',
      fieldclass=TimeField, default=datetime.datetime.now),
 # dict(length=35, startpos=60, endpos=94, name='logischer_dateiname'),
 dict(length=35, startpos=95, endpos=129, name='physischer_dateiname', choices=['XOO00']),
 dict(length=35, startpos=130, endpos=164, name='dfue_partner'),
 dict(length=8, startpos=165, endpos=172, name='nachrichtenart', choices=['      ']),
 dict(length=2, startpos=173, endpos=174, name='firma', choices=['01']),
 # dict(length=35, startpos=175, endpos=209, name='belegnummer'),
 dict(length=10, startpos=210, endpos=219, name='umgebung'),
 dict(length=10, startpos=220, endpos=229, name='sendestatus'),
 # dict(length=15, startpos=230, endpos=244, name='1.Res. 15 St.'),
 # dict(length=15, startpos=245, endpos=259, name='2.Res. 15 St.'),
 # dict(length=8, startpos=260, endpos=267, name='1.Res. 8 St.'),
 # dict(length=8, startpos=268, endpos=275, name='2.Res. 8 St.'),
 # dict(length=3, startpos=276, endpos=278, name='1.Res. 3 St.'),
 # dict(length=3, startpos=279, endpos=281, name='2.Res. 3 St.'),
 dict(length=2, startpos=282, endpos=283, name='testkennzeichen'),
 # dict(length=10, startpos=284, endpos=293, name='versionsnummer'),
 # dict(length=10, startpos=294, endpos=303, name='freigabenummer'),
 # dict(length=178, startpos=304, endpos=481, name='reserve_178'),
 dict(length=8, startpos=482, endpos=489, name='erstellungs_datum'),
 dict(length=6, startpos=490, endpos=495, name='erstellungs_zeit'),
 dict(length=1, startpos=496, endpos=496, name='status'),
]
# fix difference in array counting between SoftM and Python
for feld in FELDERXH:
    feld['startpos'] = feld['startpos'] - 1
XHsatzklasse = generate_field_datensatz_class(FELDERXH, name='XHheader', length=496, doc=doctext)


# Rechnungskopf


doctext = """Kopfdaten (XOO00EF1) = Diese Satzart enthält die Kopfdaten einer Rechnung und kann beliebig
oft pro Übertragung vorkommen."""
FELDERF1 = [
 dict(length=3, startpos=1, endpos=3, name='belegart'),
 dict(length=35, startpos=4, endpos=38, name='rechnungsnr', fieldclass=IntegerField,
      doc='100-10 bei StratEDI'),
 dict(length=8, startpos=39, endpos=46, name='rechnungsdatum', fieldclass=DateField,
      doc='100-11 bei StratEDI'),
 dict(length=8, startpos=47, endpos=54, name='liefertermin', fieldclass=DateField),
 dict(length=35, startpos=55, endpos=89, name='lieferscheinnr', fieldclass=IntegerField),
 dict(length=8, startpos=90, endpos=97, name='lieferscheindatum', fieldclass=DateField),
 dict(length=20, startpos=98, endpos=117, name='kundenbestellnummer'),
 dict(length=8, startpos=118, endpos=125, name='kundenbestelldatum', fieldclass=DateField),
 dict(length=9, startpos=126, endpos=134, name='auftragsnr', fieldclass=IntegerField),
 dict(length=8, startpos=135, endpos=142, name='auftragsdatum', fieldclass=DateField),
 dict(length=17, startpos=143, endpos=159, name='iln_rechnungsempfaenger', fieldclass=EanField,
      doc='119-03 bei StratEDI 119-02=IV'),
 dict(length=17, startpos=160, endpos=176, name='rechnungsempfaenger', fieldclass=IntegerField,
      doc='Kundennummer Rechnungsempfänger'),
 dict(length=17, startpos=177, endpos=193, name='ustdid_rechnungsempfaenger'),
 dict(length=17, startpos=194, endpos=210, name='eigene_iln_beim_kunden', fieldclass=EanField),
 dict(length=17, startpos=211, endpos=227, name='lieferantennummer'),
 dict(length=17, startpos=228, endpos=244, name='ustdid_absender'),
 dict(length=35, startpos=245, endpos=279, name='rechnungsliste', fieldclass=IntegerField),
 dict(length=8, startpos=280, endpos=287, name='rechnungslistendatum', fieldclass=DateField),
 dict(length=3, startpos=288, endpos=290, name='waehrung', default='EUR',
      doc='ISO Währungsschlüssel', choices=['EUR', 'USD']),
 dict(length=5, startpos=291, endpos=295, name='ust1_fuer_skonto', fieldclass=DecimalFieldNoDot, precision=2),
 dict(length=5, startpos=296, endpos=300, name='ust2_fuer_skonto', fieldclass=DecimalFieldNoDot, precision=2),
 dict(length=15, startpos=301, endpos=315, name='skontofaehig_ust1'),
 # FIXME: warum laufen ab hier die Spalten anders als in der SoftM Doku???
 dict(length=1, startpos=316, endpos=316, name='Vorzeichen Skontofähig 1'),
 dict(length=15, startpos=317, endpos=331, name='Skontofähig USt 2'),
 dict(length=1, startpos=332, endpos=332, name='Vorzeichen Skontofähig 2'),
 dict(length=8, startpos=333, endpos=340, name='skontodatum1', fieldclass=DateField),
 dict(length=3, startpos=341, endpos=343, name='skontotage1', fieldclass=IntegerField),
 dict(length=5, startpos=344, endpos=348, name='skonto1', fieldclass=DecimalFieldNoDot, precision=2),
 dict(length=16, startpos=349, endpos=364, name='skontobetrag1_ust1',
     fieldclass=DecimalFieldNoDotSigned, precision=3),
 #dict(length=1, startpos=364, endpos=364, name='Vorzeichen Skontobetrag 1'),
 dict(length=15, startpos=365, endpos=379, name='Skontobetrag 1 USt 2'),
 dict(length=1, startpos=380, endpos=380, name='Vorzeichen Skontobetrag 12'),
 dict(length=8, startpos=381, endpos=388, name='skontodatum2', fieldclass=DateField),
 dict(length=3, startpos=389, endpos=391, name='skontotage2', fieldclass=IntegerField),
 dict(length=5, startpos=392, endpos=396, name='skonto2', fieldclass=DecimalFieldNoDot, precision=2),
 dict(length=15, startpos=397, endpos=411, name='Skontobetrag 2 USt 1'),
 dict(length=1, startpos=412, endpos=412, name='Vorzeichen Skontobetrag 2 USt 1'),
 dict(length=15, startpos=413, endpos=427, name='Skontobetrag 2 USt 2'),
 dict(length=1, startpos=428, endpos=428, name='Vorzeichen Skontobetrag 2 USt 2'),
 dict(length=8, startpos=429, endpos=436, name='nettodatum', fieldclass=DateField),
 dict(length=3, startpos=437, endpos=439, name='valutatage', fieldclass=IntegerField),
 dict(length=8, startpos=440, endpos=447, name='valutadatum', fieldclass=DateField),
 dict(length=2, startpos=448, endpos=449, name='Firma', fieldclass=FixedField, default='01'),
 dict(length=4, startpos=450, endpos=453, name='Abteilung'),
 dict(length=10, startpos=454, endpos=463, name='Bibliothek'),
 dict(length=3, startpos=464, endpos=466, name='nettotage', fieldclass=IntegerField),
 dict(length=14, startpos=467, endpos=480, name='steuernummer'),
 # TODO: there seems to be something in this field!
 dict(length=15, startpos=481, endpos=495, name='filler'),  # fieldclass=FixedField, default=' ' * 15),
 dict(length=1, startpos=496, endpos=496, name='Status', fieldclass=FixedField, default=' '),
]
# fix difference in array counting between SoftM and Python
for feld in FELDERF1:
    feld['startpos'] = feld['startpos'] - 1
F1satzklasse = generate_field_datensatz_class(FELDERF1, name='F1kopfdaten', length=496, doc=doctext)


doctext = 'Auftrags-Kopf (XOO00EA1)'
FELDERA1 = [
 dict(length=3, startpos=1, endpos=3, name='Belegart'),
 dict(length=9, startpos=4, endpos=12, name='auftragsnr'),
 dict(length=8, startpos=13, endpos=20, name='auftragsdatum', fieldclass=DateField),
 dict(length=8, startpos=21, endpos=28, name='druckdatum', fieldclass=DateField),
 dict(length=20, startpos=29, endpos=48, name='kundenbestellnummer'),
 dict(length=8, startpos=49, endpos=56, name='kundenbestelldatum', fieldclass=DateField),
 dict(length=17, startpos=57, endpos=73, name='iln_rechnungsempfaenger', fieldclass=EanField),
 dict(length=17, startpos=74, endpos=90, name='rechnungsempfaenger'),
 dict(length=17, startpos=91, endpos=107, name='ustdid_rechnungsempfaenger'),
 dict(length=17, startpos=108, endpos=124, name='eigene_iln_beim_kunden'),
 dict(length=17, startpos=125, endpos=141, name='lieferantennr'),
 dict(length=17, startpos=142, endpos=158, name='ustdid_absender'),
 dict(length=3, startpos=159, endpos=161, name='ISO-WSL'),
 dict(length=5, startpos=162, endpos=166, name='USt 1 für Skonto'),
 dict(length=5, startpos=167, endpos=171, name='USt 2 für Skonto'),
 dict(length=16, startpos=172, endpos=187, name='Skontofähig USt 1',
            fieldclass=DecimalFieldNoDotSigned, precision=3),
 dict(length=16, startpos=188, endpos=203, name='Skontofähig USt 2',
            fieldclass=DecimalFieldNoDotSigned, precision=3),
 dict(length=3, startpos=204, endpos=206, name='skontotage1', fieldclass=IntegerField),
 dict(length=5, startpos=207, endpos=211, name='skonto1', fieldclass=DecimalFieldNoDot, precision=2),
 dict(length=16, startpos=212, endpos=227, name='skontobetrag1_ust1',
            fieldclass=DecimalFieldNoDotSigned, precision=3),
 dict(length=16, startpos=228, endpos=243, name='Skontobetrag 1 USt 2',
            fieldclass=DecimalFieldNoDotSigned, precision=3),
 dict(length=3, startpos=244, endpos=246, name='Skontotage 2', fieldclass=IntegerField),
 dict(length=5, startpos=247, endpos=251, name='Skonto 2'),
 dict(length=16, startpos=252, endpos=267, name='Skontobetrag 2 USt 1',
            fieldclass=DecimalFieldNoDotSigned, precision=3),
 dict(length=16, startpos=268, endpos=283, name='Skontobetrag 2 USt 2',
            fieldclass=DecimalFieldNoDotSigned, precision=3),
 dict(length=60, startpos=284, endpos=343, name='skontotext'),
 dict(length=2, startpos=344, endpos=345, name='Firma'),
 dict(length=4, startpos=346, endpos=349, name='Abteilung'),
 dict(length=10, startpos=350, endpos=359, name='Bibliothek'),
 dict(length=136, startpos=360, endpos=495, name='ReserveX1'),
 dict(length=1, startpos=496, endpos=496, name='Status'),
]
# fix difference in array counting between SoftM and Python
for feld in FELDERA1:
    feld['startpos'] = feld['startpos'] - 1
A1satzklasse = generate_field_datensatz_class(FELDERA1, name='A1auftragskopf', length=496, doc=doctext)


doctext = 'Auftrags-Lieferdaten (XOO00EA2)'
FELDERA2 = [
    dict(length=17, startpos=1, endpos=17, name='iln_Warenempfaenger'),
    dict(length=17, startpos=18, endpos=34, name='warenempfaenger', fieldclass=IntegerField),
    # dict(length=17, startpos=35, endpos=51, name='eigene ILN beim WaEmpf'),
    dict(length=17, startpos=52, endpos=68, name='unsere LiNr beim WaEmpf'),
    dict(length=17, startpos=69, endpos=85, name='liefer_iln'),
    dict(length=35, startpos=86, endpos=120, name='liefer_name1'),
    dict(length=35, startpos=121, endpos=155, name='liefer_name2'),
    dict(length=35, startpos=156, endpos=190, name='liefer_name3'),
    dict(length=35, startpos=191, endpos=225, name='liefer_name4'),
    dict(length=35, startpos=226, endpos=260, name='liefer_strasse'),
    dict(length=3, startpos=261, endpos=263, name='liefer_land'),
    dict(length=9, startpos=264, endpos=272, name='liefer_plz'),
    dict(length=35, startpos=273, endpos=307, name='liefer_ort'),
    # dict(length=30, startpos=308, endpos=337, name='Lagerbezeichnung'),
    dict(length=3, startpos=338, endpos=340, name='versandart'),
    dict(length=3, startpos=341, endpos=343, name='lieferbedingung'),
    dict(length=17, startpos=344, endpos=360, name='verband', fieldclass=IntegerField),
    dict(length=17, startpos=361, endpos=377, name='verband_iln', fieldclass=EanField),
    dict(length=1, startpos=496, endpos=496, name='Status', fieldclass=FixedField, default=' '),
]

# fix difference in array counting between SoftM and Python
for feld in FELDERA2:
    feld['startpos'] = feld['startpos'] - 1
A2satzklasse = generate_field_datensatz_class(FELDERA2, name='A2auftragslieferdaten', length=496, doc=doctext)


doctext = 'Auftrags-Position (XOO00EA3)'
FELDERA3 = [
    dict(length=5, startpos=1, endpos=5, name='positionsnr'),
    dict(length=35, startpos=6, endpos=40, name='artnr'),
    dict(length=35, startpos=41, endpos=75, name='artnr_kunde'),
    dict(length=35, startpos=76, endpos=110, name='ean', fieldclass=EanField),
    dict(length=35, startpos=111, endpos=145, name='zolltarifnummer'),
    dict(length=70, startpos=146, endpos=215, name='artikelbezeichnung'),
    dict(length=70, startpos=216, endpos=285, name='artikelbezeichnung_kunde'),
    dict(length=15, startpos=286, endpos=300, name='menge', fieldclass=DecimalFieldNoDot, precision=3),
    # dict(length=3, startpos=301, endpos=303, name='Mengeneinheit'),
    dict(length=16, startpos=304, endpos=319, name='verkaufspreis',
         fieldclass=DecimalFieldNoDotSigned, precision=3),
    dict(length=3, startpos=320, endpos=322, name='Mengeneinheit Preis'),
    dict(length=1, startpos=323, endpos=323, name='Preisdimension'),
    dict(length=16, startpos=324, endpos=339, name='wert_netto',
        fieldclass=DecimalFieldNoDotSigned, precision=3),
    dict(length=16, startpos=340, endpos=355, name='wert_brutto',
        fieldclass=DecimalFieldNoDotSigned, precision=3),
    dict(length=2, startpos=356, endpos=357, name='Kz Mehrwertsteuer'),
    dict(length=5, startpos=358, endpos=362, name='steuersatz', fieldclass=DecimalFieldNoDot, precision=2),
    dict(length=16, startpos=363, endpos=378, name='steuerbetrag', fieldclass=DecimalFieldNoDotSigned, precision=3),
    dict(length=1, startpos=379, endpos=379, name='Skontierfähig'),
    dict(length=11, startpos=380, endpos=390, name='gewicht_brutto'),
    dict(length=11, startpos=391, endpos=401, name='gewicht_netto'),
    dict(length=1, startpos=402, endpos=402, name='komponentenaufloesung', fieldclass=BooleanField),
    dict(length=5, startpos=403, endpos=407, name='anzahl_komponenten', fieldclass=IntegerField),
    dict(length=2, startpos=408, endpos=409, name='ursprungsland'),
    dict(length=8, startpos=410, endpos=417, name='liefertermin', fieldclass=DateField),
    dict(length=8, startpos=418, endpos=425, name='Kundenwunschtermin', fieldclass=DateField),
    dict(length=1, startpos=496, endpos=496, name='Status'),
]

# fix difference in array counting between SoftM and Python
for feld in FELDERA3:
    feld['startpos'] = feld['startpos'] - 1
A3satzklasse = generate_field_datensatz_class(FELDERA3, name='A3auftragsposition', length=496, doc=doctext)


doctext = 'Auftrags-Positionsrabatte (XOO00EA4)'
FELDERA4 = [
 dict(length=5, startpos=1, endpos=5, name='positionsnr'),
 dict(length=16, startpos=6, endpos=21, name='positionsrabatt_gesamt',
      fieldclass=DecimalFieldNoDotSigned, precision=3),
 dict(length=15, startpos=22, endpos=36, name='positionsrabatt1p',
      fieldclass=DecimalFieldNoDot, precision=3),
 dict(length=1, startpos=37, endpos=37, name='rabattkennzeichen1'),
  # 0 = Rabatt in Prozent
  # 1 = Rabatt als Betrag
 dict(length=16, startpos=38, endpos=53, name='rabattbetrag1', fieldclass=DecimalFieldNoDotSigned, precision=3),
 dict(length=3, startpos=54, endpos=56, name='textschluessel1'),
 dict(length=15, startpos=57, endpos=71, name='positionsrabatt2p',
      fieldclass=DecimalFieldNoDot, precision=3),
 dict(length=1, startpos=72, endpos=72, name='rabattkennzeichen2'),
 dict(length=16, startpos=73, endpos=88, name='rabattbetrag2', fieldclass=DecimalFieldNoDotSigned, precision=3),
 dict(length=3, startpos=89, endpos=91, name='textschluessel2'),
 dict(length=15, startpos=92, endpos=106, name='positionsrabatt3p',
      fieldclass=DecimalFieldNoDot, precision=3),
 dict(length=1, startpos=107, endpos=107, name='rabattkennzeichen3'),
 dict(length=16, startpos=108, endpos=123, name='rabattbetrag3',
      fieldclass=DecimalFieldNoDotSigned, precision=3),
 dict(length=3, startpos=124, endpos=126, name='textschluessel3'),
 dict(length=15, startpos=127, endpos=141, name='positionsrabatt4p',
      fieldclass=DecimalFieldNoDot, precision=3),
 dict(length=1, startpos=142, endpos=142, name='rabattkennzeichen4'),
 dict(length=16, startpos=143, endpos=158, name='rabattbetrag4',
      fieldclass=DecimalFieldNoDotSigned, precision=3),
 dict(length=3, startpos=159, endpos=161, name='textschluessel4'),
 dict(length=15, startpos=162, endpos=176, name='positionsrabatt5p',
      fieldclass=DecimalFieldNoDot, precision=3),
 dict(length=1, startpos=177, endpos=177, name='rabattkennzeichen5'),
 dict(length=16, startpos=178, endpos=193, name='rabattbetrag5',
      fieldclass=DecimalFieldNoDotSigned, precision=3),
 dict(length=3, startpos=194, endpos=196, name='textschluessel5'),
 dict(length=15, startpos=197, endpos=211, name='positionsrabatt6p',
      fieldclass=DecimalFieldNoDot, precision=3),
 dict(length=1, startpos=212, endpos=212, name='rabattkennzeichen6'),
 dict(length=16, startpos=213, endpos=228, name='rabattbetrag6',
      fieldclass=DecimalFieldNoDotSigned, precision=3),
 dict(length=3, startpos=229, endpos=231, name='textschluessel6'),
 dict(length=15, startpos=232, endpos=246, name='positionsrabatt7p',
      fieldclass=DecimalFieldNoDot, precision=3),
 dict(length=1, startpos=247, endpos=247, name='rabattkennzeichen7'),
 dict(length=16, startpos=248, endpos=263, name='rabattbetrag7',
      fieldclass=DecimalFieldNoDotSigned, precision=3),
 dict(length=3, startpos=264, endpos=266, name='textschluessel7'),
 dict(length=15, startpos=267, endpos=281, name='positionsrabatt8p',
      fieldclass=DecimalFieldNoDot, precision=3),
 dict(length=1, startpos=282, endpos=282, name='rabattkennzeichen8'),
 dict(length=16, startpos=283, endpos=298, name='rabattbetrag8',
      fieldclass=DecimalFieldNoDotSigned, precision=3),
 dict(length=3, startpos=299, endpos=301, name='textschluessel8'),
 dict(length=35, startpos=302, endpos=336, name='Gebinde'),
 dict(length=35, startpos=337, endpos=371, name='Gebindebezeichnung'),
 dict(length=5, startpos=372, endpos=376, name='Gebindeanzahl Rechnung'),
 dict(length=15, startpos=377, endpos=391, name='Volumen', fieldclass=DecimalFieldNoDot, precision=5),
 dict(length=104, startpos=392, endpos=495, name='ReserveX5'),
 dict(length=1, startpos=496, endpos=496, name='Status', fieldclass=FixedField, default=' '),
]


# fix difference in array counting between SoftM and Python
for feld in FELDERA4:
    feld['startpos'] = feld['startpos'] - 1
A4satzklasse = generate_field_datensatz_class(FELDERA4, name='A4auftragspositionsrabatte', length=496, doc=doctext)


doctext = 'Auftrags-Position Positionszuschlag (XOO00EA5)'
FELDERA5 = [
    dict(length=5, startpos=1, endpos=5, name='position', fieldclass=IntegerField),
    dict(length=5, startpos=6, endpos=10, name='zusatzposition', fieldclass=IntegerField),
    dict(length=35, startpos=11, endpos=45, name='zuschlagsart'),
    dict(length=16, startpos=46, endpos=61, name='positionszuschlag_netto',
         fieldclass=DecimalFieldNoDotSigned, precision=3),
    dict(length=16, startpos=62, endpos=77, name='positionszuschlag_brutto',
         fieldclass=DecimalFieldNoDotSigned, precision=3),
    dict(length=10, startpos=78, endpos=87, name='zuschlag_gewicht',
         fieldclass=DecimalFieldNoDot, precision=3),
    dict(length=15, startpos=88, endpos=102, name='zuschlag_kurs',
         fieldclass=DecimalFieldNoDot, precision=3),
    dict(length=3, startpos=103, endpos=105, name='zuschlag_einheit'),
    # dict(length=200, startpos=106, endpos=305, name='Reserve 1'),
    # dict(length=191, startpos=306, endpos=495, name='Reserve 2'),
    dict(length=1, startpos=496, endpos=496, name='status', fieldclass=FixedField, default=' ')
]

# fix difference in array counting between SoftM and Python
for feld in FELDERA5:
    feld['startpos'] = feld['startpos'] - 1
A5satzklasse = generate_field_datensatz_class(FELDERA5, name='A5zuschlaege', length=496, doc=doctext)


doctext = 'Auftrags-Position Setkomponenten (XOO00EA6)'
FELDERA6 = [
    dict(length=5, startpos=1, endpos=5, name='position', fieldclass=IntegerField),
    dict(length=5, startpos=6, endpos=10, name='laufende_nr', fieldclass=IntegerField),
    dict(length=35, startpos=11, endpos=45, name='artnr'),
    dict(length=35, startpos=46, endpos=80, name='artnr_kunde'),
    dict(length=35, startpos=81, endpos=115, name='ean', fieldclass=EanField),
    dict(length=35, startpos=116, endpos=150, name='zolltarifnr'),
    dict(length=70, startpos=151, endpos=220, name='bezeichnung'),
    dict(length=70, startpos=221, endpos=290, name='bezeichnung_kunde'),
    dict(length=15, startpos=291, endpos=305, name='menge', fieldclass=DecimalFieldNoDot, precision=3),
    # dict(length=3, startpos=306, endpos=308, name='mengeneinheit'),
    dict(length=4, startpos=309, endpos=312, name='ggvs_klasse'),
    dict(length=1, startpos=496, endpos=496, name='Status', fieldclass=FixedField, default=' '),
]

# fix difference in array counting between SoftM and Python
for feld in FELDERA6:
    feld['startpos'] = feld['startpos'] - 1
A6satzklasse = generate_field_datensatz_class(FELDERA6, name='A6setkomponenten', length=496, doc=doctext)


doctext = 'Bankverbindung (XOO00EA8)'
FELDERA8 = [
    dict(length=35, startpos=1, endpos=35, name='Bankkonto-Nummer'),
    dict(length=15, startpos=36, endpos=50, name='Bankleitzahl'),
    dict(length=35, startpos=51, endpos=85, name='Name-1 der Bank'),
    dict(length=35, startpos=86, endpos=120, name='Name-2 der Bank'),
    dict(length=35, startpos=121, endpos=155, name='Straße'),
    dict(length=35, startpos=156, endpos=190, name='PLZ / Ort'),
    dict(length=1, startpos=496, endpos=496, name='Status'),
]

# fix difference in array counting between SoftM and Python
for feld in FELDERA8:
    feld['startpos'] = feld['startpos'] - 1
A8satzklasse = generate_field_datensatz_class(FELDERA8, name='A8bankverbundung', length=496, doc=doctext)


doctext = 'Auftrags-Endedaten (XOO00EA9)'
FELDERA9 = [
    dict(length=16, startpos=1, endpos=16, name='gesamtbetrag', fieldclass=DecimalFieldNoDotSigned, precision=3),
    dict(length=16, startpos=17, endpos=32, name='nettowarenwert', fieldclass=DecimalFieldNoDotSigned, precision=3),
    dict(length=16, startpos=33, endpos=48, name='skontofaehig', fieldclass=DecimalFieldNoDotSigned, precision=3),
    dict(length=16, startpos=49, endpos=64, name='steuerpflichtig_ust1', fieldclass=DecimalFieldNoDotSigned, precision=3),
    dict(length=16, startpos=65, endpos=80, name='steuerpflichtig_ust2', fieldclass=DecimalFieldNoDotSigned, precision=3),
    dict(length=16, startpos=81, endpos=96, name='skontoabzug', fieldclass=DecimalFieldNoDotSigned, precision=3),
    dict(length=16, startpos=97, endpos=112, name='mehrwertsteuer', fieldclass=DecimalFieldNoDotSigned, precision=3),

    dict(length=5, startpos=113, endpos=117, name='steuersatz1', fieldclass=DecimalFieldNoDot, precision=2),
    dict(length=16, startpos=118, endpos=133, name='steuerbetrag1', fieldclass=DecimalFieldNoDotSigned, precision=3),
    dict(length=5, startpos=134, endpos=138, name='steuersatz2', fieldclass=DecimalFieldNoDot, precision=2),
    dict(length=16, startpos=139, endpos=154, name='steuerbetrag2', fieldclass=DecimalFieldNoDotSigned, precision=3),

    dict(length=16, startpos=155, endpos=170, name='nettowarenwert1', fieldclass=DecimalFieldNoDotSigned, precision=3),
    dict(length=16, startpos=171, endpos=186, name='nettowarenwert2', fieldclass=DecimalFieldNoDotSigned, precision=3),
    dict(length=16, startpos=187, endpos=202, name='versandkosten1', fieldclass=DecimalFieldNoDotSigned, precision=3),
    dict(length=16, startpos=203, endpos=218, name='versandkosten2', fieldclass=DecimalFieldNoDotSigned, precision=3),

    dict(length=16, startpos=219, endpos=234, name='verpackungskosten1', fieldclass=DecimalFieldNoDotSigned, precision=3),
    dict(length=16, startpos=235, endpos=250, name='verpackungskosten2', fieldclass=DecimalFieldNoDotSigned, precision=3),
    dict(length=16, startpos=251, endpos=266, name='nebenkosten1', fieldclass=DecimalFieldNoDotSigned, precision=3),
    dict(length=16, startpos=267, endpos=282, name='nebenkosten2', fieldclass=DecimalFieldNoDotSigned, precision=3),
    dict(length=16, startpos=283, endpos=298, name='summe_rabatte', fieldclass=DecimalFieldNoDotSigned, precision=3),
    dict(length=16, startpos=299, endpos=314, name='summe_zuschlaege', fieldclass=DecimalFieldNoDotSigned, precision=3),

    dict(length=15, startpos=315, endpos=329, name='kopfrabatt1_prozent', fieldclass=DecimalFieldNoDot, precision=3),
    dict(length=15, startpos=330, endpos=344, name='kopfrabatt2_prozent', fieldclass=DecimalFieldNoDot, precision=3),

    # Vorzeichen Kopfrabatt...

    dict(length=15, startpos=347, endpos=361, name='kopfrabatt1', fieldclass=DecimalFieldNoDot, precision=3),
    dict(length=15, startpos=362, endpos=376, name='kopfrabatt2', fieldclass=DecimalFieldNoDot, precision=3),

    dict(length=3, startpos=377, endpos=379, name='textschluessel1'),
    dict(length=3, startpos=380, endpos=382, name='textschluessel2'),

    dict(length=16, startpos=383, endpos=398, name='kopfrabatt_ust1', fieldclass=DecimalFieldNoDotSigned, precision=3),
    dict(length=16, startpos=399, endpos=414, name='kopfrabatt_ust2', fieldclass=DecimalFieldNoDotSigned, precision=3),

    dict(length=11, startpos=415, endpos=425, name='gesamtgewicht_brutto', fieldclass=DecimalFieldNoDot, precision=3),
    dict(length=11, startpos=426, endpos=436, name='gesamtgewicht_netto', fieldclass=DecimalFieldNoDot, precision=3),

    dict(length=4, startpos=437, endpos=440, name='anzahl_positionen', fieldclass=IntegerField),
    dict(length=1, startpos=496, endpos=496, name='Status'),
]

# fix difference in array counting between SoftM and Python
for feld in FELDERA9:
    feld['startpos'] = feld['startpos'] - 1
A9satzklasse = generate_field_datensatz_class(FELDERA9, name='A9auftragsendedaten', length=496, doc=doctext)


doctext = 'XOO00EFA Rg-Adresse'
FELDERFA = [
 dict(length=17, startpos=1, endpos=17, name='iln_rechnungsempfaenger', doc='119-03 bei StratEDI 119-02=IV'),
 dict(length=17, startpos=18, endpos=34, name='eigene ILN beim Re'),
 dict(length=17, startpos=35, endpos=51, name='rechnungsempfaenger', fieldclass=IntegerField),
 dict(length=35, startpos=52, endpos=86, name='rechnung_name1', doc='119-04 bei StratEDI 119-02=IV'),
 dict(length=35, startpos=87, endpos=121, name='rechnung_name2', doc='119-05 bei StratEDI 119-02=IV'),
 dict(length=35, startpos=122, endpos=156, name='rechnung_name3', doc='119-06 bei StratEDI 119-02=IV'),
 #dict(length=35, startpos=157, endpos=191, name='rechnung Name 4'),
 dict(length=35, startpos=192, endpos=226, name='rechnung_strasse', doc='119-07 bei StratEDI 119-02=IV'),
 dict(length=3, startpos=227, endpos=229, name='rechnung_land', doc='119-12 bei StratEDI 119-02=IV'),
 dict(length=9, startpos=230, endpos=238, name='rechnung_plz', doc='119-10 bei StratEDI 119-02=IV'),
 dict(length=35, startpos=239, endpos=273, name='rechnung_ort', doc='119-11 bei StratEDI 119-02=IV'),
 dict(length=222, startpos=274, endpos=495, name='ReserveX2', fieldclass=FixedField, default=' ' * 222),
 dict(length=1, startpos=496, endpos=496, name='Status'),
]
# fix difference in array counting between SoftM and Python
for feld in FELDERFA:
    feld['startpos'] = feld['startpos'] - 1
FAsatzklasse = generate_field_datensatz_class(FELDERFA, name='FArechnungsadresse', length=496, doc=doctext)


doctext = 'XOO00EF2: Rechnungs-Kopf Lieferdaten'
FELDERF2 = [
 dict(length=17, startpos=1, endpos=17, name='iln_warenempfaenger', doc='119-03 bei StratEDI 119-02=DP'),
 dict(length=17, startpos=18, endpos=34, name='warenempfaenger', fieldclass=IntegerField),
 # dict(length=17, startpos=35, endpos=51, name='eigene ILN beim WaEmpf'),
 dict(length=17, startpos=52, endpos=68, name='lieferantennr'),
 dict(length=17, startpos=69, endpos=85, name='liefer_iln'),
 dict(length=35, startpos=86, endpos=120, name='liefer_name1', doc='119-04 bei StratEDI 119-02=DP'),
 dict(length=35, startpos=121, endpos=155, name='liefer_name2', doc='119-05 bei StratEDI 119-02=DP'),
 dict(length=35, startpos=156, endpos=190, name='liefer_name3', doc='119-06 bei StratEDI 119-02=DP'),
 # dict(length=35, startpos=191, endpos=225, name='LfAdr: Name 4'),
 dict(length=35, startpos=226, endpos=260, name='liefer_strasse', doc='119-07 bei StratEDI 119-02=DP'),
 dict(length=3, startpos=261, endpos=263, name='liefer_land', doc='119-12 bei StratEDI 119-02=DP'),
 dict(length=9, startpos=264, endpos=272, name='liefer_plz', doc='119-10 bei StratEDI 119-02=DP'),
 dict(length=35, startpos=273, endpos=307, name='liefer_ort', doc='119-11 bei StratEDI 119-02=DP'),
 # dict(length=30, startpos=308, endpos=337, name='Lagerbezeichnung'),
 # dict(length=3, startpos=338, endpos=340, name='versandart'),
 # dict(length=3, startpos=341, endpos=343, name='lieferbedingung'),
 dict(length=17, startpos=344, endpos=360, name='verband', fieldclass=IntegerField),
 dict(length=17, startpos=361, endpos=377, name='verband_iln', fieldclass=EanField),
 dict(length=17, startpos=378, endpos=394, name='besteller_iln', fieldclass=EanField),
 dict(length=35, startpos=395, endpos=429, name='Bezogene Rechnungsnummer', fieldclass=IntegerField),
 dict(length=50, startpos=430, endpos=479, name='ReserveX3', fieldclass=FixedField, default=' ' * 50),
 dict(length=16, startpos=480, endpos=495, name='ReserveX3a'),
 dict(length=1, startpos=496, endpos=496, name='Status', fieldclass=FixedField, default=' '),
]


#    dict(length=8,  startpos=0,   endpos=  8, name='lieferdatum_fix', fieldclass=DateField),
#    dict(length=4,  startpos= 32, endpos= 36, name='lieferzeit_bis', fieldclass=TimeField),
#    dict(length=3,  startpos= 36, endpos= 39, name='valutatage', fieldclass=IntegerField),
#    dict(length= 5, startpos= 39, endpos= 44, name='rabatt1', fieldclass=DecimalField, precision=2,

# fix difference in array counting between SoftM and Python
for feld in FELDERF2:
    feld['startpos'] = feld['startpos'] - 1
F2satzklasse = generate_field_datensatz_class(FELDERF2, name='F2kopfdatenzusatz', length=496, doc=doctext)


doctext = 'Rechnungs-Position (XOO00EF3)'
FELDERF3 = [
 dict(length=5, startpos=1, endpos=5, name='positionsnr', fieldclass=IntegerField, doc='500-02 bei StratEDI'),
 dict(length=35, startpos=6, endpos=40, name='artnr', doc='500-05 bei StratEDI'),
 dict(length=35, startpos=41, endpos=75, name='artnr_kunde', doc='500-06 bei StratEDI'),
 dict(length=35, startpos=76, endpos=110, name='ean', fieldclass=EanField, doc='500-04 bei StratEDI'),
 dict(length=35, startpos=111, endpos=145, name='zolltarifnummer'),
 dict(length=70, startpos=146, endpos=215, name='artikelbezeichnung', doc='500-08 und 500-09 bei StratEDI'),
 dict(length=70, startpos=216, endpos=285, name='artikelbezeichnung_kunde'),
 dict(length=15, startpos=286, endpos=300, name='menge', fieldclass=DecimalFieldNoDot, precision=3,
      doc='500-12 bei StratEDI'),
 # dict(length=3, startpos=301, endpos=303, name='mengeneinheit'),
 dict(length=16, startpos=304, endpos=319, name='verkaufspreis',
      fieldclass=DecimalFieldNoDotSigned, precision=3),
 dict(length=3, startpos=320, endpos=322, name='Mengeneinheit Preis'),
 dict(length=1, startpos=323, endpos=323, name='preisdimension', default='0'),
 dict(length=16, startpos=324, endpos=339, name='wert_netto',
      fieldclass=DecimalFieldNoDotSigned, precision=3),
 dict(length=16, startpos=340, endpos=355, name='wert_brutto',
      fieldclass=DecimalFieldNoDotSigned, precision=3),
 dict(length=2, startpos=356, endpos=357, name='mwst_kz'),
 dict(length=5, startpos=358, endpos=362, name='mwstsatz', fieldclass=DecimalFieldNoDot, precision=2,
      doc='500-15 bei StratEDI.'),
 dict(length=16, startpos=363, endpos=378, name='steuerbetrag',
      fieldclass=DecimalFieldNoDotSigned, precision=3),
 dict(length=1, startpos=379, endpos=379, name='skontierfaehig', fieldclass=IntegerField),
 dict(length=11, startpos=380, endpos=390, name='Gewicht brutto'),
 dict(length=11, startpos=391, endpos=401, name='Gewicht netto'),
 dict(length=1, startpos=402, endpos=402, name='komponentenaufloesung', fieldclass=IntegerField),
 dict(length=5, startpos=403, endpos=407, name='Anzahl Komponenten', fieldclass=IntegerField),
 dict(length=2, startpos=408, endpos=409, name='ursprungsland'),
 dict(length=1, startpos=410, endpos=410, name='bonuswuerdig'),
 dict(length=85, startpos=411, endpos=495, name='ReserveX4'),
 dict(length=1, startpos=496, endpos=496, name='Status', fieldclass=FixedField, default=' '),
]
# fix difference in array counting between SoftM and Python
for feld in FELDERF3:
    feld['startpos'] = feld['startpos'] - 1
F3satzklasse = generate_field_datensatz_class(FELDERF3, name='F3positionsdaten', length=496, doc=doctext)


doctext = 'Rechnungs-Position Rabatte (XOO00EF4)'
FELDERF4 = [
    # Seems the SoftM doku is off by one here
 dict(length=5, startpos=1, endpos=5, name='positionsnr'),
 dict(length=16, startpos=6, endpos=21, name='positionsrabatt_gesamt',
      fieldclass=DecimalFieldNoDotSigned, precision=3),
 dict(length=15, startpos=22, endpos=36, name='positionsrabatt1p',
      fieldclass=DecimalFieldNoDot, precision=3),
 dict(length=1, startpos=37, endpos=37, name='rabattkennzeichen1'),
  # 0 = Rabatt in Prozent
  # 1 = Rabatt als Betrag
 dict(length=16, startpos=38, endpos=53, name='rabattbetrag1', fieldclass=DecimalFieldNoDotSigned, precision=3),
 dict(length=3, startpos=54, endpos=56, name='textschluessel1'),
 dict(length=15, startpos=57, endpos=71, name='positionsrabatt2p',
      fieldclass=DecimalFieldNoDot, precision=3),
 dict(length=1, startpos=72, endpos=72, name='rabattkennzeichen2'),
 dict(length=16, startpos=73, endpos=88, name='rabattbetrag2', fieldclass=DecimalFieldNoDotSigned, precision=3),
 dict(length=3, startpos=89, endpos=91, name='textschluessel2'),
 dict(length=15, startpos=92, endpos=106, name='positionsrabatt3p',
      fieldclass=DecimalFieldNoDot, precision=3),
 dict(length=1, startpos=107, endpos=107, name='rabattkennzeichen3'),
 dict(length=15, startpos=108, endpos=122, name='rabattbetrag3',
      fieldclass=DecimalFieldNoDot, precision=3),
 dict(length=1, startpos=123, endpos=123, name='Vorzeichen Rabatt 3'),
 dict(length=3, startpos=124, endpos=126, name='textschluessel3'),
 dict(length=15, startpos=127, endpos=141, name='positionsrabatt4p',
      fieldclass=DecimalFieldNoDot, precision=3),
 dict(length=1, startpos=142, endpos=142, name='rabattkennzeichen4'),
 dict(length=15, startpos=143, endpos=157, name='rabattbetrag4',
      fieldclass=DecimalFieldNoDot, precision=3),
 dict(length=1, startpos=158, endpos=158, name='Vorzeichen Rabatt 4'),
 dict(length=3, startpos=159, endpos=161, name='textschluessel4'),
 dict(length=15, startpos=162, endpos=176, name='positionsrabatt5p',
      fieldclass=DecimalFieldNoDot, precision=3),
 dict(length=1, startpos=177, endpos=177, name='rabattkennzeichen5'),
 dict(length=15, startpos=178, endpos=192, name='rabattbetrag5',
      fieldclass=DecimalFieldNoDot, precision=3),
 dict(length=1, startpos=193, endpos=193, name='Vorzeichen Rabatt 5'),
 dict(length=3, startpos=194, endpos=196, name='textschluessel5'),
 dict(length=15, startpos=197, endpos=211, name='positionsrabatt6p',
      fieldclass=DecimalFieldNoDot, precision=3),
 dict(length=1, startpos=212, endpos=212, name='rabattkennzeichen6'),
 dict(length=15, startpos=213, endpos=227, name='rabattbetrag6',
      fieldclass=DecimalFieldNoDot, precision=3),
 dict(length=1, startpos=228, endpos=228, name='Vorzeichen Rabatt 6'),
 dict(length=3, startpos=229, endpos=231, name='textschluessel6'),
 dict(length=15, startpos=232, endpos=246, name='positionsrabatt7p',
      fieldclass=DecimalFieldNoDot, precision=3),
 dict(length=1, startpos=247, endpos=247, name='rabattkennzeichen7'),
 dict(length=15, startpos=248, endpos=262, name='rabattbetrag7',
      fieldclass=DecimalFieldNoDot, precision=3),
 dict(length=1, startpos=263, endpos=263, name='Vorzeichen Rabatt 7'),
 dict(length=3, startpos=264, endpos=266, name='textschluessel7'),
 dict(length=15, startpos=267, endpos=281, name='positionsrabatt8p',
      fieldclass=DecimalFieldNoDot, precision=3),
 dict(length=1, startpos=282, endpos=282, name='rabattkennzeichen8'),
 dict(length=15, startpos=283, endpos=297, name='rabattbetrag8', fieldclass=DecimalFieldNoDot, precision=3),
 dict(length=1, startpos=298, endpos=298, name='Vorzeichen Rabatt 8'),
 dict(length=3, startpos=299, endpos=301, name='textschluessel8'),
 dict(length=35, startpos=302, endpos=336, name='Gebinde'),
 dict(length=35, startpos=337, endpos=371, name='Gebindebezeichnung'),
 dict(length=5, startpos=372, endpos=376, name='Gebindeanzahl Rechnung'),
 dict(length=15, startpos=377, endpos=391, name='Volumen', fieldclass=DecimalFieldNoDot, precision=5),
 dict(length=104, startpos=392, endpos=495, name='ReserveX5'),
 dict(length=1, startpos=496, endpos=496, name='Status', fieldclass=FixedField, default=' '),
]
# fix difference in array counting between SoftM and Python
for feld in FELDERF4:
    feld['startpos'] = feld['startpos'] - 1
F4satzklasse = generate_field_datensatz_class(FELDERF4, name='F4positionsrabatte', length=496)


doctext = 'Auftrags-Position Positionszuschlag (XOO00EF5)'
FELDERF5 = [
    dict(length=5, startpos=1, endpos=5, name='position', fieldclass=IntegerField),
    dict(length=5, startpos=6, endpos=10, name='zusatzposition', fieldclass=IntegerField),
    dict(length=35, startpos=11, endpos=45, name='zuschlagsart'),
    dict(length=16, startpos=46, endpos=61, name='positionszuschlag_netto',
         fieldclass=DecimalFieldNoDotSigned, precision=3),
    dict(length=16, startpos=62, endpos=77, name='positionszuschlag_brutto',
         fieldclass=DecimalFieldNoDotSigned, precision=3),
    dict(length=9, startpos=78, endpos=86, name='zuschlag_gewicht',
         fieldclass=DecimalFieldNoDot, precision=3),
    dict(length=15, startpos=87, endpos=101, name='zuschlag_kurs',
         fieldclass=DecimalFieldNoDot, precision=3),
    dict(length=3, startpos=102, endpos=104, name='zuschlag_einheit'),
    # dict(length=200, startpos=105, endpos=304, name='Reserve 1'),
    # dict(length=191, startpos=305, endpos=495, name='Reserve 2'),
    dict(length=1, startpos=496, endpos=496, name='status', fieldclass=FixedField, default=' ')
]

# fix difference in array counting between SoftM and Python
for feld in FELDERF5:
    feld['startpos'] = feld['startpos'] - 1
F5satzklasse = generate_field_datensatz_class(FELDERF5, name='F5zuschlaege', length=496, doc=doctext)


doctext = 'Auftrags-Position Setkomponenten (XOO00EF6)'
FELDERF6 = [
    dict(length=5, startpos=1, endpos=5, name='position', fieldclass=IntegerField),
    dict(length=5, startpos=6, endpos=10, name='laufende_nr', fieldclass=IntegerField),
    dict(length=35, startpos=11, endpos=45, name='artnr'),
    dict(length=35, startpos=46, endpos=80, name='artnr_kunde'),
    dict(length=35, startpos=81, endpos=115, name='ean', fieldclass=EanField),
    dict(length=35, startpos=116, endpos=150, name='zolltarifnr'),
    dict(length=70, startpos=151, endpos=220, name='bezeichnung'),
    dict(length=70, startpos=221, endpos=290, name='bezeichnung_kunde'),
    dict(length=15, startpos=291, endpos=305, name='menge', fieldclass=DecimalFieldNoDot, precision=3),
    # dict(length=3, startpos=306, endpos=308, name='mengeneinheit'),
    dict(length=4, startpos=309, endpos=312, name='ggvs_klasse'),
    dict(length=1, startpos=496, endpos=496, name='Status', fieldclass=FixedField, default=' '),
]

# fix difference in array counting between SoftM and Python
for feld in FELDERF6:
    feld['startpos'] = feld['startpos'] - 1
F6satzklasse = generate_field_datensatz_class(FELDERF6, name='F6setkomponenten', length=496, doc=doctext)


doctext = "Rechnungs-Bankverbindung (XOO00EF8)"
FELDERF8 = [
 dict(length=35, startpos=1, endpos=35, name='Bankkonto-Nummer'),
 dict(length=15, startpos=36, endpos=50, name='Bankleitzahl'),
 dict(length=35, startpos=51, endpos=85, name='Name-1 der Bank'),
 dict(length=35, startpos=86, endpos=120, name='Name-2 der Bank'),
 dict(length=35, startpos=121, endpos=155, name='Straße'),
 dict(length=35, startpos=156, endpos=190, name='PLZ / Ort'),
 dict(length=200, startpos=191, endpos=390, name='Reserve 200'),
 dict(length=105, startpos=391, endpos=495, name='Reserve 105'),
 dict(length=1, startpos=496, endpos=496, name='Status'),
]
# fix difference in array counting between SoftM and Python
for feld in FELDERF8:
    feld['startpos'] = feld['startpos'] - 1
F8satzklasse = generate_field_datensatz_class(FELDERF8, name='F8bankverbindung', length=496, doc=doctext)

# ich verstehen nicht, wieso die folgenden Einträge vollkommen von der
# SoftM-EDI-Schnittstellenbeschreibung abweichen.
doctext = 'B.6.9 Rechnungs-Endedaten (XOO00EF9)'
FELDERF9 = [
 dict(length=16, startpos=1, endpos=16, name='gesamtbetrag', fieldclass=DecimalFieldNoDotSigned, precision=3),
 dict(length=16, startpos=17, endpos=32, name='warenwert', fieldclass=DecimalFieldNoDotSigned, precision=3),
 dict(length=16, startpos=33, endpos=48, name='skontofaehig', fieldclass=DecimalFieldNoDotSigned, precision=3),
 dict(length=16, startpos=49, endpos=64, name='steuerpflichtig1', fieldclass=DecimalFieldNoDotSigned, precision=3),
 dict(length=16, startpos=65, endpos=80, name='steuerpflichtig USt 2', fieldclass=FixedField, default='000000000000000+'),
 dict(length=16, startpos=81, endpos=96, name='skontoabzug', fieldclass=DecimalFieldNoDotSigned, precision=3),
 dict(length=16, startpos=97, endpos=112, name='mehrwertsteuer', fieldclass=DecimalFieldNoDotSigned, precision=3),
 dict(length=5, startpos=113, endpos=117, name='mwstsatz', fieldclass=DecimalFieldNoDot, precision=2),
 dict(length=16, startpos=118, endpos=133, name='steuerbetrag1', fieldclass=DecimalFieldNoDotSigned, precision=3),
 dict(length=5, startpos=134, endpos=138, name='steuersatz2', fieldclass=FixedField, default='00000'),
 dict(length=16, startpos=139, endpos=154, name='steuerbetrag2', fieldclass=FixedField, default='000000000000000+'),
 dict(length=16, startpos=155, endpos=170, name='nettowarenwert1', fieldclass=DecimalFieldNoDotSigned, precision=3),
 dict(length=16, startpos=171, endpos=186, name='nettowarenwert2', fieldclass=FixedField, default='000000000000000+'),
 dict(length=16, startpos=187, endpos=202, name='versandkosten1', fieldclass=DecimalFieldNoDotSigned, precision=3),

 dict(length=16, startpos=203, endpos=218, fieldclass=FixedField, default='000000000000000+',
      name="Versandkosten 2"),
 dict(length=16, startpos=219, endpos=234, fieldclass=FixedField, default='000000000000000+',
      name="Verpackungskosten1"),
 dict(length=16, startpos=235, endpos=250, fieldclass=FixedField, default='000000000000000+',
      name="Verpackungskosten2"),
 dict(length=16, startpos=251, endpos=266, fieldclass=FixedField, default='000000000000000+',
      name="Nebenkosten 1"),
 dict(length=16, startpos=267, endpos=282, fieldclass=FixedField, default='000000000000000+',
      name="Nebenkosten 2"),

 dict(length=16, startpos=283, endpos=298, name='summe_rabatte',
      fieldclass=DecimalFieldNoDotSigned, precision=3),
 dict(length=16, startpos=299, endpos=314, name='summe_zuschlaege',
      fieldclass=DecimalFieldNoDotSigned, precision=3),
 dict(length=15, startpos=315, endpos=329, name='kopfrabatt1_prozent',
      fieldclass=DecimalFieldNoDot, precision=3),
 dict(length=15, startpos=330, endpos=344, name='kopfrabatt2_prozent',
      fieldclass=DecimalFieldNoDot, precision=3),
 dict(length=1, startpos=345, endpos=345, name='kopfrabatt1_vorzeichen', fieldclass=FixedField, default='+'),
 dict(length=1, startpos=346, endpos=346, name='kopfrabatt2_vorzeichen', fieldclass=FixedField, default='+'),
 #     1  0  345   Vorzeichen Kopfrabatt 1
 #dict(length=1, startpos=346, endpos=346, name='Vorzeichen Kopfrabatt 2'),
 #     1  0     Vorzeichen Kopfrabatt 2
 dict(length=15, startpos=347, endpos=361, name='kopfrabatt1', fieldclass=DecimalFieldNoDot, precision=3),
 dict(length=15, startpos=362, endpos=376, name='kopfrabatt2', fieldclass=DecimalFieldNoDot, precision=3),
 dict(length=3, startpos=377, endpos=379, name='kopfrabatt1_text'),
 dict(length=3, startpos=380, endpos=382, name='kopfrabatt2_text'),
 dict(length=16, startpos=383, endpos=398, name='KopfrabattUSt1',
      fieldclass=DecimalFieldNoDotSigned, precision=3),
 dict(length=16, startpos=399, endpos=414, name='KopfrabattUSt2',
      fieldclass=FixedField, default='000000000000000+'),
 dict(length=11, startpos=415, endpos=425, name='Gesamtgewicht brutto', fieldclass=IntegerField),
 dict(length=11, startpos=426, endpos=436, name='Gesamtgewicht netto', fieldclass=IntegerField),
 dict(length=4, startpos=437, endpos=440, name='Anzahl Positionen', fieldclass=IntegerField),
 dict(length=55, startpos=441, endpos=495, name='filler', fieldclass=FixedField, default=' ' * 55),
 dict(length=1, startpos=496, endpos=496, name='status', fieldclass=FixedField, default=' '),
]
# fix difference in array counting between SoftM and Python
for feld in FELDERF9:
    feld['startpos'] = feld['startpos'] - 1
F9satzklasse = generate_field_datensatz_class(FELDERF9, name='F9rechnungsendedaten', length=496, doc=doctext)


doctext = 'Rechnungsliste Position (XOO00ER2)'
FELDERER = [
 dict(length=17, startpos=1, endpos=17, name='ILN Rechnungsempfänger'),
 dict(length=17, startpos=18, endpos=34, name='Mitgliedsnummer'),
 dict(length=17, startpos=35, endpos=51, name='ILN Warenempfänger'),
 dict(length=9, startpos=52, endpos=60, name='Rechnungsliste'),
 dict(length=8, startpos=61, endpos=68, name='Rechnungslistendatum'),
 dict(length=5, startpos=69, endpos=73, name='Positionsnummer'),
 dict(length=9, startpos=74, endpos=82, name='Rechnung'),
 dict(length=8, startpos=83, endpos=90, name='Rechnungsdatum'),
 dict(length=8, startpos=91, endpos=98, name='valutadatum'),
 dict(length=9, startpos=99, endpos=107, name='Lieferschein'),
 dict(length=8, startpos=108, endpos=115, name='Lieferdatum'),
 dict(length=9, startpos=116, endpos=124, name='Auftragsnummer'),
 dict(length=20, startpos=125, endpos=144, name='Kundenbestellnummer'),
 dict(length=8, startpos=145, endpos=152, name='Kundenbestelldatum'),
 dict(length=3, startpos=153, endpos=155, name='ISO-WSL'),
 dict(length=15, startpos=156, endpos=170, name='Warenwert gesamt'),
 dict(length=1, startpos=171, endpos=171, name='Vorzeichen Warenwert'),
 dict(length=15, startpos=172, endpos=186, name='Nebenkosten'),
 dict(length=1, startpos=187, endpos=187, name='Vorzeichen Nebenkosten'),
 dict(length=15, startpos=188, endpos=202, name='Verpackungskosten'),
 dict(length=1, startpos=203, endpos=203, name='Vorzeichen Verpackungskosten'),
 dict(length=15, startpos=204, endpos=218, name='Versandkosten'),
 dict(length=1, startpos=219, endpos=219, name='Vorzeichen Versandkosten'),
 dict(length=15, startpos=220, endpos=234, name='Skonto-Abzug'),
 dict(length=1, startpos=235, endpos=235, name='Vorzeichen Skonto-Abzug'),
 dict(length=2, startpos=236, endpos=237, name='Kz Mehrwertsteuer'),
 dict(length=5, startpos=238, endpos=242, name='Steuersatz in %'),
 dict(length=15, startpos=243, endpos=257, name='steuerbetrag'),
 dict(length=1, startpos=258, endpos=258, name='Vorzeichen Steuerbetrag'),
 dict(length=15, startpos=259, endpos=273, name='Provision 1'),
 dict(length=1, startpos=274, endpos=274, name='Vorzeichen Prov halbe Steuer'),
 dict(length=15, startpos=275, endpos=289, name='Steuer zu Provision 1'),
 dict(length=1, startpos=290, endpos=290, name='Vorzeichen Steuer zu Prov 1'),
 dict(length=15, startpos=291, endpos=305, name='Provision 2'),
 dict(length=1, startpos=306, endpos=306, name='Vorzeichen Prov volle Steuer'),
 dict(length=15, startpos=307, endpos=321, name='Steuer zu Provision 2'),
 dict(length=1, startpos=322, endpos=322, name='Vorzeichen Steuer zu Prov 1'),
 dict(length=15, startpos=323, endpos=337, name='Rechnungsendbetrag'),
 dict(length=1, startpos=338, endpos=338, name='Vorzeichen Endbetrag'),
 dict(length=157, startpos=339, endpos=495, name='ReserveX6'),
 dict(length=1, startpos=496, endpos=496, name='Status'),
]
# fix difference in array counting between SoftM and Python
for feld in FELDERER:
    feld['startpos'] = feld['startpos'] - 1
ERsatzklasse = generate_field_datensatz_class(FELDERER, name='ERrechnungslisteposition',
                                              length=496, doc=doctext)


doctext = 'Rechnungsliste Verband (XOO00ER1)'
FELDERR1 = [
 dict(length=17, startpos=1, endpos=17, name='verband_iln', fieldclass=EanField),
 dict(length=17, startpos=18, endpos=34, name='eigene_iln', fieldclass=FixedField,
      default='4005998000007    '),
 dict(length=17, startpos=35, endpos=51, name='lieferantennr_verband'),
 #dict(length=17, startpos=52, endpos=68, name='Abs.: UST-Identnummer'),
 #dict(length=2, startpos=69, endpos=70, name='Firma'),
 #dict(length=4, startpos=71, endpos=74, name='Abteilung'),
 #dict(length=10, startpos=75, endpos=84, name='Bibliothek'),
 dict(length=200, startpos=85, endpos=284, name='filler1', fieldclass=FixedField, default=' ' * 200),
 dict(length=200, startpos=285, endpos=484, name='filler2', fieldclass=FixedField, default=' ' * 200),
 dict(length=11, startpos=485, endpos=495, name='filler3', fieldclass=FixedField, default=' ' * 11),
 dict(length=1, startpos=496, endpos=496, name='status', fieldclass=FixedField, default=' '),
]
# fix difference in array counting between SoftM and Python
for feld in FELDERR1:
    feld['startpos'] = feld['startpos'] - 1
R1satzklasse = generate_field_datensatz_class(FELDERR1, name='R1verbandsrechnungsliste',
                                              length=496, doc=doctext)


doctext = 'Rechnungsliste Position (XOO00ER2)'
FELDERR2 = [
    dict(length=17, startpos=1, endpos=17, name='rechnung_iln', fieldclass=EanField),
    dict(length=17, startpos=18, endpos=34, name='mitgliedsnummer'),
    dict(length=17, startpos=35, endpos=51, name='liefer_iln', fieldclass=EanField),
    dict(length=9, startpos=52, endpos=60, name='listennr', fieldclass=IntegerField),
    dict(length=8, startpos=61, endpos=68, name='listendatum', fieldclass=DateField),
    #dict(length=5, startpos=69, endpos=73, name='Positionsnummer'),
    #dict(length=9, startpos=74, endpos=82, name='Rechnung'),
    #dict(length=8, startpos=83, endpos=90, name='Rechnungsdatum'),
    #dict(length=8, startpos=91, endpos=98, name='valutadatum'),
    #dict(length=9, startpos=99, endpos=107, name='Lieferschein'),
    #dict(length=8, startpos=108, endpos=115, name='Lieferdatum'),
    #dict(length=9, startpos=116, endpos=124, name='Auftragsnummer'),
    #dict(length=20, startpos=125, endpos=144, name='Kundenbestellnummer'),
    #dict(length=8, startpos=145, endpos=152, name='Kundenbestelldatum'),
    dict(length=3, startpos=153, endpos=155, name='waehrung'),
    dict(length=16, startpos=156, endpos=171, name='warenwert',
         fieldclass=DecimalFieldNoDotSigned, precision=3),
    dict(length=15, startpos=172, endpos=186, name='nebenkosten'),
    dict(length=1, startpos=187, endpos=187, name='Vorzeichen Nebenkosten'),
    dict(length=15, startpos=188, endpos=202, name='Verpackungskosten'),
    dict(length=1, startpos=203, endpos=203, name='Vorzeichen Verpackungskosten'),
    dict(length=15, startpos=204, endpos=218, name='versandkosten'),
    dict(length=1, startpos=219, endpos=219, name='Vorzeichen Versandkosten'),
    dict(length=16, startpos=220, endpos=235, name='skonto_abzug', fieldclass=DecimalFieldNoDotSigned, precision=3),
    # dict(length=1, startpos=235, endpos=235, name='Vorzeichen Skonto-Abzug'),
    dict(length=2, startpos=236, endpos=237, name='Kz Mehrwertsteuer'),
    dict(length=5, startpos=238, endpos=242, name='steuersatz_prozent'),
    dict(length=16, startpos=243, endpos=258, name='mwst', fieldclass=DecimalFieldNoDotSigned, precision=3),
    # dict(length=1, startpos=258, endpos=258, name='Vorzeichen Steuerbetrag'),
    dict(length=15, startpos=259, endpos=273, name='Provision 1'),
    dict(length=1, startpos=274, endpos=274, name='Vorzeichen Prov halbe Steuer'),
    dict(length=15, startpos=275, endpos=289, name='Steuer zu Provision 1'),
    dict(length=1, startpos=290, endpos=290, name='Vorzeichen Steuer zu Prov 1'),
    dict(length=15, startpos=291, endpos=305, name='Provision 2'),
    dict(length=1, startpos=306, endpos=306, name='Vorzeichen Prov volle Steuer'),
    dict(length=15, startpos=307, endpos=321, name='Steuer zu Provision 2'),
    dict(length=1, startpos=322, endpos=322, name='Vorzeichen Steuer zu Prov 1'),
    dict(length=15, startpos=323, endpos=337, name='Rechnungsendbetrag'),
    dict(length=1, startpos=338, endpos=338, name='Vorzeichen Endbetrag'),
    dict(length=157, startpos=339, endpos=495, name='filler', fieldclass=FixedField, default=' ' * 157),
    dict(length=1, startpos=496, endpos=496, name='status', fieldclass=FixedField, default=' '),
]
# fix difference in array counting between SoftM and Python
for feld in FELDERR2:
    feld['startpos'] = feld['startpos'] - 1
R2satzklasse = generate_field_datensatz_class(FELDERR2, name='R2rechnungslisteposition',
                                              length=496, doc=doctext)


doctext = 'Rechnungsliste Summe (XOO00ER3)'
FELDERR3 = [
 # dict(length=5, startpos=1, endpos=5, name='Anzahl Positionen'),
 dict(length=16, startpos=6, endpos=21, name='summe', fieldclass=DecimalFieldNoDotSigned, precision=3),
 dict(length=3, startpos=22, endpos=24, name='waehrung'),
 #dict(length=12, startpos=25, endpos=36, name='Umrechnungskurs'),
 #dict(length=1, startpos=37, endpos=37, name='Faktor für Umrechnungskurs'),
 dict(length=200, startpos=38, endpos=237, name='filler1', fieldclass=FixedField, default=' ' * 200),
 dict(length=200, startpos=238, endpos=437, name='filler2', fieldclass=FixedField, default=' ' * 200),
 dict(length=58, startpos=438, endpos=495, name='filler3', fieldclass=FixedField, default=' ' * 58),
 dict(length=1, startpos=496, endpos=496, name='status', fieldclass=FixedField, default=' '),
]
# fix difference in array counting between SoftM and Python
for feld in FELDERR3:
    feld['startpos'] = feld['startpos'] - 1
R3satzklasse = generate_field_datensatz_class(FELDERR3, name='R3verbandsrechnungslistensummen',
                                              length=496, doc=doctext)

FELDERTEXT = [
 dict(length=60, startpos=1, endpos=60, name='textzeile1'),
 dict(length=60, startpos=61, endpos=120, name='textzeile2'),
 dict(length=60, startpos=121, endpos=180, name='textzeile3'),
 dict(length=60, startpos=181, endpos=240, name='textzeile4'),
 dict(length=60, startpos=241, endpos=300, name='textzeile5'),
 dict(length=60, startpos=301, endpos=360, name='textzeile6'),
 dict(length=60, startpos=361, endpos=420, name='textzeile7'),
 dict(length=60, startpos=421, endpos=480, name='textzeile8'),
 dict(length=15, startpos=481, endpos=495, name='ReserveX7'),
 dict(length=1, startpos=496, endpos=496, name='Status'),
]
# fix difference in array counting between SoftM and Python
for feld in FELDERTEXT:
    feld['startpos'] = feld['startpos'] - 1
TEXTsatzklasse = generate_field_datensatz_class(FELDERTEXT, name='generic_text', length=496)


# from http://stackoverflow.com/questions/1305532/convert-python-dict-to-object
# see huTools.structured.Struct for a more sophisticated implementation.
class Struct:
    def __init__(self, **entries):
        self.__dict__.update(entries)

    def __repr__(self):
        return "<Struct: %r>" % self.__dict__


def parse_to_objects(lines):
    """Implementiert das Parsen einer liste von SoftM EDI-Datensätzen in Objekte."""
    satzresolver = dict(XH=XHsatzklasse,
        F1=F1satzklasse,
        F2=F2satzklasse,
        F3=F3satzklasse,
        F4=F4satzklasse,  # Rabatte
        F5=F5satzklasse,
        F6=F6satzklasse,
        # F7 Chargen
        F8=F8satzklasse,  # Bankverbindung
        F9=F9satzklasse,  # Rechnungsende
        # ER=ERsatzklasse,

        A1=A1satzklasse,
        A2=A2satzklasse,
        A3=A3satzklasse,
        A4=A4satzklasse,
        A5=A5satzklasse,
        A6=A6satzklasse,
        A8=A8satzklasse,
        A9=A9satzklasse,
        AV=generate_field_datensatz_class(FELDERTEXT, name='versandarttext', length=496),
        AL=generate_field_datensatz_class(FELDERTEXT, name='lieferbedinungstext', length=496),
        AN=generate_field_datensatz_class(FELDERTEXT, name='nebenkostentext', length=496),
        AK=generate_field_datensatz_class(FELDERTEXT, name='kopftext', length=496),
        AP=generate_field_datensatz_class(FELDERTEXT, name='positionstext', length=496),
        AX=generate_field_datensatz_class(FELDERTEXT, name='kopfrabatttext', length=496),
        AE=generate_field_datensatz_class(FELDERTEXT, name='endetext', length=496),
        AR=generate_field_datensatz_class(FELDERTEXT, name='positionsrabatttext', length=496),

        R1=R1satzklasse,
        R2=R2satzklasse,
        R3=R3satzklasse,
        FA=FAsatzklasse,
        FR=generate_field_datensatz_class(FELDERTEXT, name='positionsrabatttext', length=496),
        FP=generate_field_datensatz_class(FELDERTEXT, name='positionstext', length=496),
        FK=generate_field_datensatz_class(FELDERTEXT, name='kopftext', length=496),
        FX=generate_field_datensatz_class(FELDERTEXT, name='kopfrabatttext', length=496),
        FE=generate_field_datensatz_class(FELDERTEXT, name='endtexte', length=496),
        # FV Versandarttexte
        # FL Lieferbedingungstexte
        # FN Nebenkosten
        )
    ret = []
    lineno = 0
    for rawline in lines:
        lineno += 1
        # remove newline & EOF
        line = rawline.rstrip('\r\n').strip(' \x1a')
        if not line:
            # skip empty lines
            continue
        # remove erstellungsdatum
        erstellungsdatum = line[519:]
        line = line[:519]
        # remove line-header
        line = line[19:]
        # pad line if it is to short now
        line = "% 500s" % line
        satzart, version, data = line[:2], line[2:4], line[4:]
        satzklasse = satzresolver.get(satzart, None)
        if satzklasse:
            satz = satzklasse()
            satz.parse(data)
            ret.append((satzart, Struct(**satz.as_dict())))
            del satz
        else:
            print "Zeile %s:" % lineno, repr(satzart), repr(version), repr(erstellungsdatum),
            print len(line), len(data)
            print "unbekannter Satz:", satzart, version
            print repr(rawline)
            raise RuntimeError("unbekannter Satz: %r %r" % (str(satzart), str(version)))
    return ret
