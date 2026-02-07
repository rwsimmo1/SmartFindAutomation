import asyncio
from playwright.sync_api import sync_playwright
from playwright._impl._errors import TimeoutError as PlaywrightTimeoutError, TargetClosedError
import time
import logging
import json
from pathlib import Path

# Import everything needed from your main script
from SmartFindScripts import (
    INFO_MESSAGE_OVERLAY_SELECTOR, WEBSITE_URL, USERNAME, PASSWORD,
    USERNAME_SELECTOR, PASSWORD_SELECTOR, LOGIN_BUTTON_SELECTOR,
    TEXT_TO_READ_SELECTOR, AVAILABLE_JOBS_TAB_SELECTOR, ACTIVE_JOBS_TAB_SELECTOR,
    DATE_RANGE_SELECTOR, JOBS_TABLE_SELECTOR, BUTTON_TO_CLICK_SELECTOR,
    TEXT_TO_COPY_SELECTOR, JOB_CLASSIFICATION_INDEX_DEFAULT, JOB_LOCATION_INDEX_DEFAULT,
    ACTIVE_TABLE_ID, DATE_FILTER_BUTTON_SELECTOR, DATE_RANGE_BUTTON_SELECTOR, START_DATE_INPUT_SELECTOR,
    END_DATE_INPUT_SELECTOR, APPLY_FILTER_BUTTON_SELECTOR,
    process_row, rank_jobs, decline_job, active_jobs_tab, verify_job_active,
    read_dates_from_command_line, send_email, accept_job,
    # Import new refactored functions
    is_session_expired, login_to_website, should_accept_job,
    apply_date_filters, get_available_jobs_from_table, process_and_notify_top_job
)
from send_with_google_app_password import find_app_password

# File to track notified jobs
NOTIFIED_JOBS_FILE = Path(__file__).parent / "notified_jobs.json"

# TEST MODE: Set to True to inject dummy job data for testing
TEST_MODE = False  # Change to True to enable test mode

def load_notified_jobs():
    """Load the set of already-notified jobs from a JSON file."""
    if NOTIFIED_JOBS_FILE.exists():
        try:
            with open(NOTIFIED_JOBS_FILE, 'r') as f:
                data = json.load(f)
                # Convert list of lists back to set of tuples
                return {tuple(job) for job in data}
        except Exception as e:
            logging.warning(f"Error loading notified jobs: {e}. Starting fresh.")
            return set()
    return set()

def save_notified_jobs(notified_jobs):
    """
    Save the set of already-notified jobs to a JSON file.
    
    Args:
        notified_jobs: Set of tuples representing notified jobs.
    """
    try:
        # Convert set of tuples to list of lists for JSON serialization
        data = [list(job) for job in notified_jobs]
        with open(NOTIFIED_JOBS_FILE, 'w') as f:
            json.dump(data, f, indent=2)
    except Exception as e:
        logging.error(f"Error saving notified jobs: {e}")

def search_and_notify_jobs(page, logger, start_date, end_date, notified_jobs, first_iteration=False):
    """
    Search for jobs, rank them, and send notifications for new top jobs.
    Returns the updated set of notified jobs.
    
    Args:
        page: Playwright page object
        logger: Logger instance
        start_date: Start date for job search
        end_date: End date for job search
        notified_jobs: Set of already-notified jobs
        first_iteration: True if this is the first search iteration (sets date filters)
    """
    # TEST MODE: Inject dummy job data for testing
    if TEST_MODE:
        logger.warning("*** TEST MODE ENABLED - Using dummy job data ***")
        possible_jobs = [
            ['12345', '09:00 AM  04:30 PM',  'LISA  MONTGOMERY', 'HS HISTORY', 'JOHN CHAMPE HIGH'],
        ]
        logger.info(f"TEST MODE: Using {len(possible_jobs)} dummy jobs")
        
        top_job = rank_jobs(possible_jobs)
        if top_job:
            logger.info(f"Top ranked job: {top_job}")
            top_job_tuple = tuple(top_job)
            if top_job_tuple in notified_jobs:
                logger.info(f"Job already notified, skipping: {top_job}")
                return notified_jobs
            
            logger.info(f"TEST MODE: Would notify about job: {top_job}")
            if should_accept_job(top_job):
                logger.info(f"TEST MODE: Job meets all high criteria - would accept job")
            else:
                logger.info(f"TEST MODE: Job does not meet all high criteria - would only notify")
            
            notified_jobs.add(top_job_tuple)
            save_notified_jobs(notified_jobs)
            logger.info(f"TEST MODE: Job notification recorded: {top_job}")
        
        return notified_jobs
    
    # Check if session expired and re-login if needed
    if is_session_expired(page):
        logger.warning("Session expired. Re-logging in...")
        login_to_website(page, logger)
        first_iteration = True
    
    # Apply date filters
    apply_date_filters(page, logger, start_date, end_date, first_iteration)
    
    # Get available jobs from table
    possible_jobs, rows = get_available_jobs_from_table(page, logger)
    
    # If info message was shown, return early
    if possible_jobs is None:
        return notified_jobs
    
    # If no jobs found, return
    if not possible_jobs:
        logger.info("No acceptable jobs found in the jobs table.")
        return notified_jobs
    
    # Rank jobs and process the top one
    top_job = rank_jobs(possible_jobs)
    if top_job:
        notified_jobs = process_and_notify_top_job(
            page, logger, top_job, rows, notified_jobs,
            save_notified_jobs, find_app_password
        )
    else:
        logger.info("No jobs to rank or accept.")
    
    return notified_jobs

def automate_website():
    """
    Automates a series of web interactions using Playwright.
    Runs in a loop every 40 seconds, maintaining the browser session.
    """
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s [%(levelname)s] %(message)s',
        handlers=[logging.StreamHandler()]
    )
    logger = logging.getLogger(__name__)

    # Get optional dates from command line
    start_date, end_date = read_dates_from_command_line()
    logger.info(f"User supplied date range: {start_date} to {end_date}")

    # Load previously notified jobs
    notified_jobs = load_notified_jobs()
    logger.info(f"Loaded {len(notified_jobs)} previously notified jobs.")

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context()
            page = context.new_page()

            # Login once before the loop
            login_to_website(page, logger)

            logger.info("Starting periodic job search loop (40 second interval). Press Ctrl+C to stop.")
            
            try:
                iteration_count = 0
                while True:
                    iteration_count += 1
                    logger.info(f"=== Starting search iteration #{iteration_count} ===")
                    is_first = (iteration_count == 1)
                    
                    try:
                        notified_jobs = search_and_notify_jobs(page, logger, start_date, end_date, notified_jobs, first_iteration=is_first)
                    except (PlaywrightTimeoutError, TargetClosedError) as e:
                        logger.warning(f"Timeout or target closed error during search: {e}")
                        logger.info("Checking if session expired...")
                        
                        # Check if we're on the login page
                        if is_session_expired(page):
                            logger.warning("Session expired detected. Re-logging in and retrying...")
                            login_to_website(page, logger)
                            # Retry the search with first_iteration=True to re-apply filters
                            try:
                                notified_jobs = search_and_notify_jobs(page, logger, start_date, end_date, notified_jobs, first_iteration=True)
                                logger.info("Successfully recovered from session expiration.")
                            except Exception as retry_error:
                                logger.error(f"Failed to recover from session expiration: {retry_error}")
                        else:
                            # Not a session issue, navigate to login anyway as a safety measure
                            logger.warning("Not on login page but got timeout. Forcing re-login as safety measure...")
                            page.goto(WEBSITE_URL)
                            login_to_website(page, logger)
                            try:
                                notified_jobs = search_and_notify_jobs(page, logger, start_date, end_date, notified_jobs, first_iteration=True)
                                logger.info("Successfully recovered after forced re-login.")
                            except Exception as retry_error:
                                logger.error(f"Failed to recover after forced re-login: {retry_error}")
                    
                    logger.info("=== Search iteration complete ===")
                    logger.info("Sleeping for 40 seconds...")
                    time.sleep(40)
            except KeyboardInterrupt:
                logger.info("\nStopped by user.")

            logger.info("Closing the browser.")
            try:
                context.close()
                browser.close()
            except Exception as e:
                logger.debug(f"Browser cleanup error (can be ignored): {e}")
    except Exception as e:
        logger.error(f"An unexpected error occurred: {e}", exc_info=True)

if __name__ == "__main__":
    automate_website()