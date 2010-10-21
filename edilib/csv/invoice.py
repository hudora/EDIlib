# encoding: utf-8
"""
invoice.py - Export an invoice as CSV

Created by Christian Klein on 2010-10-21.
Copyright (c) 2010 HUDORA GmbH. All rights reserved.
"""

from cStringIO import StringIO
import csv


def export_csv(invoice):
    """Exportiere Rechnung im SimpleInvoiceProtocol als CSV"""
    
    def create_row(recordtype, obj):
        """
        Erzeuge den Datensatz des entsprechenden Typs.
        Die Daten werden aus `obj` gelesen.
        """
        
        # Zuordnung von Satztypen zu Feldernamen
        fields = {
            'K':  ['iln', 'name1', 'name2', 'name3', 'strasse', 'land', 'ort', 'steuernr_kunde', 'kundennr'],
            'L':  ['absenderadresse/iln', 'absenderadresse/name1', 'absenderadresse/name2', 'absenderadresse/name3', 'absenderadresse/strasse',
                   'absenderadresse/land', 'absenderadresse/plz', 'absenderadresse/ort', 'hint/steuernr_lieferant'],
            'S1': ['versandkosten', 'warenwert', 'abschlag_prozent', 'hint/abschlag', 'rechnungsbetrag', 'rechnung_steueranteil',
                   'steuer_prozent', 'zu_zahlen', 'skonto_prozent', 'skontotage', 'hint/skontodatum', 'hint/skontobetrag',
                   'zu_zahlen_bei_skonto', 'hint/rechnungsbetrag_bei_skonto', 'hint/rechnung_steueranteil_bei_skonto'],
            'S2': ['leistungsdatum', 'kundenauftragsnr', 'infotext_kunde', 'kundennr', 'auftragsnr', 'zahlungstage', 'hint/zahlungsdatum'],
            'O':  ['guid', 'menge', 'artnr', 'ean', 'name', 'zu_zahlen', 'infotext_kunde', 'einzelpreis', 'warenwert', 'abschlag_prozent'],
        }
        
        if not recordtype in fields:
            return []
        
        row = [recordtype, guid]
        for attr in fields[recordtype]:
            # indirekte Referenzierung auflösen
            if '/' in attr:
                objname, attr = attr.split('/')
                obj = obj.get(objname, {})
            
            value = unicode(obj.get(attr, ''))
            row.append(value.encode('iso8859-1'))
        
        return row
    
    # GUID der Rechnung, wird für jeden Satz gebraucht
    guid = invoice.get('guid', '').encode('iso8859-1')
    
    fileobj = StringIO()
    writer = csv.writer(fileobj, dialect='excel')
    
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
