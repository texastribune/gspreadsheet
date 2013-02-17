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

"""
__all__ = ["GSpreadsheet", "ReadOnlyException"]

from UserDict import DictMixin
import logging
import re
import os

from gdata.service import RequestError

from .auth import Auth
# from .utils import PrintFeed


logger = logging.getLogger(__name__)


class BaseException(Exception):
    pass


class ReadOnlyException(BaseException):
    """Attempted to write to a read only sheet."""
    pass


class GDataRow(DictMixin):
    # TODO use collections.MutableMapping as the docs recommend
    """A dict-like object that represents a row of a worksheet"""
    def __init__(self, entry, sheet, deferred_save=False):
        self._entry = entry
        self._data = dict([(key, value.text) for key, value in
            entry.custom.iteritems()])
        self._defer_save = deferred_save
        self._changed = False
        self._sheet = sheet

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

    def __copy__(self):
        """Get an ordinary dict of the row"""
        return self._data.copy()

    #def __del__(self):
    #    self.delete()
    #    return super(GDataRow, self).__del__()

    def keys(self):
        return self._data.keys()

    def copy(self):
        """Get an ordinary dict of the row"""
        return self.__copy__()

    def save(self):
        """Save the row back to the spreadsheet"""
        if self._sheet.readonly:
            raise ReadOnlyException
        if not self._changed:
            # nothing to save
            return
        gd_client = self._sheet.client
        assert gd_client is not None
        try:
            entry = gd_client.UpdateRow(self._entry, self._data)
        except RequestError as e:
            error_data = e.args[0]
            if error_data.status == 403:
                #  Forbidden
                raise
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
        if self._sheet.readonly:
            raise ReadOnlyException
        gd_client = self._sheet.client
        assert gd_client is not None
        return gd_client.DeleteRow(self._entry)


class GSpreadsheet(object):
    """
    A Google spreadsheet.

    Parameters:
      readonly -  default: True
    """
    client = None
    email = None
    password = None
    key = None  # your spreadsheet key
    worksheet = 'default'  # The worksheet's id (e.g. 'od6', 'od7') or 'default'
    readonly = False

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

        self.feed = self.get_feed()
        self.fieldnames = self.feed.entry[0].custom.keys()

    def get_client(self):
        """Get the google data client."""
        if self.client is not None:
            return self.client
        return Auth(self.email, self.password)

    def get_feed(self):
        return self.client.GetListFeed(self.key, self.worksheet)

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
        """Get the link to browse to this spreadsheet."""
        # Can you tell I'm a Django programmer?
        return self.feed.GetHtmlLink().href

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
            row = GDataRow(entry, sheet=self)
            yield row

    def append(self, row_dict):
        """Add a row to the spreadsheet, returns the new row"""
        # TODO validate row_dict.keys() match
        entry = self.client.InsertRow(row_dict, self.key, self.worksheet)
        self.feed.entry.append(entry)
        return GDataRow(entry, sheet=self)
