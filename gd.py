from __future__ import print_function

import os.path
import math
from pprint import pprint
import uuid
import filetype
import io

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError


# from __future__ import print_function

import google.auth
from googleapiclient.http import MediaFileUpload
from googleapiclient.http import MediaIoBaseDownload
# from googleapiclient.http import ResumableUpload

# If modifying these scopes, delete the file token.json.
SCOPES = ['https://www.googleapis.com/auth/drive',
          'https://www.googleapis.com/auth/drive.readonly']


# Authorize the acc
def authorize():
    """Shows basic usage of the Drive v3 API.
    Prints the names and ids of the first 10 files the user has access to.
    """
    creds = None
    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open('token.json', 'w') as token:
            token.write(creds.to_json())

    return creds


# Get all files in gDrive
def get_main_files(types):
    creds = authorize()

    if types == 'folders':
        query = "mimeType='application/vnd.google-apps.folder'"
    if types == "files":
        query = "mimeType!='application/vnd.google-apps.folder'"
    if types == 'all':
        query = f""

    try:
        service = build('drive', 'v3', credentials=creds)

        # Call the Drive v3 API
        results = service.files().list(q=query,
                                       pageSize=500,
                                       fields="nextPageToken, files(id, name)").execute()
        # pprint(results)
        items = results.get('files', [])

        if not items:
            print('No files found.')
            return
        print('Files:')
        for item in items:
            # print(u'{0} - {1}'.format(item['name'], item['id']))
            pass
        return items
    except HttpError as error:
        # TODO(developer) - Handle errors from drive API.
        print(f'An error occurred: {error}')


# Upload any files to gDrive
def upload_any_file(file_path_to_upload, gd_folder_id, file_name):
    """Insert new file.
    Returns : Id's of the file uploaded

    Load pre-authorized user credentials from the environment.
    TODO(developer) - See https://developers.google.com/identity
    for guides on implementing OAuth2 for the application.
    """
    kind = filetype.guess(file_path_to_upload)

    creds = authorize()

    try:
        # create drive api client
        service = build('drive', 'v3', credentials=creds)

        # folder = '12K6mXsQBiiU7LTpw_Sd82RJcpmN7T7-c'
        # application/octet-stream
        if gd_folder_id == '':
            lst = []
        else:
            lst = [gd_folder_id]
        file_metadata = {'name': file_name, "parents": lst}
        media = MediaFileUpload(file_path_to_upload,
                                mimetype=kind.mime, resumable=True, chunksize=(20 * 1024 * 1024))
        # pylint: disable=maybe-no-member
        file = service.files().create(body=file_metadata, media_body=media,
                                      fields='id')

        response = None
        while response is None:
            status, response = file.next_chunk()
            if status:
                percentage = str(math.floor(int(status.resumable_progress) /
                                 int(status.total_size) * 100)) + "%"
                print(percentage)
                # print("Uploaded %d%%." % int(status.resumable_progress * 100))
        print("Upload Complete!")
        file = response.get('id')
        # print(F'File ID: {file.get("id")}')

    except HttpError as error:
        print(F'An error occurred: {error}')
        file = None

    # return file.get('id')
    return file


# Search files and folders
def search_inside_file(folder_id, types, is_main):

    creds = authorize()
    if not is_main:
        if types == 'folders':
            query = f"'{folder_id}' in parents and mimeType='application/vnd.google-apps.folder'"
        if types == "files":
            query = f"'{folder_id}' in parents and mimeType!='application/vnd.google-apps.folder'"
        if types == 'all':
            query = f"'{folder_id}' in parents"
    else:
        if types == 'folders':
            query = f"mimeType='application/vnd.google-apps.folder'"
        if types == "files":
            query = f"mimeType!='application/vnd.google-apps.folder'"
        if types == 'all':
            query = f""

    try:
        # create drive api client
        service = build('drive', 'v3', credentials=creds)
        files = []
        page_token = None
        while True:
            # pylint: disable=maybe-no-member
            response = service.files().list(
                q=query,
                spaces='drive',
                fields='nextPageToken, '
                'files(id, name, mimeType, quotaBytesUsed)',
                pageToken=page_token).execute()
            # print(response)
            for file in response.get('files', []):
                # Process change
                # print(F'Found file: {file.get("name")}, {file.get("id")}')
                pass
            files.extend(response.get('files', []))
            page_token = response.get('nextPageToken', None)
            if page_token is None:
                break
        return files

    except HttpError as error:
        print(F'An error occurred: {error}')
        files = None


def createFolder(folderName, parentID):
    try:
        creds = authorize()
        service = build('drive', 'v3', credentials=creds)
        # Create a folder on Drive, returns the newely created folders ID
        body = {
            'name': folderName,
            'mimeType': "application/vnd.google-apps.folder"
        }
        if parentID:
            body['parents'] = [parentID]
            print(body)
        root_folder = service.files().create(body=body).execute()
        return root_folder['id']
    except HttpError as error:
        print(F'An error occurred: {error}')
        return None


# 3 layers from top
def get_hirarchi():
    hierarchi = {"main_folders": {}, "main_files": []}
    main_folders = search_inside_file(
        folder_id='', types='folders', is_main=True)
    main_files = search_inside_file(folder_id='', types='files', is_main=True)

    hierarchi.update({"main_files": main_files})
    folder_lst = []
    for folder in main_folders:
        folder_lst.append({"name": folder.get('name'), "id": folder.get('id')})
    hierarchi.update({"main_folders": folder_lst})
    f = []
    i = 0
    for folder in hierarchi.get('main_folders'):
        id = folder.get('id')
        name = folder.get('name')

        sub_folders = search_inside_file(
            folder_id=id, types='folders', is_main=False)
        if sub_folders is not None:
            folder.update({'folders': sub_folders})
            for sub_folder in sub_folders:
                if sub_folder is not None:
                    # print(sub_folder)
                    id = sub_folder.get('id')
                    name = sub_folder.get('name')
                    sub_sub_folders = search_inside_file(
                        folder_id=id, types='folders', is_main=False)
                    if sub_sub_folders is not None:
                        sub_folder.update({'folders': sub_sub_folders})

    return hierarchi


def get_drive_info():
    creds = authorize()
    try:
        service = build('drive', 'v3', credentials=creds)

        result = service.about().get(fields="*").execute()
        result = result.get("storageQuota", {})
        # {'limit': '16106127360', 'usage': '74702344', 'usageInDrive': '74702344', 'usageInDriveTrash': '0'}
        total = int(result.get('limit'))
        drive_usage = int(result.get('usageInDrive'))
        total_usage = int(result.get('usage'))
        other_usage = total_usage - drive_usage
        trash = int(result.get('usageInDriveTrash'))
        availible = total - total_usage

        return total, total_usage, availible, other_usage, trash

    except HttpError as error:
        print(F'An error occurred: {error}')
        return None


def download_file(real_file_id):
    """Downloads a file
    Args:
        real_file_id: ID of the file to download
    Returns : IO object with location.

    Load pre-authorized user credentials from the environment.
    TODO(developer) - See https://developers.google.com/identity
    for guides on implementing OAuth2 for the application.
    """
    creds = authorize()

    try:
        # create drive api client
        service = build('drive', 'v3', credentials=creds)

        file_id = real_file_id

        # pylint: disable=maybe-no-member
        request = service.files().get_media(fileId=file_id)
        data = service.files().get(fileId=file_id, fields='*').execute()
        name = data["name"]
        mime_type = data["mimeType"]
        size = data["size"]
        if "video" in mime_type:
            duration = data["videoMediaMetadata"]['durationMillis']
            print(name, mime_type, size, duration)
        else:
            print(name, mime_type, size)
        file = io.BytesIO()

        downloader = MediaIoBaseDownload(file, request)
        done = False
        while done is False:
            status, done = downloader.next_chunk()
            print(F'Download {int(status.progress() * 100)}.')

        with open(name, 'wb') as j:
            j.write(file.getvalue())
            j.close()

    except HttpError as error:
        print(F'An error occurred: {error}')
        file = None

    return name, size, mime_type

    # main func
if __name__ == '__main__':

    # with open('hi.json', "w") as f:
    #     data = str(get_hirarchi())
    #     data = data.replace("'", '"')
    #     f.write(data)

    download_file('1pnQ2xeuNJ7pq1g-4s9MtVXZVko3Mv545')
    # a = search_inside_file('12K6mXsQBiiU7LTpw_Sd82RJcpmN7T7-c', 'files', False)
