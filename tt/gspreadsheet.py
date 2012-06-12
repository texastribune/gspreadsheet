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
    client = None
    key = None  # your spreadsheet key
    worksheet = None    # your worksheet id

    def __init__(self, url=None, **kwargs):
        for key, value in kwargs.items():
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
        gd_client.email = settings.GOOGLE_DATA_ACCOUNT['username']
        gd_client.password = settings.GOOGLE_DATA_ACCOUNT['password']
        gd_client.source = "texastribune-ttspreadimporter-1"
        gd_client.ProgrammaticLogin()
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

    def get_worksheets(self):
        self.worksheets = self.client.GetWorksheetsFeed(self.key)
        return self.worksheets

    @property
    def readline(self):
        for entry in self.feed.entry:
            row = dict([(key, entry.custom[key].text)
                for key in entry.custom])
            yield row

    def close():
        #TODO
        pass


if __name__ == "__main__":
    #https://docs.google.com/a/texastribune.org/spreadsheet/ccc?key=
    #    0AqSs84LBQ21-dFZfblMwUlBPOVpFSmpLd3FGVmFtRVE
    #CORPORATE_SPREADSHEET_KEY =
    #    0Am5sCFhTpENwdGlZX1R5WGw4NVNrZXJhbDVtRlBCOVE
    #https://docs.google.com/a/texastribune.org/spreadsheet/ccc?key=
    #    0AqSs84LBQ21-dHVUYXpXQzhzWl9yMGNkZEtqOHFmRmc
    sheet = Importer(key='tuTazWC8sZ_r0cddKj8qfFg', worksheet="od6",
        url="https://docs.google.com/a/texastribune.org/spreadsheet/ccc?key=0AqSs84LBQ21-dFZfblMwUlBPOVpFSmpLd3FGVmFtRVE")
