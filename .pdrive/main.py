from __future__ import print_function

import os.path
import pickle
import json

from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

CWD = os.getcwd()
SCOPES = ['https://www.googleapis.com/auth/drive']
CLIENT_SECRET_FILE = CWD + "/.pdrive/credentials.json"
CONFIG_FILE = CWD + "/.pdrive/config.json"
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
                flow = InstalledAppFlow.from_client_secrets_file(cwd + '/.pdrive/credentials.json', SCOPES)
                creds = flow.run_local_server(port=0)
            # Save the credentials for the next run
            with open('token.pickle', 'wb') as token:
                pickle.dump(creds, token)

        return creds


def get_files():
    _files = []
    for root, dirs, f in os.walk(CWD):
        for file in f:
            if "pdf" in file:
                _files.append(os.path.join(root, file))
            if "jpg" in file:
                _files.append(os.path.join(root, file))

    _files = [f.replace(CWD + "/", '') for f in _files]

    _result = {
        'files': [],
        'dirs': [{'name': CWD, 'id': 'id from config'}]
    }

    for file in _files:
        f_name = file.split('/')[-1]
        dir = file.split('/')[:-1]

        if len(dir) > 0:
            dir_name = "/".join(dir)
            _result['dirs'].append({'name': dir_name, 'id': None})
            _result['files'].append({"name": f_name, 'parent': dir_name})
        else:
            _f = {'name': f_name, 'parent': CWD}
            _result['files'].append(_f)

    return _result


def read_config():
    with open(CONFIG_FILE, 'r') as file:
        data = file.read()

    return json.loads(data)


def upload_files(_files):
    oauth = Oauth(SCOPES, CLIENT_SECRET_FILE, APPLICATION_NAME)
    cred = oauth.get_credential()

    service = build('drive', 'v3', credentials=cred)
    file_metadata = {'name': 'lighthouse.jpg', 'parents': ['11PAmwwAGXpdFItSAp0cTDlmUI3KGpA8z']}
    media = MediaFileUpload(CWD + '/lighthouse.jpg', mimetype='image/jpeg')
    file = service.files().create(body=file_metadata,
                                        media_body=media,
                                        fields='id').execute()
    print('File ID: %s' % file.get('id'))


def get_drive_files():
    oauth = Oauth(SCOPES, CLIENT_SECRET_FILE, APPLICATION_NAME)
    cred = oauth.get_credential()

    service = build('drive', 'v3', credentials=cred)
    results = service.files().list(pageSize=10, fields="nextPageToken, files(id, name)").execute()
    items = results.get('files', [])

    if not items:
        print('No files found.')
    else:
        print('Files:')
        for item in items:
            print(u'{0} ({1})'.format(item['name'], item['id']))

def main():
    config = read_config()
    files = get_files()


if __name__ == '__main__':
    main()
