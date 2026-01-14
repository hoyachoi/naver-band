import sys
import os
import unittest
from unittest.mock import MagicMock, patch
import json

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))
sys.path.append(os.path.dirname(__file__))

# Import the handler
# Depending on how imports are resolved, we might need to patch imports if dependencies are missing
# But ideally we install dependencies first.
try:
    from src.handler import lambda_handler
except ImportError:
    # If running from root and src is not a package in path
    from handler import lambda_handler

class TestArchiver(unittest.TestCase):

    @patch('src.handler.BandClient')
    @patch('src.handler.DriveUploader')
    @patch('src.handler.generate_docs_by_year')
    @patch.dict(os.environ, {
        'BAND_ACCESS_TOKEN': 'fake_token',
        'BAND_KEY': 'fake_band_key',
        'GOOGLE_CREDENTIALS_JSON': '{"type": "service_account"}',
        'DRIVE_FOLDER_ID': 'fake_folder_id'
    })
    def test_handler_flow(self, mock_generate, mock_uploader_cls, mock_band_cls):
        # Setup Mocks
        mock_band_instance = mock_band_cls.return_value
        # Mock post data: 2021-01-01
        mock_band_instance.get_posts.return_value = [{'content': 'test', 'created_at': 1609459200000}]

        mock_generate.return_value = ['/tmp/band_posts_2021.docx']

        mock_uploader_instance = mock_uploader_cls.return_value
        mock_uploader_instance.upload_file.return_value = 'file_id_123'

        # Invoke Handler
        event = {'body': {}}
        context = {}
        response = lambda_handler(event, context)

        # Verify
        self.assertEqual(response['statusCode'], 200)
        body = json.loads(response['body'])
        self.assertEqual(body['files_uploaded'], 1)
        self.assertEqual(body['file_ids'], ['file_id_123'])

        # Check calls
        mock_band_cls.assert_called_with('fake_token')
        mock_band_instance.get_posts.assert_called_with('fake_band_key')
        mock_generate.assert_called_once()
        mock_uploader_cls.assert_called_once()
        mock_uploader_instance.upload_file.assert_called_with('/tmp/band_posts_2021.docx', 'fake_folder_id')

if __name__ == '__main__':
    unittest.main()
