"""
Tests for GSpreadsheet

Currently, requires email and password to exist in the environment. Tests also
connect to a live spreadsheet whose contents cannot be guaranteed. So take the
results of these tests with a grain of salt.

"""
try:
    # python2.6 compatibility
    from unittest2 import TestCase, skipIf
except ImportError:
    from unittest import TestCase, skipIf
import os

from .gspreadsheet import GSpreadsheet, ReadOnlyException
from .auth import Auth

KEY = "0AvtWFMTdBQSLdFI3Y2M0RnI5OTBMa2FydXNFelBDTUE"
WORKSHEET = 'od6'
TEST_URL = "https://docs.google.com/spreadsheet/ccc?key=%s#gid=0" % KEY
WRITABLE_TEST_URL = "https://docs.google.com/spreadsheet/ccc?key=%s#gid=1" % KEY


class GSpreadsheetTest(TestCase):
    def test_to_JSON(self):
        sheet = GSpreadsheet(TEST_URL)
        # pretty lame, I know, but it's a start
        self.assertTrue(sheet.to_JSON())


class BasicAuthTests(TestCase):
    def test_can_connect_and_reuse_client(self):
        sheet = GSpreadsheet(TEST_URL)
        self.assertTrue(sheet)
        client = sheet.client
        sheet = GSpreadsheet(TEST_URL, client=client)
        self.assertTrue(sheet)
        # TODO assert only one auth was made


class Basics(TestCase):
    def test_can_connect_and_iterate_using_url(self):
        sheet = GSpreadsheet(TEST_URL)
        self.assertEqual(sheet.worksheet, WORKSHEET)
        names = ['A', 'B']
        for i, row in enumerate(sheet):
            self.assertEqual(row['name'], names[i])

        # test_can_get_length_of_sheet
        self.assertEqual(len(sheet), i + 1)

    def test_can_connect_and_iterate_using_url_no_gid(self):
        sheet = GSpreadsheet(TEST_URL.split("#")[0])
        self.assertEqual(sheet.worksheet, 'default')
        names = ['A', 'B']
        for i, row in enumerate(sheet):
            self.assertEqual(row['name'], names[i])

    def test_can_connect_and_iterate_using_key(self):
        sheet = GSpreadsheet(key=KEY)
        self.assertEqual(sheet.worksheet, 'default')
        names = ['A', 'B']
        for i, row in enumerate(sheet):
            self.assertEqual(row['name'], names[i])

    def test_can_connect_and_iterate_using_key_and_worksheet(self):
        sheet = GSpreadsheet(key=KEY, worksheet=WORKSHEET)
        self.assertEqual(sheet.worksheet, WORKSHEET)
        names = ['A', 'B']
        for i, row in enumerate(sheet):
            self.assertEqual(row['name'], names[i])

    def test_can_connect_and_manually_iterate(self):
        sheet = GSpreadsheet(TEST_URL)
        row = sheet.next()
        self.assertEqual(row['name'], 'A')
        row = sheet.next()
        self.assertEqual(row['name'], 'B')

        # continue in the same test to avoid making a new connection :(

        # test_fieldnames_exist_and_are_accurate(self):
        # assertListEqual requires python>=2.7
        self.assertListEqual(sorted(sheet.fieldnames),
            sorted(['name', 'widgets', 'date', 'price']))

        # test_can_mark_row_as_readonly(self):
        sheet.readonly = True
        with self.assertRaises(ReadOnlyException):
            row['name'] = 'C'

        with self.assertRaises(ReadOnlyException):
            row.save()

        with self.assertRaises(ReadOnlyException):
            row.delete()

        # test_copy_of_row_is_dict(self):
        from copy import copy
        self.assertEqual(type(copy(row)), dict)
        self.assertEqual(type(row.copy()), dict)


@skipIf('GOOGLE_ACCOUNT_EMAIL' not in os.environ or
        'GOOGLE_ACCOUNT_PASSWORD' not in os.environ,
        'These tests require being logged in')
class LoggedInTests(TestCase):
    def test_can_use_client_created_from_auth(self):
        client = Auth()
        sheet = GSpreadsheet(TEST_URL, client=client)
        self.assertTrue(sheet)

    def test_can_append_row(self):
        import datetime
        from . import __version__ as VERSION

        sheet = GSpreadsheet(WRITABLE_TEST_URL)

        self.assertTrue(sheet.is_authed)
        data_to_write = dict(
            date=datetime.datetime.utcnow().isoformat(' ').split('.')[0],
            value=str(VERSION),
        )
        sheet.append(data_to_write)

    def test_can_defer_saves_and_delete_rows(self):
        # yeah this is two tests, but the delete is sorta the tests's teardown

        # setup, write a dummy row
        sheet = GSpreadsheet(WRITABLE_TEST_URL, deferred_save=True)

        data_to_write = dict(
            date='DELETEME',
            value='-1',
        )
        row = sheet.append(data_to_write)
        row['value'] = '-2'
        self.assertTrue(row._defer_save)
        self.assertEqual(row._entry.custom['value'].text, '-1')
        row.save()
        self.assertEqual(row._entry.custom['value'].text, '-2')
        row.delete()
