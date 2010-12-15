#!/usr/bin/env python
# encoding: utf-8
"""
desadv.py
"""

# Format laut http://www.gs1belu.org/files/DESADV(EANCOM2002_S3).pdf 
# UNA http://www.gs1.se/EANCOM%202000/part1/una.htm

# Fragen:
#  - warum hat UNB mit date_to_EDIFACT keine Time lt. http://www.gs1.se/EANCOM%202000/part1/unb.htm ?
#  - UNH, message identifier, message type release number: muesste das nicht 96A statt 09A heissen? 


import base64
import logging
import struct
from datetime import date
from datetime import datetime
from edilib.edifact.invoic import date_to_EDIFACT
from time import time


def split_and_normalize_text(text, length, parts=2):
    """ liefert den uebergebenen Text in <parts> Teilstrings zu max. <length>
        Zeichen zurueck und ersetzt dabei alle "gefaehrlichen" Zeichen, die
        nicht ins EDIFACT IMD segment passen.
        http://www.gs1.se/EANCOM%202000/desadv/gdx.htm#3IMDDESADV580 """
    if not text:
        return ['', '']
    text = (text.replace(':', ' ')
                .replace('+', ' ')
                .replace('\n', ' '))
    return (text[i:i+length] for i in range(0, parts*length, length))


def lieferschein_to_DESADV(lieferschein):
    #logging.info("------------> %s" % lieferschein)
    params = dict(absenderadresse_iln='4005998000007',
                  absenderadresse_name1='HUDORA GmbH',
                  absenderadresse_name2='Fakturierung',
                  absenderadresse_name3='',
                  absenderadresse_strasse=u'Jägerwald 13',
                  absenderadresse_ort='Remscheid',
                  absenderadresse_plz='42897',
                  absenderadresse_land='DE')

    params.update(lieferschein)
    params.update(dict(uebertragungsnr=base64.b32encode(struct.pack('>d', time())).strip('=\n')[:14],
                       msgrefnr=base64.b32encode(struct.pack('>d', time()-1000000000)).strip('=\n')[:14],
                       date=date.today().strftime('%y%m%d'),
                       time=datetime.now().strftime('%H%M'),
                       #lieferdatum=date_to_EDIFACT(lieferschein['anlieferdatum']),
                       #lieferdatum_latest=date_to_EDIFACT(lieferschein['anlieferdatum']),
                       ))

    # TEST
    #params['absenderadresse_iln'] = '4007731' # Metro
    #params['absenderadresse_iln'] = '5400102' # Carrefour
    #params['iln'] = '5400107009992' # BRICO Belgium
    # TEST

    envelope = ["UNA:+.? ",     # :     component data element separator
                                # +     data element separator
                                # .     decimal notation
                                # ?     release character
                                # [spc] reserved
                                # '     segment terminator
                "UNB+UNOC:3+%(absenderadresse_iln)s:14+%(iln)s:14+%(date)s:%(time)s+%(uebertragungsnr)s" % params]
                # UNOC  syntax identifier, UNOC equals ISO-8859 character set
                # 4     syntax version 4
                # iln   interchange sender: EAN location number (n13)
                # 14                        EAN international
                # iln   interchange recpt:  EAN location number (n13)
                # 14                        EAN international
                # date  date/time of preparation: date
                # time                            time 
                # uebertragungsnr   interchange control reference

    msg = []
    msg.append("UNH+%(msgrefnr)s+DESADV:D:96A:UN:EAN005" % params)
               # http://www.gs1.se/EANCOM%202000/desadv/gd1.htm#3UNHDESADV10
               # msgrefnr   unique message reference number
               # DESADV     message identifier: message type identifier
               # D                              message type version number, D equals "Draft Directory"
               # 96A                            message type release number, 96A equals Vesion 96A
               # UN                             controlling agency
               # EAN005                         association assigned code

    msg.append("BGM+351+%(lieferscheinnr)s+9" % params)
               # http://www.gs1.se/EANCOM%202000/desadv/gd2.htm#3BGMDESADV20
               # 351        document/message name: document/message name, 351 equals "Despatch Advice"
               # liefersnr  document/message number
               # 9          message function, 9 equals "Original"

    #msg.append("DTM+64:%(lieferdatum)s:102" % params)         # fruehestmoeglicher Lieferzeitpunkt
    #msg.append("DTM+63:%(lieferdatum_latest)s:102" % params)  # spaetmoeglichster Lieferzeitpunkt
               # http://www.gs1.se/EANCOM%202000/desadv/gd3.htm#3DTMDESADV30
               # 64         date/time period qualifier, 64 equals "delivery date/time, earliest"
               #                                        63 equals "delivery date/time, latest"
               # datum      date/time/period
               # 102        date/time/period format qualifier, 102 equals "CCYYMMDD"

    msg.append("RFF+ON:%(auftragsnr)s" % params)
               # http://www.gs1.se/EANCOM%202000/desadv/gd7.htm#3RFFDESADV80
               # ON         reference qualifier, ON equals "order number"
               # %s         reference number

    msg.append("NAD+SU+%(absenderadresse_iln)s::9+%(absenderadresse_name1)s:%(absenderadresse_name2)s:%(absenderadresse_name3)s++%(absenderadresse_strasse)s+%(absenderadresse_ort)s++%(absenderadresse_plz)s+%(absenderadresse_land)s" % params)
               # http://www.gs1.se/EANCOM%202000/desadv/gd9.htm#3NADDESADV110
               # SU         party qualifier, SU means "Supplier"
               # iln        party identification details: identification
               # [empty]                                  code list qualifier
               # 9                                        code list resp. agency, 9 equals EAN
               # name1      name and address: line 1
               # name2                        line 2
               # name3                        line 3 
               # [empty]    party name
               # strasse    street: street and number, line 1
               # ort        city name
               # [empty]    country sub-entity identification
               # plz        postcode identification
               # land       country

    msg.append("NAD+DP+%(iln)s::9+%(name1)s:%(name2)s:%(name3)s++%(strasse)s+%(ort)s++%(plz)s+%(land)s" % params)
               # http://www.gs1.se/EANCOM%202000/desadv/gd9.htm#3NADDESADV110
               # DP         party qualifier, DP means "Delivery Party"
               # iln        party identification details: identification
               # [empty]                                  code list qualifier
               # 9                                        code list resp. agency, 9 equals EAN
               # name1      name and address: line 1
               # name2                        line 2
               # name3                        line 3 
               # [empty]    party name
               # strasse    street: street and number, line 1
               # ort        city name
               # [empty]    country sub-entity identification
               # plz        postcode identification
               # land       country

    msg.append("RFF+AVC:%(kundennr)s" % params)
               # http://www.gs1.se/EANCOM%202000/desadv/gdb.htm#3RFFDESADV140 
               # AVC        reference qualifier, AVC
               # kundennr   reference number

    msg.append("CPS+1")
               # http://www.gs1.se/EANCOM%202000/desadv/gdm.htm#3CPSDESADV380
               # 1          hierachical id number

    for idx, position in enumerate(lieferschein['positionen']):
        msg.append("LIN+%d++%s:SA" % (idx+1, position['artnr']))
                   # http://www.gs1.se/EANCOM%202000/desadv/gdv.htm#3LINDESADV560
                   # %d         line item number
                   # [empty]    action request/notification
                   # %s         item number identification: item number
                   # SA                                     item number type, SA equals "Supplier's article number"

        msg.append("QTY+12:%d" % (position['menge']))
                   # http://www.gs1.se/EANCOM%202000/desadv/gdz.htm#3QTYDESADV600
                   # 12         quantity qualifier, 12 equals "despatch quantity"
                   # %d         quantity
        
        if 'name' in position:
            parts = u'+'.join(split_and_normalize_text(position['name'], 34))
            msg.append("IMD+F++:::%s" % parts)
                       # http://www.gs1.se/EANCOM%202000/desadv/gdx.htm#3IMDDESADV580
                       # F        item description type, F equals "free form"
                       # [empty]  item characteristics
                       # [empty]  item description: item description identification
                       # [empty]                    code list qualifier
                       # [empty]                    code list responsible agency
                       # %s                         item description, part 1
                       # %s                         item description, part 2
                   
        if 'infotext_kunde' in position:
            parts = u'+'.join(split_and_normalize_text(position['infotext_kunde'], length=70, parts=5))
            msg.append("FTX+ZZZ+002+%s" % parts)
                       # http://www.gs1.se/EANCOM%202000/desadv/gd13.htm#3FTXDESADV660
                       # ZZZ    text subject qualifier, ZZZ equals "mutually defined"
                       # 002    text reference: free text, coded, 002 equals "standard text"
                       # %s     text literal, max 5 parts with 70 chars each

    msg.append("CNT+2:%d" % len(lieferschein['positionen']))
               # http://www.gs1.se/EANCOM%202000/desadv/gd1k.htm#3CNTDESADV980
               # 2       control qualifier, 2 equals "number of line items in message"
               # %d      control value

    msg.append("UNT+%d+%s" % (len(msg)+1, params['msgrefnr']))
               # http://www.gs1.se/EANCOM%202000/desadv/gd1l.htm#3UNTDESADV990
               # %d      number of segments in the message
               # %s      message reference number as in UNH given
    
    envelope.extend(msg)
    envelope.append("UNZ+1+%(uebertragungsnr)s" % params)
                    # http://www.gs1.se/EANCOM%202000/part1/unz.htm
                    # 1                 number of messages within the interchange
                    # uebertragungsnr   interchange control reference, same as in UNB

    #return u'\n'.join(map(lambda row: row+u"'", envelope)).encode('iso-8859-1', 'replace')
    # bei einem Encode nach 8859-1 bleiben die Umlaute in Ergebnis, was aber
    # fuer den gewaehlten Encoding-Type UNOC nicht zulaessig ist. Deshalb 'ascii'
    # mit 'ignore' wirft die Umlaute raus. Reicht das? Only time will tell.
    return u'\n'.join(map(lambda row: row+u"'", envelope)).encode('ascii', 'ignore')


if __name__ == '__main__':
    lieferschein = {"iln": "4005998000007",
                    "name1": "HUDORA GmbH",
                    "name2": "Abt. Cybernetics",
                    "name3": "Anlieferung: Tor 2",
                    "strasse": u"Jägerwald 13", 
                    "ort": "Remscheid",
                    "plz": "42897",
                    "land": "DE",
                    "tel": "+49 2191 60912 0",
                    "fax": "+49 2191 60912 50",
                    "mobil": "+49 175 00000xx",
                    "email": "nobody@hudora.de",
                    "anlieferdatum": "2007-09-23",
                    "kundennr": "4711",
                    "paletten": 2.6,
                    "lieferscheinnr": 'LFRS0005',
                    "kundennr": 'SC12345',
                    "auftragsnr": 'AUFTRAG12345',
                    "datum": '2010-12-01',
                    "positionen": [{"auftragpos_guid": 'GA00001',
                                    "kommipos_guid": 'GK00002',
                                    "menge": 234,
                                    "artnr": "08/15",
                                    "name": "Nasenschoner",
                                    "infotext_kunde": "infotext"},
                                   {"auftragpos_guid": 'GA00003',
                                    "kommipos_guid": 'GK00004',
                                    "menge": 5,
                                    "artnr": "12345",
                                    "name": "Whatever"}]}
    print lieferschein_to_DESADV(lieferschein)
    
