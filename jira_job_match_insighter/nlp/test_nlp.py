import pytest
import nltk
from jira_job_match_insighter.log_manager.logger import Logger
from jira_job_match_insighter.google.google_docs_reader import GoogleDocsReader
from jira_job_match_insighter.google.google_sheets_reader import GoogleSheetsReader
from jira_job_match_insighter.nlp.missing_keywords_finder import MissingKeywordsFinder
from jira_job_match_insighter.nlp.main import MissingKeywordsFinderAndSaver

test_nlp_logger = Logger().setup_logging()


@pytest.fixture(scope="module")
def setup():
    nltk.download('stopwords')
    nltk.download('punkt')
    test_nlp_logger.info("Starting NLP tests")
    yield
    test_nlp_logger.info("NLP tests completed")


@pytest.fixture
def constants():
    return {
        'TEST_RESUME_DOC_ID': '1-eDP23td-nkIy-SY3ap1KELAP8EIigMBo6mfrUTfC3k',
        'TEST_JOB_SHEET_ID': '1i81y3GAdEqnqSjAfRxY6tRB_lpeSkw0Y8QzaE_1J_6g',
        'TEST_JOB_SHEET_NAME': 'Sheet1',
        'TEST_OUTPUT_SHEET_ID': '1kw4VmfLfMsLAue0I60D8eVPbH7MsXw79LYrY5WLM_P4',
        'TEST_OUTPUT_SHEET_NAME': 'Sheet1'
    }


def test_find_and_save_missing_keywords(setup, constants):
    test_nlp_logger.info("Running test_find_and_save_missing_keywords")

    MissingKeywordsFinderAndSaver.find_and_save_missing_keywords(
        resume_doc_id=constants['TEST_RESUME_DOC_ID'],
        job_sheet_id=constants['TEST_JOB_SHEET_ID'],
        job_sheet_name=constants['TEST_JOB_SHEET_NAME'],
        output_sheet_id=constants['TEST_OUTPUT_SHEET_ID'],
        output_sheet_name=constants['TEST_OUTPUT_SHEET_NAME']
    )

    # Assertion 1: Check if the missing keywords are found in the resume
    resume_text = GoogleDocsReader.get_google_doc_content(constants['TEST_RESUME_DOC_ID'])
    job_description_text = GoogleSheetsReader.get_google_sheet_content(
        constants['TEST_JOB_SHEET_ID'], constants['TEST_JOB_SHEET_NAME']
    )[0]['job_description']
    missing_keywords = MissingKeywordsFinder.get_missing_keywords(resume_text, job_description_text)
    assert missing_keywords is not None and len(missing_keywords) > 0, \
        f"Missing keywords were not found in the resume. Found: {missing_keywords}"

    # Assertion 2: Check if the missing keywords are saved to the output sheet
    output_sheet_content = GoogleSheetsReader.get_google_sheet_content(
        constants['TEST_OUTPUT_SHEET_ID'], constants['TEST_OUTPUT_SHEET_NAME']
    )
    assert len(output_sheet_content) > 0, \
        f"Missing keywords were not saved to the output sheet. Found: {output_sheet_content}"
