import os
import logging
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

class DriveUploader:
    SCOPES = ['https://www.googleapis.com/auth/drive']

    def __init__(self, service_account_info):
        """
        Initializes the DriveUploader.
        :param service_account_info: Can be a dictionary (parsed JSON) or a file path string.
        """
        self.logger = logging.getLogger(__name__)
        try:
            if isinstance(service_account_info, dict):
                self.creds = service_account.Credentials.from_service_account_info(
                    service_account_info, scopes=self.SCOPES)
            else:
                self.creds = service_account.Credentials.from_service_account_file(
                    service_account_info, scopes=self.SCOPES)

            self.service = build('drive', 'v3', credentials=self.creds)
        except Exception as e:
            self.logger.error(f"Failed to authenticate with Google Drive: {e}")
            raise

    def upload_file(self, file_path, folder_id=None):
        """
        Uploads a file to Google Drive.
        :param file_path: Local path to the file.
        :param folder_id: Optional Google Drive Folder ID to upload into.
        :return: The uploaded file's ID.
        """
        file_name = os.path.basename(file_path)
        file_metadata = {'name': file_name}
        if folder_id:
            file_metadata['parents'] = [folder_id]

        # Mime type for docx
        mime_type = 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
        media = MediaFileUpload(file_path, mimetype=mime_type)

        try:
            self.logger.info(f"Uploading {file_name}...")
            file = self.service.files().create(
                body=file_metadata,
                media_body=media,
                fields='id'
            ).execute()
            self.logger.info(f"File ID: {file.get('id')} uploaded successfully.")
            return file.get('id')
        except Exception as e:
            self.logger.error(f"Failed to upload file {file_name}: {e}")
            return None
