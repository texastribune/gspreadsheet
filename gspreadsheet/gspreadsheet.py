"""
A wrapper around a wrapper to get Google spreadsheets look like csv.DictReader


Usage:
------
Add this import:

    from gspreadheet import GSpreadsheet

Get a spreadsheet if you know the key and worksheet:

    sheet = GSpreadsheet(key='tuTazWC8sZ_r0cddKj8qfFg', worksheet="od6")

Get a spreadsheet if you just know the url:

    sheet = GSpreadsheet(url="https://docs.google.com/spreadsheet/"
                             "ccc?key=0AqSs84LBQ21-dFZfblMwUlBPOVpFSmpLd3FGVmFtRVE")

Since just knowing the url is the most common use case, specifying it as a
kwarg is optional. Just pass whatever url is in your browser as the first arg.

    sheet = GSpreadsheet("https://docs.google.com/spreadsheet/"
                         "ccc?key=0AqSs84LBQ21-dFZfblMwUlBPOVpFSmpLd3FGVmFtRVE")

Google will also complain if you're anonymous. Best specify some credentials.
Get a spreadsheet as a certain user:

    sheet = GSpreadsheet(email="foo@example.com", password="12345",
                         key='tuTazWC8sZ_r0cddKj8qfFg', worksheet="od6")

Then iterate over each row.

    for row in sheet:
        print row
        if row['deleteme']:
            row.delete()  # delete the row from the worksheet
        row['hash'] = md5(row['name'])  # compute the hash and save it back

    data = row.copy()   # get the last row as a plain dict
    sheet.add_row(data)  # copy the last row and append it back to the sheet

Future Plans/TODOs:
-------------------
Let you address by cells
Let you authenticate multiple times (it's cached so you can only authenticate once)
Tests

"""
__all__ = ['GSpreadsheet']

from UserDict import DictMixin
import logging
import re
import os

from gdata.spreadsheet.service import SpreadsheetsService
from gdata.service import RequestError

# from .utils import PrintFeed


logger = logging.getLogger(__name__)
# cache client between uses
gd_client = None


class GDataRow(DictMixin):
    # TODO use collections.MutableMapping as the docs recommend
    """A dict-like object that represents a row of a worksheet"""
    def __init__(self, entry, deferred_save=False):
        self._entry = entry
        self._data = dict([(key, entry.custom[key].text) for key in entry.custom])
        self._defer_save = deferred_save
        self._changed = False

    def __getitem__(self, *args):
        return self._data.__getitem__(*args)

    def __setitem__(self, key, value):
        if self._data.get(key) != value:
            self._data[key] = value
            self._changed = True
        if not self._defer_save:
            return self.save()

    def __delitem__(self, *args):
        raise NameError("Deleting Values Not Allowed")

    #def __del__(self):
    #    self.delete()
    #    return super(GDataRow, self).__del__()

    def keys(self):
        return self._data.keys()

    def copy(self):
        """Get an ordinary dict of the row"""
        return self._data.copy()

    def save(self):
        """Save the row back to the spreadsheet"""
        if not self._changed:
            # nothing to save
            return
        assert gd_client is not None
        try:
            entry = gd_client.UpdateRow(self._entry, self._data)
        except RequestError as e:
            error_data = e.args[0]
            if error_data.status == 409:
                # conflict
                raise
            else:
                raise
        self._entry = entry
        # reset `_changed` flag
        self._changed = False
        return entry

    def delete(self):
        """Delete the row from the spreadsheet"""
        assert gd_client is not None
        return gd_client.DeleteRow(self._entry)


class GSpreadsheet(object):
    email = None
    password = None
    key = None  # your spreadsheet key
    worksheet = None    # your worksheet id

    def __init__(self, url=None, **kwargs):
        for key, value in kwargs.iteritems():
            setattr(self, key, value)

        # Get key from url
        if url is not None:
            try:
                self.key = re.search(r'key=([0-9a-zA-Z\-]+)', url).group(1)
            except (AttributeError, IndexError):
                # TODO raise ImproperlyConfigured
                print "! not a valid url:", url
                raise

        # DELETEME grab email as pass from environ
        if self.email is None:
            self.email = os.environ.get('GO_EMAIL')
        if self.password is None:
            self.password = os.environ.get('GO_PASS')

        self.client = self.get_client()

        # Now look for the worksheet
        if url is not None:
            try:
                worksheet_index = int(re.search(r'#gid=(\d+)', url).group(1))
                worksheets = self.list_worksheets()
                self.worksheet = worksheets[worksheet_index][0]
            except (AttributeError, IndexError):
                pass

        self.get_feed()

    def get_client(self):
        """Get the google data client."""
        global gd_client
        if gd_client:
            return gd_client

        gd_client = SpreadsheetsService()
        gd_client.source = "texastribune-ttspreadimporter-1"
        if self.email and self.password:
            gd_client.ClientLogin(self.email, self.password)
        return gd_client

    def get_feed(self):
        if self.worksheet:
            self.feed = self.client.GetListFeed(self.key, self.worksheet)
        else:
            # print missing worksheet, falling back
            # or choose a worksheet
            # self.get_worksheets()
            self.feed = self.client.GetListFeed(self.key)
        return self.feed

    def __unicode__(self):
        if hasattr(self, 'spreadsheet_name'):
            return u"GSpreadsheet: %s (%s)" % (self.spreadsheet_name,
                                                     self.feed.title.text)
        return u"GSpreadsheet: %s" % self.feed.title.text

    def __str__(self):
        return str(self.__unicode__())

    def __repr__(self):
        return self.__unicode__()

    def get_absolute_url(self):
        # TODO there's a better way hidden in gdata
        return ""

    def get_worksheets(self):
        if hasattr(self, 'spreadsheet_name') and hasattr(self, '_worksheets'):
            return self._worksheets
        # for debugging
        worksheets = self.client.GetWorksheetsFeed(self.key)
        self.spreadsheet_name = worksheets.title.text
        self._worksheets = worksheets
        return worksheets

    def list_worksheets(self):
        """
        List what worksheet keys exist

        Returns a list of tuples of the form:
            (WORKSHEET_ID, WORKSHEET_NAME)
        You can then retrieve the specific WORKSHEET_ID in the future by
        constructing a new GSpreadsheet(worksheet=WORKSHEET_ID, ...)
        """
        # for debugging
        worksheets = self.get_worksheets()
        return [(x.link[3].href.split('/')[-1], x.title.text) for x in worksheets.entry]

    def __iter__(self):
        return self.readrow_as_dict()

    def next(self):
        """Retrieve the next row."""
        # I'm pretty sure this is the completely wrong way to go about this, but
        # oh well, this works/
        if not hasattr(self, '_iter'):
            self._iter = self.readrow_as_dict()
        return self._iter.next()

    def readrow_as_dict(self):
        for entry in self.feed.entry:
            row = GDataRow(entry)
            yield row

    def add_row(self, row_dict):
        """Add a row to the spreadsheet, returns the new row"""
        # TODO validate row_dict.keys() match
        if self.worksheet:
            entry = self.client.InsertRow(row_dict, self.key, self.worksheet)
        else:
            entry = self.client.InsertRow(row_dict, self.key)
        self.feed.entry.append(entry)
        return GDataRow(entry)
