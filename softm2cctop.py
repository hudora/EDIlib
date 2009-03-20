#!/usr/bin/env python
# encoding: utf-8
"""
softm2cctop convert SoftM INVOICE to StratEDI INVOICE records.

Created by Maximillian Dornseif on 2008-10-31.
Copyright (c) 2008 HUDORA. All rights reserved.
"""

import os
import os.path
import sys
import copy
import pprint
from decimal import Decimal

# From http://superjared.com/entry/django-and-crontab-best-friends/
from django.core.management import setup_environ
import settings
setup_environ(settings)

#from django.db import transaction


from huTools.fs import makedirhier

from benedict.models import SoftMTransmission

from edilib.cctop.invoic import interchangeheader000, transaktionskopf100, transaktionsreferenz111
from edilib.cctop.invoic import addressen119, zahlungsbedingungen120, rechnungsposition500, zusatzkosten140
from edilib.cctop.invoic import belegsummen900, belegabschlaege913, rechnungsliste990
from edilib.softm import parse_to_objects

from benedict.models import log_action, ADDITION, CHANGE

import paperlist


# globals
g_is_credit = False
g_invoices = []
g_is_invoicelist = None
g_iln_rechnungsempfaenger = None
EDEKA_ILNS = ['4311501000007'] # TODO automaticly generation of this list ???


def _is_edeka():
    global g_iln_rechnungsempfaenger
    return g_iln_rechnungsempfaenger in EDEKA_ILNS


def _is_credit():
    global g_is_credit
    return g_is_credit

def convert_interchangehead(transmission_records, previous_output_records, sequence_no, config):
    """Converts a SoftM XH record to an StratEDI 000 record.

    sequence_no is a counter for each transmission"""

    xh = transmission_records['XH']
    rec000 = interchangeheader000()
    rec000.sender_iln = config['operatoriln']
    rec000.empfaenger_iln = xh.dfue_partner
    rec000.erstellungsdatum = xh.erstellungs_datum
    rec000.erstellungszeit = xh.erstellungs_zeit[:4] # remove seconds
    # Fortlaufende achtstellige Sendenummer
    rec000.datenaustauschreferenz = sequence_no
    # rec000.referenznummer = xh.dateiname
    rec000.anwendungsreferenz = xh.umgebung
    rec000.testkennzeichen = xh.testkennzeichen

    global g_iln_rechnungsempfaenger
    g_iln_rechnungsempfaenger = rec000.empfaenger_iln
    paperlist.update_header(rec000) #dict(hudora_iln=rec000.sender_iln, empf_iln=''))
    return [rec000]


def convert_transmissionhead(invoice_records, previous_output_records, sequence_no, config):
    """Converts SoftM F1 & F2 to StratEDI 100, 111, 119.BY, 119.SU, 119.DP, 119.IV & 120 records."""

    f1 = invoice_records['F1']
    f2 = invoice_records['F2']
    f3 = invoice_records['F3']
    r1 = invoice_records['R1']

    rec100 = transaktionskopf100()
    rec111 = transaktionsreferenz111()
    rec119_lieferaddr = addressen119()
    rec119_rechnungsaddr = addressen119()
    rec119_verkaeuferaddr = addressen119()
    rec119_kaeuferaddr = addressen119()
    rec120 = zahlungsbedingungen120()
    rec140 = zusatzkosten140()

    # Eindeutige Nachrichtenreferenz des Absenders; laufende Nummer der Nachrichten im Datenaustausch
    # beginnt mit "1" und wird für jede Rechnung/Gutschrift innerhalb einer Übertragungsdatei
    # um 1 erhöht.
    rec100.referenz = sequence_no

    global g_invoices
    rechnr = str(f1.rechnungsnr)
    g_invoices.append(rechnr)
    print "Rechnungsnummer: ", rechnr,

    rec100.belegnr = f1.rechnungsnr
    rec100.belegdatum = f1.rechnungsdatum

    paperlist.collect_invoice_info(dict(rechn_nr=rec100.belegnr, rechn_datum=str(rec100.belegdatum)[:10]))

    # Gutschrift oder Rechnung?
    print "\tBELEGART: ", f1.belegart # 380 (Rechnung), 381 (Gutschrift),  83 (Wertgutschrift) oder 84 (Wertbelastung)
    # print "Skontobetrag: ", f1.skontobetrag1_ust1
    #print "USt fuer Skonto1:", f1.ust1_fuer_skonto
    #print "USt fuer Skonto2:", f1.ust2_fuer_skonto
    #print "Skonto%:", f1.skonto1

    rec100.transaktionsart = f1.belegart.lstrip('0')
    global g_is_credit
    if rec100.transaktionsart in ['380', '84']:
        g_is_credit = False
    elif rec100.transaktionsart in ['381', '83']:
        g_is_credit = True
        paperlist.comment('Gutschrift')
    else:
        raise RuntimeError("Belegart %s unbekannt" % f1.belegart)


    rec111.auftragsnr = f1.auftragsnr
    rec111.auftragsdatum = f1.auftragsdatum
    rec111.lieferdatum = f1.liefertermin
    rec111.lieferscheinnr = f1.lieferscheinnr
    rec111.lieferscheindatum = f1.lieferscheindatum
    rec111.rechnungslistennr = f1.rechnungsliste
    rec111.rechnungslistendatum = f1.rechnungslistendatum

    # Specific for EDEKA - TODO: make less specific.
    rec111.abkommensnr = '20'

    # Lieferant
    rec119_verkaeuferaddr.partnerart = 'SU'
    rec119_verkaeuferaddr.iln = f1.eigene_iln_beim_kunden
    # TODO: was ist der Unterschied zwischen ustdid und steuernr?
    rec119_verkaeuferaddr.ustdid = f1.ustdid_absender
    rec119_verkaeuferaddr.steuernr = f1.steuernummer
    rec119_verkaeuferaddr.weeenr = config['operatorweeenr']
    rec119_verkaeuferaddr.tel = config['operatortel']
    rec119_verkaeuferaddr.fax = config['operatorfax']

    try:
        # R1 entries are related to invoice lists (Vorsicht gef. Halbwissen!). So if this is a
        # single invoice, we have to handle this here
        rec119_verkaeuferaddr.gegebenepartnerid = invoice_records['R1'].lieferantennr_verband
    except:
        pass

    # Warenempfänger
    rec119_lieferaddr.partnerart = 'DP'
    rec119_lieferaddr.iln = f2.iln_warenempfaenger
    rec119_lieferaddr.name1 = f2.liefer_name1
    rec119_lieferaddr.name2 = f2.liefer_name2
    rec119_lieferaddr.name3 = f2.liefer_name3
    rec119_lieferaddr.strasse1 = f2.liefer_strasse
    rec119_lieferaddr.plz = f2.liefer_plz
    rec119_lieferaddr.ort = f2.liefer_ort
    rec119_lieferaddr.land = f2.liefer_land
    rec119_lieferaddr.internepartnerid = f2.warenempfaenger

    paperlist.collect_invoice_info(dict(name_ort=rec119_lieferaddr.name1+', '+rec119_lieferaddr.ort,
        iln=rec119_lieferaddr.iln))

    # Kaeufer
    rec119_kaeuferaddr.partnerart = 'BY'
    if f2.besteller_iln:
        rec119_kaeuferaddr.iln = f2.besteller_iln
    else:
        rec119_kaeuferaddr.iln = f2.iln_warenempfaenger
        # rec119_kaeuferaddr.iln = g_iln_rechnungsempfaenger

    # Rechnungsempfänfger
    rec119_rechnungsaddr.partnerart = 'IV'
    rec119_rechnungsaddr.iln = f1.iln_rechnungsempfaenger
    rec119_rechnungsaddr.internepartnerid = f1.rechnungsempfaenger
    rec119_rechnungsaddr.gegebenepartnerid = f1.lieferantennummer
    rec119_rechnungsaddr.ustdid = f1.ustdid_rechnungsempfaenger
    # rec119_rechnungsaddr.partnerabteilung

    rec120.mwstsatz = f3.mwstsatz # dies ist ein Zufälliger Rechnungspositionssatz
    rec120.waehrung = f1.waehrung

    rec140.mwstsatz = f1.ust1_fuer_skonto
    rec140.skontoprozent = f1.skonto1
    rec140.skontobetrag = abs(f1.skontobetrag1_ust1)
    # rec140.frachtbetrag = f1.xxx
    # rec140.verpackungsbetrag = f1.xxx
    # rec140.versicherungsbetrag = f1.xxx
    rec140.skontotage = f1.skontotage1
    rec140.skontodatum = f1.skontodatum1

    paperlist.collect_invoice_info(dict(skonto=rec140.skontobetrag))

    # pprint.pprint(f1.__dict__)
    # Nicht genutzte Felder aus SoftM
    # f1.
    # f1.ust1_fuer_skonto', fieldclass=DecimalFieldNoDot, precision=2),
    # f1.ust2_fuer_skonto', fieldclass=DecimalFieldNoDot, precision=2),
    # f1.'Skontofähig USt 1'),
    # f1.'Skontofähig USt 2'),
    # f1.Skontodatum 1'),
    # f1.Skontotage 1'),
    # f1.Skonto 1'),
    # f1.'Skontobetrag 1 USt 1'),
    # f1.'Skontobetrag 1 USt 2'),
    # f1.Skontodatum 2'),
    # f1.Skontotage 2'),
    # f1.Skonto 2'),
    # f1.'Skontobetrag 2 USt 1'),
    # f1.'Skontobetrag 2 USt 2'),
    # f1.='Nettodatum'),
    # f1.valutatage', fieldclass=IntegerField),
    # f1.='valutadatum', fieldclass=DateField),
    # f1.Firma'), # , fieldclass='FixedField', default='01'),
    # f1.Abteilung'),
    # f1.'Bibliothek'),
    # f1.nettotage'),
    # f1.e='iln_besteller', fieldclass=EanField),
    # f1.e='Reserve', fieldclass=FixedField, default=' ' *18),
    # f1.Status', fieldclass=FixedField, default=' '),
    # f2.'Lagerbezeichnung'),
    # f2.versandart'),
    # f2.lieferbedingung'),
    # f2.verband', fieldclass=IntegerField),
    # f2.verband_iln', fieldclass=EanField),

    return [rec100, rec111,
            rec119_lieferaddr, rec119_rechnungsaddr, rec119_kaeuferaddr, rec119_verkaeuferaddr,
            rec120, rec140]


last_mwst = None


def convert_invoice_position(position_records, previous_output_records):
    """Converts SoftM F3 records to StratEDI 500 records."""

    global last_mwst
    f3 = position_records['F3']
    f4 = position_records['F4']

    rec500 = rechnungsposition500()
    rec500.positionsnummer = f3.positionsnr
    rec500.berechnete_menge = f3.menge
    rec500.ean = f3.ean
    rec500.artnr_lieferant = f3.artnr
    rec500.artnr_kunde = f3.artnr_kunde
    rec500.artikelbezeichnung1 = f3.artikelbezeichnung[:35]
    rec500.artikelbezeichnung2 = f3.artikelbezeichnung[35:70]
    rec500.mwstsatz = f3.mwstsatz
    if last_mwst and (last_mwst != f3.mwstsatz):
        raise RuntimeError("Wechsel im Steuersatz zwischen Auftragspositionen: %s | %s" %
                           (last_mwst, f3.mwstsatz))
    last_mwst = f3.mwstsatz

    # MOA-5004 Bruttowarenwert = Menge x Bruttopreis ohne MWSt., vor Abzug der Artikelrabatte
    rec500.bruttostueckpreis = abs(f3.verkaufspreis)
    rec500.bruttowarenwert = abs(f3.wert_brutto)

    # MOA-5004 Nettowarenwert = Menge x Bruttopreis ./. Artikelrabatte bzw. Menge x Nettopreis
    # (Rabatte sind im Preis eingerechnet)
    # Bei Gutschriftspositionen ist der Nettowarenwert negativ einzustellen.
    rec500.nettostueckpreis = abs(f3.verkaufspreis)
    rec500.nettowarenwert = abs(f3.wert_netto)

    # pruefen ob netto = menge x brutto ./. Artikelrabatt
    dbg_nettoval = rec500.nettostueckpreis * rec500.berechnete_menge - f4.positionsrabatt_gesamt
    if  dbg_nettoval != rec500.nettowarenwert:
        if not (dbg_nettoval == abs(rec500.nettowarenwert) and _is_credit()):
            import ipdb; ipdb.set_trace()
            raise RuntimeError("Netto-Warenwert unschlüssig: %r * %r != %r" %
                    (rec500.nettostueckpreis, rec500.berechnete_menge, rec500.nettowarenwert))

    if rec500.bruttostueckpreis * rec500.berechnete_menge != rec500.bruttowarenwert:
        if not (abs(rec500.bruttostueckpreis * rec500.berechnete_menge) == abs(rec500.bruttowarenwert)
                and _is_credit()):
            raise RuntimeError("Brutto-Warenwert unschlüssig: %r * %r != %r" % (rec500.bruttostueckpreis,
                               rec500.berechnete_menge, rec500.bruttowarenwert))

    # MOA-5004 Summe aller Zu- und Abschläge aus Satzart(en) 513 mit vorzeichengerechter Darstellung
    # rec500.summeabschlaege

    return ([rec500], rec500.nettowarenwert, rec500.bruttowarenwert)


def convert_invoice_footer(invoice_records, previous_output_records, nettosum, bruttosum):
    """Converts SoftM F9 record to StratEDI 900 and optionally 913 records."""

    rec900 = belegsummen900()
    rec913 = belegabschlaege913()
    f9 = invoice_records['F9']
    f1 = invoice_records['F1']

    if nettosum != f9.warenwert:
        if not (abs(nettosum) == abs(f9.warenwert) and _is_credit()):
            raise RuntimeError("Netto-Summe unschlüssig: %r != %r" % (nettosum, f9.warenwert))

    # FIXME das fliegt bei einigen Gutschriften raus. Macht es denn ueberhaupt sinn, dass die
    # bruttosumme gleich dem *Netto*warenwert ist? Bisher flog das nur nicht raus, weil netto meist
    # gleich brutto ist, dh. keine Positionsrabatte abgezogen wurden
    #if bruttosum != f9.nettowarenwert1:
    #    if not (abs(bruttosum) == abs(f9.nettowarenwert1) and _is_credit()):
    #        raise RuntimeError("Brutto-Summe unschlüssig: %r != %r" % (bruttosum, f9.nettowarenwert1))

    sum_kopfrabatte = f9.kopfrabatt1 + f9.kopfrabatt2
    if f9.summe_rabatte != sum_kopfrabatte:
        if not (abs(f9.summe_rabatte) == abs(sum_kopfrabatte) and _is_credit()):
            raise RuntimeError("Rabatte unschlüssig: %r != %r" % (f9.summe_rabatte, sum_kopfrabatte))

    rec900.nettowarenwert_gesamt = abs(f9.warenwert)
    #print "rec900.nettowarenwert_gesamt", rec900.nettowarenwert_gesamt
    rec900.steuerpflichtiger_betrag = abs(f9.steuerpflichtig1)
    #print "rec900.steuerpflichtiger_betrag", rec900.steuerpflichtiger_betrag
    rec900.rechnungsendbetrag = abs(f9.gesamtbetrag)
    #print "rec900.rechnungsendbetrag", rec900.rechnungsendbetrag
    rec900.mwst_gesamtbetrag = abs(f9.mehrwertsteuer)
    #print "rec900.mwst_gesamtbetrag", rec900.mwst_gesamtbetrag
    rec900.skontofaehiger_betrag = abs(f9.skontofaehig)
    #print "rec900.skontofaehiger_betrag", rec900.skontofaehiger_betrag
    # Ist das nur Zuschlaege oder Zuschlaege + Rabatte?
    #print "Rabatt=8.50 2%", f9.kopfrabatt1, f9.kopfrabatt1_prozent
    #print "gesamtrabatt=8.49", f9.summe_rabatte
    # Dies ist "Vorzeichenbehaftet" - siehe http://cybernetics.hudora.biz/intern/fogbugz/default.php?4554

    # rec900.zu_und_abschlage = -1 * f9.summe_rabatte

    if _is_edeka():
        # Skonto wird fuer Edeka als Rabatt eingetragen
        skonto = -f1.skontobetrag1_ust1
        rec900.zu_und_abschlage = skonto
        rec900.steuerpflichtiger_betrag = rec900.nettowarenwert_gesamt + skonto
        rec900.mwst_gesamtbetrag = rec900.steuerpflichtiger_betrag * last_mwst / Decimal('100.0')
        rec900.rechnungsendbetrag = rec900.steuerpflichtiger_betrag + rec900.mwst_gesamtbetrag
        pass
    else:
        # Zuschlaegen getreu ihrer Vorzeichen
        rec900.zu_und_abschlage = f9.summe_rabatte + f9.summe_zuschlaege

    # Vorzeichen muss noch eingearbeitet werden.
    # f9.Vorzeichen Summe Zuschläge'),
    # rec900.gesamt_verkaufswert

    rec913.abschlag_prozent = f9.kopfrabatt1_prozent
    rec913.abschlag = f9.kopfrabatt1

    paperlist.collect_invoice_info(dict(warenwert=rec900.nettowarenwert_gesamt,
        rechnungsendbetrag=rec900.rechnungsendbetrag, umsatzsteuer=rec900.mwst_gesamtbetrag))

    if f9.kopfrabatt1 > 0:
        return [rec900, rec913]
    return [rec900]


def convert_invoice(softm_record_list, stratedi_records, config):
    """Handles a SoftM invoce."""

    softm_records = dict(softm_record_list)
    ret = []

    sequence = iter(xrange(len(softm_record_list)))

    ret.extend(convert_transmissionhead(softm_records, stratedi_records, sequence.next(), config))

    # the now we have to extract the per invoice records from softm_record_list
    # every position starts with a F3 record
    tmp_softm_record_list = copy.deepcopy(softm_record_list)

    # Skonto aus allen f1 eintraegen ermitteln
    f1list = [x[1] for x in softm_record_list if x[0] == 'F1']
    if f1list:
        skonto = sum([rec.skontobetrag1_ust1 for rec in f1list])
        paperlist.update_footer(dict(skonto=skonto))

    # remove everything until we hit the first F3
    while tmp_softm_record_list and tmp_softm_record_list[0] and tmp_softm_record_list[0][0] != 'F3':
        tmp_softm_record_list.pop(0)

    nettosum = 0
    bruttosum = 0
    while tmp_softm_record_list:
        # slice of segment untill the next F3
        position = [tmp_softm_record_list.pop(0)]
        while tmp_softm_record_list and tmp_softm_record_list[0] and tmp_softm_record_list[0][0] != 'F3':
            position.append(tmp_softm_record_list.pop(0))

        # process position
        records, netto, brutto = convert_invoice_position(dict(position), stratedi_records)
        # print("netto: %f \t brutto: %f" % (netto, brutto)),
        ret.extend(records)
        nettosum += netto
        bruttosum += brutto
        # print("nettosum: %f \t bruttosum: %f" % (nettosum, bruttosum))


    ret.extend(convert_invoice_footer(softm_records, stratedi_records, nettosum, bruttosum))
    return ret

    # TODO: FK satz?


def convert_invoicelist(softm_record_list, stratedi_records, config):
    """Handles the invoices of an SoftM invoice list."""

    ret = []
    softm_records = dict(softm_record_list)
    # the now we have to extract the per invoice records from softm_record_list
    # every position starts with a F1 record
    tmp_softm_record_list = copy.deepcopy(softm_record_list)

    # remove everything until we hit the first F1
    while tmp_softm_record_list and tmp_softm_record_list[0] and tmp_softm_record_list[0][0] != 'F1':
        tmp_softm_record_list.pop(0)

    while tmp_softm_record_list:
        # slice of segment untill the next F1
        invoice = [tmp_softm_record_list.pop(0)]
        while tmp_softm_record_list and tmp_softm_record_list[0] and tmp_softm_record_list[0][0] != 'F1':
            invoice.append(tmp_softm_record_list.pop(0))

        # always also send the R1 records to the invoice processor
        invoice.append(('R1', softm_records.get('R1',''), )) # FIXME: R1 sind glaube ich Rechnungslisten -> was machen bei Einzelrechnungen?

        # tell paperlist module to create a new invoice entry
        paperlist.add_invoice()

        # process invoice
        ret.extend(convert_invoice(invoice, stratedi_records, config))

    return ret


def convert_invoicelistfooter(softm_record_list, stratedi_records, config):
    """Converts SoftM R1, R2 & R3 records to a StratEDI 990 record."""

    softm_record_dict = dict(softm_record_list)
    r1 = softm_record_dict.get('R1', None)
    r3 = softm_record_dict.get('R3', None)

    r2list = [x[1] for x in softm_record_list if x[0] == 'R2']

    #990-15: MwSt-Betrag der Rechnungsliste: fehlt
    #990-17: Stpfl. Betrag der Rechnungsliste: fehlt
    rec990 = rechnungsliste990()

    if r2list:
        rec990.rechnungslistennr = r2list[-1].listennr
        rec990.rechnungslistendatum = r2list[-1].listendatum

    rec990.hudora_iln2 = rec990.hudora_iln = config['operatoriln']

    if r1:
        rec990.empfaenger_iln = r1.verband_iln
        rec990.lieferantennr = r1.lieferantennr_verband

    # rec990.zahlungsleistender_iln
    # rec990.valutadatum
    if r3:
        rec990.rechnungslistenendbetrag = r3.summe
    # rec990.nettowarenwert = r3.summe

    rec990.mwst = sum([rec.mwst for rec in r2list])
    rec990.steuerpflichtiger_betrag = sum([rec.warenwert for rec in r2list])

    # EDEKA specific
    rec990.abkommen = '20'

    # Footer information for paperlist
    paperlist.update_footer(dict(warenwert=abs(rec990.steuerpflichtiger_betrag),
                          umsatzsteuer=abs(rec990.mwst),
                          rechnungsendbetrag=abs(rec990.rechnungslistenendbetrag)))

    return [rec990]


def convert(softm_record_list, transmissionid, additionalconfig={}):
    """Convert a SoftM Transmission to StratEDI Format.

    Expexts a list of records already parsed by husoftm.dateexportschnittstelle."""

    config = dict(operatoriln='4005998000007',
                  operatorweeenr='DE 70323035',
                  operatorfax='+49 2191 60912-50',
                  operatortel='+49 2191 60912-0',
                  transmissionid=str(transmissionid))

    config.update(additionalconfig)

    stratedi_records = []
    softm_records = dict(softm_record_list)

    sequence = iter(xrange(len(softm_record_list)))

    stratedi_records.extend(convert_interchangehead(softm_records, stratedi_records, sequence.next(), config))
    stratedi_records.extend(convert_invoicelist(softm_record_list, stratedi_records, config))
    if g_is_invoicelist:
        stratedi_records.extend(convert_invoicelistfooter(softm_record_list, stratedi_records, config))
    return stratedi_records


def softm2cctop(infile, outfile, transmission):
    import codecs
    softm_record_list = parse_to_objects(codecs.open(infile, 'r', 'cp850'))
    out = '\r\n'.join([record.serialize() for record in convert(softm_record_list, transmission.guid)])
    codecs.open(outfile, 'w', 'iso-8859-1').write(out + '\r\n')


def main():
    """Main function to be called by cron."""
    inputdir = "/usr/local/edi/transfer/softm/pull/new"
    workdir = "/usr/local/edi/transfer/softm/pull/tmp"
    outputdir = "/usr/local/edi/transfer/stratedi/push/new"

    makedirhier(workdir)

   #logging.basicConfig(level=logging.DEBUG,
   #                    format='%(asctime)s %(levelname)s %(message)s',
   #                    filename=os.path.join(workdir, 'INVOIC_Log.txt'),
   #                    filemode='a+')
   #
   #logging.debug("Verarbeite %r nach %r. Logs in %r" % (inputdir, outputdir, workdir))

    # Process all files in a directory
    # fname = 'RL00513.TXT'
    # for count, filename in enumerate([os.path.join(inputdir, fname)]): #enumerate(os.listdir(inputdir)):
    transmissions = SoftMTransmission.objects.all()
    for count, transmission in enumerate(transmissions.iterator()):
        filename = transmission.filename
        # skip weird invoice. TODO to check w/ cgiermann:
        if filename.upper() in ['RL00614_UPDATED.txt'.upper(),
                                'RL00602_UPDATED.txt'.upper()]:
            continue
        # if filename.upper() != 'RL00603_UPDATED.txt'.upper(): # sent to stratedi 19.03.2009
            # continue
        #if filename.upper() != 'RL00513.TXT': # dbg
            #continue
        # if filename.upper() != 'RL00430.TXT': # diese hier ging an stratedi
            # continue
        global g_is_invoicelist
        g_is_invoicelist = None
        if filename.upper().startswith('RG'):
            g_is_invoicelist = False
        elif filename.upper().startswith('RL'):
            g_is_invoicelist = True
            continue
        assert(g_is_invoicelist!=None)

        print
        print count, filename
        if filename.lower().endswith('.txt'):
            msg = "softm2cctop: "
            try:
                global g_invoices
                g_invoices = []
                workfilename = os.path.join(workdir, filename)
                paperlist.new_paperlist(workfilename.lower().replace('txt', 'paper')) # TODO nice extension
                softm2cctop(os.path.join(inputdir, filename), workfilename, transmission)
            except:
                # import ipdb; ipdb.set_trace()
                (klass, error_obj, tback) = sys.exc_info()
                msg += "failed w/ msg: %s" % error_obj.message
                transmission.status = 'parsing_failed'
                paperlist.invalidate()
                if not '--tryall' in sys.argv:
                    raise
            else:
                transmission.status = 'ok'
                msg += "passed"
            finally:
                paperlist.finish_paperlist(not g_is_invoicelist)
                transmission.references_invoices = '\n'.join(g_invoices)
                transmission.save()
                log_action(transmission, CHANGE, message=msg)

    #tweet = "%d INVOIC Dateien nach cctop konvertiert" % count
    #TwitHTTP('edi', 'edi').sendTwitter(tweet)

if __name__ == '__main__':
    main()

