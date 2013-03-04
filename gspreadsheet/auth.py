from gdata.spreadsheet.service import SpreadsheetsService


def Auth(email=None, password=None):
    """Get a reusable google data client."""
    gd_client = SpreadsheetsService()
    gd_client.source = "texastribune-ttspreadimporter-1"
    if email and password:
        gd_client.ClientLogin(email, password)
    return gd_client
