from jira_job_match_insighter.google.google_docs_reader import GoogleDocsReader
from jira_job_match_insighter.google.google_sheets_reader import GoogleSheetsReader
from jira_job_match_insighter.google.google_sheets_saver import GoogleSheetsSaver
from jira_job_match_insighter.nlp.missing_keywords_finder import MissingKeywordsFinder
from jira_job_match_insighter.log_manager.logger import Logger


class MissingKeywordsFinderAndSaver(object):
    missing_keywords = {}
    logger = Logger().setup_logging()

    @classmethod
    def find_and_save_missing_keywords(
            cls, resume_doc_id, job_sheet_id,
            job_sheet_name, output_sheet_id, output_sheet_name
    ):
        try:
            resume_text = GoogleDocsReader.get_google_doc_content(resume_doc_id)
        except Exception as e:
            cls.logger.error(f"Failed to read resume: {e}")
            return None

        try:
            job_data_list = GoogleSheetsReader.get_google_sheet_content(job_sheet_id, job_sheet_name)
        except Exception as e:
            cls.logger.error(f"Failed to read job data: {e}")
            return None

        for job_data in job_data_list:
            job_title = job_data['job_title']
            job_description_text = job_data['job_description']

            try:
                missing_keywords = MissingKeywordsFinder.get_missing_keywords(resume_text, job_description_text)
                cls.missing_keywords[job_title] = missing_keywords
            except Exception as e:
                cls.logger.error(f"Failed to analyze for job {job_title}: {e}")

        GoogleSheetsSaver.save_missing_keywords_to_sheet(cls.missing_keywords, output_sheet_id, output_sheet_name)


if __name__ == '__main__':
    MissingKeywordsFinderAndSaver.find_and_save_missing_keywords(
        resume_doc_id='1-eDP23td-nkIy-SY3ap1KELAP8EIigMBo6mfrUTfC3k',
        job_sheet_id='1i81y3GAdEqnqSjAfRxY6tRB_lpeSkw0Y8QzaE_1J_6g',
        job_sheet_name='Sheet1',
        output_sheet_id='1kw4VmfLfMsLAue0I60D8eVPbH7MsXw79LYrY5WLM_P4',
        output_sheet_name='Sheet1'
    )
