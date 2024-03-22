import re
from googleapiclient.errors import HttpError

from jira_job_match_insighter.google.google_clients_initializer import GoogleClientsInitializer
from jira_job_match_insighter.log_manager.logger import Logger


class ScrapedDataManager(object):
    google_logger = Logger().setup_logging()
    google_clients_initializer = GoogleClientsInitializer()

    @classmethod
    def save_to_google_sheet(cls, job_data):
        try:
            if not job_data:
                cls.google_logger.error("No job data to save.")
                return

            if not cls.google_clients_initializer.ensure_google_clients_initialized():
                cls.google_logger.error("Google Sheets API client is not initialized.")
                return

            if cls.google_clients_initializer.sheets_service is None:
                cls.google_logger.error("Google Sheets API client is not initialized: sheets_service is None.")
                return

            sheet_id = "1i81y3GAdEqnqSjAfRxY6tRB_lpeSkw0Y8QzaE_1J_6g"
            sheet_metadata = cls.google_clients_initializer.sheets_service.spreadsheets().get(spreadsheetId=sheet_id).execute()
            sheet_id, sheet_name = cls.check_current_sheet_and_create_new_spreadsheet(sheet_metadata)

            try:
                existing_data = cls.google_clients_initializer.sheets_service.spreadsheets().values().get(
                    spreadsheetId=sheet_id,
                    range=f"{sheet_name}!A2:Z"
                ).execute().get("values", [])
                existing_job_links = {row[1]: True for row in existing_data if len(row) > 1}
                new_job_link = job_data.get("job_link", "")

                if new_job_link in existing_job_links:
                    cls.google_logger.info(f"Duplicate job found: {new_job_link}. Skipping.")
                    return
            except Exception as e:
                cls.google_logger.error(f"An error occurred while fetching existing data: {e}")
                return

            try:
                last_row_data = cls.google_clients_initializer.sheets_service.spreadsheets().values().get(
                    spreadsheetId=sheet_id,
                    range=f"{sheet_name}!A:A"
                ).execute()
            except Exception as e:
                cls.google_logger.error(f"An error occurred while fetching last row data: {e}")
                return

            last_row = len(last_row_data.get("values", [])) + 1

            # Write to the selected sheet
            range_name = f"{sheet_name}!A{last_row}"

            # If it's a new sheet or the sheet is empty, add headers
            if last_row == 1:
                header = list(job_data.keys())
                cls.google_clients_initializer.sheets_service.spreadsheets().values().append(
                    spreadsheetId=sheet_id,
                    range=range_name,
                    body={"values": [header]},
                    valueInputOption="RAW"
                ).execute()
                last_row += 1

            # Write to the selected sheet
            range_name = f"{sheet_name}!A{last_row}"

            # Convert job_data to a format suitable for Sheets
            rows = [list(job_data.values())]

            # Update the sheet with job_data
            body = {
                "values": rows
            }

            try:
                response = cls.google_clients_initializer.sheets_service.spreadsheets().values().append(
                    spreadsheetId=sheet_id,
                    range=range_name,
                    body=body,
                    valueInputOption="RAW"
                ).execute()

                if 'updates' not in response:
                    cls.google_logger.error(f"Unexpected API response: {response}")

            except HttpError as e:
                cls.google_logger.error(f"HTTP error occurred while appending data to Google Sheet: {e}")
            except Exception as e:
                cls.google_logger.error(f"An unknown error occurred while appending data to Google Sheet: {e}")

        except Exception as e:
            cls.google_logger.error(f"An unexpected error occurred while saving to Google Sheet: {e}")

    @classmethod
    def check_current_sheet_and_create_new_spreadsheet(cls, sheet_metadata):
        # Load existing spreadsheet IDs from a file or database
        folder_id = "1olc6i5a43J-5xTMjJgk-GU9MDdQu9DxH"
        existing_spreadsheet_ids = cls.load_existing_spreadsheet_ids(folder_id)
        try:
            for existing_id in existing_spreadsheet_ids:
                existing_sheet_metadata = cls.google_clients_initializer.sheets_service.spreadsheets().get(spreadsheetId=existing_id).execute()
                existing_sheets = existing_sheet_metadata.get("sheets", "")
                existing_rows = existing_sheets[-1]["properties"]["gridProperties"]["rowCount"]
                existing_cols = existing_sheets[-1]["properties"]["gridProperties"]["columnCount"]
                existing_total_cells = existing_rows * existing_cols

                if existing_total_cells < 5_000_000:
                    return existing_id, existing_sheets[-1]["properties"]["title"]
        except Exception as e:
            cls.google_logger.error(f"An error occurred while checking existing sheets: {e}")

        try:
            # If no existing spreadsheet has space, create a new one
            existing_file_name = sheet_metadata["properties"]["title"]
            last_number = re.findall(r'\d+', existing_file_name)
            new_number = int(last_number[-1]) + 1 if last_number else 1
            new_file_name = f"{existing_file_name}_{new_number}"

            spreadsheet_body = {
                "properties": {"title": new_file_name}
            }

            new_spreadsheet = cls.google_clients_initializer.sheets_service.spreadsheets().create(
                body=spreadsheet_body,
                fields="spreadsheetId"
            ).execute()

            new_sheet_id = new_spreadsheet["spreadsheetId"]
            new_sheet_name = "Sheet1"

            # Update the list of existing spreadsheet IDs
            cls.update_existing_spreadsheet_ids(new_sheet_id, folder_id)

            return new_sheet_id, new_sheet_name
        except Exception as e:
            cls.google_logger.error(f"An error occurred while creating a new spreadsheet: {e}")

    @classmethod
    def load_existing_spreadsheet_ids(cls, folder_id):
        try:
            query = f"'{folder_id}' in parents"
            results = cls.google_clients_initializer.drive_service.files().list(q=query, fields="files(id, name)").execute()
            items = results.get('files', [])
            spreadsheet_ids = [item["id"] for item in items]
            return spreadsheet_ids
        except Exception as e:
            cls.google_logger.error(f"An error occurred while loading existing spreadsheet IDs: {e}")

    @classmethod
    def update_existing_spreadsheet_ids(cls, new_sheet_id, folder_id):
        try:
            # Move the new spreadsheet to the dedicated folder
            file = cls.google_clients_initializer.drive_service.files().get(fileId=new_sheet_id, fields="parents").execute()
            previous_parents = ",".join(file.get('parents'))
            cls.google_logger.info(f"Previous parent folder(s) for the spreadsheet: {previous_parents}")

            updated_file = cls.google_clients_initializer.drive_service.files().update(
                fileId=new_sheet_id,
                addParents=folder_id,
                removeParents=previous_parents,
                fields="id, parents"
            ).execute()

            updated_parents = ",".join(updated_file.get('parents'))
            cls.google_logger.info(f"Updated parent folder(s) for the spreadsheet: {updated_parents}")
        except Exception as e:
            cls.google_logger.error(f"An error occurred while updating existing spreadsheet IDs: {e}")
