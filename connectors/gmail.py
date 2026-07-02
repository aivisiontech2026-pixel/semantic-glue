#Authenticate
# The first time you run this, a browser opens for Google sign-in. 
# After authorization, a token.json file is created and reused on future runs.


import os
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow


#different scopes for different operations
#gmail.readonly - to read emails
#gmail.send - to send emails
#gmail.modify - to modify emails (mark as read/unread, move to trash, etc.)
#gmail.compose - to compose emails
#mail.google.com - full access to Gmail account (read, send, delete, etc.)


#everytime we are changing the SCOPES we need to delete
#existing token.json file
#SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]

#to send an email we need to change the scope
SCOPES = ["https://www.googleapis.com/auth/gmail.send"] 

#to send an email we need to change the scope
#SCOPES = ["https://www.googleapis.com/auth/gmail.compose"] 

creds = None

if os.path.exists("token.json"):
    creds = Credentials.from_authorized_user_file("token.json", SCOPES)

if not creds or not creds.valid:
    if creds and creds.expired and creds.refresh_token:
        creds.refresh(Request())
    else:
        flow = InstalledAppFlow.from_client_secrets_file(
            "credentials.json", SCOPES
        )
        creds = flow.run_local_server(port=0)

    with open("token.json", "w") as token:
        token.write(creds.to_json())


# to Build the Gmail service
#--------------------------------------
from googleapiclient.discovery import build

service = build("gmail", "v1", credentials=creds)



#List the latest emails (display snippet of latest 10 mails)
#---------------------------------------------------
# results = service.users().messages().list(
#     userId="me",
#     maxResults=10
# ).execute()

# messages = results.get("messages", [])

# for msg in messages:
#     message = service.users().messages().get(
#         userId="me",
#         id=msg["id"]
#     ).execute()

#     print(message["snippet"])



#     #send an email (change the scope to )
#     #---------------------------
from email.mime.text import MIMEText
import base64

message = MIMEText("Hello from Gmail API!")
message["to"] = "rekhalb@gmail.com, manjulalb@gmail.com"
message["subject"] = "Test Email"

raw = base64.urlsafe_b64encode(message.as_bytes()).decode()

service.users().messages().send(
    userId="me",
    body={"raw": raw}
).execute()

print("Email sent!")



# read a specific email 
# (if message_id is not provided, fetch the latest)
# # -----------
# if "message_id" not in globals():
#     results = service.users().messages().list(userId="me", maxResults=1).execute()
#     messages = results.get("messages", [])
#     if not messages:
#         print("No messages found.")
#         raise SystemExit
#     message_id = messages[0]["id"]

# message = service.users().messages().get(
#     userId="me",
#     id=message_id
# ).execute()

# print(message.get("snippet"))