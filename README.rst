gspreadsheet
============

A wrapper around a wrapper to get Google spreadsheets to look like
csv.DictReader_.

If you're used to working with CSVs or a human, you'll find that working with
Google's Python API for spreadsheets is so frustrating. With ``gspreadsheet``,
you can adapt your existing csv code to work with Google Spreadsheets with just
two line changes. As an added bonus, if you alter the dict, those changes get
saved back to the original spreadsheet.

.. _csv.DictReader: http://docs.python.org/2/library/csv.html#csv.DictReader

Installation
------------

::

    pip install gspreadsheet

Usage
-----
If your old CSV code looked like this::

    from csv import DictReader
    reader = DictReader(open('myspreadsheet.csv'))
    for row in reader:
        process(row)

It would look like this with gspreadsheet::

    from gspreadsheet import GSpreadsheet
    reader = GSpreadsheet("https://docs.google.com/myspreadsheet")
    for row in reader:
        process(row)

So looking at more examples...

Get a spreadsheet if you know the key and worksheet::

    sheet = GSpreadsheet(key='tuTazWC8sZ_r0cddKj8qfFg', worksheet="od6")

Get a spreadsheet if you just know the url::

    sheet = GSpreadsheet(url="https://docs.google.com/spreadsheet/"
                             "ccc?key=0AqSs84LBQ21-dFZfblMwUlBPOVpFSmpLd3FGVmFtRVE")

Since just knowing the url is the most common use case, specifying it as a kwarg
is optional. Just pass whatever url is in your browser as the first argument.::

    sheet = GSpreadsheet("https://docs.google.com/spreadsheet/"
                         "ccc?key=0AqSs84LBQ21-dFZfblMwUlBPOVpFSmpLd3FGVmFtRVE")

Get a spreadsheet as a certain user::

    sheet = GSpreadsheet(email="foo@example.com", password="12345",
                         key='tuTazWC8sZ_r0cddKj8qfFg', worksheet="od6")

You can also specify the email and password using environment variables:
``GOOGLE_ACCOUNT_EMAIL`` and ``GOOGLE_ACCOUNT_PASSWORD``.

And as an authenticated user, you can modify the spreadsheet.::

    for row in sheet:
        print row
        if row['deleteme']:
            row.delete()  # delete the row from the worksheet
            continue
        row['hash'] = md5(row['name']).hexdigest()  # compute the hash and save it back

    data = row.copy()   # get the last row as a plain dict
    sheet.add_row(data)  # copy the last row and append it back to the sheet

Scary Warnings
--------------

I really want to say this is alpha software, but we've been using bits and
pieces of this for over a year now. Everything is subject to change, even the
names. This also relies on google's relatively ancient gdata package, which does
not have support for Python 3.

Similar Python packages
-----------------------

* gspread_

.. _gspread: https://github.com/burnash/gspread
