#!/usr/bin/env python
# encoding: utf-8
"""
datenexportschnittstelle.py - Read the SoftM EDI Datenexportschnittstelle (INVOIC/DESADV)

Based on trunk/web/MoftS/lib/pySoftM/EDI.py

Created by Maximillian Dornseif on 2007-05-07.
Copyright (c) 2007, 2008 HUDORA GmbH. All rights reserved.
"""


import datetime
import os
from edilib.recordbased import generate_field_datensatz_class, DateField, TimeField
from edilib.recordbased import IntegerField, DecimalFieldNoDot, DecimalFieldNoDotSigned, FixedField, EanField

class enterfieldhere(object):
    def __init__(self):
        assert(0)
    pass


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
 dict(length=3, startpos=288, endpos=290, name='waehrung', fieldclass=FixedField, default='EUR',
      doc='ISO Währungsschlüssel'),
 dict(length=5, startpos=291, endpos=295, name='ust1_fuer_skonto', fieldclass=DecimalFieldNoDot, precision=2),
 dict(length=5, startpos=296, endpos=300, name='ust2_fuer_skonto', fieldclass=DecimalFieldNoDot, precision=2),
 dict(length=15, startpos=301, endpos=315, name='Skontofähig USt 1'),
 # FIXME: warum laufen ab hier die Spalten anders als in der SoftM Doku???
 dict(length=1, startpos=316, endpos=316, name='Vorzeichen Skontofähig 1'),
 dict(length=15, startpos=317, endpos=331, name='Skontofähig USt 2'),
 dict(length=1, startpos=332, endpos=332, name='Vorzeichen Skontofähig 2'),
 dict(length=8, startpos=333, endpos=340, name='skontodatum1'),
 dict(length=3, startpos=341, endpos=343, name='skontotage1'),
 dict(length=5, startpos=344, endpos=348, name='skonto1', fieldclass=DecimalFieldNoDot, precision=2),
 dict(length=16, startpos=349, endpos=364, name='skontobetrag1_ust1',
     fieldclass=DecimalFieldNoDotSigned, precision=3),
 #dict(length=1, startpos=364, endpos=364, name='Vorzeichen Skontobetrag 1'),
 dict(length=15, startpos=365, endpos=379, name='Skontobetrag 1 USt 2'),
 dict(length=1, startpos=380, endpos=380, name='Vorzeichen Skontobetrag 12'),
 dict(length=8, startpos=381, endpos=388, name='Skontodatum 2'),
 dict(length=3, startpos=389, endpos=391, name='Skontotage 2'),
 dict(length=5, startpos=392, endpos=396, name='Skonto 2'),
 dict(length=15, startpos=397, endpos=411, name='Skontobetrag 2 USt 1'),
 dict(length=1, startpos=412, endpos=412, name='Vorzeichen Skontobetrag 2 USt 1'),
 dict(length=15, startpos=413, endpos=427, name='Skontobetrag 2 USt 2'),
 dict(length=1, startpos=428, endpos=428, name='Vorzeichen Skontobetrag 2 USt 2'),
 dict(length=8, startpos=429, endpos=436, name='Nettodatum'),
 dict(length=3, startpos=437, endpos=439, name='valutatage', fieldclass=IntegerField),
 dict(length=8, startpos=440, endpos=447, name='valutadatum', fieldclass=DateField),
 dict(length=2, startpos=448, endpos=449, name='Firma', fieldclass=FixedField, default='01'),
 dict(length=4, startpos=450, endpos=453, name='Abteilung'),
 dict(length=10, startpos=454, endpos=463, name='Bibliothek'),
 dict(length=3, startpos=464, endpos=466, name='nettotage'),
 dict(length=14, startpos=467, endpos=480, name='steuernummer'),
 # TODO: there seems to be something in this field!
 dict(length=15, startpos=481, endpos=495, name='filler'), # fieldclass=FixedField, default=' ' * 15),
 dict(length=1, startpos=496, endpos=496, name='Status', fieldclass=FixedField, default=' '),
]
# fix difference in array counting between SoftM and Python
for feld in FELDERF1:
    feld['startpos'] = feld['startpos'] - 1
F1satzklasse = generate_field_datensatz_class(FELDERF1, name='F1kopfdaten', length=496, doc=doctext)


doctext = 'Auftrags-Kopf (XOO00EA1)'
FELDERA1 = [
 dict(length=3, startpos=1, endpos=3, name='Belegart'),
 dict(length=9, startpos=4, endpos=12, name='Auftrag'),
 dict(length=8, startpos=13, endpos=20, name='Auftragsdatum'),
 dict(length=8, startpos=21, endpos=28, name='AB Druckdatum'),
 dict(length=20, startpos=29, endpos=48, name='Kundenbestellnummer'),
 dict(length=8, startpos=49, endpos=56, name='Kundenbestelldatum'),
 dict(length=17, startpos=57, endpos=73, name='ILN Rechnungsempfänger'),
 dict(length=17, startpos=74, endpos=90, name='Rechnungsempfänger'),
 dict(length=17, startpos=91, endpos=107, name='USt-IDNr. RgEmpf'),
 dict(length=17, startpos=108, endpos=124, name='eigene ILN beim RgEmpf'),
 dict(length=17, startpos=125, endpos=141, name='unsere LiNr beim RgEmpf'),
 dict(length=17, startpos=142, endpos=158, name='eigene USt-IDNr.'),
 dict(length=3, startpos=159, endpos=161, name='ISO-WSL'),
 dict(length=5, startpos=162, endpos=166, name='USt 1 für Skonto'),
 dict(length=5, startpos=167, endpos=171, name='USt 2 für Skonto'),
 dict(length=15, startpos=172, endpos=186, name='Skontofähig USt 1'),
 dict(length=15, startpos=187, endpos=201, name='Skontofähig USt 2'),
 dict(length=3, startpos=202, endpos=204, name='Skontotage 1'),
 dict(length=5, startpos=205, endpos=209, name='Skonto 1'),
 dict(length=15, startpos=210, endpos=224, name='Skontobetrag 1 USt 1'),
 dict(length=15, startpos=225, endpos=239, name='Skontobetrag 1 USt 2'),
 dict(length=3, startpos=240, endpos=242, name='Skontotage 2'),
 dict(length=5, startpos=243, endpos=247, name='Skonto 2'),
 dict(length=15, startpos=248, endpos=262, name='Skontobetrag 2 USt 1'),
 dict(length=15, startpos=263, endpos=277, name='Skontobetrag 2 USt 2'),
 dict(length=60, startpos=278, endpos=337, name='Skontotext'),
 dict(length=2, startpos=338, endpos=339, name='Firma'),
 dict(length=4, startpos=340, endpos=343, name='Abteilung'),
 dict(length=10, startpos=344, endpos=353, name='Bibliothek'),
 dict(length=142, startpos=354, endpos=495, name='Reserve'),
 dict(length=1, startpos=496, endpos=496, name='Status'),
]
# fix difference in array counting between SoftM and Python
for feld in FELDERA1:
    feld['startpos'] = feld['startpos'] - 1
A1satzklasse = generate_field_datensatz_class(FELDERA1, name='A1auftragskopf', length=496, doc=doctext)

doctext = 'XOO00EFA Rg-Adresse'
FELDERFA = [
 dict(length=17, startpos=1, endpos=17, name='iln_rechnungsempfaenger', doc='119-03 bei StratEDI 119-02=IV'),
 dict(length=17, startpos=18, endpos=34, name='eigene ILN beim Re'),
 dict(length=17, startpos=35, endpos=51, name='rechnungsempfaenger', fieldclass=IntegerField),
 dict(length=35, startpos=52, endpos=86, name= 'rechnung_name1', doc='119-04 bei StratEDI 119-02=IV'),
 dict(length=35, startpos=87, endpos=121, name='rechnung_name2', doc='119-05 bei StratEDI 119-02=IV'),
 dict(length=35, startpos=122, endpos=156, name='rechnung_name3', doc='119-06 bei StratEDI 119-02=IV'),
 #dict(length=35, startpos=157, endpos=191, name='rechnung Name 4'),
 dict(length=35, startpos=192, endpos=226, name='rechnung_strasse', doc='119-07 bei StratEDI 119-02=IV'),
 dict(length=3, startpos=227, endpos=229, name='rechnung_land', doc='119-12 bei StratEDI 119-02=IV'),
 dict(length=9, startpos=230, endpos=238, name='rechnung_plz', doc='119-10 bei StratEDI 119-02=IV'),
 dict(length=35, startpos=239, endpos=273, name='rechnung_ort', doc='119-11 bei StratEDI 119-02=IV'),
 dict(length=222, startpos=274, endpos=495, name='Reserve', fieldclass=FixedField, default=' '*222),
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
 # dict(length=17, startpos=52, endpos=68, name='unsere LiNr beim WaEmpf'),
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
 dict(length=66, startpos=430, endpos=495, name='Reserve', fieldclass=FixedField, default=' '*66),
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
 dict(length=5, startpos=1, endpos=5, name='positionsnr', doc='500-02 bei StratEDI'),
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
 dict(length=85, startpos=411, endpos=495, name='Reserve'),
 dict(length=1, startpos=496, endpos=496, name='Status', fieldclass=FixedField, default=' '),
]
# fix difference in array counting between SoftM and Python
for feld in FELDERF3:
    feld['startpos'] = feld['startpos'] - 1
F3satzklasse = generate_field_datensatz_class(FELDERF3, name='F3positionsdaten', length=496, doc=doctext)

doctext = 'Rechnungs-Position Rabatte (XOO00EF4)'
FELDERF4 = [
 dict(length=5, startpos=1, endpos=5, name='Position'),
 dict(length=15, startpos=6, endpos=20, name='positionsrabatt_gesamt',
      fieldclass=DecimalFieldNoDot, precision=3),
 dict(length=15, startpos=21, endpos=35, name='Positionsrabatt 1 in %',
      fieldclass=DecimalFieldNoDot, precision=3),
 dict(length=1, startpos=36, endpos=36, name='Rabattkennzeichen 1'),
 dict(length=15, startpos=37, endpos=51, name='Rabattbetrag 1'), #, fieldclass=DecimalFieldNoDot, precision=3),
 dict(length=1, startpos=52, endpos=52, name='Vorzeichen Rabatt 1'),
 dict(length=3, startpos=53, endpos=55, name='TxtSl Rabatt 1'),
 dict(length=15, startpos=56, endpos=70, name='Positionsrabatt 2 in %',
      fieldclass=DecimalFieldNoDot, precision=3),
 dict(length=1, startpos=71, endpos=71, name='Rabattkennzeichen 2'),
 dict(length=15, startpos=72, endpos=86, name='Rabattbetrag 2', fieldclass=DecimalFieldNoDot, precision=3),
 dict(length=1, startpos=87, endpos=87, name='Vorzeichen Rabatt 2'),
 dict(length=3, startpos=88, endpos=90, name='TxtSl Rabatt 2'),
 dict(length=15, startpos=91, endpos=105, name='Positionsrabatt 3 in %',
      fieldclass=DecimalFieldNoDot, precision=3),
 dict(length=1, startpos=106, endpos=106, name='Rabattkennzeichen 3'),
 dict(length=15, startpos=107, endpos=121, name='Rabattbetrag 3',
      fieldclass=DecimalFieldNoDot, precision=3),
 dict(length=1, startpos=122, endpos=122, name='Vorzeichen Rabatt 3'),
 dict(length=3, startpos=123, endpos=125, name='TxtSl Rabatt 3'),
 dict(length=15, startpos=126, endpos=140, name='Positionsrabatt 4 in %',
      fieldclass=DecimalFieldNoDot, precision=3),
 dict(length=1, startpos=141, endpos=141, name='Rabattkennzeichen 4'),
 dict(length=15, startpos=142, endpos=156, name='Rabattbetrag 4',
      fieldclass=DecimalFieldNoDot, precision=3),
 dict(length=1, startpos=157, endpos=157, name='Vorzeichen Rabatt 4'),
 dict(length=3, startpos=158, endpos=160, name='TxtSl Rabatt 4'),
 dict(length=15, startpos=161, endpos=175, name='Positionsrabatt 5 in %',
      fieldclass=DecimalFieldNoDot, precision=3),
 dict(length=1, startpos=176, endpos=176, name='Rabattkennzeichen 5'),
 dict(length=15, startpos=177, endpos=191, name='Rabattbetrag 5',
      fieldclass=DecimalFieldNoDot, precision=3),
 dict(length=1, startpos=192, endpos=192, name='Vorzeichen Rabatt 5'),
 dict(length=3, startpos=193, endpos=195, name='TxtSl Rabatt 5'),
 dict(length=15, startpos=196, endpos=210, name='Positionsrabatt 6 in %',
      fieldclass=DecimalFieldNoDot, precision=3),
 dict(length=1, startpos=211, endpos=211, name='Rabattkennzeichen 6'),
 dict(length=15, startpos=212, endpos=226, name='Rabattbetrag 6',
      fieldclass=DecimalFieldNoDot, precision=3),
 dict(length=1, startpos=227, endpos=227, name='Vorzeichen Rabatt 6'),
 dict(length=3, startpos=228, endpos=230, name='TxtSl Rabatt 6'),
 dict(length=15, startpos=231, endpos=245, name='Positionsrabatt 7 in %',
      fieldclass=DecimalFieldNoDot, precision=3),
 dict(length=1, startpos=246, endpos=246, name='Rabattkennzeichen 7'),
 dict(length=15, startpos=247, endpos=261, name='Rabattbetrag 7',
      fieldclass=DecimalFieldNoDot, precision=3),
 dict(length=1, startpos=262, endpos=262, name='Vorzeichen Rabatt 7'),
 dict(length=3, startpos=263, endpos=265, name='TxtSl Rabatt 7'),
 dict(length=15, startpos=266, endpos=280, name='Positionsrabatt 8 in %',
      fieldclass=DecimalFieldNoDot, precision=3),
 dict(length=1, startpos=281, endpos=281, name='Rabattkennzeichen 8'),
 dict(length=15, startpos=282, endpos=296, name='Rabattbetrag 8', fieldclass=DecimalFieldNoDot, precision=3),
 dict(length=1, startpos=297, endpos=297, name='Vorzeichen Rabatt 8'),
 dict(length=3, startpos=298, endpos=300, name='TxtSl Rabatt 8'),
 dict(length=35, startpos=301, endpos=335, name='Gebinde'),
 dict(length=35, startpos=336, endpos=370, name='Gebindebezeichnung'),
 dict(length=5, startpos=371, endpos=375, name='Gebindeanzahl Rechnung'),
 dict(length=15, startpos=376, endpos=390, name='Volumen', fieldclass=DecimalFieldNoDot, precision=5),
 dict(length=105, startpos=391, endpos=495, name='Reserve'),
 dict(length=1, startpos=496, endpos=496, name='Status', fieldclass=FixedField, default=' '),
]
# fix difference in array counting between SoftM and Python
for feld in FELDERF4:
    feld['startpos'] = feld['startpos'] - 1
F4satzklasse = generate_field_datensatz_class(FELDERF4, name='F4positionsrabatte', length=496)

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
 dict(length=16, startpos=118, endpos=133, name='Steuerbetrag 1', fieldclass=DecimalFieldNoDotSigned, precision=3),
 dict(length=5, startpos=134, endpos=138, name='Steuersatz 2', fieldclass=FixedField, default='00000'),
 dict(length=16, startpos=139, endpos=154, name='Steuerbetrag 2', fieldclass=FixedField, default='000000000000000+'),
 dict(length=16, startpos=155, endpos=170, name='nettowarenwert1', fieldclass=DecimalFieldNoDotSigned, precision=3),
 dict(length=16, startpos=171, endpos=186, name='nettowarenwert2', fieldclass=FixedField, default='000000000000000+'),

 # dict(length=15, startpos=176, endpos=190, name='Versandkosten 1', fieldclass=DecimalFieldNoDot,
 #      precision=3),
 # 15   15  3  187  201 Versandkosten 1
 #      1  0  202  202 Vorz. Versandkosten 1
 # dict(length=15, startpos=191, endpos=205, name='Versandkosten 2', fieldclass=DecimalFieldNoDot,
 #      precision=3),
 # 15   15  3  203  217 Versandkosten 2
 #      1  0  218  218 Vorz. Versandkosten 2
 # dict(length=15, startpos=206, endpos=220, name='Verpackungskosten 1', fieldclass=DecimalFieldNoDot,
 #      precision=3),
 # 15   15  3  219  233 Verpackungskosten 1
 #      1  0  234  234 Vorz. Verpackungsk. 1 
 # dict(length=15, startpos=221, endpos=235, name='Verpackungskosten 2', fieldclass=DecimalFieldNoDot,
 #      precision=3),
 # 15   15  3  235  249 Verpackungskosten 2
 #      1  0  250  250 Vorz. Verpackungsk. 2
 # dict(length=15, startpos=236, endpos=250, name='Nebenkosten 1', fieldclass=DecimalFieldNoDot, precision=3),
 #15   15  3  251  265 Nebenkosten 1
 #      1  0  266  266 Vorz. Nebenkosten 1
 # dict(length=15, startpos=251, endpos=265, name='Nebenkosten 2', fieldclass=DecimalFieldNoDot, precision=3),
 # 15   15  3  267  281 Nebenkosten 2
 #      1  0  282  282 Vorz. Nebenkosten 2
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
 #fieldclass=FixedField, default='000000000000000'),
 dict(length=3, startpos=377, endpos=379, name='TxtSl Kopfrabatt 1'),
 dict(length=3, startpos=380, endpos=382, name='TxtSl Kopfrabatt 2'),
 dict(length=16, startpos=383, endpos=398, name='Kopfrabatt USt 1',
      fieldclass=DecimalFieldNoDotSigned, precision=3),
 dict(length=16, startpos=399, endpos=414, name='Kopfrabatt USt 2',
      fieldclass=FixedField, default='000000000000000+'),
 dict(length=11, startpos=415, endpos=425, name='Gesamtgewicht brutto', fieldclass=IntegerField),
 dict(length=11, startpos=426, endpos=436, name='Gesamtgewicht netto', fieldclass=IntegerField),
 dict(length=4, startpos=437, endpos=440, name='Anzahl Positionen', fieldclass=IntegerField),
 dict(length=55, startpos=441, endpos=495, name='filler', fieldclass=FixedField, default=' '*55),
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
 dict(length=8, startpos=91, endpos=98, name='Valutadatum'),
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
 dict(length=15, startpos=243, endpos=257, name='Steuerbetrag'),
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
 dict(length=157, startpos=339, endpos=495, name='Reserve'),
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
 dict(length=200, startpos=85, endpos=284, name='filler1', fieldclass=FixedField, default=' '*200),
 dict(length=200, startpos=285, endpos=484, name='filler2', fieldclass=FixedField, default=' '*200),
 dict(length=11, startpos=485, endpos=495, name='filler3', fieldclass=FixedField, default=' '*11),
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
    #dict(length=8, startpos=91, endpos=98, name='Valutadatum'),
    #dict(length=9, startpos=99, endpos=107, name='Lieferschein'),
    #dict(length=8, startpos=108, endpos=115, name='Lieferdatum'),
    #dict(length=9, startpos=116, endpos=124, name='Auftragsnummer'),
    #dict(length=20, startpos=125, endpos=144, name='Kundenbestellnummer'),
    #dict(length=8, startpos=145, endpos=152, name='Kundenbestelldatum'),
    dict(length=3, startpos=153, endpos=155, name='waehrung'),
    dict(length=16, startpos=156, endpos=171, name='warenwert',
         fieldclass=DecimalFieldNoDotSigned, precision=3),
    dict(length=15, startpos=172, endpos=186, name='Nebenkosten'),
    dict(length=1, startpos=187, endpos=187, name='Vorzeichen Nebenkosten'),
    dict(length=15, startpos=188, endpos=202, name='Verpackungskosten'),
    dict(length=1, startpos=203, endpos=203, name='Vorzeichen Verpackungskosten'),
    dict(length=15, startpos=204, endpos=218, name='Versandkosten'),
    dict(length=1, startpos=219, endpos=219, name='Vorzeichen Versandkosten'),
    dict(length=16, startpos=220, endpos=235, name='skonto_abzug', fieldclass=DecimalFieldNoDotSigned, precision=3),
    # dict(length=1, startpos=235, endpos=235, name='Vorzeichen Skonto-Abzug'),
    dict(length=2, startpos=236, endpos=237, name='Kz Mehrwertsteuer'),
    dict(length=5, startpos=238, endpos=242, name='Steuersatz in %'),
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
    dict(length=157, startpos=339, endpos=495, name='filler', fieldclass=FixedField, default=' '*157),
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
 dict(length=200, startpos=38, endpos=237, name='filler1', fieldclass=FixedField, default=' '*200),
 dict(length=200, startpos=238, endpos=437, name='filler2', fieldclass=FixedField, default=' '*200),
 dict(length=58, startpos=438, endpos=495, name='filler3', fieldclass=FixedField, default=' '*58),
 dict(length=1, startpos=496, endpos=496, name='status', fieldclass=FixedField, default=' '),
]
# fix difference in array counting between SoftM and Python
for feld in FELDERR3:
    feld['startpos'] = feld['startpos'] - 1
R3satzklasse = generate_field_datensatz_class(FELDERR3, name='R3verbandsrechnungslistensummen',
                                              length=496, doc=doctext)

FELDERTEXT = [
 dict(length=60, startpos=1, endpos= 60, name='Textzeile 1'),
 dict(length=60, startpos= 61, endpos=120, name='Textzeile 2'),
 dict(length=60, startpos=121, endpos=180, name='Textzeile 3'),
 dict(length=60, startpos=181, endpos=240, name='Textzeile 4'),
 dict(length=60, startpos=241, endpos=300, name='Textzeile 5'),
 dict(length=60, startpos=301, endpos=360, name='Textzeile 6'),
 dict(length=60, startpos=361, endpos=420, name='Textzeile 7'),
 dict(length=60, startpos=421, endpos=480, name='Textzeile 8'),
 dict(length=15, startpos=481, endpos=495, name='Reserve'),
 dict(length= 1, startpos=496, endpos=496, name='Status'),
]
# fix difference in array counting between SoftM and Python
for feld in FELDERTEXT:
    feld['startpos'] = feld['startpos'] - 1
TEXTsatzklasse = generate_field_datensatz_class(FELDERTEXT, name='generic_text', length=496)


def parse_to_objects(lines):
    satzresolver = dict(XH=XHsatzklasse,
        F1=F1satzklasse,
        F2=F2satzklasse,
        F8=F8satzklasse,
        F9=F9satzklasse,
        F3=F3satzklasse,
        F4=F4satzklasse,
        # ER=ERsatzklasse,
        A1=A1satzklasse,
        R1=R1satzklasse,
        R2=R2satzklasse,
        R3=R3satzklasse,
        FA=FAsatzklasse,
        FP=generate_field_datensatz_class(FELDERTEXT, name='positionstext', length=496),
        FK=generate_field_datensatz_class(FELDERTEXT, name='versandbedingungen', length=496),
        FE=generate_field_datensatz_class(FELDERTEXT, name='lieferbedingungen', length=496),
        F6=generate_field_datensatz_class(FELDERTEXT, name='rechnungspositionstexte', length=496),
        FX=generate_field_datensatz_class(FELDERTEXT, name='kopfrabatt', length=496),
        FR=generate_field_datensatz_class(FELDERTEXT, name='positionsrabatt', length=496),
        )
    ret = []
    for lineno, rawline in enumerate(lines):
        lineno += 1 # in python 2.6 use enumerate(lines, start=1):

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
        # print data
        satzklasse = satzresolver.get(satzart, None)
        #print satzart, satzklasse
        if satzklasse:
            satz = satzklasse()
            satz.parse(data)
            ret.append((satzart, satz, ))
        else:
            print "Zeile:", lineno + ":", repr(satzart), repr(version), repr(erstellungsdatum), len(line), len(data)
            print '...................................'
            print "unbekannter Satz:", satzart, version
            print repr(rawline)
            print '^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^'
            raise "unbekannter Satz: %s %s" % (str(satzart), str(version), )
    return ret


