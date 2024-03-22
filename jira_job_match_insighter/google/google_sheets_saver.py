from jira_job_match_insighter.google.google_clients_initializer import GoogleClientsInitializer
from jira_job_match_insighter.log_manager.logger import Logger


class GoogleSheetsSaver:
    google_logger = Logger().setup_logging()
    google_clients_initializer = GoogleClientsInitializer()
    sheets_client = google_clients_initializer.sheets_client

    @classmethod
    def save_missing_keywords_to_sheet(cls, missing_keywords, sheet_id, sheet_name):
        try:
            # Initialize Google Sheets client
            sheet = cls.sheets_client.open_by_key(sheet_id)
            worksheet = sheet.worksheet(sheet_name)

            first_row = worksheet.row_values(1)
            title_row = ["Job Title", "Missing Keywords"]

            if first_row != title_row:
                worksheet.insert_row(title_row, 1)

            row_number = 2  # Start from the second row
            for job_title, keywords in missing_keywords.items():
                data_row = [job_title, ", ".join(keywords)]
                worksheet.insert_row(data_row, row_number)
                row_number += 1

            cls.google_logger.info("Successfully saved missing keywords to Google Sheet.")
        except Exception as e:
            cls.google_logger.error(f"Failed to save missing keywords to Google Sheet: {e}")
