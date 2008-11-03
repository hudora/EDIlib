#!/usr/bin/env python
# encoding: utf-8

"""Functionality for basic parsing of StratEDI ORDERS data.

Created by Maximillian Dornseif 2008-08-12."""

import datetime
from edilib.recordbased import generate_field_datensatz_class, FixedField, DecimalField, IntegerField
from edilib.recordbased import DateField, EanField, TimeField


class BenedictException(RuntimeError):
    """Baseclass for more detailed exceptions."""
    pass
    

class UnknownRecordException(BenedictException):
    """Is raised if an unknown record occures."""
    pass
    

class MalformedRecordException(BenedictException):
    """Is raised if an record is malformed."""
    pass
    

class MalformedFileException(BenedictException):
    """Is raised if the intra record structure is malformed."""
    pass
    
INTERCHANGEHEADER000 = [
    dict(length=3, startpos=1, endpos=3, name='satzart', fieldclass=FixedField, default="000"),
    dict(length=35, startpos=4, endpos=38, name='sender_iln'),
    dict(length=35, startpos=39, endpos=73, name='empfaenger_iln'),
    dict(length=8, startpos=74, endpos=81, name='erstellungsdatum', fieldclass=DateField, default=datetime.datetime.now),
    dict(length=4, startpos=82, endpos=85, name='erstellungszeit', fieldclass=TimeField, default=datetime.datetime.now),
    dict(length=14, startpos=86, endpos=99, name='datenaustauschreferenz', fieldclass=IntegerField,
         doc='Fortlaufende achtstellige Sendenummer.'),
    dict(length=14, startpos=100, endpos=113, name='referenznummer', fieldclass=IntegerField),
    dict(length=14, startpos=114, endpos=127, name='anwendungsreferenz'),
    # This has to be changed to 0 for production data
    dict(length=1, startpos=128, endpos=128, name='testkennzeichen'),
    dict(length=5, startpos=129, endpos=133, name='schnittstellenversion', fieldclass=FixedField, default='4.5  '),
    dict(length=379, startpos=134, endpos=512, name='filler', fieldclass=FixedField, default=' '* 379),
]
# fix since this is not in python notation fix "off by one" errors
for feld in INTERCHANGEHEADER000:
    feld['startpos'] -= 1

class InterchangeheaderHandler(object):
    """Validates if parsed record is well formed."""
    
    def __init__(self, thisparser):
        self.parser = thisparser
    
    def validate(self, previousparsers):
        """Executes Validation and raises Exceptions on failures."""
        
        if previousparsers != []:
            raise MalformedFileException("Interchangeheader always must be the first record." +
                                         (" Previous records = %r" % ([self.parser] + previousparsers)))
    
    def contribute_to_order(self, dummy):
        """Return a dict contributing to the OrderProtocol."""
        return {} # FIXME


transaktionskopf = [
    dict(startpos=1, endpos=3, length=3, name='satzart', fieldclass=FixedField, default="100"),
    dict(startpos=4, endpos=17, length=14, name='referenz',
        doc="UNH-0062"),
    dict(startpos=18, endpos=23, length=6, name='typ', fieldclass=FixedField, default="ORDERS",
        doc="UNH-0065"),
    dict(startpos=24, endpos=26, length=3, name='version', fieldclass=FixedField, default="D  ",
        doc="UNH-0052"),
    dict(startpos=27, endpos=29, length=3, name='release', fieldclass=FixedField, default='96A',
        doc="UNH-0054"),
    dict(startpos=30, endpos=31, length=2, name='organisation1', fieldclass=FixedField, default="UN",
        doc="UNH-0051"),
    dict(startpos=32, endpos=37, length=6, name='organisation2', fieldclass=FixedField, default='EAN008',
        doc="UNH-0057"),
    dict(startpos=38, endpos=40, length=3, name='transaktionsart', fieldclass=FixedField, default='220',
        doc="BGM-1001"),
    dict(startpos=41, endpos=43, length=3, name='transaktionsfunktion', fieldclass=FixedField, default='9  ',
        doc="BGM-1225"),
    dict(startpos=44, endpos=78, length=35, name='belegnummer',
        doc="BGM-1004"),
    dict(startpos=79, endpos=86, length=8, name='belegdatum', fieldclass=DateField,
        doc="DTM-2380"),
    dict(startpos=87, endpos=89, length=3, name='antwortart',
        doc="BGM-4343"),
    dict(startpos=90, endpos=90, length=1, name='selbstabholung', # Boolean?
        doc="TOD-4055"),
    dict(startpos=91, endpos=125, length=35, name='dokumentanname',
        doc="BGM-1000"),
    dict(startpos=126, endpos=512, length=387, name='filler', fieldclass=FixedField, default=' '*387),
    ]
# fix since this is not in python notation fix "off by one" errors
for feld in transaktionskopf:
    feld['startpos'] -= 1
    

class TransaktionskopfHandler(object):
    """Validates if parsed record is well formed."""
    
    def __init__(self, thisparser):
        self.parser = thisparser
    
    def validate(self, previousparsers):
        """Executes Validation and raises Exceptions on failures."""
        
        if previousparsers != []:
            raise MalformedFileException("Transaktionskopf always must be the first record." +
                                         (" Previous records = %r" % ([self.parser] + previousparsers)))

    def contribute_to_order(self, dummy):
        """Return a dict contributing to the OrderProtocol."""
        return {'kundenauftragsnr': unicode(self.parser.belegnummer),
                'bestelldatum': self.parser.belegdatum}
    

addressen = [
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
        doc="RFF-1154"),           
    dict(startpos=452, endpos=471, length=20, name='ansprechpartner',
        doc="CTA-3412"),           
    dict(startpos=472, endpos=491, length=20, name='tel',
        doc="COM-3148"),           
    dict(startpos=492, endpos=511, length=20, name='fax',
        doc="COM-3148"),           
    dict(startpos=512, endpos=512, length=1, name='filler', fieldclass=FixedField, default=' '),
    ]

# fix since this is not in python notation fix "off by one" errors
for feld in addressen:
    feld['startpos'] -= 1
    

class AddressenHandler(object):
    """Validates if parsed record is well formed."""
    
    def __init__(self, parser):
        self.parser = parser
    
    def validate(self, previousparsers):
        """Executes Validation and raises Exceptions on failures."""
        
        if previousparsers[0].satzart != '100':
            raise MalformedFileException("Addresssatz without Transaktionskopf Previous records = %r"
                                         % previousparsers)
        if previousparsers[-1].satzart not in ['100', '119']:
            raise MalformedFileException("Addresssatz can only follow a Transaktionskopf or an Addresssatz."
                                         + ("Previous records = %r" % previousparsers))
        if self.parser.partnerart == 'SU' and self.parser.iln != '4005998000007':
            raise MalformedRecordException("Supplier MUST be HUDORA/4005998000007: %r" % self.parser)
    
    def contribute_to_order(self, dummy):
        """Return a dict contributing to the OrderProtocol."""
        if self.parser.partnerart in ['DP', 'IV']:
            
            # for fixing non ISO 3166-1 alpha-2 data (seen with TRU)
            landfix = {'D': 'DE'}
            
            adrtype = {'DP': 'lieferadresse', 'IV': 'rechnungsadresse'}[self.parser.partnerart]
            return {adrtype: {'iln': unicode(self.parser.iln),
                              'name1': unicode(self.parser.name1),
                              'name2': unicode(self.parser.name2),
                              'name3': unicode(self.parser.name3),
                              'strasse': ' '.join([self.parser.strasse1,
                                                   self.parser.strasse2,
                                                   self.parser.strasse3]).strip(),
                              'plz': unicode(self.parser.plz),
                              'ort': unicode(self.parser.ort),
                              'land': unicode(landfix.get(self.parser.land, self.parser.land)),
                              'tel': unicode(self.parser.tel),
                              'fax': unicode(self.parser.fax),
            }}
        else:
            return {}
    

zahlungsbedingungen = [
    dict(startpos=1, endpos=3, length=3, name='satzart', fieldclass=FixedField, default="120"),
    dict(startpos=4, endpos=6, length=3, name='waehrung', fieldclass=FixedField, default='EUR',
        doc="CUX-6345"),
    dict(startpos=7, endpos=11, length=5, name='mwstsatz', fieldclass=FixedField, default=' ' * 5,
        doc="TAX-5278"),
    dict(startpos=12, endpos=14, length=3, name='zahlungsziel', fieldclass=FixedField, default=' ' * 3,
        doc="PAT8-2152"),
    dict(startpos=15, endpos=22, length=8, name='valutadatum', fieldclass=FixedField, default=' ' * 8,
        doc="DTM8-2380"),
    dict(startpos=23, endpos=30, length=8, name='faelligkeitsdatum', fieldclass=FixedField, default=' ' * 8,
        doc="DTM8-2380"),
    dict(startpos=31, endpos=33, length=3, name='incoterms', choices=['DDP'],
        doc="TOD-4053"),
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
for feld in zahlungsbedingungen:
    feld['startpos'] -= 1
    

class ZahlungsbedingungenHandler(object):
    """Validates if parsed record is well formed."""
    
    def __init__(self, parser):
        self.parser = parser
    
    def validate(self, previousparsers):
        """Executes Validation and raises Exceptions on failures."""
        
        if previousparsers[-1].satzart not in ['119']:
            raise MalformedFileException("Zahlungsbedingungensatz can only follow a Addresssatz." +
                                         ("Previous records = %r" % previousparsers))
    

texte = [
    dict(startpos=1, endpos=3, length=3, name='satzart', fieldclass=FixedField, default="130"),
    dict(startpos=4, endpos=6, length=3, name='textzuordnung', choices=['AAI'],
         doc="""FTX-4451: Text subject code qualifier
                AAI General information: The text contains general information"""),
    dict(startpos=7, endpos=356, length=350, name='text',
        doc="FTX-4440"),
    dict(startpos=357, endpos=512, length=156, name='filler', fieldclass=FixedField, default=' ' * 156),
]
# fix since this is not in python notation fix "off by one" errors
for feld in texte:
    feld['startpos'] -= 1
    

class TexteHandler(object):
    """Validates if parsed record is well formed."""
    
    def __init__(self, parser):
        self.parser = parser
    
    def validate(self, previousparsers):
        """Executes Validation and raises Exceptions on failures."""
        
        if previousparsers[-1].satzart not in ['119', '120', '130']:
            raise MalformedFileException("Textsatz can only follow a Addresss- or a Zahlungsbedingungs or" +
                                   (" other Textsatz. Previous records = %r" % previousparsers))
    
    def contribute_to_order(self, orderdict):
        """Return a dict contributing to the OrderProtocol."""
        text = orderdict.get('bestelltext', '')
        text = u'\n'.join([text, self.parser.text]).strip()
        return {'bestelltext': text}

zusatzkosten = [
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
for feld in zusatzkosten:
    feld['startpos'] -= 1


class ZusatzkostenHandler(object):
    """Validates if parsed record is well formed."""
    
    def __init__(self, parser):
        self.parser = parser
    
    def validate(self, previousparsers):
        """Executes Validation and raises Exceptions on failures."""
        
        if previousparsers[-1].satzart not in ['119', '120', '130']:
            raise MalformedFileException("Zusatzkostensatz can only follow a Addresss-, Zahlungsbedingungs" +
                                   (" or Zusatzkostensatz. Previous records = %r" % previousparsers))
    
    def contribute_to_order(self, dummy):
        """Return a dict contributing to the OrderProtocol."""
        return {'skontotage': unicode(self.parser.skontotage),
                'skontoprozent': self.parser.skontoprozent}
    

auftragsposition = [
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
    dict(startpos=271, endpos=285, length=15, name='bestellmenge', fieldclass=DecimalField,
        precision=3, doc="QTY-6060"),
    # FIXME
    #dict(startpos=286, endpos=300, length=15, name='menge_ohne_berechnung', fieldclass=FixedField,
    #    default = '               ', doc="QTY-6060"),
    dict(startpos=301, endpos=303, length=3, name='waehrung', fieldclass=FixedField, default='EUR',
        doc="CUX-6345"),
    dict(startpos=304, endpos=308, length=5, name='mwstsatz', fieldclass=FixedField, default=' ' * 5,
        doc="TAX-5278"),
    dict(startpos=309, endpos=323, length=15, name='nettostueckpreis', fieldclass=DecimalField,
        precision=4, doc="PRI-5118"),
    dict(startpos=324, endpos=338, length=15, name='bruttostueckpreis', fieldclass=FixedField,
        default=' ' * 15, doc="PRI-5118"),
    dict(startpos=339, endpos=353, length=15, name='verkaufspreis', fieldclass=FixedField,
        default=' ' * 15, doc="PRI-5118"),
    dict(startpos=354, endpos=368, length=15, name='aktionspreis', fieldclass=FixedField,
        default=' ' * 15, doc="PRI-5118"),
    dict(startpos=369, endpos=383, length=15, name='listenpreis', fieldclass=FixedField,
        default=' ' * 15, doc="PRI-5118"),
    dict(startpos=384, endpos=392, length=9, name='preisbasis', fieldclass=FixedField,
        default=' ' * 9, doc="PRI-5284"),
    dict(startpos=393, endpos=395, length=3, name='mengeneinheit', choices=['PCE'],
        doc="PRI-6411"),
    dict(startpos=396, endpos=413, length=18, name='nettowarenwert', fieldclass=FixedField,
        default=' ' * 18, doc="MOA-5004"),
    dict(startpos=414, endpos=431, length=18, name='bruttowarenwert', fieldclass=FixedField,
        default=' ' * 18, doc="MOA-5004"),
    dict(startpos=432, endpos=449, length=18, name='summeabschlaege', fieldclass=FixedField,
        default=' ' * 18, doc="MOA-5004"),
    dict(startpos=450, endpos=456, length=7, name='verpackungsart', choices=['CT'],
        doc="PAC-7065"),
    dict(startpos=457, endpos=463, length=7, name='verpackungszahl', fieldclass=IntegerField,
        doc="PAC-7065"),
    dict(startpos=464, endpos=464, length=1, name='gebinde', fieldclass=IntegerField,
        default=' ', doc="PIA-7143"),
    dict(startpos=465, endpos=479, length=15, name='bestellte_vs_gelieferte_menge', fieldclass=FixedField,
        default=' ' * 15, doc="QTY-6060"),
    dict(startpos=480, endpos=494, length=15, name='aktionsvariante', fieldclass=FixedField,
        default='               ', doc="PIA-7143"),
    dict(startpos=495, endpos=497, length=3, name='steuerbefreit', fieldclass=FixedField,
        default='   ', doc="TAX-5305"),
    dict(startpos=498, endpos=507, length=10, name='kennzeichen', fieldclass=FixedField,
        default='          ', doc="?"),
    dict(startpos=508, endpos=512, length=5, name='filler', fieldclass=FixedField, default=' ' * 5),
]
# fix since this is not in python notation fix "off by one" errors
for feld in auftragsposition:
    feld['startpos'] -= 1


class AuftragspositionHandler(object):
    """Validates if parsed record is well formed."""
    
    def __init__(self, parser):
        self.parser = parser
    
    def validate(self, previousparsers):
        """Executes Validation and raises Exceptions on failures."""
        
        if previousparsers[-1].satzart not in ['119', '120', '130', '140', '500', '515']:
            raise MalformedFileException("Auftragspositionssatz can only follow a Addresss-," +
                                   " Zahlungsbedingungs-, Zusatzkosten, Auftragspositions- or" +
                                   (" Positionsterminsatz.Previous records = %r" % previousparsers))
    
    def contribute_to_order(self, orderdict):
        """Return a dict contributing to the OrderProtocol."""
        orderdict['positionen'].append({'menge': int(self.parser.bestellmenge),
                'ean': unicode(self.parser.ean),
                'artnr': unicode(self.parser.artnr_lieferant),
                'kundenartnr': unicode(self.parser.artnr_kunde),
                'name': u' '.join([self.parser.artikelbezeichnung1, self.parser.artikelbezeichnung2]).strip(),
                })
        return {'positionen': orderdict['positionen']}
    

# weglassen
positionstermine = [
    dict(startpos=1, endpos=3, length=3, name='satzart', fieldclass=FixedField, default="515"),
    dict(startpos=4, endpos=11, length=8, name='lieferdatum_bevorzugt', fieldclass=DateField,
         doc="DTM-2380"),
    dict(startpos=12, endpos=19, length=8, name='lieferdatum_min', fieldclass=DateField,
         doc="DTM-2380"),
    dict(startpos=20, endpos=27, length=8, name='lieferdatum_max', fieldclass=DateField,
         doc="DTM-2380"),
    dict(startpos=28, endpos=35, length=8, name='lieferdatum_zugesagt', fieldclass=DateField,
         doc="DTM-2380"),
    dict(startpos=36, endpos=43, length=8, name='lieferdatum_laut_lieferplan', fieldclass=DateField,
         doc="DTM-2380"),
    dict(startpos=44, endpos=51, length=8, name='versanddatum', fieldclass=DateField,
         doc="DTM-2380"),
    dict(startpos=52, endpos=59, length=8, name='pick_up_datum', fieldclass=DateField,
         doc="DTM-2380"),
    dict(startpos=60, endpos=67, length=8, name='letztes_lieferdatum', fieldclass=DateField,
         doc="DTM-2380"),
    # die folgenden Felder verwenden wir nicht
    dict(startpos=68, endpos=73, length=6, name='lieferwoche_bevorzugt', fieldclass=FixedField,
         default=' ' * 6, doc="DTM-2380"),
    dict(startpos=74, endpos=79, length=6, name='lieferwoche_min', fieldclass=FixedField,
         default=' ' * 6, doc="DTM-2380"),
    dict(startpos=80, endpos=85, length=6, name='lieferwoche_max', fieldclass=FixedField,
         default=' ' * 6, doc="DTM-2380"),
    dict(startpos=86, endpos=91, length=6, name='lieferwoche_zugesagt', fieldclass=FixedField,
         default=' ' * 6, doc="DTM-2380"),
    dict(startpos=92, endpos=95, length=4, name='lieferuhrzeit', fieldclass=FixedField,
         default=' ' * 4, doc="DTM-2380"),
    dict(startpos=96, endpos=512, length=417, name='filler', fieldclass=FixedField, default=' ' * 417),
]
# fix since this is not in python notation fix "off by one" errors
for feld in positionstermine:
    feld['startpos'] -= 1


class PositionsterminHandler(object):
    """Validates if parsed record is well formed."""
    
    def __init__(self, parser):
        self.parser = parser
    
    def validate(self, previousparsers):
        """Executes Validation and raises Exceptions on failures."""
        
        if previousparsers[-1].satzart not in ['500']:
            raise MalformedFileException("Positionsterminsatz can only follow a Auftragspositionssatz. " +
                                         (" Previous records = %r" % previousparsers))
    
    def contribute_to_order(self, orderdict):
        """Return a dict contributing to the OrderProtocol."""
        orderdict['positionen'][-1].update({'anlieferdatum_min': self.parser.lieferdatum_min,
                                            'anlieferdatum_max': self.parser.lieferdatum_max})
        return {'positionen': orderdict['positionen']}
    

belegsummen = [
    dict(startpos=1, endpos=3, length=3, name='satzart', fieldclass=FixedField, default="900"),
    dict(startpos=4, endpos=21, length=18, name='gesammtbetrag', fieldclass=DecimalField,
         precision=2, doc="MOA-5004"),
    dict(startpos=22, endpos=39, length=18, name='mwst_gesammtbetrag', fieldclass=FixedField,
         default=' ' * 18, doc="MOA-5004"),
    dict(startpos=40, endpos=512, length=473, name='filler', fieldclass=FixedField, default=' ' * 473),
]


# fix since this is not in python notation fix "off by one" errors
for feld in belegsummen:
    feld['startpos'] -= 1


class BelegsummenHandler(object):
    """Validates if parsed record is well formed."""
    
    def __init__(self, parser):
        self.parser = parser
    
    def validate(self, previousparsers):
        """Executes Validation and raises Exceptions on failures."""
        
        if previousparsers[-1].satzart not in ['500', '515']:
            raise MalformedFileException("Belegsummensatz can only follow a Auftragspositions- or" +
                                         ("Positionsterminsatz. Previous records = %r" % previousparsers))
        
        summe = 0
        for parser in previousparsers:
            if parser.satzart == '500':
                summe += (parser.nettostueckpreis * parser.bestellmenge)
        if summe != self.parser.gesammtbetrag:
            raise MalformedFileException("sums do not validate (%d|%d) %r: %r" % (summe,
                                           self.parser.gesammtbetrag, self.parser, previousparsers))
    
    def contribute_to_order(self, dummy):
        """Return a dict contributing to the OrderProtocol."""
        # we contribute nothing since all relevant verifycations are already done in validate()
        return {}
    
# TRU hat uebertraaegt faelschlicherweise bereits in der Bestellung einen 913 Satz. Dieser ist im Grunde
# unter INVOC dokumentiert, ist allerdings an dieser Stelle nicht, wie dokumentiert 600 Zeichen lang, sondern
# 512
abschlaege = [
    dict(startpos=1, endpos=3, length=3, name='satzart', fieldclass=FixedField, default="913"),
    dict(startpos=4, endpos=6, length=3, name='kennzeichen', choices=['A']),
    dict(startpos=7, endpos=9, length=3, name='art', choices=['GRB', 'RCH', 'AA ', 'DI ']),
    dict(startpos=10, endpos=12, length=3, name='kalkulationsfolgeanzeige', fieldclass=FixedField,
         default=' ' * 3),
    dict(startpos=13, endpos=17, length=5, name='mwstsatz', fieldclass=FixedField, default=' ' * 5),
    dict(startpos=18, endpos=25, length=8, name='prozent', fieldclass=DecimalField),
    dict(startpos=26, endpos=43, length=18, name='betrag'),
    dict(startpos=44, endpos=58, length=15, name='naturalrabatt', fieldclass=FixedField, default=' ' * 15),
    dict(startpos=59, endpos=73, length=15, name='abschlag_je_einheit', fieldclass=FixedField,
         default=' ' * 15),
    dict(startpos=74, endpos=91, length=18, name='abschlagsbasis', fieldclass=FixedField, default=' ' * 18),
    dict(startpos=92, endpos=126, length=35, name='art_abschlag'),
    dict(startpos=127, endpos=512, length=386, name='filler', fieldclass=FixedField, default=' ' * 386),
]


# fix since this is not in python notation fix "off by one" errors
for feld in abschlaege:
    feld['startpos'] -= 1


class AbschlaegeHandler(object):
    """Validates if parsed record is well formed."""
    
    def __init__(self, parser):
        self.parser = parser
    
    def validate(self, previousparsers):
        """Executes Validation and raises Exceptions on failures."""
        
        if previousparsers[-1].satzart not in ['900', '913']:
            raise MalformedFileException("Abschlaegesatz can only follow a Belegsummensatz." +
                                         (" Previous records = %r" % previousparsers))
    

ordersparser = {
    '000': generate_field_datensatz_class(INTERCHANGEHEADER000, name='interchangeheader', length=512),
    '100': generate_field_datensatz_class(transaktionskopf, name='transaktionskopf', length=512),
    '119': generate_field_datensatz_class(addressen, name='addresse', length=512),
    '120': generate_field_datensatz_class(zahlungsbedingungen, name='zahlungsbedingungen', length=512),
    '130': generate_field_datensatz_class(texte, name='texte', length=512),
    '140': generate_field_datensatz_class(zusatzkosten, name='zusatzkosten', length=512),
    '500': generate_field_datensatz_class(auftragsposition, name='auftragsposition', length=512),
    '515': generate_field_datensatz_class(positionstermine, name='positionstermin', length=512),
    '900': generate_field_datensatz_class(belegsummen, name='belegsummen', length=512),
    '913': generate_field_datensatz_class(abschlaege, name='abschlaege', length=512),
}


recordhandlers = {
    '000': InterchangeheaderHandler,
    '100': TransaktionskopfHandler,
    '119': AddressenHandler,
    '120': ZahlungsbedingungenHandler,
    '130': TexteHandler,
    '140': ZusatzkostenHandler,
    '500': AuftragspositionHandler,
    '515': PositionsterminHandler,
    '900': BelegsummenHandler,
    '913': AbschlaegeHandler,
}


def parse_rawdata(data):
    """Parses a Stratedi ORDERS file and returns a objects following the AuftragsProtokoll.
    
    In fact it returns (header, [Auftrag, Auftrag, ...]).
    """
    
    firstline = ''
    header = None
    parsers = []
    auftraege = []
    orderdict = {'positionen': []}
    for line in data.split('\n'):
        line = line.strip('\r\n')
        if not line:
            # empty line
            continue
        
        # pad / truncate to 512 bytes
        line = "%-512s" % line[:512]
        
        satzart = line[:3]
        if satzart not in ordersparser:
            raise UnknownRecordException("unknown satzart %r" % satzart)
        
        parser = ordersparser[satzart]()
        parser.parse(line)
        if satzart == '000':
            # special case: interchange header
            firstline = line
            header = recordhandlers[satzart](parser)
        else:
            if satzart == '100':
                # new auftrag starting
                if parsers:
                    auftraege.append(orderdict)
                parsers = []
                orderdict = {'positionen': []}
            
            if satzart not in recordhandlers:
                print "WARNING: no validator for record %r" % satzart
            else:
                handler = recordhandlers[satzart](parser)
                handler.validate(parsers)
                parsers.append(parser)
                if hasattr(handler, 'contribute_to_order'):
                    orderdict.update(handler.contribute_to_order(orderdict))
                else:
                    print "WARNING: no extractor for record %r" % satzart
        
    return (header, auftraege)
