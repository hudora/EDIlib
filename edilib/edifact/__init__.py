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

def date_to_EDIFACT(d):
    return d.strftime('%Y%m%d')

def invoice_to_INVOICD09A(invoice):
    import time, struct, base64, os
    dict(# der ID darf 14-stellig sein, unserer ist eine 13stellige codeirte Unix Timestamp
         uebertragungsnr=base64.b32encode(struct.pack('>d', time.time())).strip('=\n')[:14],
         unhnr=base64.b32encode(struct.pack('>d', time.time()-1000000000)).strip('=\n')[:14],
         rechungsdatum=date_to_EDIFACT(invoice['rechungsdatum']),
         leistungsdatum=date_to_EDIFACT(invoice['leistungsdatum']),
         date=date_to_EDIFACT(datetime.date.today()),
         time=datetime.datedatetime.now().strftime('%H%M'),
        )
    envelope = []
    envelope.append("UNA:+.? '")
    envelope.append("UNB+UNOC:4+%(iln)s:14+%(absenderadresse_iln)s:14+%(date)s:%(time)s+%(uebertragungsnr)s'")

    k = []
    k.append("UNH+%(unhnr)s+INVOIC:D:09A:UN:EAN010'")
    k.append("BGM+385+%(rechnungsnr)s+9'") # oder 380 = Rechung
    # k.append("BGM+262+300200+9'") # oder 381 = Gutschrift
    k.append("DTM+137:%(rechungsdatum)s:102'")
    # Alternativ: DTM+3:%(rechungsdatum)s:102'
    k.append("DTM+263:%(leistungsdatum)s%(leistungsdatum)s:718'")
    # Alternativ: DTM+700:%(leistungszeitpunkt)s:102'
    # k.append("DTM+35:%(anlieferzeitpunkt)s:102'")
    # PAI	-C	1	- Payment instructions
    # PAT -M 1	- Payment terms basis This segment is used by the issuer of the invoice to specify the payment terms for the complete invoice.
    # DTM -C 5	- Date/time/period This segment is used to specify any dates associated with the payment terms for the invoice.
    # PCD -C 1	- Percentage details This segment is used to specify percentages which will be allowed or charged if the invoicee pays (does not pay) to terms.
    # MOA -C 1	- Monetary amount This segment is used to specify monetary values which will be allowed or charged if the invoicee pays (does not pay) to terms.
    # PAI	-C	1	- Payment instructions This segment is used to specify payment instructions related to payment terms.
    if 'kundenauftragsnr' in inv: # Order document identifier, buyer assigned
        k.append("RFF+ON:%(kundenauftragsnr)s'" % inv)
    if 'lieferscheinnr' in inv: # Delivery note number
        k.append("RFF+DQ:%(lieferscheinnr)s'" % inv)
    if 'guid' in inv:
        k.append("RFF+ZZZ:%(guid)s'" % inv) # Mutually defined reference number
    if 'auftragsnr' in inv:
        k.append("RFF+AAJ:%(auftragsnr)s'" % inv) # AAJ	Delivery order number - Reference number assigned by issuer to a delivery order.
    if 'infotext_kunde' in inv: # Supplier remarks Remarks from or for a supplier of goods or services.
        k.append("FTX+SUR+++%(infotext_kunde)s'" % inv)
    if 'erfasst_von' in inv: # Internal auditing information Text relating to internal auditing information.
        k.append("FTX+AEZ+++Erfasser: %(erfasst_von)s'" % inv)
    # FTX+AAI	General information
    # FTX+AAJ	Additional conditions of sale/purchase Additional conditions specific to this order or pro
    # FTX+AAR	Terms of delivery (4053) Free text of the non Incoterms terms of delivery. For Incoterms, use: 4053.
    # FTX+ABN	Accounting information The text contains information related to accounting.
    # FTX+AFB	Comment Denotes that the associated text is a comment.
    # FTX+AFD	Help text Denotes that the associated text is an item of help text.
    # FTX+BLU	Waste information Text describing waste related information.
    # FTX+PAC	Packing/marking information Information regarding the packaging and/or marking of goods.
    # FTX+PAI	Payment instructions information The free text contains payment instructions information relevant to the message.
    # FTX+PMD	Payment detail/remittance information The free text contains payment details.
    # FTX+PMT	Payment information Note contains payments information.
    # Avisierungshinweise: FTX+WHI	Warehouse instruction/information Note contains warehouse information.

    k.append("NAD+SU+%(absenderadresse_iln)s::9+%(absenderadresse_name1)s:%(absenderadresse_name2)s:%(absenderadresse_name3)s++%(absenderadresse_strasse)s:::+%(absenderadresse_ort)s++%(absenderadresse_plz)s+%(absenderadresse_land)s'")
    # Kontoverbindung FII	-C	5	- Financial institution information
    k.append("RFF+VA:%(hint_steuernr_lieferant)s'")
    k.append("NAD+BY+%(iln)s::9++%(name1)s:%(name2)s:%(name3)s+%(strasse)s+%(ort)s++%(plz)s+%(land)s'")
    k.append("RFF+AVC:%(kundennr)s'")
    k.append("RFF+VA:%(hint_steuernr_kunde)s")
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
        od = dict(positionsnummer=len(positionen)+1)
        p.append("LIN+%(positionsnummer)s++%(ean):SRV'" % od)
        p.append("IMD+F++:::%(name)s:%(artnr)s'" % od)
        p.append("QTY+47:%(menge)s:'")
        p.append("DTM+35:%(leistungsdatum)s:102'")
        if abschlag:
            k.append("FTX+ABN+++Abschlag: %(abschlag)s %'" % od)
        p.append("MOA+77:%(zu_zahlen)s'" % od) # - Rechnungsbetrag (Gesamtpositionsbetrag zuzüglich Zuschläge und MWSt, abzüglich Abschläge) (DE5025 = 77); Mussfeld 77	Invoice line item amount [5068] Total sum charged with respect to a single line item of an invoice.
        p.append("MOA+66:%(warenwert)s'" % od) # 66 Goods item total Net price x quantity for the line item.
        p.append("MOA+203:%s'" % (warenwert-hint_abschlag)) # Netto – Netto Einkaufspreis (AAA) durch Menge X Preis 203	Line item amount Goods item total minus allowances plus charges for line item. See also Code 66.
        # abschlag_prozent
        # einzelpreis* - Preis von einer Einheit ohne Mehrwertsteuer
        # - Gebindewert (DE5025 = 35E); Mussfeld *); N 11+2 MOA+35E:500'
        p.append("PRI+INV:%(einzelpreis)s'" % od)  # INV	Invoice price Referenced price taken from an invoice.
        p.append("TAX+7+VAT+++:::19+S'")
        p.append("RFF+ON:%(bestellnr)s'"  % od)
        p.append("RFF+DQ:%(lieferscheinnr)s'" % od)
        positionen.append(p)

    k.extend(positionen)
    # VERSANDKOSTEN

#UNS+S'
#MOA+124:%(mwst)s' # 124	Tax amount Tax imposed by government or other official authority related to the weight/volume charge or valuation charge.
#MOA+125:450'  # Taxable amount Amount on which a tax has to be applied.
#MOA+128:%(zu_zahlen)s' # Total amount The amount specified is the total amount.
#MOA+77:540' # 77	Invoice line item amount [5068] Total sum charged with respect to a single line item of an invoice.
#MOA+79:%(gesammtpreis)s' # 79	Total line items amount The sum of all the line item amounts

#TAX+7+VAT+++:::19+S'
#UNT+%(segmentzahl)+%(14streferenzb)s'
#UNZ+1+%(14streferenza)s'




