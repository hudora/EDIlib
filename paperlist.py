#!/usr/bin/env python
# encoding: utf-8

from decimal import Decimal
import codecs

import husoftm.kunden


def _floatvals2string(d):
    """FIXME: Weiss gerade nicht, wie ich Decimal anders in String mit nur 2 Nachkommastellen formatieren soll.

    Diese Funktion wandelt alle values vom Typ Decimal in einen formatierten String um."""
    for k, v in d.items():
        if isinstance(v, Decimal):
            d[k] = ('%20.2f' % v).strip()
    return d


class Paperlist(object):

    def __init__(self, filename):
        self.filename = filename
        self._is_finished = False
        self.paperlist = None
        self.invoices = []
        self.footer = dict(warenwert='TODO', skonto='TODO', umsatzsteuer='TODO', rechnungsendbetrag='TODO',
                            iln='', name_ort='', rechn_nr='', rechn_datum='', leergut='')
        self.valid = False
        self.comments = [] # dbg purpose
        self.__formatstring = None

    def _get_headerstring(self):
        """Returns formatted Header for paperlist."""
        headerdict = self.headerdict # alias

        headerdict['empf_fax'] = '+49 (0) 40/6377-4222'

        # basic consistency check
        assert('hudora_iln' in headerdict)
        assert('empf_iln' in headerdict)
        assert('rechnungslistennr' in headerdict)
        assert('datum' in headerdict)
        assert('empf_name1' in headerdict)
        assert('empf_name2' in headerdict)
        assert('empf_strasse' in headerdict)
        assert('empf_plz' in headerdict)
        assert('empf_ort' in headerdict)
        assert('empf_fax' in headerdict)
        assert('steuernr' in headerdict)
        assert('empf_unsere_lieferantennr' in headerdict)

        paperlist = """
Absender: (ILN %(hudora_iln)s)
HUDORA GmbH                                     Kontonummer des Vertragslieferanten: %(empf_unsere_lieferantennr)s
Jaegerwald 13
42897 Remscheid
Steuernummer %(steuernr)s


                                                                             Nummer            Datum
Empfaenger: (ILN %(empf_iln)s)                           Sammelabrechnung   %(rechnungslistennr)06i            %(datum)s
%(empf_name1)s %(empf_name2)s
%(empf_strasse)s
%(empf_plz)s %(empf_ort)s
Per Fax an %(empf_fax)s

"""
        paperlist = paperlist % headerdict
        return paperlist

    def _footer(self, formatstring):
        """Positioniert die Summenzeile an der richtigen Stelle."""
        skonto = sum([float(inv.get('skonto', 0)) for inv in self.invoices])
        self.footer['skonto'] = skonto
        #if (abs(float(self.footer['skonto']) - float(skonto)) > 0.009):
            #raise RuntimeError('Skonto nicht plausibel: %s != %s' % (float(self.footer['skonto']), float(skonto)))
        formatstring = formatstring % _floatvals2string(self.footer)
        splitted = formatstring.split('|')
        leftside = ' '.join(splitted[:5])
        leftformatstring = '%%%is' % len(leftside)
        leftside = leftformatstring % '|    Summe '
        rightside = '|'
        rightside += '|'.join(splitted[5:])
        return leftside+rightside

    def _formatstring(self):
        """Returns a formatstring which has the correct fieldlength of addressfield, so that everything is lined-up correctly."""
        if not self.__formatstring:
            maxlen = max([len(tmpdict.get('name_ort', ''))+2 for tmpdict in self.invoices])
            self.__formatstring = "| %%(name_ort)-%is | %%(iln)13s | %%(rechn_nr)12s | %%(rechn_datum)12s | %%(warenwert)15s | %%(skonto)12s | %%(leergut)15s | %%(umsatzsteuer)12s | %%(rechnungsendbetrag)14s |"
            self.__formatstring = self.__formatstring % maxlen
        return self.__formatstring

    def _invoice_header(self):
        """Returns a string containing the column headers for the invoice list."""
        s = self._formatstring() % dict(name_ort="",
                                   iln=" ",
                                   rechn_nr="Rechnungs-",
                                   rechn_datum="Rechnungs-",
                                   warenwert="",
                                   skonto="",
                                   leergut="Leergut/Fracht/",
                                   umsatzsteuer="",
                                   rechnungsendbetrag="Rechnungs-")
        s += '\n'
        s += self._formatstring() % dict(name_ort=u"Warenempfänger",
                                   iln="ILN",
                                   rechn_nr="nummer",
                                   rechn_datum="datum",
                                   warenwert="Warenwert",
                                   skonto="Skonto",
                                   leergut="Verpackung",
                                   umsatzsteuer="Umsatzsteuer",
                                   rechnungsendbetrag="betrag")
        return s

    def comment(self, msg):
        """Append a comment to the paperlist. More or less for debugging purposes."""
        self.comments.append(msg)

    # FIXME this could be handeld by destructor
    def finish(self):
        """Finishes paperlist by writing its contents to a file."""

        # make sure, not to write to the file twice
        if self._is_finished:
            raise RuntimeError("Datei wurde bereits geschrieben.")
            return

        if not self.valid:
            paperlist = "V E R A R B E I T U N G S F E H L E R ! ! !"
        else:
            paperlist = [self._get_headerstring()]
            # header
            invoice_header = self._invoice_header()
            # table
            sepa = '=' * len(invoice_header.split('\n')[0])
            paperlist.append(sepa)
            paperlist.append(invoice_header)
            paperlist.append(sepa)
            formatstring = self._formatstring()
            for inv in self.invoices:
                paperlist.append(formatstring % _floatvals2string(inv))
            paperlist.append(sepa)
            # footer
            footer = self._footer(formatstring)
            paperlist.append(footer)
            paperlist.append(' '*footer.index('|') + '='*len(footer.lstrip()))

            paperlist = "\n".join(paperlist)

            # dbg
            if self.comments:
                paperlist += '\n' * 3
                paperlist += '---8<--' * 8
                paperlist += '\n' * 4
                paperlist += '\n'.join(self.comments)

        print self.filename
        codecs.open(self.filename, "w", 'utf-8').write(paperlist)
        self._is_finished = True

    def update_header_from_rec000(self, rec000):
        """Headerinformationen aus einem SoftM 000-record auslesen."""
        assert(self.paperlist==None)

        datum = rec000.erstellungsdatum
        datum = "%s-%s-%s" % (datum[:4], datum[4:6], datum[6:])
        headerdict = dict(hudora_iln=rec000.sender_iln, empf_iln=rec000.empfaenger_iln,
                          datum=datum, rechn_nr=rec000.datenaustauschreferenz)
        kundendict = husoftm.kunden.get_kunde_by_iln(rec000.empfaenger_iln)
        # print kundendict.__dict__
        d = {}
        for k, v in kundendict.__dict__.items():
            d['empf_'+k] = v

        headerdict.update(d)
        headerdict['steuernr'] = 12657370941
        self.headerdict = headerdict

    def update_header(self, data):
        self.headerdict.update(data)
        pass

    def update_footer(self, data):
        """Dictionary fuer Listenende aktualisieren."""
        self.footer.update(data)

    def collect_invoice_info(self, data):
        """Aktuellen Rechnungseintrag updaten."""
        self.invoices[-1].update(data)

    def add_invoice(self):
        """Einen neuen Rechnungseintrag (leeres dict) erzeugen."""
        d = dict(
                name_ort="TODO",
                iln="TODO",
                rechn_nr="TODO",
                rechn_datum="TODO",
                warenwert="TODO",
                skonto="TODO",
                leergut="-",
                umsatzsteuer="TODO",
                rechnungsendbetrag="TODO")
        self.invoices.append(d)
