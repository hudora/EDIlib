#!/usr/bin/env python
# encoding: utf-8
"""
__init__.py

Created by Maximillian Dornseif on 2010-10-08.
Copyright (c) 2010 HUDORA. All rights reserved.
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


def date_to_EDIFACT(d, fmt='%Y%m%d'):
    """Convert date to EDIfact date"""

    if hasattr(d, 'strftime'):
        return d.strftime(fmt)
    if hasattr(d, 'replace'):
        return d.replace('-', '')[:8]
    return d


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


def invoice_to_INVOICD01B(invoice):
    """
    Convert from a dictionary in SimpleInvoiceProtocol format to edifact d01b format.

    Returns a (latin-1) encoded bytestream which must not be re-encoded,
    because the encoding is codified in the header.  ## XXXXX: CODIFIED?!
    """

    # TODO: ?! Warum hier die Daten?!
    param = dict(absenderadresse_iln=u'4005998000007',
                 absenderadresse_name1=u'HUDORA GmbH',
                 absenderadresse_name2=u'Fakturierung',
                 absenderadresse_name3=u'',
                 absenderadresse_strasse=u'Jägerwald 13',
                 absenderadresse_ort=u'Remscheid',
                 absenderadresse_plz=u'42897',
                 absenderadresse_land=u'DE')
    param.update(invoice)
    param.update(dict(  # der ID darf 14-stellig sein, unserer ist ein 13stelliger, kodierter Unix-Timestamp
         uebertragungsnr=base64.b32encode(struct.pack('>d', time.time())).strip('=\n')[:14],
         unhnr=base64.b32encode(struct.pack('>d', time.time() - 1000000000)).strip('=\n')[:14],
         rechnungsdatum=date_to_EDIFACT(invoice['rechnungsdatum']),
         leistungsdatum=date_to_EDIFACT(invoice.get('leistungsdatum', invoice.get('rechnungsdatum'))),
         date=date_to_EDIFACT(datetime.date.today(), fmt='%y%m%d'),
         time=datetime.datetime.now().strftime('%H%M'),
         absenderadresse_iln='4005998000007',
        ))

    # Convert monetary values from Eurocent to Euro
    for key in 'rechnungsbetrag', 'warenwert', 'zu_zahlen', 'rechnung_steueranteil', 'versandkosten':
        param[key] = huTools.monetary.cent_to_euro(invoice[key])

    # Message Envelope:
    # Add 'Service String Advice' with tandard delimiter characters
    envelope = ["UNA:+.? '"]

    # Add 'Interchange Header'
    # UN/ECE level C (ISO 8859-1), Syntax Version 3
    # Partner identification via GS1 GLN (= 14)
    envelope.append("UNB+UNOC:3+%(absenderadresse_iln)s:14+%(iln)s:14+%(date)s:%(time)s+%(uebertragungsnr)s'" % param)

    # UNH - Message Header:
    header = ["UNH+%(unhnr)s+INVOIC:D:01B:UN:EAN010'" % param]
    # Begin of Message: Document code 380 (Commercial Invoice), Message function code 9 (Original)
    header.append("BGM+380+%(rechnungsnr)s+9'" % param)
    # DTM - Date/Time/Period
    # Function code qualifier: 137 (Document/message date/time)
    # Format code 102 (CCYYMMDD)
    header.append("DTM+137:%(rechnungsdatum)s:102'" % param)
    # Function code qualifier: 35 (Delivery date/time, actual)
    header.append("DTM+35:%(leistungsdatum)s:102'" % param)

    # DTM -C 5  - Date/time/period This segment is used to specify any dates associated with the payment terms for the invoice.
    # PCD -C 1  - Percentage details This segment is used to specify percentages which will be allowed or charged if the invoicee pays (does not pay) to terms.
    # MOA -C 1  - Monetary amount This segment is used to specify monetary values which will be allowed or charged if the invoicee pays (does not pay) to terms.
    # PAI       -C      1       - Payment instructions This segment is used to specify payment instructions related to payment terms.

    # PAI - Payment instructions
    # ALI - Additional information

    # FTX - Free text
    if 'infotext_kunde' in param:  # Supplier remarks Remarks from or for a supplier of goods or services.
        header.append("FTX+SUR+++%(infotext_kunde)s'" % param)

    # RFF - Reference
    if 'lieferscheinnr' in param:  # Delivery note number
        header.append("RFF+DQ:%(lieferscheinnr)s'" % param)
        # DTM for delivery note
    if 'kundenauftragsnr' in param:  # Order document identifier, buyer assigned (ON)
        header.append("RFF+ON:%(kundenauftragsnr)s'" % param)
        # DTM for ordering date
    if 'guid' in param:  # Originator's reference (ABO)
        header.append("RFF+ABO:%(guid)s'" % param)
    if 'auftragsnr' in param:  # Order number (supplier) (VN)
        header.append("RFF+VN:%(auftragsnr)s'" % param)

    # NAD - Name and addres:
    # Name and address of seller given as GLN
    header.append("NAD+SU+%(absenderadresse_iln)s::9'" % param)
    # FII - Financial information
    # "FII+RB+%(IBAN)s+:25:5'"
    # "FII+RB+%(BIC)s+:25:17'"
    header.append("FFI+RB+%(kontonr)s:TODONAME+BANKNAME:25:5'")
    if param.get('unsere_lieferantennr'):
        header.append("RFF+YC1:%(unsere_lieferantennr)s'" % param)
    if 'hint_steuernr_lieferant' in param:
        header.append("RFF+VA:%(hint_steuernr_lieferant)s'" % param)

    # Name and address of Buyer given as GLN
    header.append("NAD+BY+%(iln)s::9'" % param)
    header.append("RFF+IT:%(kundennr)s'" % param)
    if 'hint_steuernr_kunde' in param:
        header.append("RFF+VA:%(hint_steuernr_kunde)s'" % param)

    # Name and address of supplier given as GLN
    header.append("NAD+DP+%(absenderadresse_iln)s::9'" % param)

    # Name and address of ultimate consignee given as GLN
    if param.get('lieferadresse', {}).get('iln'):
        header.append("NAD+UC+%(iln)s::9'" % param['lieferadresse'])

    # Tax Record: Function code qualifier 7 (Tax), Name code VAT (Value added tax),
    # Tax rate, Category code S (Standard)
    header.append("TAX+7+VAT+++:::%(steuer_prozent)s+S'" % param)

    # Currency Record: Reference currency, Currency type code qualifier 4 (Invoicing currency)
    if not 'waehrung' in param:
        param['waehrung'] = 'EUR'
    header.append("CUX+2:%(waehrung)s:4'" % param)

    # Skonto
    if param.get('skonto_prozent'):
        header.append("PAT+3'")
        param['hint_skontodatum'] = date_to_EDIFACT(param['hint_skontodatum'], fmt='%y%m%d')
        header.append("DTM+12:%(hint_skontodatum):102'" % param)
        header.append("PCD+12:%(skonto_prozent)s'" % param)

    # Due date
    header.append("PAT+3'")
    param['hint_zahlungsdatum'] = date_to_EDIFACT(param['hint_zahlungsdatum'], fmt='%y%m%d')
    header.append("DTM+13:%(hint_zahlungsdatum):102'" % param)

    # Monetary amount for freight charge
    if param.get('versandkosten'):
        header.append("ALC+C+FC'")
        header.append("MOA+8:%(versandkosten).2f'" % param)
        header.append("TAX+7+VAT+++:::%(steuer_prozent)s+S'" % param)

    envelope.extend(header)
    number_of_records = len(header)

    # Orderline / Positions
    for positionsnummer, orderline in enumerate(invoice['orderlines']):
        position = []
        orderline = copy.copy(orderline)
        orderline.update(dict(positionsnummer=positionsnummer + 1))

        if 'ean' in orderline:
            position.append("LIN+%(positionsnummer)s++%(ean)s:SRV'" % orderline)
        else:
            position.append("LIN+%(positionsnummer)s++:SRV'" % orderline)

        # Additional Product ID
        # artnr is supplier's item no (SA), defined by supplier (91)
        # kundenartnr is buyer's item no (IN), defined by buyer (92)
        if 'kundenartnr' in orderline:
            position.append("PIA+%(positionsnummer)s+%(artnr)s:SA::91+%(kundenartnr)s:IN::92'")

        # Item description
        if 'name' in orderline:
            position.append("IMD+A++:::%(name)s::DE'" % orderline)
        else:
            raise RuntimeError("no product name")

        # Line item is an invoicing unit
        position.append("IMD+C++IN::9'")
        # Line item is a consumer unit
        position.append("IMD+C++CU::9'")
        # Quantity given in peaces (PCE)
        position.append("QTY+47:%(menge)s:PCE'" % orderline)

        if orderline.get('abschlag'):
            position.append("FTX+ABN+++Abschlag?: %(abschlag)s %%'" % orderline)

        # TODO: Artikelnettobetrag
        # TODO: Als Dezimalzahl huTools.monetary.cent_to_euro()
        # position.append("MOA+203:%(zu_zahlen)s'" % orderline)  # - Rechnungsbetrag
        # position.append("MOA+66:%(warenwert)s'" % orderline)  # 66 Goods item total Net price x quantity for the line item.
        # TODO: p.append("MOA+203:%s'" % (warenwert-hint_abschlag)) # Netto – Netto Einkaufspreis (AAA) durch Menge X Preis 203
        # Line item amount Goods item total minus allowances plus charges for line item. See also Code 66.

        # Price information, prices as calculation net (AAA) per 1 piece (PCE)
        position.append("PRI+AAA:%(einzelpreis)s:::1:PCE'" % orderline)

        # Das sind unbekannte Felder...
        if 'bestellnr' in orderline:
            position.append("RFF+ON:%(bestellnr)s'" % orderline)
        if 'lieferscheinnr' in orderline:
            position.append("RFF+DQ:%(lieferscheinnr)s'" % orderline)

        # Free text
        if position.get('infotext_kunde'):
            position.append("FTX+ZZZ+++%s'" % split_text(position['infotext_kunde'], 512, max_records=3))

        envelope.extend(position)
        number_of_records += len(position)

    # Message Footer:
    footer = ["UNS+S'"]
    # Invoice amount (77)
    footer.append("MOA+77:%(zu_zahlen).2f'" % param)
    # Total line items amount (79)
    footer.append("MOA+79:%(warenwert).2f'" % param)
    # Taxable amount (125)
    footer.append("MOA+125:%(rechnungsbetrag).2f'" % param)
    # Tax amount (124)
    footer.append("MOA+124:%(rechnung_steueranteil).2f'" % param)
    envelope.extend(footer)

    # TODO: hint/abschlag, abschlag_prozent?

    number_of_records += len(footer)
    envelope.append("UNT+%d+%s'" % (number_of_records + 1, param['unhnr']))
    envelope.append("UNZ+1+%(uebertragungsnr)s'" % param)
    return u'\n'.join(envelope).encode('iso-8859-1')


def invoice_to_INVOICD09A(invoice):
    """
    Convert from a dictionary in SimpleInvoiceProtocol format to edifact d09a format.

    Returns a (latin-1) encoded bytestream which must not be re-encoded, because the encoding is codified in the header.
    """
    param = dict(absenderadresse_iln='4005998000007',
                 absenderadresse_name1='HUDORA GmbH',
                 absenderadresse_name2='Fakturierung',
                 absenderadresse_name3='',
                 absenderadresse_strasse=u'Jägerwald 13',
                 absenderadresse_ort='Remscheid',
                 absenderadresse_plz='42897',
                 absenderadresse_land='DE')
    param.update(invoice)
    param.update(dict(  # der ID darf 14-stellig sein, unserer ist eine 13stellige codeirte Unix Timestamp
         uebertragungsnr=base64.b32encode(struct.pack('>d', time.time())).strip('=\n')[:14],
         unhnr=base64.b32encode(struct.pack('>d', time.time() - 1000000000)).strip('=\n')[:14],
         rechnungsdatum=date_to_EDIFACT(invoice['rechnungsdatum']),
         leistungsdatum=date_to_EDIFACT(invoice.get('leistungsdatum', invoice.get('rechnungsdatum'))),
         date=date_to_EDIFACT(datetime.date.today()),
         time=datetime.datetime.now().strftime('%H%M'),
         absenderadresse_iln='4005998000007',
        ))

    for key in "name1 name2 name3 strasse ort plz".split():
        if key not in param:
            param[key] = ''
    for key in param:
        if hasattr(param, 'encode'):
            param[key] = param.encode('iso-8859-1', '.').replace('+', '?+').replace(':', '?:').replace("'", "?'")
    for key in param.get('hint', {}):
        if hasattr(param['hint'][key], 'encode'):
            param['hint_' + key] = param['hint'][key].encode('iso-8859-1', '.').replace('+', '?+').replace(':', '?:').replace("'", "?'")

    envelope = []
    envelope.append("UNA:+.? '")
    envelope.append("UNB+UNOC:4+%(iln)s:14+%(absenderadresse_iln)s:14+%(date)s:%(time)s+%(uebertragungsnr)s'" % param)

    k = []
    k.append("UNH+%(unhnr)s+INVOIC:D:09A:UN:EAN010'" % param)
    k.append("BGM+385+%(rechnungsnr)s+9'" % param)  # oder 380 = Rechung
    # k.append("BGM+262+300200+9'")  # oder 381 = Gutschrift
    k.append("DTM+137:%(rechnungsdatum)s:102'" % param)
    # Alternativ: DTM+3:%(rechnungsdatum)s:102'
    k.append("DTM+263:%(leistungsdatum)s%(leistungsdatum)s:718'" % param)
    # Alternativ: DTM+700:%(leistungszeitpunkt)s:102'
    # k.append("DTM+35:%(anlieferzeitpunkt)s:102'")
    # PAI       -C      1       - Payment instructions
    # PAT -M 1  - Payment terms basis This segment is used by the issuer of the invoice to specify the payment terms for the complete invoice.
    # DTM -C 5  - Date/time/period This segment is used to specify any dates associated with the payment terms for the invoice.
    # PCD -C 1  - Percentage details This segment is used to specify percentages which will be allowed or charged if the invoicee pays (does not pay) to terms.
    # MOA -C 1  - Monetary amount This segment is used to specify monetary values which will be allowed or charged if the invoicee pays (does not pay) to terms.
    # PAI       -C      1       - Payment instructions This segment is used to specify payment instructions related to payment terms.
    if 'kundenauftragsnr' in param:  # Order document identifier, buyer assigned
        k.append("RFF+ON:%(kundenauftragsnr)s'" % param)
    if 'lieferscheinnr' in param:  # Delivery note number
        k.append("RFF+DQ:%(lieferscheinnr)s'" % param)
    if 'guid' in param:
        k.append("RFF+ZZZ:%(guid)s'" % param)  # Mutually defined reference number
    if 'auftragsnr' in param:
        k.append("RFF+AAJ:%(auftragsnr)s'" % param)  # AAJ       Delivery order number - Reference number assigned by issuer to a delivery order.
    if 'infotext_kunde' in param:  # Supplier remarks Remarks from or for a supplier of goods or services.
        k.append("FTX+SUR+++%(infotext_kunde)s'" % param)
    if 'erfasst_von' in param:  # Internal auditing information Text relating to internal auditing information.
        k.append("FTX+AEZ+++Erfasser: %(erfasst_von)s'" % param)
    # FTX+AAI   General information
    # FTX+AAJ   Additional conditions of sale/purchase Additional conditions specific to this order or pro
    # FTX+AAR   Terms of delivery (4053) Free text of the non Incoterms terms of delivery. For Incoterms, use: 4053.
    # FTX+ABN   Accounting information The text contains information related to accounting.
    # FTX+AFB   Comment Denotes that the associated text is a comment.
    # FTX+AFD   Help text Denotes that the associated text is an item of help text.
    # FTX+BLU   Waste information Text describing waste related information.
    # FTX+PAC   Packing/marking information Information regarding the packaging and/or marking of goods.
    # FTX+PAI   Payment instructions information The free text contains payment instructions information relevant to the message.
    # FTX+PMD   Payment detail/remittance information The free text contains payment details.
    # FTX+PMT   Payment information Note contains payments information.
    # Avisierungshinweise: FTX+WHI      Warehouse instruction/information Note contains warehouse information.

    k.append("NAD+SU+%(absenderadresse_iln)s::9+%(absenderadresse_name1)s:%(absenderadresse_name2)s:%(absenderadresse_name3)s++%(absenderadresse_strasse)s:::+%(absenderadresse_ort)s++%(absenderadresse_plz)s+%(absenderadresse_land)s'" % param)
    # Kontoverbindung FII       -C      5       - Financial institution information
    if 'hint_steuernr_lieferant' in param:
        k.append("RFF+VA:%(hint_steuernr_lieferant)s'" % param)
    k.append("NAD+BY+%(iln)s::9++%(name1)s:%(name2)s:%(name3)s+%(strasse)s+%(ort)s++%(plz)s+%(land)s'" % param)
    k.append("RFF+AVC:%(kundennr)s'" % param)
    if 'hint_steuernr_kunde' in param:
        k.append("RFF+VA:%(hint_steuernr_kunde)s'" % param)
    k.append("CUX+2:EUR:4'")
    # Lieferanschrift
    # NAD+DP+9012345000028::9'
    # - Warenendempfänger (DE3035 = UC); Kannfeld; N 13
    # NAD+UC+9012345000035::9'
    # - Besteller (DE3035 = OB); Kannfeld; N 13
    # NAD+OB+9012345000042::9'

# versandkosten
    positionen = []
    for orderline in invoice['orderlines']:
        p = []
        od = copy.copy(orderline)
        od.update(dict(positionsnummer=len(positionen) + 1))
        if 'ean' in od:
            p.append("LIN+%(positionsnummer)s++%(ean)s:SRV'" % od)
        else:
            p.append("LIN+%(positionsnummer)s++:SRV'" % od)
        if 'name' in od:
            p.append("IMD+F++:::%(name)s:%(artnr)s'" % od)
        else:
            p.append("IMD+F++::::%(artnr)s'" % od)
        p.append("QTY+47:%(menge)s:'" % od)
        p.append("DTM+35:%(leistungsdatum)s:102'" % param)
        if 'abschlag' in od and od['abschlag']:
            p.append("FTX+ABN+++Abschlag?: %(abschlag)s %%'" % od)
        p.append("MOA+77:%(zu_zahlen)s'" % od)  # - Rechnungsbetrag (Gesamtpositionsbetrag zuzüglich Zuschläge und MWSt, abzüglich Abschläge) (DE5025 = 77); Mussfeld 77     Invoice line item amount [5068] Total sum charged with respect to a single line item of an invoice.
        p.append("MOA+66:%(warenwert)s'" % od)  # 66 Goods item total Net price x quantity for the line item.
        # TODO: p.append("MOA+203:%s'" % (warenwert-hint_abschlag)) # Netto – Netto Einkaufspreis (AAA) durch Menge X Preis 203       Line item amount Goods item total minus allowances plus charges for line item. See also Code 66.
        # abschlag_prozent

        # einzelpreis* - Preis von einer Einheit ohne Mehrwertsteuer
        # - Gebindewert (DE5025 = 35E); Mussfeld *); N 11+2 MOA+35E:500'
        p.append("PRI+INV:%(einzelpreis)s'" % od)  # INV        Invoice price Referenced price taken from an invoice.
        p.append("TAX+7+VAT+++:::19+S'")
        if 'bestellnr' in od:
            p.append("RFF+ON:%(bestellnr)s'" % od)
        if 'lieferscheinnr' in od:
            p.append("RFF+DQ:%(lieferscheinnr)s'" % od)
        positionen.append(p)

    for p in positionen:
        k.extend(p)

    # VERSANDKOSTEN
    # 64    Freight charge - Amount to be paid for moving goods, by whatever means, from one place to another, inclusive discounts,
    # allowances, rebates, adjustment factors and additional cost relating to freight costs (UN/ECE Recommendation no 23).
    if invoice.get('versandkosten'):
        k.append("MOA+64:%(versandkosten)s'" % invoice)

#UNS+S'
#MOA+124:%(mwst)s'  # 124        Tax amount Tax imposed by government or other official authority related to the weight/volume charge or valuation charge.
#MOA+125:450'  # Taxable amount Amount on which a tax has to be applied.
#MOA+128:%(zu_zahlen)s'  # Total amount The amount specified is the total amount.
#MOA+77:540'  # 77       Invoice line item amount [5068] Total sum charged with respect to a single line item of an invoice.
#MOA+79:%(gesammtpreis)s'  # 79  Total line items amount The sum of all the line item amounts

#TAX+7+VAT+++:::19+S'
#UNT+%(segmentzahl)+%(14streferenzb)s'
#UNZ+1+%(14streferenza)s'

    envelope.extend(k)
    envelope.append("UNT+%d+%s'" % (len(k) + 1, param['unhnr']))
    envelope.append("UNZ+1+%(uebertragungsnr)s'" % param)

    return u'\n'.join(envelope).encode('iso-8859-1', 'ignore')
