from jira_job_match_insighter.google.google_clients_initializer import GoogleClientsInitializer
from jira_job_match_insighter.log_manager.logger import Logger


class GoogleSheetsReader(object):
    google_logger = Logger().setup_logging()
    google_clients_initializer = GoogleClientsInitializer()
    sheets_client = google_clients_initializer.sheets_client

    @classmethod
    def get_google_sheet_content(cls, sheet_id, sheet_name):
        if cls.google_clients_initializer.ensure_google_clients_initialized():
            try:
                sheet = cls.sheets_client.open_by_key(sheet_id)
                worksheet = sheet.worksheet(sheet_name)
                job_data = worksheet.get_all_records()
                return job_data
            except Exception as e:
                cls.google_logger.error(f"Failed to get Google Sheet content: {e}")
                return None
        else:
            return None
