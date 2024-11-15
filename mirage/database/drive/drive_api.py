from pathlib import Path
from googleapiclient.discovery import build
from google.oauth2 import service_account

import consts
from mirage.config.config_manager import ConfigManager


class DriveApi:
    KEY_MIRAGE_FOLDER_ID = 'databases.drive.mirage_folder_id'

    def __init__(self):
        self._scopes = ['https://www.googleapis.com/auth/drive']
        self._service_account_file = f'{consts.CONFIG_FOLDER}/{consts.DRIVE_SERVICE_ACCOUNT_FILENAME}'
        self._mirage_folder_id = ConfigManager.config.get(DriveApi.KEY_MIRAGE_FOLDER_ID)

    def _authenticate(self):
        return service_account.Credentials.from_service_account_file(self._service_account_file, scopes=self._scopes)

    def upload_file(self, file_path: Path):
        creds = self._authenticate()
        service = build('drive', 'v3', credentials=creds)

        file_metadata = {
            'name': file_path.name,
            'parents': [self._mirage_folder_id]
        }

        # pylint: disable=maybe-no-member
        service.files().create(
            body=file_metadata,
            media_body=str(file_path)
        ).execute()
