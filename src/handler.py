import os
import json
import logging
import sys

# Ensure current directory is in path for imports if needed
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from band_client import BandClient
    from doc_generator import generate_docs_by_year
    from drive_uploader import DriveUploader
except ImportError:
    # Try importing with package prefix if running from root
    from src.band_client import BandClient
    from src.doc_generator import generate_docs_by_year
    from src.drive_uploader import DriveUploader

logger = logging.getLogger()
logger.setLevel(logging.INFO)

def lambda_handler(event, context):
    """
    Main entry point for the serverless function.
    """
    logger.info("Received event: " + json.dumps(event))

    # Load Configuration from Env Vars
    BAND_ACCESS_TOKEN = os.environ.get('BAND_ACCESS_TOKEN')
    DEFAULT_BAND_KEY = os.environ.get('BAND_KEY')
    GOOGLE_CREDENTIALS_JSON = os.environ.get('GOOGLE_CREDENTIALS_JSON') # Should be a JSON string
    DRIVE_FOLDER_ID = os.environ.get('DRIVE_FOLDER_ID')

    if not BAND_ACCESS_TOKEN or not GOOGLE_CREDENTIALS_JSON:
        logger.error("Missing required environment variables.")
        return {
            'statusCode': 500,
            'body': json.dumps('Server configuration error: Missing env vars')
        }

    # Determine execution mode and parameters
    band_key = DEFAULT_BAND_KEY

    # Check if it's an API Gateway event (manual trigger) with query params
    # or a direct invocation payload
    params = {}
    if 'queryStringParameters' in event and event['queryStringParameters']:
        params = event['queryStringParameters']
    elif 'body' in event and event['body']:
        try:
            if isinstance(event['body'], str):
                params = json.loads(event['body'])
            else:
                params = event['body']
        except:
            pass

    if params.get('band_key'):
        band_key = params['band_key']

    if not band_key:
         return {
            'statusCode': 400,
            'body': json.dumps('Missing band_key configuration')
        }

    try:
        # 1. Fetch Posts
        logger.info(f"Fetching posts for band: {band_key}")
        client = BandClient(BAND_ACCESS_TOKEN)
        posts = client.get_posts(band_key)

        if not posts:
            logger.info("No posts found.")
            return {
                'statusCode': 200,
                'body': json.dumps('No posts found to archive.')
            }

        # 2. Generate Docs
        # Lambda writes to /tmp
        logger.info("Generating documents...")
        generated_files = generate_docs_by_year(posts, output_dir="/tmp")

        # 3. Upload to Drive
        logger.info("Uploading to Drive...")
        creds_info = json.loads(GOOGLE_CREDENTIALS_JSON)
        uploader = DriveUploader(creds_info)

        uploaded_ids = []
        for file_path in generated_files:
            file_id = uploader.upload_file(file_path, DRIVE_FOLDER_ID)
            if file_id:
                uploaded_ids.append(file_id)

        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'Archiving complete',
                'files_uploaded': len(uploaded_ids),
                'file_ids': uploaded_ids
            })
        }

    except Exception as e:
        logger.error(f"Execution failed: {e}", exc_info=True)
        return {
            'statusCode': 500,
            'body': json.dumps(f'Internal Server Error: {str(e)}')
        }
