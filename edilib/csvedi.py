# encoding: utf-8
"""
invoice.py - Export an deliverynote/invoice as CSV

Created by Christian Klein on 2010-10-21.
Copyright (c) 2010, 2011 HUDORA GmbH. All rights reserved.
"""

from cStringIO import StringIO
import csv


def invoice_to_csv(invoice, delimiter=';'):
    """Exportiere Rechnung im SimpleInvoiceProtocol als CSV"""

    def create_row(recordtype, obj):
        """
        Erzeuge den Datensatz des entsprechenden Typs.
        Die Daten werden aus `obj` gelesen.
        """

        # Zuordnung von Satztypen zu Feldernamen
        fields = {
            'K': ['iln', 'name1', 'name2', 'name3', 'strasse', 'land', 'ort', 'steuernr_kunde', 'kundennr'],
            'L': ['absenderadresse/iln', 'absenderadresse/name1', 'absenderadresse/name2', 'absenderadresse/name3', 'absenderadresse/strasse',
                   'absenderadresse/land', 'absenderadresse/plz', 'absenderadresse/ort', 'hint/steuernr_lieferant'],
            'S1': ['versandkosten', 'warenwert', 'abschlag_prozent', 'hint/abschlag', 'rechnungsbetrag', 'rechnung_steueranteil',
                   'steuer_prozent', 'zu_zahlen', 'skonto_prozent', 'skontotage', 'hint/skontodatum', 'hint/skontobetrag',
                   'zu_zahlen_bei_skonto', 'hint/rechnungsbetrag_bei_skonto', 'hint/rechnung_steueranteil_bei_skonto'],
            'S2': ['leistungsdatum', 'kundenauftragsnr', 'infotext_kunde', 'kundennr', 'auftragsnr', 'zahlungstage', 'hint/zahlungsdatum'],
            'O': ['guid', 'menge', 'artnr', 'ean', 'name', 'zu_zahlen', 'infotext_kunde', 'einzelpreis', 'warenwert', 'abschlag_prozent'],
        }

        if not recordtype in fields:
            return []

        row = [recordtype, guid]
        for attr in fields[recordtype]:
            # indirekte Referenzierung auflösen
            if '/' in attr:
                objname, attr = attr.split('/')
                obj = obj.get(objname, {})

            try:
                value = obj.get(attr, '')
                value = unicode(value).encode('iso8859-1')
            except UnicodeDecodeError, exception:
                raise RuntimeError(u"Error in Record %s, field %s: %s" % (recordtype, attr, str(exception)))
            row.append(value)

        return row

    # GUID der Rechnung, wird für jeden Satz gebraucht
    guid = invoice.get('guid', '').encode('iso8859-1')

    fileobj = StringIO()
    writer = csv.writer(fileobj, delimiter=delimiter)

    # Schreibe Satz (L)ieferant
    writer.writerow(create_row('L', invoice))

    # Schreibe Satz (K)unde
    writer.writerow(create_row('K', invoice))

    # Schreibe Satz Rechnungs(S)umme
    writer.writerow(create_row('S1', invoice))
    writer.writerow(create_row('S2', invoice))

    # Schreibe Sätze (O)rderline
    for orderline in invoice.get('orderlines', []):
        writer.writerow(create_row('O', orderline))

    return fileobj.getvalue()


def lieferschein_to_csv(lieferschein, delimiter=';'):
    """Liefert den Lieferschein als CSV-formatierten String zurueck, wobei jede Position
       als eigene Zeile im CSV ausgegeben wird."""
    buf = StringIO()
    writer = csv.writer(buf, delimiter=delimiter)
    for position in lieferschein.get('positionen', []):
        writer.writerow(['P',
                         lieferschein['lieferscheinnr'],
                         lieferschein['auftragsnr'],
                         lieferschein['kundennr'],
                         position['auftragpos_guid'],
                         position['kommipos_guid'],
                         position['menge'],
                         position['artnr'],
                         position['infotext_kunde']])
    return buf.getvalue()
