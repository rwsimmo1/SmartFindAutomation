import asyncio
from playwright.sync_api import sync_playwright
import time
import logging

# Import everything needed from your main script
from SmartFindScript import (
    INFO_MESSAGE_OVERLAY_SELECTOR, WEBSITE_URL, USERNAME, PASSWORD,
    USERNAME_SELECTOR, PASSWORD_SELECTOR, LOGIN_BUTTON_SELECTOR,
    TEXT_TO_READ_SELECTOR, AVAILABLE_JOBS_TAB_SELECTOR, ACTIVE_JOBS_TAB_SELECTOR,
    DATE_RANGE_SELECTOR, JOBS_TABLE_SELECTOR, BUTTON_TO_CLICK_SELECTOR,
    TEXT_TO_COPY_SELECTOR, JOB_CLASSIFICATION_INDEX_DEFAULT, JOB_LOCATION_INDEX_DEFAULT,
    ACTIVE_TABLE_ID, DATE_FILTER_BUTTON_SELECTOR, DATE_RANGE_BUTTON_SELECTOR, START_DATE_INPUT_SELECTOR,
    END_DATE_INPUT_SELECTOR, APPLY_FILTER_BUTTON_SELECTOR,
    process_row, rank_jobs, decline_job, active_jobs_tab, verify_job_active,
    read_dates_from_command_line, send_email
)
from send_with_google_app_password import find_app_password

def automate_website():
    """
    Automates a series of web interactions using Playwright.
    """
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s [%(levelname)s] %(message)s',
        handlers=[logging.StreamHandler()]
    )
    logger = logging.getLogger(__name__)

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context()
            page = context.new_page()

            logger.info("Navigating to the login page...")
            page.goto(WEBSITE_URL)

            # --- Log into the page ---
            logger.info("Logging in...")
            # Wait for the username input to appear and perform a simple clear+fill
            page.wait_for_selector(USERNAME_SELECTOR)
            username_input = page.locator(USERNAME_SELECTOR)
            username_input.fill("")
            username_input.fill(USERNAME)
            password_input = page.locator(PASSWORD_SELECTOR)
            password_input.fill("")
            password_input.fill(PASSWORD)
            page.locator(LOGIN_BUTTON_SELECTOR).click()

            # --- Read text from the page ---
            logger.info("Reading text from the page...")
            welcome_text = page.locator(TEXT_TO_READ_SELECTOR).inner_text()
            logger.info(f"Read text: '{welcome_text}'")

            # --- Get optional dates from command line ---
            # read_dates_from_command_line() returns (start_date, end_date) or (None, None)
            start_date, end_date = read_dates_from_command_line()
            logger.info(f"User supplied date range: {start_date} to {end_date}")
            if start_date is not None and end_date is not None:
                logger.info(f"Using date range from {start_date} to {end_date}")
                # Click to open date range selector and set dates
                page.locator(DATE_FILTER_BUTTON_SELECTOR).click()
                page.locator(DATE_RANGE_BUTTON_SELECTOR).click()
                # Convert start_date and end_date to MM/DD/YYYY string format
                start_date_str = start_date.strftime("%m/%d/%Y")
                end_date_str = end_date.strftime("%m/%d/%Y")
                page.locator(START_DATE_INPUT_SELECTOR).fill(start_date_str)
                page.locator(END_DATE_INPUT_SELECTOR).fill(end_date_str)
                page.locator(APPLY_FILTER_BUTTON_SELECTOR).click()
            else:
                logger.info("No date range supplied on the command line; continuing without date filters.")

            # --- Click the Available Jobs tab ---
            logger.info("Clicking the Available jobs tab...")
            page.locator(AVAILABLE_JOBS_TAB_SELECTOR).click()

            # --- "Copy" text by storing it in a variable ---
            logger.info("Locating and 'copying' current date range...")
            copied_text = page.locator(DATE_RANGE_SELECTOR).inner_text()
            logger.info(f"Date Range': '{copied_text}'")

            # --- Test for info message overlay and that it is visable ---
            try:
                info_div = page.wait_for_selector(INFO_MESSAGE_OVERLAY_SELECTOR)
            except Exception as e:
                logger.info(f"Info message overlay not found or timed out.")
                info_div = None
            if info_div and info_div.is_visible():
                # Display the info message and exit
                info_text = info_div.inner_text()
                logger.info(f"Info message: {info_text}")
            else: 
                # --- Interact with a table ---
                logger.info("Interacting with the jobs table...")
                rows = []
                jobs_table = page.locator(JOBS_TABLE_SELECTOR)
                if jobs_table:
                    try:
                        page.wait_for_selector(JOBS_TABLE_SELECTOR + " tbody tr")
                        rows = jobs_table.locator("tbody tr").all()
                    except Exception as e:
                        logger.info(f"Error waiting for table rows: {e}")
                        rows = []
                if rows:
                    logger.info(f"Found {len(rows)} rows in the jobs table.")
                    possible_jobs = []
                    for index, row in enumerate(rows):
                        cell_texts = process_row(row)
                        if cell_texts:  # Only add non-empty rows
                            possible_jobs.append(cell_texts)
                        else:
                            # Job was rejected based on criteria
                            # Let's decline the job by clicking on the decline button
                            # decline_job(driver, row, index)
                            logger.warning(f"Rejected job at row {index + 1}.")
                    logger.info(f"Possible jobs collected: {possible_jobs}")
                    if possible_jobs:
                        # Rank the possible jobs and select the top one
                        top_job = rank_jobs(possible_jobs)
                        if top_job:
                            logger.info(f"Top ranked job: {top_job}")
                            # Find the row corresponding to the top job and accept it
                            for index, row in enumerate(rows):
                                cell_texts = process_row(row)
                                if cell_texts == top_job:
                                    logger.info(f"Notify job at row {index + 1}: {top_job}")
                                    google_app_service = "SmartFindAutomationGoogleApp"
                                    service_username = "SmartFindAutomation"
                                    password = find_app_password(google_app_service, service_username)
                                    if not password:
                                        logger.error("Google App password for service_username '%s' not found in Credential Manager.", 
                                                service_username)
                                        logger.error("Please add it to Windows Credential Manager (use Windows Credential Manager UI or keyring.set_password) and try again.")
                                        continue  # Skip to next job or exit loop
                                    send_email(
                                        to_address="rwsimmo@gmail.com, simm.sean16@gmail.com",
                                        subject="SmartFindAutomation: Job Available",
                                        body=f"A new job has is available:\n\n{top_job}",
                                        from_address="rwsimmo@gmail.com",
                                        password=password)
                                    # active_jobs_tab(page)
                                    # verify_job_active(page, top_job, ACTIVE_TABLE_ID)
                                    break
                        else:
                            logger.info("No jobs to rank or accept.")
                else:
                    logger.info("No acceptable jobs found in the jobs table.")

            logger.info("Closing the browser.")
            context.close()
            browser.close()
    except Exception as e:
        logger.error(f"An unexpected error occurred: {e}", exc_info=True)

if __name__ == "__main__":
    automate_website()