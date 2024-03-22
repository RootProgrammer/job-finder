from pathlib import Path
import gspread
from google.auth.transport.requests import Request
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build

from jira_job_match_insighter.log_manager.logger import Logger


class GoogleClientsInitializer(object):
    google_logger = Logger().setup_logging()
    base_dir = Path(__file__).resolve().parent.parent
    drive_service = None
    sheets_service = None
    sheets_client = None
    docs_service = None

    def __init__(self):
        self.initialize_google_clients()

    @classmethod
    def initialize_google_clients(cls):
        scopes = [
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive",
            "https://www.googleapis.com/auth/documents"
        ]
        service_account_file = cls.base_dir / "json" / "employment-402321-5a17626d7b60.json"
        credentials = Credentials.from_service_account_file(str(service_account_file), scopes=scopes)

        if credentials.expiry is None or credentials.expired:
            credentials.refresh(Request())

        try:
            cls.sheets_service = build("sheets", "v4", credentials=credentials)
            cls.sheets_client = gspread.service_account(filename=str(service_account_file))
            cls.drive_service = build('drive', 'v3', credentials=credentials)
            cls.docs_service = build('docs', 'v1', credentials=credentials)
        except Exception as e:
            cls.google_logger.exception(f"AAn error occurred while initializing Google clients: {e}")

    @classmethod
    def ensure_google_clients_initialized(cls):
        if (
                cls.sheets_service is None
                and cls.sheets_client is None
                and cls.drive_service is None
                and cls.docs_service is None
        ):
            try:
                cls.initialize_google_clients()
            except Exception as e:
                cls.google_logger.error(f"Failed to initialize Google API clients: {e}")
                return False
        return True
