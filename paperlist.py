#!/usr/bin/env python
# encoding: utf-8

from decimal import Decimal
import codecs

import husoftm.kunden

# quite a lot g's here:
g_paperlist = None
g_invoices = None
g_footer = None
g_filename = None
g_invalid = None
g_comments = [] # dbg purpose


def _footer(formatstring):
    # skonto = sum([float(inv.get('skonto', 0)) for inv in g_invoices])
    # g_footer['skonto'] = skonto
    formatstring = formatstring % _floatvals2string(g_footer)
    splitted = formatstring.split('|')
    leftside = ' '.join(splitted[:5])
    leftformatstring = '%%%is' % len(leftside)
    leftside = leftformatstring % '|    Summe '
    rightside = '|'
    rightside += '|'.join(splitted[5:])
    return leftside+rightside


def _formatstring():
    s = "| %%(name_ort)-%is | %%(iln)13s | %%(rechn_nr)16s | %%(rechn_datum)14s | %%(warenwert)16s | %%(skonto)16s | %%(leergut)26s | %%(umsatzsteuer)16s | %%(rechnungsendbetrag)19s |"
    s = s % _get_max_address_len()
    return s


def _invoice_header():
    s = _formatstring() % dict(name_ort="Name",
                               iln="ILN",
                               rechn_nr="Rechnungsnummer",
                               rechn_datum="Rechnungsdatum",
                               warenwert="Warenwert",
                               skonto="Skonto",
                               leergut="Leergut/Fracht/Verpackung",
                               umsatzsteuer="Umsatzsteuer",
                               rechnungsendbetrag="Rechnungsendbetrag")
    return s


def _calc_address_len(inv_dict):
    name_ort = inv_dict['name_ort']
    return len(name_ort)+2


def _get_max_address_len():
    global g_invoices
    l = [_calc_address_len(d) for d in g_invoices]
    maxlen = max(l)
    return maxlen


def _floatvals2string(d):
    """Kotz.... Weiss gerade nicht, wie ich Decimal in String formatieren soll."""
    for k, v in d.items():
        if isinstance(v, Decimal):
            d[k] = ('%20.2f' % v).strip() # doppelkotz
    return d


def comment(msg):
    global g_comments
    g_comments.append(msg)


def invalidate():
    global g_invalid
    g_invalid = True

def finish_paperlist(hack_ist_einzelrechnung):

    global g_paperlist
    global g_invoices
    global g_footer
    global g_filename
    global g_invalid
    global g_comments
    if g_invalid:
        paperlist = "V E R A R B E I T U N G S F E H L E R ! ! !"

    elif hack_ist_einzelrechnung:
        pass

    else:
        paperlist = [g_paperlist]
        invoice_header = _invoice_header()
        sepa = '=' * len(invoice_header)
        paperlist.append(sepa)
        paperlist.append(invoice_header)
        paperlist.append(sepa)
        # import ipdb; ipdb.set_trace()
        formatstring = _formatstring()
        for inv in g_invoices:
            paperlist.append(formatstring % _floatvals2string(inv))
        paperlist.append(sepa)
        footer =  _footer(formatstring)
        paperlist.append(footer)
        paperlist.append(' '*footer.index('|') + '='*len(footer.lstrip()))

        paperlist = "\n".join(paperlist)

        # dbg
        if g_comments:
            paperlist += '\n' * 3
            paperlist += '---8<--' * 8
            paperlist += '\n' * 4
            paperlist += '\n'.join(g_comments)

    if not hack_ist_einzelrechnung:
        codecs.open(g_filename, "w", 'utf-8').write(paperlist)

    # reset global variables
    g_paperlist = None
    g_invoices = None
    g_footer = None
    g_filename = None
    g_invalid = None
    g_comments = []


def new_paperlist(filename):
    global g_filename
    g_filename = filename


def update_header(rec000):
    global g_invoices
    g_invoices = []
    assert(g_paperlist==None)

    headerdict = dict(hudora_iln=rec000.sender_iln, empf_iln=rec000.empfaenger_iln,
            datum=rec000.erstellungsdatum, rechn_nr=rec000.datenaustauschreferenz)
    kundendict = husoftm.kunden.get_kunde_by_iln(rec000.empfaenger_iln)
    # print kundendict.__dict__
    d = {}
    for k, v in kundendict.__dict__.items():
        d['empf_'+k] = v

    headerdict.update(d)


    assert(headerdict.has_key('hudora_iln'))
    assert(headerdict.has_key('empf_iln'))
    assert(headerdict.has_key('rechn_nr'))
    assert(headerdict.has_key('datum'))
    assert(headerdict.has_key('empf_name1'))
    assert(headerdict.has_key('empf_name2'))
    assert(headerdict.has_key('empf_strasse'))
    assert(headerdict.has_key('empf_plz'))
    assert(headerdict.has_key('empf_ort'))
    assert(headerdict.has_key('empf_unsere_lieferantennr'))

    global g_paperlist
    g_paperlist = """
Absender: (ILN %(hudora_iln)s)
HUDORA GmbH                                     Kontonummer des Vertragslieferanten: %(empf_unsere_lieferantennr)s
Jaegerwald 13
42897 Remscheid


                                                                             Nummer            Datum
Empfaenger: (ILN %(empf_iln)s)                           Sammelabrechnung   %(rechn_nr)06i            %(datum)s
%(empf_name1)s %(empf_name2)s
%(empf_strasse)s
%(empf_plz)s %(empf_ort)s

"""
    g_paperlist = g_paperlist % headerdict


def update_footer(data):
    """Fill global variable with footer information."""
    global g_footer
    if not g_footer:
        g_footer = dict(warenwert='TODO', skonto='TODO', umsatzsteuer='TODO', rechnungsendbetrag='TODO',
                        iln='', name_ort='', rechn_nr='', rechn_datum='', leergut='')
    g_footer.update(data)


def collect_invoice_info(data):
    """Aktuellen Rechnungseintrag updaten."""
    g_invoices[-1].update(data)


def add_invoice():
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
    g_invoices.append(d)


if __name__ == '__main__':
    class Rec000_mini_mock(object):
        def __init__(self):
            self.empfaenger_iln=4311501000007
            self.sender_iln='4005998000007'
            self.datenaustauschreferenz = 500
            self.erstellungsdatum = '22.02.2009'

    rec000 = Rec000_mini_mock()
    new_paperlist(rec000)
    print g_paperlist

