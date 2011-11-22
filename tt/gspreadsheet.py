"""
A wrapper around a wrapper to get Google spreadsheets look like DictReader
"""
import re

from django.conf import settings

from gdata.spreadsheet.service import SpreadsheetsService


#http://code.google.com/apis/spreadsheets/data/1.0/developers_guide_python.html
def PrintFeed(feed):
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


class Importer(object):
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
            self.worksheet = None
            try:
                self.key = re.search(r'key=([0-9a-zA-Z\-]+)',url).group(1)
            except (AttributeError, IndexError):
                # TODO raise ImproperlyConfigured
                print "! not a valid url:", url
        self.connect()
        self.get_feed()

    def connect(self):
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

    def __repr__(self):
        return "Google Spreadsheet: %s" % self.get_absolute_url()
        self.sheet.feed.title.text

    def get_absolute_url(self):
        return "https://docs.google.com/a/texastribune.org/spreadsheet/ccc?key=%s" % (self.key)

    def get_worksheets(self):
        self.worksheets = self.client.GetWorksheetsFeed(self.key)
        return self.worksheets

    def __iter__(self):
        return self.readrow()

    # FIXME
    def next(self):
        out = self.readrow().next()
        return out

    def readrow(self):
        for entry in self.feed.entry:
            row = dict([(key, entry.custom[key].text)
                        for key in entry.custom])
            yield row


if __name__ == "__main__":
    sheet = Importer(key='tuTazWC8sZ_r0cddKj8qfFg', worksheet="od6",
        url="https://docs.google.com/a/texastribune.org/spreadsheet/ccc?key=0AqSs84LBQ21-dFZfblMwUlBPOVpFSmpLd3FGVmFtRVE")
