from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

SHEET_ID = "1ioSGAiS7zsrDs7d3w0IE7JsLInNJjXagB9AdyDN2x14"  # <- tu destino

creds = Credentials.from_authorized_user_file("token.json", [
    "https://www.googleapis.com/auth/spreadsheets"
])
svc = build("sheets", "v4", credentials=creds, cache_discovery=False)

meta = svc.spreadsheets().get(
    spreadsheetId=SHEET_ID, fields="properties(title),sheets(properties(title))"
).execute()

print("Título:", meta["properties"]["title"])
print("Pestañas:", [s["properties"]["title"] for s in meta["sheets"]])
