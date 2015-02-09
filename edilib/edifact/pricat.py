#!/usr/bin/env python
# encoding: utf-8
"""
edilib/edifact/pricat.py

Created by Christian Klein on 2015-02-09.
Copyright (c) 2015 HUDORA. All rights reserved.
"""

# Das Nachrichtenformat entspicht ISO 9735:1998 Version 4. Als Zeichensatz verwenden wir ISO 8859-1 "Latin-1".
# Als Datumsformat verwenden wir ISO 8601 / RfC 3339 mit vierstelligen Jahren aber ohne Trennzeichen in CEST
# oder CET. Für Ländercodes folgen wir ISO 3166-1 alpha-2. Bei Dezimaltrennzeichen folgen wir der
# Internationalen Konvention und verernden einen Punkt. All diese Konventionen sind auch entsprechend im
# Message-Framing codiert.
#
# Beispiel aus http://www.exite-info.at/files_at/REWE_INVOIC_Lieferscheindetail.pdf

import copy
import datetime
import time
import struct
import base64
import huTools.monetary


def split_text(text, length, max_records=1, separator=':'):
    """Split text into records of `length` characters separated by `separator`

    If max_records is given, create at most `max_records` records.

    >>> split_text('AAABBBCCCDDD', 3)
    'AAA'
    >>> split_text('AAABBBCCCDDD', 3, max_records=3)
    'AAA:BBB:CCC'
    >>> split_text('ABC', 1, max_records=2, separator='.')
    'A.B'
    """

    records = []
    while text:
        records.append(text[:length])
        text = text[length:]
        if len(records) == max_records:
            break
    return separator.join(records)


def eap_to_PRICATD96A(eaps):
    """
    Convert EDIFACT PRICAT D.96A

    Returns a (latin-1) encoded bytestream which must not be re-encoded.
    """

    param.update(dict(  # der ID darf 14-stellig sein, unserer ist ein 13stelliger, kodierter Unix-Timestamp
         uebertragungsnr=base64.b32encode(struct.pack('>d', time.time())).strip('=\n')[:14],
         referenznr='%.0f' % time.time(),
         date=date_to_EDIFACT(datetime.date.today(), fmt='%y%m%d'),
         time=datetime.datetime.now().strftime('%H%M'),
         absenderadresse_iln='4005998000007',
         katalognr='1',
        ))

    # Message Envelope:
    # Add 'Service String Advice' with standard delimiter characters
    envelope = ["UNA:+.? '"]

    # Add 'Interchange Header'
    # UN/ECE level C (ISO 8859-1), Syntax Version 2
    # Partner identification via GS1 GLN (= 14)
    envelope.append("UNB+UNOC:2+%(absenderadresse_iln)s:14+%(iln)s:14+%(date)s:%(time)s+%(uebertragungsnr)s'" % param)

    # UNH - Message Header:
    # PRICAT D.96A, Association assigned code EAN008
    header = ["UNH+%(referenznr)s+PRICAT:D:96A:UN:EAN008'" % param]
    # Begin of Message: Document code 9 (Price/sales catalogue), Message function code 9 (Original)
    header.append("BGM+380+%(katalognr)s+9'" % param)
    # DTM - Date/Time/Period
    # Function code qualifier: 137 (Document/message date/time)
    # Format code 102 (CCYYMMDD)
    header.append("DTM+137:%(TODO)s:102'" % param)

    # NAD - Name and addres:
    # Name and address of manufacturer given as GLN
    header.append("NAD+MF+%(absenderadresse_iln)s::9'" % param)
    # Name and address of Buyer given as GLN
    header.append("NAD+BY+%(iln)s::9'" % param)
    # Name and address of message sender given as GLN
    header.append("NAD+FR+%(absenderadresse_iln)s::9'" % param)

    # RFF-Segmente werden hier nicht eingefügt

    # Tax Record: Function code qualifier 7 (Tax), Name code VAT (Value added tax),
    # Tax rate, Category code S (Standard)
    header.append("TAX+7+VAT+++:::%(steuer_prozent)s+S'" % param)

    # Currency Record: Reference currency, Currency type code qualifier 4 (Invoicing currency)
    if not 'waehrung' in param:
        param['waehrung'] = 'EUR'
    header.append("CUX+2:%(waehrung)s:4'" % param)

    # Produktgruppen - PGI-Segment

    # Name and address of supplier given as GLN
    header.append("NAD+SU+%(absenderadresse_iln)s::9'" % param)

    envelope.extend(header)
    number_of_records = len(header)

    # Orderline / Positions
    for positionsnummer, eap in enumerate(eaps, 1):

        position = []

        orderline = copy.copy(eap)
        orderline.update(positionsnummer=positionsnummer)

        # Product ID as EAN
        position.append("LIN+%(positionsnummer)s+1+%(ean)s:EN'" % orderline)

        # Additional Product ID
        # artnr is supplier's item no (SA), defined by supplier (91)
        position.append("PIA+%(positionsnummer)s+%(artnr)s:SA:'" % orderline)
        # artnr is supplier's item no (SA), defined by manufacturer
        position.append("PIA+%(positionsnummer)s+%(artnr)s:MF:'" % orderline)

        position.append("IMD+F+FBY+%(name)'")

        if eap.als_einzelstueck_erhaeltlich:
            pass
        position.append("QTY+59:%(ve1_beinhaltet_menge)s:PCE'" % orderline)
        position.append("QTY+53:%(ve1_beinhaltet_menge)s:PCE'" % orderline)

        position.append("DTM+7+%(datum)s:102'" % param)

        envelope.extend(position)
        number_of_records += len(position)

    envelope.append("UNT+%d+%s'" % (number_of_records + 1, param['referenznr']))
    envelope.append("UNZ+1+%(uebertragungsnr)s'" % param)
    return u'\n'.join(envelope).encode('iso-8859-1')
