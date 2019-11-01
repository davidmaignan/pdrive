from __future__ import print_function

import os.path
import pickle

from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

dirpath = os.getcwd()
SCOPES = ['https://www.googleapis.com/auth/drive']
CLIENT_SECRET_FILE = dirpath + "/.pdrive/credentials.json"
APPLICATION_NAME = "Drive API Python"


class Oauth:
    def __init__(self, scopes, client_secret_file, application_name):
        self.scopes = scopes
        self.client_secret_file = client_secret_file
        self.application_name = application_name

    def get_credential(self):
        cwd = os.getcwd()
        token_file = cwd + "/token.pickle"

        creds = None
        # The file token.pickle stores the user's access and refresh tokens, and is
        # created automatically when the authorization flow completes for the first
        # time.
        if os.path.exists(token_file):
            with open(token_file, 'rb') as token:
                creds = pickle.load(token)
        # If there are no (valid) credentials available, let the user log in.
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(dirpath + '/.pdrive/credentials.json', SCOPES)
                creds = flow.run_local_server(port=0)
            # Save the credentials for the next run
            with open('token.pickle', 'wb') as token:
                pickle.dump(creds, token)

        return creds



def main():
    oauth = Oauth(SCOPES, CLIENT_SECRET_FILE, APPLICATION_NAME)
    creds = oauth.get_credential()

    service = build('drive', 'v3', credentials=creds)

    # file_metadata = {'name': 'lighthouse.jpg'}
    # media = MediaFileUpload(dirpath + '/lighthouse.jpg', mimetype='image/jpeg')
    # file = service.files().create(body=file_metadata,
    #                                     media_body=media,
    #                                     fields='id').execute()
    
    # print('File ID: %s' % file.get('id'))

    # Call the Drive v3 API
    results = service.files().list(pageSize=10, fields="nextPageToken, files(id, name)").execute()
    items = results.get('files', [])

    if not items:
        print('No files found.')
    else:
        print('Files:')
        for item in items:
            print(u'{0} ({1})'.format(item['name'], item['id']))


if __name__ == '__main__':
    main()


