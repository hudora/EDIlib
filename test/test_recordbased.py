#!/usr/bin/env python
# encoding: utf-8
"""
test_recordbased.py - tests for huProtocols.recordbased

Created by Maximillian Dornseif on 2007-05-13.
Copyright (c) 2007 HUDORA GmbH. All rights reserved.
"""

import unittest
from edilib.recordbased import *
import datetime


class FieldTestsString(unittest.TestCase):
    """Test for Field and it's descendants."""
    
    def test_basic_field(self):
        """Test basic (string) field."""
        fieldinstance = Field('name', 5, 'XX', doc='Documentation!')
        self.assertEqual(fieldinstance.formated(), 'XX   ')
        self.assertEqual(len(fieldinstance.formated()), 5)
        fieldinstance.set('BBBB')
        self.assertEqual(fieldinstance.formated(), 'BBBB ')
        self.assertEqual(len(fieldinstance.formated()), 5)
        self.assertEqual(fieldinstance.get(), 'BBBB')
        
        self.assertEqual(fieldinstance.doc, 'Documentation!')
    
    def test_fixed_field(self):
        """Test fixed string field."""
        fieldinstance = FixedField('name', 1, 'Z')
        self.assertEqual(fieldinstance.formated(), 'Z')
        self.assertEqual(str(fieldinstance), 'Z')
        
        self.assertRaises(FieldImmutable, fieldinstance.set, 'A') # setting values is disallowed
        fieldinstance.set('Z') # ... except for 'correct' values
        self.assertRaises(InvalidFieldDefinition, FixedField, 'name', 2, 'Y') # length does not fit default
        self.assertRaises(InvalidFieldDefinition, FixedField, 'name', 3) # no default 
        self.assertEqual(fieldinstance.doc, None) # defaults to None
    
    def test_right_adjusted(self):
        """Test RightAdjusted (string) field."""
        fieldinstance = RightAdjustedField('name', 5, 'XX')
        self.assertEqual(len(fieldinstance.formated()), 5)
        self.assertEqual(fieldinstance.formated(), '   XX')
        fieldinstance.set('BBBB')
        self.assertEqual(fieldinstance.formated(), ' BBBB')
        self.assertEqual(len(fieldinstance.formated()), 5)
    
    def test_ean_field(self):
        """Test EAN field."""
        fieldinstance = EanField(name='name', length=17, default='4005998000007')
        self.assertEqual(fieldinstance.formated(), '4005998000007    ')
        self.assertEqual(str(fieldinstance), '4005998000007')
        self.assertRaises(SizeMismatch, fieldinstance.set, 'BBBBBBBBBBBBBBBBB')
        self.assertEqual(str(fieldinstance), '4005998000007')
        self.assertRaises(InvalidData, fieldinstance.set, '4005998000000')
        fieldinstance.set('4005998000014')
        self.assertEqual(str(fieldinstance), '4005998000014')
        fieldinstance.parse('  4005998000021  ')
        self.assertEqual(str(fieldinstance), '4005998000021')
        fieldinstance = EanField(name='name', length=13)
        fieldinstance.parse('             ')
        self.assertEqual(str(fieldinstance), '')
    

class FieldTestsNumeric(unittest.TestCase):
    """Test for Field and it's descendants."""
    
    def test_integer(self):
        """Test integer field."""
        fieldinstance = IntegerField('name', 6)
        self.assertEqual(len(fieldinstance.formated()), 6)
        self.assertEqual(fieldinstance.formated(), '      ')
        fieldinstance = IntegerField('name', 5, 50)
        self.assertEqual(len(fieldinstance.formated()), 5)
        self.assertEqual(fieldinstance.formated(), '   50')
        fieldinstance.set(60000)
        self.assertEqual(len(fieldinstance.formated()), 5)
        self.assertEqual(fieldinstance.formated(), '60000')
        fieldinstance.set(-3)
        self.assertEqual(fieldinstance.formated(), '   -3')
    
    def test_integer_zeropadded(self):
        """Test zeropadded integer field."""
        fieldinstance = IntegerFieldZeropadded('name', 10)
        fieldinstance.set(60000)
        self.assertEqual(fieldinstance.formated(), '0000060000')
    
    def test_decimal(self):
        """Test basic DecimalField functionality."""
        fieldinstance = DecimalField('name', 6)
        self.assertEqual(len(fieldinstance.formated()), 6)
        self.assertEqual(fieldinstance.formated(), '      ')
        fieldinstance = DecimalField('name', 5, 50)
        self.assertEqual(len(fieldinstance.formated()), 5)
        self.assertEqual(fieldinstance.formated(), '   50')
        fieldinstance = DecimalField('name', 5, 60.6)
        self.assertEqual(len(fieldinstance.formated()), 5)
        self.assertEqual(fieldinstance.formated(), ' 60.6')
        fieldinstance = DecimalField('name', 5, 70.0)
        self.assertEqual(len(fieldinstance.formated()), 5)
        self.assertEqual(fieldinstance.formated(), ' 70.0')
        fieldinstance = DecimalField('name', 5, '80.99')
        self.assertEqual(len(fieldinstance.formated()), 5)
        self.assertEqual(fieldinstance.formated(), '80.99')
        fieldinstance = DecimalField('name', 5, 1/3.0)
        self.assertEqual(len(fieldinstance.formated()), 5)
        self.assertEqual(fieldinstance.formated(), '0.333')
        fieldinstance.set(1/3.0)
        self.assertEqual(fieldinstance.formated(), '0.333')
        fieldinstance = DecimalField('name', 3, 1/3.0)
        self.assertEqual(len(fieldinstance.formated()), 3)
        self.assertEqual(fieldinstance.formated(), '  0')
        fieldinstance = DecimalField('name', 3, 1000)
        self.assertRaises(FieldTooLong, fieldinstance.formated)
    
    def test_decimal_precision(self):
        """Test 'precision' functionalitiy of DecimalField."""
        fieldinstance = DecimalField('name', 6, precision=1)
        self.assertEqual(len(fieldinstance.formated()), 6)
        self.assertEqual(fieldinstance.formated(), '      ')
        fieldinstance = DecimalField('name', 6, precision=3)
        self.assertEqual(len(fieldinstance.formated()), 6)
        self.assertEqual(fieldinstance.formated(), '      ')
        fieldinstance.set(1/3.0)
        self.assertEqual(fieldinstance.formated(), ' 0.333')
        fieldinstance.set(10)
        self.assertEqual(fieldinstance.formated(), '10.000')
        self.assertRaises(FieldTooLong, fieldinstance.set, 100)

    def test_decimal_no_dot(self):
        """Test basic DecimalFieldNoDot functionality."""
        fieldinstance = DecimalFieldNoDot('name', length=10, precision=3)
        self.assertEqual(len(fieldinstance.formated()), 10)
        self.assertEqual(fieldinstance.formated(), '          ')
        fieldinstance.set(50)
        self.assertEqual(fieldinstance.formated(), '     50000')
        fieldinstance.set(60.6)
        self.assertEqual(fieldinstance.formated(), '     60600')
        fieldinstance.set(1/3.0)
        self.assertEqual(fieldinstance.formated(), '      0333')
    
    def test_decimal_no_dot_padded(self):
        """Test basic DecimalFieldNoDotZeropadded functionality."""
        fieldinstance = DecimalFieldNoDotZeropadded('name', length=10, precision=3)
        self.assertEqual(len(fieldinstance.formated()), 10)
        self.assertEqual(fieldinstance.formated(), '0000000000')
        fieldinstance.set(50)
        self.assertEqual(fieldinstance.formated(), '0000050000')
        fieldinstance.set(60.6)
        self.assertEqual(fieldinstance.formated(), '0000060600')
        fieldinstance.set(1/3.0)
        self.assertEqual(fieldinstance.formated(), '0000000333')
    
    def test_decimal_parse(self):
        fieldinstance = DecimalFieldNoDotZeropadded('name', length=5, precision=2)
        fieldinstance.parse('01900')
        self.assertEqual(fieldinstance.formated(), '01900')
        self.assertEqual(fieldinstance.get(), 19)
    
    def test_decimal_signed(self):
        fieldinstance = DecimalFieldNoDotSigned('name', length=7, precision=3)
        fieldinstance.parse('018000+')
        self.assertEqual(fieldinstance.get(), 18)
        self.assertEqual(fieldinstance.formated(), '018000+')
        fieldinstance.parse('016000-')
        self.assertEqual(fieldinstance.get(), -16)
        # self.assertEqual(fieldinstance.formated(), '016000-')
        fieldinstance.parse('017000 ')
        self.assertEqual(fieldinstance.get(), 17)
    

class FieldSpecial(unittest.TestCase):
    """Test for Field and it's descendants."""
    
    def test_date(self):
        """Test date field."""        
        fieldinstance = DateField('name', 8)
        self.assertEqual(len(fieldinstance.formated()), 8)
        self.assertEqual(fieldinstance.formated(), '        ')
        fieldinstance.set(datetime.date(2007, 1, 2))
        self.assertEqual(fieldinstance.formated(), '20070102')
        self.assertEqual(len(fieldinstance.formated()), 8)
        fieldinstance.set(datetime.datetime(2007, 2, 3))
        self.assertEqual(fieldinstance.formated(), '20070203')
        self.assertEqual(len(fieldinstance.formated()), 8)
        self.assertRaises(InvalidFieldDefinition, DateField, 'name', 6)
        fieldinstance = DateField('name')
        self.assertEqual(len(fieldinstance.formated()), 8)
        
        fieldinstance = DateField('name', default=datetime.datetime(1980, 05, 04))
        self.assertEqual(fieldinstance.get_parsed('00000000'), datetime.datetime(1980, 05, 04))
        
    def test_datefieldreverse(self):
        """Test date field."""
        fieldinstance = DateFieldReverse('name', 8)
        fieldinstance.set(datetime.date(2007, 1, 2))
        self.assertEqual(fieldinstance.formated(), '02012007')
    
    def test_time(self):
        """Test time field."""
        fieldinstance = TimeField('name', 4)
        self.assertEqual(len(fieldinstance.formated()), 4)
        self.assertEqual(fieldinstance.formated(), '    ')
        fieldinstance.set(datetime.datetime(2007, 1, 2, 11, 22))
        self.assertEqual(fieldinstance.formated(), '1122')
        self.assertEqual(len(fieldinstance.formated()), 4)
        self.assertRaises(InvalidFieldDefinition, TimeField, 'name', 6)
        fieldinstance = TimeField('name')
        self.assertEqual(len(fieldinstance.formated()), 4)
    
    def test_choices(self):
        """Test choices parameter available to all field types."""
        fieldinstance = Field('name', 8, choices=['A', 'B'])
        fieldinstance.set('A')
        self.assertRaises(FieldNoValidChoice, fieldinstance.set, 'C')
        fieldinstance.set('B')
    

class FieldParseTestsStrings(unittest.TestCase):
    """Test for Field and it's descendants parsing capability."""
    
    def test_basic_field(self):
        """Test parsing basic (string) field."""
        fieldinstance = Field('name', 5, 'xX')
        
        fieldinstance.parse('  X  ')
        self.assertEqual(fieldinstance.formated(), '  X  ')
        self.assertEqual(str(fieldinstance), '  X')
        
        fieldinstance.parse(' X   ')
        self.assertEqual(fieldinstance.formated(), ' X   ')
        self.assertEqual(str(fieldinstance), ' X')
        
        fieldinstance.parse('Xxfoo')
        self.assertEqual(fieldinstance.formated(), 'Xxfoo')
        self.assertEqual(str(fieldinstance), 'Xxfoo')
        
        self.assertRaises(SizeMismatch, fieldinstance.parse, 'Xxfoox')
    
    def test_fixed_field(self):
        """Test parsing of fixed string field."""
        fieldinstance = FixedField('name', 1, 'Z')
        fieldinstance.parse('Z')
        self.assertRaises(FieldImmutable, fieldinstance.parse, 'Y')
        self.assertRaises(SizeMismatch, fieldinstance.parse, 'ZZ')
    
    def test_rightadjusted_field(self):
        """Test parsing of right adjusted string field."""
        fieldinstance = RightAdjustedField('name', 5, 'xX')
        
        fieldinstance.parse('  X  ')
        self.assertEqual(fieldinstance.formated(), '  X  ')
        self.assertEqual(str(fieldinstance), 'X  ')
        
        fieldinstance.parse(' X   ')
        self.assertEqual(fieldinstance.formated(), ' X   ')
        self.assertEqual(str(fieldinstance), 'X   ')
        
        fieldinstance.parse('Xxfoo')
        self.assertEqual(fieldinstance.formated(), 'Xxfoo')
        self.assertEqual(str(fieldinstance), 'Xxfoo')
    

class FieldParseTestsNumeric(unittest.TestCase):
    """Test for Field and it's descendants parsing capability."""
    
    def test_integer_field(self):
        """Test parsing of integer field."""
        fieldinstance = IntegerField('name', 5, 17)
        
        fieldinstance.parse('  2  ')
        self.assertEqual(fieldinstance.formated(), '    2')
        self.assertEqual(str(fieldinstance), '2')
        
        fieldinstance.parse(' 3   ')
        self.assertEqual(fieldinstance.formated(), '    3')
        self.assertEqual(str(fieldinstance), '3')
        
        fieldinstance.parse('00004')
        self.assertEqual(fieldinstance.formated(), '    4')
        self.assertEqual(str(fieldinstance), '4')
        self.assertEqual(fieldinstance.value, 4)
        
        fieldinstance.parse('   -4')
        self.assertEqual(fieldinstance.formated(), '   -4')
        self.assertEqual(str(fieldinstance), '-4')
        self.assertEqual(fieldinstance.value, -4)
        
        # test default
        fieldinstance.parse('     ')
        self.assertEqual(fieldinstance.formated(), '   17')
        self.assertEqual(str(fieldinstance), '17')
        fieldinstance = IntegerField('name', 5)
        self.assertEqual(fieldinstance.formated(), '     ')
        self.assertEqual(str(fieldinstance), '')
        
        # test errors
        self.assertRaises(SizeMismatch, fieldinstance.parse, '991234')
        self.assertRaises(SizeMismatch, fieldinstance.parse, '9912')
        self.assertRaises(SizeMismatch, fieldinstance.parse, '')
        self.assertRaises(ValueError, fieldinstance.parse, 'X-Y-Z')
        self.assertRaises(ValueError, fieldinstance.parse, 'AAAAA')
        self.assertRaises(ValueError, fieldinstance.parse, '0xfff')
        # this works through multi inherance
        self.assertRaises(InvalidData, fieldinstance.parse, '    X')
        self.assertRaises(ValueError, fieldinstance.parse, '    X')
    
    def test_integer_field_zeropadded(self):
        """Test parsing of zeropadded  integer field."""
        fieldinstance = IntegerFieldZeropadded('name', 5, 17)
        fieldinstance.parse('  2  ')
        self.assertEqual(str(fieldinstance), '2')
        fieldinstance.parse(' 3   ')
        self.assertEqual(str(fieldinstance), '3')
        fieldinstance.parse('00004')
        self.assertEqual(fieldinstance.value, 4)
    
    def test_decimal_field(self):
        """Test parsing of decimal field."""
        fieldinstance = DecimalField('name', 10)

        fieldinstance.parse('          ')
        self.assertEqual(str(fieldinstance), '')
        fieldinstance.parse(' 3        ')
        self.assertEqual(str(fieldinstance), '3')
        fieldinstance.parse('0000000004')
        self.assertEqual(fieldinstance.formated(), '         4')
        self.assertEqual(str(fieldinstance), '4')
        self.assertEqual(fieldinstance.value, 4)        
        fieldinstance.parse('        -4')
        self.assertEqual(fieldinstance.formated(), '        -4')
        self.assertEqual(str(fieldinstance), '-4')
        self.assertEqual(fieldinstance.value, -4)
        fieldinstance.parse('00000005  ')
        self.assertEqual(fieldinstance.value, 5)
        fieldinstance.parse('00000005.0')
        self.assertEqual(str(fieldinstance), '5.0')
        fieldinstance.parse('6.00000000')
        self.assertEqual(str(fieldinstance), '6.00000000')
        fieldinstance.parse('    7.000 ')
        self.assertEqual(fieldinstance.formated(), '     7.000')
        self.assertEqual(fieldinstance.value, 7)
        
    def test_decimal_field_with_prec(self):
        """Test parsing of decimal fields woth precision set."""
        fieldinstance = DecimalField('name', 10, precision=3)
        
        fieldinstance.parse(' 3        ')
        self.assertEqual(str(fieldinstance), '3')
        self.assertEqual(fieldinstance.formated(), '     3.000')
        fieldinstance.parse('0000000004')
        self.assertEqual(fieldinstance.formated(), '     4.000')
        fieldinstance.parse('        -4')
        self.assertEqual(fieldinstance.formated(), '    -4.000')
        self.assertEqual(str(fieldinstance), '-4')
        self.assertEqual(fieldinstance.value, -4)
        fieldinstance.parse('00000005  ')
        self.assertEqual(fieldinstance.value, 5)
        fieldinstance.parse('00000005.0')
        self.assertEqual(fieldinstance.formated(), '     5.000')
        fieldinstance.parse('    7.000 ')
        self.assertEqual(fieldinstance.formated(), '     7.000')
        
        self.assertRaises(InvalidData, fieldinstance.parse, '6.00000000')
    

class FieldParseTestsSpecial(unittest.TestCase):
    """Test for Field and it's descendants parsing capability."""
    
    def test_date_field(self):
        """Test parsing of date field."""
        fieldinstance = DateField('name', 8, default='20070102')
        self.assertEqual(fieldinstance.formated(), '20070102')
        
        fieldinstance.parse('20070506')
        self.assertEqual(str(fieldinstance), '2007-05-06')
        self.assertEqual(fieldinstance.value, datetime.datetime(2007, 5, 6))
        
        self.assertRaises(InvalidData, fieldinstance.parse, '88888888')
        
        fieldinstance = DateField('name', 8, default=datetime.datetime(2007, 7, 8))
        fieldinstance.parse('        ')
        self.assertEqual(str(fieldinstance), '2007-07-08')
        self.assertEqual(fieldinstance.value, datetime.datetime(2007, 7, 8))
        
    def test_date_field_reverse(self):
        """Test parsing of DateFieldReverse field."""
        fieldinstance = DateFieldReverse('name', 8)
        fieldinstance.parse('06052007')
        self.assertEqual(fieldinstance.value, datetime.datetime(2007, 5, 6))
    
    def test_time_field(self):
        """Test parsing of date field."""
        fieldinstance = TimeField('name', 4)
        self.assertEqual(fieldinstance.formated(), '    ')
        
        # I'm affraid this test is platform dependant
        fieldinstance.parse('1314')
        self.assertEqual(str(fieldinstance), '13:14')
        self.assertEqual(fieldinstance.value, datetime.datetime(1900, 1, 1, 13, 14))
        
        self.assertRaises(InvalidData, fieldinstance.parse, '2526')
        self.assertRaises(InvalidData, fieldinstance.parse, '2525')
        fieldinstance.parse('    ')
        self.assertEqual(str(fieldinstance), '')
        self.assertEqual(fieldinstance.value, '')
        self.assertEqual(fieldinstance.formated(), '    ')
        
    
class FieldDatensatzBasic(unittest.TestCase):
    """Test for records generated by generate_field_datensatz_class()"""
    
    def test_descriptors(self):
        """Test descriptor access via attributes and the ability to route arround them."""
        felder1 = [dict(name='feld1', length=3, startpos=1, endpos=4, fieldclass=Field)]
        klass = generate_field_datensatz_class(felder1, 'KlassenNameABC')
        instance1 = klass()
        self.assertTrue('feld1_field' in vars(instance1).keys())
        self.assertEqual(type(instance1.feld1), type(''))
        self.assertEqual(instance1.feld1, '')
        self.assertEqual(type(instance1.feld1_field), type(Field(name='foo')))
    
    def test_fields(self):
        felder1 = [dict(name='feld1', length=3, startpos=1, endpos=4),
                   dict(name='feld2', length=5, startpos=10, endpos=15)]
        klass = generate_field_datensatz_class(felder1, 'KlassenNameABC')
        instance1 = klass()
        instance1.feld2='X'
        self.assertEqual('X', instance1.fields()['feld2'])
        self.assertTrue('feld1' in instance1.fields().keys())
        self.assertTrue('feld2' in instance1.fields().keys())
    
    def test_basicgeneration(self):
        """Test basic functionality of generate_field_datensatz_class()."""
        felder1 = [dict(name='feld1', length=3, startpos=1, endpos=4),
                   dict(name='feld2', length=5, startpos=10, endpos=15)]
        klass = generate_field_datensatz_class(felder1, 'KlassenNameABC')
        instance1 = klass()
        self.assertEqual(instance1.feld1_field.formated(), '   ')
        self.assertEqual(instance1.feld2_field.formated(), '     ')
        self.assertTrue('KlassenNameABC' in repr(instance1))
        
        # ensure that different classed don't mix attributes
        felder2 = [dict(name='felda', length=3, startpos=1, endpos=4),
                   dict(name='feldb', length=5, startpos=10, endpos=15)]
        klass2 = generate_field_datensatz_class(felder2)
        instance2 = klass2()
        self.assertEqual(instance2.felda_field.formated(), '   ')
        self.assertEqual(instance2.feldb_field.formated(), '     ')
        self.assertRaises(AttributeError, getattr, instance2, 'feld1')
    
    def test_instances_dont_mix(self):
        """Test that changes in instance A do not influence instance B."""
        felder1 = [dict(name='feld1', length=3, startpos=1, endpos=4)]
        klass = generate_field_datensatz_class(felder1, 'KlassenNameABC')
        instance1 = klass()
        instance2 = klass()
        instance1.feld1 = 'foo'
        instance2.feld1 = 'bar'
        self.assertEqual(instance1.feld1, 'foo')
    
    def test_lengthfehler(self):
        """Test that generate_field_datensatz_class() catches inconsitent field length information."""
        felder1 = [dict(name='feld1', length=1, startpos=0, endpos=0)]
        self.assertRaises(InvalidFieldDefinition, generate_field_datensatz_class, felder1)
        felder1 = [dict(name='feld1', length=1, startpos=0, endpos=2)]
        self.assertRaises(InvalidFieldDefinition, generate_field_datensatz_class, felder1)
        felder1 = [dict(name='feld1', length=1, startpos=0, endpos=1)]
        generate_field_datensatz_class(felder1)
    
    def test_ueberschneidung(self):
        """Test generate_field_datensatz_class() catches overlapping fields."""
        felder1 = [dict(name='feld1', length=3, startpos=1, endpos=4),
                   dict(name='feld2', length=3, startpos=2, endpos=5)]
        self.assertRaises(InvalidFieldDefinition, generate_field_datensatz_class, felder1)
    
    def test_doc(self):
        """Test generate_field_datensatz_class() writing __doc__"""
        felder = [dict(name='felda', length=3, startpos=1, endpos=4),
                   dict(name='feldb', length=5, startpos=10, endpos=15)]
        klass = generate_field_datensatz_class(felder, doc="Urzeit war's da Ümir hausste ...")
        self.assertEqual(klass.__doc__, "Urzeit war's da Ümir hausste ...")
    
    def test_assignment(self):
        """Test assignments work for fields."""
        felder = [dict(name='belegnummer', length=35, startpos=0, endpos=35, fieldclass=RightAdjustedField),
                  dict(name='kunden_iln', length=17, startpos=35, endpos=52)]
        klass = generate_field_datensatz_class(felder, name='test23')
        instance = klass()
        self.assertEqual(instance.belegnummer, '')
        self.assertEqual(instance.belegnummer_field.formated(), '                                   ')
        self.assertEqual(instance.kunden_iln_field.formated(), '                 ')
        self.assertEqual(len(instance.serialize()), 35+17)
        self.assertEqual(instance.serialize(), '                                                    ')
        instance.belegnummer = '123'
        self.assertEqual(len(instance.serialize()), 35+17)
        self.assertEqual(instance.serialize(), '                                123                 ')
        instance.kunden_iln = '9999999999999'
        self.assertEqual(len(instance.serialize()), 35+17)
        self.assertEqual(instance.serialize(), '                                1239999999999999    ')
    

class FieldDatensatzParseAndBack(unittest.TestCase):
    """Test for records generated by generate_field_datensatz_class()"""
    
    def test_length(self):
        """Test generated records are padded automatically."""
        felder = [dict(name='belegnummer', length=35, startpos=0, endpos=35),
                  dict(name='kunden_iln', length=17, startpos=35, endpos=52)]
        klass = generate_field_datensatz_class(felder, name='test23', length=512)
        instance = klass()
        self.assertEqual(len(instance.serialize()), 512)
    
    def test_serialize(self):
        """Test that generated records can serialize() themselfs."""
        felder = [
            dict(length=4, startpos=0, endpos=4, name='position'),
            dict(length=15, startpos=4, endpos=19, name='artikelnummer', fieldclass=RightAdjustedField),
            dict(length=15, startpos=19, endpos=34, name='menge', fieldclass=DecimalField, precision=3),
            dict(length=8, startpos=34, endpos=42, name='date', fieldclass=DateField),
            dict(length=4, startpos=42, endpos=46, name='time', fieldclass=TimeField),
            dict(length=8, startpos=46, endpos=54, name='date2', fieldclass=DateFieldReverse),
            dict(length=1, startpos=54, endpos=55, name='fixed', fieldclass=FixedField, default='#'),
            dict(length=8, startpos=55, endpos=63, name='int1', fieldclass=IntegerField),
            dict(length=8, startpos=63, endpos=71, name='int2', fieldclass=IntegerFieldZeropadded),
            ]
        klass = generate_field_datensatz_class(felder, name='test12', length=71)
        instance = klass()
        instance.position = 9999
        instance.artikelnummer = '14650/42z'
        instance.menge = 111111
        instance.int1 = 2222222
        instance.int2 = 33333
        instance.date = datetime.datetime(2006, 5, 6)
        instance.date2 = datetime.datetime(2006, 7, 8)
        instance.time = datetime.datetime(2000, 1, 1, 22, 33)
        self.assertEqual(len(instance.serialize()), 71)
        self.assertEqual(instance.serialize(),
                         '9999      14650/42z     111111.00020060506223308072006# 222222200033333')
    
    def test_parse(self):
        """Test parsing of serialized records."""
        felder = [
            dict(length=4, startpos=0, endpos=4, name='position'),
            dict(length=15, startpos=4, endpos=19, name='artikelnummer', fieldclass=RightAdjustedField),
            dict(length=15, startpos=19, endpos=34, name='menge', fieldclass=DecimalField, precision=3),
            dict(length=8, startpos=34, endpos=42, name='date', fieldclass=DateField),
            dict(length=4, startpos=42, endpos=46, name='time', fieldclass=TimeField),
            dict(length=8, startpos=46, endpos=54, name='date2', fieldclass=DateFieldReverse),
            dict(length=1, startpos=54, endpos=55, name='fixed', fieldclass=FixedField, default='#'),
            dict(length=8, startpos=55, endpos=63, name='int1', fieldclass=IntegerField),
            dict(length=8, startpos=63, endpos=71, name='int2', fieldclass=IntegerFieldZeropadded),
            ]
        klass = generate_field_datensatz_class(felder, name='test12', length=71)
        instance = klass()
        instance.parse('9999      14650/42z     111111.00020060506223308072006# 222222200033333')
        self.assertEqual(instance.position, '9999')
        self.assertEqual(instance.artikelnummer, '14650/42z')
        self.assertEqual(instance.menge, 111111)
        self.assertEqual(instance.date, datetime.datetime(2006, 5, 6))
        self.assertEqual(instance.date2, datetime.datetime(2006, 7, 8))
        self.assertEqual(instance.fixed, '#')
        self.assertEqual(instance.int1, 2222222)
        self.assertEqual(instance.int2, 33333)


if __name__ == '__main__':
    unittest.main()
