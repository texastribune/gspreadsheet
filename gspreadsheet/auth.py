import os

from gdata.spreadsheet.service import SpreadsheetsService


def Auth(email=None, password=None):
    """Get a reusable google data client."""
    gd_client = SpreadsheetsService()
    gd_client.source = "texastribune-ttspreadimporter-1"
    if email is None:
        email = os.environ.get('GOOGLE_ACCOUNT_EMAIL')
    if password is None:
        password = os.environ.get('GOOGLE_ACCOUNT_PASSWORD')
    if email and password:
        gd_client.ClientLogin(email, password)
    return gd_client
