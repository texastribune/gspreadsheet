from gdata.spreadsheet.service import SpreadsheetsService


def Auth(email, password):
    """Get a reusable google data client."""
    gd_client = SpreadsheetsService()
    gd_client.source = "texastribune-ttspreadimporter-1"
    gd_client.ClientLogin(email, password)
    return gd_client
