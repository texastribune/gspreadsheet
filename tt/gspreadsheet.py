"""
A wrapper around a wrapper to get Google spreadsheets look like DictReader


Usage:
------

Get a spreadsheet if you know the key and worksheet:

    sheet = GSpreadsheet(key='tuTazWC8sZ_r0cddKj8qfFg', worksheet="od6")

Get a spreadsheet if you just know the url:

    sheet = GSpreadsheet(url="https://docs.google.com/a/texastribune.org/spreadsheet/"
                             "ccc?key=0AqSs84LBQ21-dFZfblMwUlBPOVpFSmpLd3FGVmFtRVE")

Get a spreadsheet as a certain user:

    sheet = GSpreadsheet(email="foo@example.com", password="12345",
                         key='tuTazWC8sZ_r0cddKj8qfFg', worksheet="od6")

    for row in sheet:
        print row


Future Plans/TODOs:
-------------------
Let you address by cells
attach original metadata to each row/cell
let you write back to the spreadsheet
"""
import re
from UserDict import DictMixin

from django.conf import settings
from gdata.spreadsheet.service import SpreadsheetsService


# cache client between uses
gd_client = None

#http://code.google.com/apis/spreadsheets/data/1.0/developers_guide_python.html
def PrintFeed(feed):
  """Example function from Google to print a feed"""
  import gdata
  for i, entry in enumerate(feed.entry):
    if isinstance(feed, gdata.spreadsheet.SpreadsheetsCellsFeed):
      print '%s %s\n' % (entry.title.text, entry.content.text)
    elif isinstance(feed, gdata.spreadsheet.SpreadsheetsListFeed):
      print '%s %s %s' % (i, entry.title.text, entry.content.text)
      # Print this row's value for each column (the custom dictionary is
      # built from the gsx: elements in the entry.) See the description of
      # gsx elements in the protocol guide.
      print 'Contents:'
      for key in entry.custom:
        print '  %s: %s' % (key, entry.custom[key].text)
      print '\n',
    else:
      print '%s %s\n' % (i, entry.title.text)

# TODO use collections.MutableMapping as the docs recommend
class GDataRow(DictMixin):
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
        global gd_client
        assert gd_client is not None
        entry = gd_client.UpdateRow(self._entry, self._data)
        self._entry = entry
        # reset `_changed` flag
        self._changed = False
        return entry


class GSpreadsheet(object):
    email = None
    password = None
    key = None  # your spreadsheet key
    worksheet = None    # your worksheet id

    def __init__(self, url=None, **kwargs):
        for key, value in kwargs.items():
            # allow username as an alias to email
            if key == "username":
                key = "email"
            if hasattr(self, key) and key[0] != "_":
                setattr(self, key, value)
            else:
                # TODO raise ImproperlyConfigured
                print "!", key, "not a valid thingy"

        if url is not None:
            self.key = None
            # TODO parse worksheet from url, should not overwrite if none specified
            #self.worksheet = None
            try:
                self.key = re.search(r'key=([0-9a-zA-Z\-]+)',url).group(1)
            except (AttributeError, IndexError):
                # TODO raise ImproperlyConfigured
                print "! not a valid url:", url
        self.connect()
        self.get_feed()

    def connect(self):
        global gd_client
        if gd_client:
            return
        gd_client = SpreadsheetsService()
        gd_client.source = "texastribune-ttspreadimporter-1"

        # login
        if hasattr(settings, 'GOOGLE_DATA_ACCOUNT'):
            user_email = settings.GOOGLE_DATA_ACCOUNT['username']
            user_password = settings.GOOGLE_DATA_ACCOUNT['password']
            email = self.email or user_email
            password = self.password or user_password
        else:
            email = self.email
            password = self.password
        if email and password:
            gd_client.ClientLogin(email, password)

        self.client = gd_client

    def get_feed(self):
        if not self.worksheet:
            # print missing worksheet, falling back
            # or choose a worksheet
            # self.get_worksheets()
            self.feed = self.client.GetListFeed(self.key)
        else:
            self.feed = self.client.GetListFeed(self.key, self.worksheet)
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
        return "https://docs.google.com/a/texastribune.org/spreadsheet/ccc?key=%s" % (self.key)

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

    # FIXME
    def next(self):
        out = self.readrow_as_dict().next()
        return out

    def readrow_as_dict(self):
        for entry in self.feed.entry:
            row = GDataRow(entry)
            yield row
