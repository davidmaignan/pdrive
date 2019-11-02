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


def get_files(_config):
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
        'dirs': [{'name': CWD, 'id': _config['root_id']}]
    }

    for file in _files:
        f_name = file.split('/')[-1]
        dir = file.split('/')[:-1]

        if len(dir) > 0:
            dir_name = "/".join(dir)
            _result['dirs'].append({'name': dir_name, 'id': None})
            _result['files'].append({"name": f_name, 'path': file,  'parent': dir_name, 'parent_id': None})
        else:
            _f = {'name': f_name, 'parent': CWD, 'parent_id': _config['root_id']}
            _result['files'].append(_f)

    return _result


def read_config():
    with open(CONFIG_FILE, 'r') as file:
        data = file.read()

    return json.loads(data)


def save_config(_config):
    with open(CONFIG_FILE, 'w') as outfile:
        json.dump(_config, outfile, indent=4)


def get_service():
    oauth = Oauth(SCOPES, CLIENT_SECRET_FILE, APPLICATION_NAME)
    cred = oauth.get_credential()

    return build('drive', 'v3', credentials=cred)


def drive_mkdirs(_dirs, _config):
    for current_dir in _dirs:
        d = next((item for item in _config['dirs'] if item["name"] == current_dir['name']), None)
        if d is not None:
            current_dir['id'] = d['id']
        else:
            drive_mkdir(current_dir, _config, _config['root_id'])


def drive_mkdir(c_dir, _config, parent_id):
    names = c_dir['name'].split("/", maxsplit=1)
    d = next((item for item in _config['dirs'] if item["name"] == names[0]), None)

    if d is None:
        _id = drive_mkdir_request(names[0], parent_id)
        _config['dirs'].append({'name': names[0], 'id': _id, 'parent_id': parent_id})
        parent_id = _id
    else:
        parent_id = d['id']

    parent_name = names[0]

    while len(names) > 1:
        names = names[-1].split("/", maxsplit=1)
        d = next((item for item in _config['dirs'] if item["name"] == names[0]), None)
        if d is None:
            _id = drive_mkdir_request(names[0], parent_id)
            name = "%s/%s" % (parent_name, names[0])
            _config['dirs'].append({'name': name , 'id': _id,  'parent_id': parent_id})
            parent_id = _id
            parent_name = name
        else:
            parent_name = "%s/%s" % (parent_name, names[0])
            parent_id = d['id']


def drive_mkdir_request(name, _parent_id):
    print("mkdir: %s" % name)
    file_metadata = {
        'name': name,
        'mimeType': 'application/vnd.google-apps.folder',
        'parents': [_parent_id]
    }

    service = get_service()

    try:
        file = service.files().create(body=file_metadata, fields='id').execute()
        return file.get('id')
    except:
        print("Cannot create dir: %s" % name)


def drive_upload_files(_files, _config):
    for file in _files:
        d = next((item for item in _config['files'] if item["name"] == file['name']), None)
        if d is None:
            parent = next((item for item in _config['dirs'] if item["name"] == file['parent']), None)
            if parent is not None:
                upload_files(file, parent, _config)
            else:
                print("Cannot upload file: %s (parent %s is missing)" % (file['name'], file['parent']))


def upload_files(_file, _parent, _config):
    file_path = _file['parent'] + "/" + _file['name']
    if _file['parent'] != _config['root_path']:
        file_path = _config['root_path'] + "/" + file_path

    print(_file)
    print(_parent)
    print("---")

    oauth = Oauth(SCOPES, CLIENT_SECRET_FILE, APPLICATION_NAME)
    cred = oauth.get_credential()
    service = build('drive', 'v3', credentials=cred)
    file_metadata = {'name': _file['name'], 'parents': [_parent['id']]}
    media = MediaFileUpload(file_path, mimetype='image/jpeg')
    try:
        print("Uploading: file %s" % file_path)
        file = service.files().create(body=file_metadata,
                                            media_body=media,
                                            fields='id').execute()
        _config['files'].append({'name': _file['name'], 'parent':_parent, 'id': file['id']})
    except Exception as e:
        print("Failed to upload: %s" % file_path)
        print(e)


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
    files_dirs = get_files(config)

    # Create dir
    drive_mkdirs(files_dirs['dirs'], config)

    # Save config
    save_config(config)

    print(files_dirs['files'])

    # Copy new files
    drive_upload_files(files_dirs['files'], config)
    save_config(config)


if __name__ == '__main__':
    main()
