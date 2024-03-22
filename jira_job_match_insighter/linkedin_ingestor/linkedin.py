import json
import requests
from datetime import datetime
from pathlib import Path
from splinter import Browser
from splinter.exceptions import ElementDoesNotExist
from selenium.common.exceptions import TimeoutException
from selenium.common.exceptions import StaleElementReferenceException
from jira_job_match_insighter.log_manager.logger import Logger
from jira_job_match_insighter.google.scraped_data_manager import ScrapedDataManager
from jira_job_match_insighter.linkedin_ingestor.linkedin_job_post_locators import LinkedinJobPostLocators


"""
The responsibility of this class would be:
    - to extract all the information from a job posting links and put it in someway
    Testing GPGKey
"""


class LinkedInJobPostIngestorHandler(object):
    linkedin_logger = Logger().setup_logging()
    linkedin_job_list_query = (
        "https://www.linkedin.com/jobs/search?"
        "keywords=Software%20Engineer"
        "&"
        "location=Canada"
        "&"
        "locationId=&geoId=101174742"
        "&"
        "f_TPR=r2592000"
        "&"
        "f_E=4%2C5"
        "&"
        "f_JT=F%2CC"
        "&"
        "position=1"
        "&"
        "pageNum=0"
    )
    request = requests.get(linkedin_job_list_query, allow_redirects=True)
    now = datetime.now()
    now_str = now.strftime("%Y-%m-%d--%H_%M_%S")
    icon_x_path = "/html/body/div[1]/header/nav/a/icon"
    base_dir = Path(__file__).resolve().parent.parent
    artifact_folder = base_dir / "output" / "artifact"
    json_output_folder = base_dir / "output" / "artifact" / "json_output"
    screenshot_folder = base_dir / "output" / "artifact" / "screenshots"
    scraped_data_manager = ScrapedDataManager()
    output_filename = None
    start = 0
    end = 6
    step_size = 1
    wait_time = 2

    def __init__(self):
        self.open_browser()
        self.output_filename = self.output_filename_with_time_stamp()

    @classmethod
    def open_browser(cls):
        with Browser("firefox") as browser:
            try:
                browser.visit(cls.linkedin_job_list_query)
                if browser.evaluate_script("document.readyState") == "complete":
                    cls.linkedin_logger.info("Page is loaded... ... ...")
                    return browser

            except TimeoutException:
                cls.linkedin_logger.exception("Timed out waiting for page to load")

    @classmethod
    def create_folder(cls, folder_path):
        folder = Path(folder_path)
        folder.mkdir(parents=True, exist_ok=True)
        return folder

    @classmethod
    def does_folder_exist(cls, folder_path):
        folder = Path(folder_path)
        try:
            return folder.exists() and folder.is_dir()
        except PermissionError as e:
            cls.linkedin_logger.error(f"Permission error occurred: {e}")
            return False
        except Exception as e:
            cls.linkedin_logger.exception(f"Exception occurred: {e}")
            return False

    @classmethod
    def get_all_information_from_job_list_expanded(cls):
        field_value = None
        x_paths = cls.load_job_x_paths()
        cls.save_job_data(field_value, x_paths)

    @classmethod
    def save_job_data(cls, field_value, x_paths):
        with Browser("firefox") as browser:
            browser.visit(cls.linkedin_job_list_query)
            if browser.is_element_present_by_xpath(cls.icon_x_path, wait_time=cls.wait_time / 2):
                if browser.is_element_visible_by_xpath(cls.icon_x_path, wait_time=cls.wait_time / 2):
                    browser.reload()
                    cls.clear_view_for_scrapping(browser)

                    for i in range(cls.start, cls.end, cls.step_size):
                        job_data = cls.scrap_job_data(browser, field_value, i, x_paths)

                        if job_data:
                            cls.scraped_data_manager.save_to_google_sheet(job_data)
                            cls.scroll_and_output_json_file(browser, i, job_data)

    @classmethod
    def clear_view_for_scrapping(cls, browser):
        try:
            cls.close_popup(browser)
            cls.show_more(browser)
            cls.close_popup(browser)
            # cls.close_messaging(browser) # after login
        except ElementDoesNotExist as e:
            cls.linkedin_logger.exception(f"Exception occurred: {e}")

    @classmethod
    def load_job_x_paths(cls):
        job_post = LinkedinJobPostLocators()
        x_paths = {
            "job_title": job_post.job_title,
            "job_link": job_post.job_link,
            "company_name": job_post.company_name,
            "location": job_post.location,
            "time_ago": job_post.time_ago,
            "be_among_first_xx_applicant": job_post.be_among_first_xx_applicant,
            "similar_jobs": job_post.similar_jobs,
            "job_criteria_list": job_post.job_criteria_list,
            "job_description": job_post.job_description
        }
        return x_paths

    @classmethod
    def scrap_job_data(cls, browser, field_value, i, x_paths):
        job_data = {}

        if not cls.does_folder_exist(cls.screenshot_folder):
            cls.create_folder(cls.screenshot_folder)

        for x_path_key, x_path_value in x_paths.items():
            if browser.is_element_present_by_xpath(x_path_value, wait_time=cls.wait_time / 2):
                if browser.is_element_visible_by_xpath(x_path_value, wait_time=cls.wait_time / 2):
                    elements = browser.find_by_xpath(x_path_value)
                    try:
                        cls.see_more_jobs(browser)
                        cls.scroll_and_click_next_job_post(browser=browser, i=i, scroll=True, click=True)
                        field_value = cls.scrap_field_value(elements, x_path_key, x_path_value, browser)
                    except (ElementDoesNotExist, IndexError) as e:
                        cls.linkedin_logger.exception(f"Exception occurred: {e}")
                        cls.linkedin_logger.error(f"Current URL: {browser.url}")
                        screenshot_path = (cls.screenshot_folder /
                                           f"screenshot_{datetime.now().strftime('%Y%m%d%H%M%S')}.png")
                        browser.screenshot(str(screenshot_path))
                    finally:
                        if not field_value:
                            cls.scroll_and_click_next_job_post(browser=browser, i=i, scroll=True, click=True)
                            field_value = cls.scrap_field_value(elements, x_path_key, x_path_value, browser)
                else:
                    field_value = None
            job_data[x_path_key] = field_value

        return job_data

    @classmethod
    def scrap_field_value(cls, elements, x_path_key, x_path_value, browser):
        if len(elements) > 0:
            try:
                # Re-fetch the element to ensure it's not stale
                elements = browser.find_by_xpath(x_path_value)

                # Debugging: Log the state of the element
                cls.linkedin_logger.info(f"Element state before interaction: {elements[0]}")

                # Interact with the element
                return elements[0]["href"] if x_path_key == "job_link" else elements[0].text
            except StaleElementReferenceException:
                # Handle or log the exception
                cls.linkedin_logger.error("Element is stale. Re-fetching the element.")
                # Code to re-fetch the element
                elements = browser.find_by_xpath(x_path_value)
                return elements[0]["href"] if x_path_key == "job_link" else elements[0].text

    @classmethod
    def scroll_and_output_json_file(cls, browser, i, job_data):
        cls.scroll_and_click_next_job_post(browser=browser, i=i, scroll=True, click=False)
        cls.output_filename = cls.output_filename_with_time_stamp()
        cls.json_output(job_data)
        return browser

    @classmethod
    def scroll_and_click_next_job_post(cls, browser, i, scroll, click):
        next_job_post_xpath = f"/html/body/div[1]/div/main/section[2]/ul/li[{i + 1}]"
        next_job_post = browser.find_by_xpath(next_job_post_xpath)
        if browser.is_element_present_by_xpath(next_job_post_xpath, wait_time=cls.wait_time/2):
            if browser.is_element_visible_by_xpath(next_job_post_xpath, wait_time=cls.wait_time/2):
                if scroll:
                    browser.execute_script("arguments[0].scrollIntoView();", next_job_post._element)

                if click:
                    next_job_post.click()
                    cls.show_more(browser)

    @classmethod
    def output_filename_with_time_stamp(cls):
        timestamp = datetime.now().strftime("%Y-%m-%d--%H_%M_%S")
        cls.output_filename = cls.json_output_folder / f"{timestamp}.json"
        return cls.output_filename

    @classmethod
    def json_output(cls, job_data):
        # Convert the dictionary to a JSON-formatted string
        json_string = json.dumps(job_data, indent=2)
        # Replace escaped newlines with actual newlines
        # json_string = json_string.replace("\\n", "\n    ")
        # Write the JSON string to a file
        with open(cls.output_filename, "w") as json_file:
            json_file.write(json_string)

    @classmethod
    def close_messaging(cls, browser):
        close_messaging_xpath = "/html/body/div[4]/button"
        # /html/body/div[4]/button

        try:

            close_messaging_element = browser.find_by_xpath(close_messaging_xpath)
            browser.execute_script("arguments[0].scrollIntoView();", close_messaging_element)
            close_messaging_element.click()

        except ElementDoesNotExist:
            cls.linkedin_logger.warning(f"No element found for XPath: {close_messaging_xpath}")
        except Exception as e:
            cls.linkedin_logger.error(f"An error occurred while closing messaging: {e}")

    @classmethod
    def close_popup(cls, browser):
        close_popup_xpath = "//*[@id=\"close-small\"]"
        try:
            # Wait until the element is present and visible
            if browser.is_element_present_by_xpath(close_popup_xpath, wait_time=cls.wait_time/2):
                if browser.is_element_visible_by_xpath(close_popup_xpath, wait_time=cls.wait_time/2):
                    close_popup_element = browser.find_by_xpath(close_popup_xpath)
                    browser.execute_script("arguments[0].scrollIntoView();", close_popup_element._element)
                    close_popup_element.click()

        except ElementDoesNotExist:
            cls.linkedin_logger.warning(f"No element found for XPath: {close_popup_xpath} - Popup")
        except Exception as e:
            cls.linkedin_logger.error(f"An error occurred while closing The popup: {e}")

    @classmethod
    def show_more(cls, browser):
        show_more_xpath = "/html/body/div[1]/div/section/div[2]/div/section[1]/div/div/section/button[1]"
        if browser.is_element_present_by_xpath(show_more_xpath, wait_time=cls.wait_time/2):
            if browser.is_element_visible_by_xpath(show_more_xpath, wait_time=cls.wait_time/2):
                show_more_element = browser.find_by_xpath(show_more_xpath)
                browser.execute_script("arguments[0].scrollIntoView();", show_more_element._element)
                show_more_element.click()

    @classmethod
    def see_more_jobs(cls, browser):
        see_more_jobs_xpath = "/html/body/div[1]/div/main/section[2]/button"
        if browser.is_element_present_by_xpath(see_more_jobs_xpath, wait_time=cls.wait_time/2):
            if browser.is_element_visible_by_xpath(see_more_jobs_xpath, wait_time=cls.wait_time/2):
                see_more_jobs_element = browser.find_by_xpath(see_more_jobs_xpath)
                browser.execute_script("arguments[0].scrollIntoView();", see_more_jobs_element._element)
                see_more_jobs_element.click()
