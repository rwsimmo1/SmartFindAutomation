import asyncio
from playwright.sync_api import sync_playwright
from playwright._impl._errors import TimeoutError as PlaywrightTimeoutError, TargetClosedError
import time
import logging
import json
from pathlib import Path

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
    read_dates_from_command_line, send_email, accept_job
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
    """Save the set of already-notified jobs to a JSON file."""
    try:
        # Convert set of tuples to list of lists for JSON serialization
        data = [list(job) for job in notified_jobs]
        with open(NOTIFIED_JOBS_FILE, 'w') as f:
            json.dump(data, f, indent=2)
    except Exception as e:
        logging.error(f"Error saving notified jobs: {e}")

def should_accept_job(job):
    """Check if a job meets all high criteria (location, classification, and time range).
    
    Args:
        job: List of cell texts representing a job
        
    Returns:
        True if job should be accepted automatically, False otherwise
    """
    if len(job) < 5:
        return False
    
    # Define high criteria (same as in rank_jobs)
    high_locations = {"JOHN CHAMPE HIGH", "FREEDOM HIGH", "LIGHTRIDGE HIGH", "BRIAR WOODS HIGH", "INDEPENDENCE HIGH",
                      "PARK VIEW HIGH", "LOUDOUN COUNTY HIGH", "RIVERSIDE HIGH", "BRIAR WOODS HIGH"}
    high_classifications = {"HS HISTORY", "HS GOVERNMENT", "HS ENGLISH", "HS MATH", "HS SCIENCE", "HS DRAMA", 
                            "HS INSTRUMENTAL MUSIC", "HS CHORAL MUSIC", "HS MARKETING", "HS BUSINESS", "HS GERMAN",
                            "HS LIBRARY ASSISTANT", "HS LIBRARIAN/MEDIA SPECIALIST", "HS FAMILY & CONSUMER SCIENCE",
                            "HS TECHNOLOGY ED"}
    high_time_range = "09:00 AM  04:30 PM"
    
    location = job[4]
    classification = job[3]
    time_range = job[1] if len(job) > 1 else ""
    
    # Check if all three criteria are met
    has_high_location = any(loc in location for loc in high_locations)
    has_high_classification = any(cls in classification for cls in high_classifications)
    has_high_time = high_time_range in time_range
    
    return has_high_location and has_high_classification and has_high_time

def is_session_expired(page):
    """Check if the session has expired by checking if we're on the login page."""
    try:
        current_url = page.url
        return "logOnInitAction" in current_url or "login" in current_url.lower()
    except Exception:
        return False

def login_to_website(page, logger):
    """Log into the website and return the page object."""
    logger.info("Navigating to the login page...")
    page.goto(WEBSITE_URL)

    logger.info("Logging in...")
    page.wait_for_selector(USERNAME_SELECTOR)
    username_input = page.locator(USERNAME_SELECTOR)
    username_input.fill("")
    username_input.fill(USERNAME)
    password_input = page.locator(PASSWORD_SELECTOR)
    password_input.fill("")
    password_input.fill(PASSWORD)
    page.locator(LOGIN_BUTTON_SELECTOR).click()

    logger.info("Reading text from the page...")
    welcome_text = page.locator(TEXT_TO_READ_SELECTOR).inner_text()
    logger.info(f"Read text: '{welcome_text}'")
    
    return page

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
        # Create dummy jobs with different criteria for testing
        possible_jobs = [
            ['12345', '09:00 AM  04:30 PM',  'LISA  MONTGOMERY', 'HS HISTORY', 'JOHN CHAMPE HIGH'],
           # ['12346', '08:00 AM  03:00 PM', 'AARON ROGERS', 'HS ENGLISH', 'FREEDOM HIGH'],
           # ['12347', '09:00 AM  04:30 PM', 'DAN QUINN', 'HS MATH', 'WILLARD MIDDLE'],
        ]
        logger.info(f"TEST MODE: Using {len(possible_jobs)} dummy jobs")
        
        # Skip directly to ranking and notification
        top_job = rank_jobs(possible_jobs)
        if top_job:
            logger.info(f"Top ranked job: {top_job}")
            
            # Check if we've already notified about this job
            top_job_tuple = tuple(top_job)
            if top_job_tuple in notified_jobs:
                logger.info(f"Job already notified, skipping: {top_job}")
                return notified_jobs
            
            # In test mode, we don't have real rows, so we'll simulate the notification
            logger.info(f"TEST MODE: Would notify about job: {top_job}")
            
            # Check if job should be accepted automatically
            if should_accept_job(top_job):
                logger.info(f"TEST MODE: Job meets all high criteria - would accept job")
                logger.info(f"TEST MODE: Set TEST_MODE=False and set breakpoint at line ~235 to test with real browser")
            else:
                logger.info(f"TEST MODE: Job does not meet all high criteria - would only notify")
            
            # Send actual email notification if desired in test mode
            # Uncomment below to send real email in test mode:
            # google_app_service = "SmartFindAutomationGoogleApp"
            # service_username = "SmartFindAutomation"
            # password = find_app_password(google_app_service, service_username)
            # if password:
            #     send_email(...)
            
            # Mark this job as notified
            notified_jobs.add(top_job_tuple)
            save_notified_jobs(notified_jobs)
            logger.info(f"TEST MODE: Job notification recorded: {top_job}")
        
        return notified_jobs
    
    # Check if session expired and re-login if needed
    if is_session_expired(page):
        logger.warning("Session expired. Re-logging in...")
        login_to_website(page, logger)
        # After re-login, we need to set up date filters again
        first_iteration = True
    
    if start_date is not None and end_date is not None:
        if first_iteration:
            logger.info(f"Using date range from {start_date} to {end_date}")
            # Click to open date range selector and set dates
            page.locator(DATE_FILTER_BUTTON_SELECTOR).click()
            page.locator(DATE_RANGE_BUTTON_SELECTOR).click()
            # Convert start_date and end_date to MM/DD/YYYY string format
            start_date_str = start_date.strftime("%m/%d/%Y")
            end_date_str = end_date.strftime("%m/%d/%Y")
            page.locator(START_DATE_INPUT_SELECTOR).fill(start_date_str)
            page.locator(END_DATE_INPUT_SELECTOR).fill(end_date_str)
        # Always click Apply Filter when date range is set
        page.locator(APPLY_FILTER_BUTTON_SELECTOR).click()
        
        # Wait for the success message to disappear before continuing
        logger.info("Waiting for filter success message to disappear...")
        try:
            # Wait for the specific message text to appear and then disappear
            success_message = page.get_by_text("Your Filter Setting has been modified")
            success_message.wait_for(state="visible", timeout=5000)
            # Then wait for it to disappear
            success_message.wait_for(state="hidden", timeout=10000)
            logger.info("Filter success message cleared.")
        except Exception as e:
            logger.warning(f"Could not detect/wait for success message: {e}")
        
        # If session expired during filter apply, re-login and re-apply filter
        if is_session_expired(page):
            logger.warning("Session expired after applying filter. Re-logging in...")
            login_to_website(page, logger)
            if start_date is not None and end_date is not None:
                logger.info(f"Re-applying date range from {start_date} to {end_date}")
                page.locator(DATE_FILTER_BUTTON_SELECTOR).click()
                page.locator(DATE_RANGE_BUTTON_SELECTOR).click()
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

    # --- Test for info message overlay and that it is visible ---
    try:
        info_div = page.wait_for_selector(INFO_MESSAGE_OVERLAY_SELECTOR)
    except Exception as e:
        logger.info(f"Info message overlay not found or timed out.")
        info_div = None
    
    if info_div and info_div.is_visible():
        # Display the info message and exit
        info_text = info_div.inner_text()
        logger.info(f"Info message: {info_text}")
        return notified_jobs
    
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
                logger.warning(f"Rejected job at row {index + 1}.")
        
        logger.info(f"Possible jobs collected: {possible_jobs}")
        if possible_jobs:
            # Rank the possible jobs and select the top one
            top_job = rank_jobs(possible_jobs)
            if top_job:
                logger.info(f"Top ranked job: {top_job}")
                
                # Check if we've already notified about this job
                top_job_tuple = tuple(top_job)
                if top_job_tuple in notified_jobs:
                    logger.info(f"Job already notified, skipping: {top_job}")
                    return notified_jobs
                
                # Find the row corresponding to the top job and notify about it
                for index, row in enumerate(rows):
                    cell_texts = process_row(row)
                    if cell_texts == top_job:
                        logger.info(f"Notify job at row {index + 1}: {top_job}")
                        
                        # Check if job should be accepted automatically
                        job_accepted = False
                        if should_accept_job(top_job):
                            logger.info(f"Job meets all high criteria - accepting job at row {index + 1}")
                            try:
                                accept_job(page, row, index)
                                active_jobs_tab(page)
                                verify_job_active(page, top_job, ACTIVE_TABLE_ID)
                                job_accepted = True
                                logger.info(f"Successfully accepted job: {top_job}")
                            except Exception as e:
                                logger.error(f"Error accepting job: {e}")
                        
                        google_app_service = "SmartFindAutomationGoogleApp"
                        service_username = "SmartFindAutomation"
                        password = find_app_password(google_app_service, service_username)
                        if not password:
                            logger.error("Google App password for service_username '%s' not found in Credential Manager.", 
                                    service_username)
                            logger.error("Please add it to Windows Credential Manager (use Windows Credential Manager UI or keyring.set_password) and try again.")
                            return notified_jobs
                        
                        # Construct email body
                        email_body = f"A new job has is available:\n\n{top_job}"
                        if job_accepted:
                            email_body += "\n\n✓ Job Accepted"
                        
                        send_email(
                            to_address="rwsimmo@gmail.com, simm.sean16@gmail.com",
                            subject="SmartFindAutomation: Job Available",
                            body=email_body,
                            from_address="rwsimmo@gmail.com",
                            password=password)
                        
                        # Mark this job as notified
                        notified_jobs.add(top_job_tuple)
                        save_notified_jobs(notified_jobs)
                        logger.info(f"Job notification sent and recorded: {top_job}")
                        break
            else:
                logger.info("No jobs to rank or accept.")
    else:
        logger.info("No acceptable jobs found in the jobs table.")
    
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