import io
import math
import os
import re
import PyPDF2

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaIoBaseDownload


def get_google_drive_api_service(client_secrets_file):
    """
    Service to Access Qbiz Google Drive Files. Access through Google Ouath will
    be necessary the first time
    """
    SCOPES = ["https://www.googleapis.com/auth/drive.readonly", "https://www.googleapis.com/auth/drive.metadata.readonly"]

    creds = None

    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists("token.json"):
        print("token.json found")
        creds = Credentials.from_authorized_user_file("token.json", SCOPES)

    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                client_secrets_file, SCOPES
            )
            creds = flow.run_local_server(port=0)
    # Save the credentials for the next run
    with open("token.json", "w") as token:
        token.write(creds.to_json())

    return build("drive", "v3", credentials=creds)


def get_drive_metadata_list(service):
    """
    Get metadata of all files from Google Drive.

    Args:
    - service (str): Google Drive Service.

    Returns:
    - List[Dict]: List of files with metadata of file.
    """
    query_str = "not (name contains 'career development' or name contains 'Career Development') " \
              + "and (name contains '.pdf' or mimeType='application/vnd.google-apps.document'" \
              + "or mimeType='application/vnd.google-apps.presentation' or mimeType='application/vnd.google-apps.spreadsheet')" \
              + "and (modifiedTime > '2020-01-01')"

    results = (
        service.files()
        .list(q=query_str, pageSize=1000, includeItemsFromAllDrives=True, supportsAllDrives=True, fields="nextPageToken, files(id, name, mimeType)")
        .execute()
    )

    items = results.get("files", [])
    print(len(items), " files found")

    if not items:
        print("No files found.")
        return None

    else:
        return items


def text_blocks_for_google_doc_and_pres(item, service):
    """
    Extract the text content of a google document or presentation file,
    and call a function to create 300 word text blocks.

    Args:
    - item Dict[str]: Google Drive doc metadata
    - service (str): Google Drive Service.

    Returns:
    - Dict[str]: Dictionary with index and text block.
    """
    if item['mimeType'] in ("application/vnd.google-apps.document",
                            "application/vnd.google-apps.presentation"):
        try:
            request_file = service.files().export_media(fileId=item['id'],
                                                        mimeType='text/plain').execute()
            text = str(request_file)
        except HttpError as error:
            print(f"An error occurred: {error}")
            return []
        return text_blocks_for_a_file(item['name'], text, 300, 10, True)
    else:
        return []


def text_blocks_for_google_spreadsheet(item, service):
    """
    Extract the text content of a google spreadsheet,
    and call a function to create 300 word text blocks.

    Args:
    - item Dict[str]: Google Drive doc metadata
    - service (str): Google Drive Service.

    Returns:
    - Dict[str]: Dictionary with index and text block.
    """

    if item['mimeType'] == "application/vnd.google-apps.spreadsheet":
        try:
            request_file = service.files().export_media(fileId=item['id'],
                                                        mimeType='text/csv').execute()
            text = str(request_file)
        except HttpError as error:
            print(f"An error occurred: {error}")
            return []
        return text_blocks_for_a_file(item['name'], text, 300, 10, True)
    else:
        return []


def text_blocks_for_pdfs(item, service):
    """
        Extract the text content of a pdf file,
        and call a function to create 300 word text blocks.

        Args:
        - item Dict[str]: Google Drive doc metadata
        - service (str): Google Drive Service.

        Returns:
        - Dict[str]: Dictionary with index and text block.
    """
    if item['name'][-3:] == "pdf":
        try:
            request_file = service.files().get_media(fileId=item['id'])
            file = io.BytesIO()
            downloader = MediaIoBaseDownload(file, request_file)
            done = False
            while done is False:
                status, done = downloader.next_chunk()
                file_retrieved: str = file.getvalue()
                file_io = io.BytesIO(file_retrieved)
                pdf_file = PyPDF2.PdfReader(file_io)
                text = ""

                # Loop through each page and extract text
                for page_num in range(len(pdf_file.pages)):
                    page = pdf_file.pages[page_num]
                    text += page.extract_text()
                    return text_blocks_for_a_file(item['name'], text, 300, 10,
                                                  True)
        except HttpError as error:
            print(f"An error occurred: {error}")
            return []
    else:
        return []


def text_blocks_for_a_file(file_name, text_content, words_per_block,
                           buffer_length, remove_urls):
    """
        Split text into blocks including n words. Return blocks in an array of dict (json) objects.

        Returns:
        - Dict[str]: Dictionary with index and text block.
    """
    if remove_urls:
        text_content = re.sub(r'http\S+', '', text_content)
    list_of_words = text_content.split()
    # create word blocks
    n_o_blocks = math.ceil(len(list_of_words) / words_per_block)
    array_of_blocks = []
    for i in range(n_o_blocks):
        start_word = i * words_per_block
        end_word = (
                               i + 1) * words_per_block + buffer_length  # take extra words (These will be overlapping between blocks, which is intended. Imperfect effort not to cut blocks in the middle of sentence)
        block = {
            "block_id": f"{file_name}_block_{i}",
            "text_block": 'Using document ' + file_name + ' as a source:' + ' '.join(
                list_of_words[start_word:end_word])
        }
        array_of_blocks.append(block)
    return array_of_blocks


# Reference: https://medium.com/@matheodaly.md/using-google-drive-api-with-python-and-a-service-account-d6ae1f6456c2
def create_text_blocks(service, items):
    text_blocks = []

    print("Files:")

    for item in items:
        print(f"{item['name']} ({item['id']}) ({item['mimeType']})")
        text_blocks.extend(text_blocks_for_google_doc_and_pres(item, service))
        text_blocks.extend(text_blocks_for_google_spreadsheet(item, service))
        text_blocks.extend(text_blocks_for_pdfs(item, service))

    return text_blocks