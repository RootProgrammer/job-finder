import pytest
from selenium.common.exceptions import NoSuchWindowException
from jira_job_match_insighter.log_manager.logger import Logger
from jira_job_match_insighter.linkedin_ingestor.linkedin import LinkedInJobPostIngestorHandler

test_linkedin_logger = Logger().setup_logging()


# Create a fixture for the job_post_list
# This could be a fixture that other test functions could use as well
@pytest.fixture
def job_post_list():
    return LinkedInJobPostIngestorHandler()


def test_ingest(job_post_list):
    test_linkedin_logger.info("Starting to Ingest ... ...")

    # Folder Creations
    test_linkedin_logger.info("Creating an artifact folder ... ...")
    job_post_list.create_folder(job_post_list.artifact_folder)
    test_linkedin_logger.info("Check if artifact folder exists ... ...")
    artifact_path_exists = job_post_list.does_folder_exist("output\\artifact")
    test_linkedin_logger.info(f"The artifact path exists: {artifact_path_exists}")

    test_linkedin_logger.info("Creating an json output folder ... ...")
    job_post_list.create_folder(job_post_list.json_output_folder)
    test_linkedin_logger.info("Check if json output folder exists ... ...")
    json_output_path_exists = job_post_list.does_folder_exist("output\\artifact\\json_output")
    test_linkedin_logger.info(f"The artifact path exists: {json_output_path_exists}")

    # Scraping the job posting
    test_linkedin_logger.info("Open Browser")
    try:
        job_post_list.get_all_information_from_job_list_expanded()
    except NoSuchWindowException:
        # Handle the exception here, e.g., by logging an error message and/or reopening the browser
        test_linkedin_logger.error("Browser window not found. Attempting to recover...")
        # Code to reopen browser or switch window

    print("Nothing")
