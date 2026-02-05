# First, you need to install the required libraries:
# pip install playwright python-dotenv keyring

import time
import os
import sys
import logging
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv
import keyring
from datetime import datetime

load_dotenv()

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

# Define constants for the website and user credentials
WEBSITE_URL = os.getenv("SMARTFIND_WEBSITE_URL")
# Prefer project-specific env vars to avoid colliding with OS-level USERNAME on Windows
USERNAME = os.getenv("SMARTFIND_USERNAME")  # or None
# retrieve password from Windows Credential Manager:
PASSWORD = keyring.get_password("SmartFind", USERNAME)

if PASSWORD is None:
    raise RuntimeError("Password not found in keyring for service 'SmartFind' and username: " + str(USERNAME))

# Log a masked username for diagnostics (don't log full secrets)
if USERNAME:
    masked = USERNAME if len(USERNAME) <= 3 else USERNAME[:3] + "***"
    logger.info(f"Using username: {masked}")

# Define selectors for Playwright (as strings)
USERNAME_SELECTOR = "#userId"
PASSWORD_SELECTOR = "#userPin"
LOGIN_BUTTON_SELECTOR = "#submitBtn"
TEXT_TO_READ_SELECTOR = "#desktop-header.pds-page-head"
MESSAGE_OVERLAY_SELECTOR = ".pds-message-content span"
INFO_MESSAGE_OVERLAY_SELECTOR = "div.pds-message-info"
AVAILABLE_JOBS_TAB_SELECTOR = "#available-tab-link"
ACTIVE_JOBS_TAB_SELECTOR = "#active-tab-link"
DATE_RANGE_SELECTOR = ".banner-custom.hide-buttons .text"
JOBS_TABLE_SELECTOR = "#parent-table-desktop-available"
BUTTON_TO_CLICK_SELECTOR = "button:has-text('Next Page')"
TEXT_TO_COPY_SELECTOR = ".article-content p:first-of-type"
ACTIVE_TABLE_ID = "parent-table-desktop-active"
JOB_CLASSIFICATION_INDEX_DEFAULT = 3
JOB_LOCATION_INDEX_DEFAULT = 4
DATE_FILTER_BUTTON_SELECTOR = "#date-header > pds-icon"
# DATE_RANGE_BUTTON_SELECTOR = "#date-type-range-option-0"
DATE_RANGE_BUTTON_SELECTOR = "text=Date Range"
START_DATE_INPUT_SELECTOR = "#start-date-filter-input"
END_DATE_INPUT_SELECTOR = "#end-date-filter-input"
APPLY_FILTER_BUTTON_SELECTOR = "#apply-filter"

def read_dates_from_command_line():
    """
    Reads start_date and end_date from the command line in MM/DD/YYYY format.
    Returns:
        (start_date, end_date): Tuple of datetime.date objects, (None, None) if no dates provided.
    Raises:
        ValueError: If the dates are provided but in wrong format.
    """
    if len(sys.argv) < 3:
        return None, None
    start_str = sys.argv[1]
    end_str = sys.argv[2]
    try:
        start_date = datetime.strptime(start_str, "%m/%d/%Y").date()
        end_date = datetime.strptime(end_str, "%m/%d/%Y").date()
    except ValueError:
        raise ValueError("Dates must be in MM/DD/YYYY format.")
    return start_date, end_date

def rank_jobs(possible_jobs):
    """
    Ranks jobs based on location and classification, and returns the top ranked job.
 
    Args:
        possible_jobs: List of job rows, where each row is a list of cell texts.

    Returns:
        The top ranked job (list of cell texts) or None if no jobs are available.
    """
    # Define ranking groups
    high_locations = {"JOHN CHAMPE HIGH", "FREEDOM HIGH", "LIGHTRIDGE HIGH", "BRIAR WOODS HIGH", "INDEPENDENCE HIGH",
                      "PARK VIEW HIGH", "LOUDOUN COUNTY HIGH", "RIVERSIDE HIGH", "BRIAR WOODS HIGH"}
    mid_locations = {"WILLARD", "GUM SPRING", "LUNSFORD"}
    high_classifications = {"HS HISTORY", "HS GOVERNMENT", "HS ENGLISH", "HS MATH", "HS SCIENCE", "HS DRAMA", 
                            "HS INSTRUMENTAL MUSIC", "HS CHORAL MUSIC", "HS MARKETING", "HS BUSINESS", "HS GERMAN",
                            "HS LIBRARY ASSISTANT", "HS LIBRARIAN/MEDIA SPECIALIST", "HS FAMILY & CONSUMER SCIENCE",
                            "HS TECHNOLOGY ED"}
    mid_classifications = {"MUSIC", "DRAMA", "LIBRARY", "LIBRARIAN", "GERMAN"}
    high_time_range = "09:00 AM  04:30 PM"

    ranked_jobs = []

    for job in possible_jobs:
        # Defensive: Ensure job has enough columns
        if len(job) < 4:
            continue

        location = job[3]
        classification = job[2]

        # Location ranking
        if any(loc in location for loc in high_locations):
            location_score = 3
        elif any(loc in location for loc in mid_locations):
            location_score = 2
        else:
            location_score = 1

        # Classification ranking
        if any(cls in classification for cls in high_classifications):
            classification_score = 3
        elif any(cls in classification for cls in mid_classifications):
            classification_score = 2
        else:
            classification_score = 1

        # Combined score
        total_score = location_score + classification_score
        ranked_jobs.append((total_score, job))

    # Sort jobs by score descending, return the top ranked job
    if ranked_jobs:
        ranked_jobs.sort(reverse=True, key=lambda x: x[0])
        return ranked_jobs[0][1]
    else:
        return None

def click_reason_radio_button(page, label_text):
    """
    Clicks a radio button based on its label text.
    
    Args:
        page: Playwright page object.
        label_text: The text label of the radio button to click.

    Returns:
        None
    """
    # Find all <li> elements inside the radio button list
    radio_items = page.locator("ul li")
    count = radio_items.count()
    for i in range(count):
        item = radio_items.nth(i)
        if label_text in item.inner_text():
            item.click()
            print(f'Clicked the "{label_text}" radio button.')
            break

def decline_job(page, row, index):
    """
    Declines a job by clicking the decline button and confirming the action.

    Args:
        page: Playwright page object.  
        row: Playwright locator for the table row.
        index: Index of the row (for logging purposes).

    Returns:
        None
    """
    decline_button = row.locator(".decline-icon")
    decline_button.click()
    page.wait_for_selector("header h4")
    header_text = page.locator("header h4").inner_text()
    print(f"Popup Header Text: {header_text}")
    click_reason_radio_button(page, "PERSONAL 2")
    confirm_decline_button = page.locator("#confirm-dialog")
    confirm_decline_button.click()
    print(f"Declined job at row {index + 1}.")

def accept_job(page, row, index):
    """
    Accepts a job by clicking the accept button and confirming the action.

    Args:
        page: Playwright page object.
        row: Playwright locator for the table row.
        index: Index of the row (for logging purposes).
    Returns:
        None
    """
    accept_button = row.locator(".accept-icon")
    accept_button.click()
    page.wait_for_selector("header h4")
    header_text = page.locator("header h4").inner_text()
    print(f"Popup Header Text: {header_text}")
    confirm_accept_button = page.locator("#confirm-dialog")
    confirm_accept_button.click()
    page.wait_for_selector(MESSAGE_OVERLAY_SELECTOR)
    message_text = page.locator(MESSAGE_OVERLAY_SELECTOR).inner_text()
    print(f"Message Overlay Text: {message_text}")
    print(f"Accepted job at row {index + 1}.")

def process_row(row):
    """
    Process a table row and return its cell texts if job is not rejected,
    otherwise return an empty list.

    Args:
        row: Playwright locator for the table row.
    
    Returns:
        List of cell texts if job is acceptable, else empty list.
    """
    return_row = True
    cells = row.locator("td")
    count = cells.count()
    cell_texts = [cells.nth(i).inner_text().replace('\n', ' ') for i in range(count) if cells.nth(i).inner_text().strip() != ""]
    print(f"Row: {cell_texts}")
    # Sometimes the employee name cell is missing, so we need to adjust the indices accordingly
    job_classification_index = JOB_CLASSIFICATION_INDEX_DEFAULT
    job_location_index = JOB_LOCATION_INDEX_DEFAULT
    if len(cell_texts) < 5:
        job_classification_index = JOB_CLASSIFICATION_INDEX_DEFAULT-1
        job_location_index = JOB_LOCATION_INDEX_DEFAULT-1
    if len(cell_texts) > job_classification_index and ("SPED" or "ADAPTED PE") in cell_texts[job_classification_index]:
        print("SPED Job.")
        return_row = False
    if len(cell_texts) > job_classification_index and "MS PHYS ED" in cell_texts[job_classification_index]:
        print("MS PHYS ED Job.")
        return_row = False
    if len(cell_texts) > job_classification_index and "HS EL" in cell_texts[job_classification_index]:
        print("HS EL Job.")
        return_row = False
    if len(cell_texts) > job_location_index and "WOODGROVE HIGH" in cell_texts[job_location_index]:
        print("WOODGROVE HIGH Job.")
        return_row = False
    if return_row:
        return cell_texts
    else:
        return []
    
def active_jobs_tab(page):
    """
    Clicks the Active Jobs tab.
    Args:
        page: Playwright page object.
    Returns: None
    """
    logger.info("Clicking the Active jobs tab...")
    page.locator(ACTIVE_JOBS_TAB_SELECTOR).click()

def verify_job_active(page, job, table_id):
    """
    Verifies that the specified job is now active.
    Args:
        job: The job (list of cell texts) to verify as active.
    Returns: None
    """
    logger.info(f"Verifying that the job '{job}' is now active...")
    # Here you would add code to verify that the job is listed in the active jobs section.
    # This could involve checking for the presence of the job in a table or list.
    active_jobs_table_selector = f"#{table_id}"
    page.wait_for_selector(active_jobs_table_selector + " tbody tr")
    active_jobs_table = page.locator(active_jobs_table_selector)
    active_rows = active_jobs_table.locator("tbody tr").all()
    found = False
    for row in active_rows:
        cells = row.locator("td")
        cell_texts = [cells.nth(i).inner_text().replace('\n', ' ') for i in range(cells.count()) if cells.nth(i).inner_text().strip() != ""]
        if cell_texts == job:
            found = True
            break
    if found:
        logger.info(f"Job '{job}' is now active.")
    else:
        logger.warning(f"Job '{job}' was not found in the active jobs table.")

def send_email(to_address, subject, body, from_address=None, password=None, smtp_server="smtp.gmail.com", smtp_port=587):
    """
    Send an email to the specified address(es).
    
    Parameters:
    -----------
    to_address : str or list of str
        Recipient email address(es). If str, can be comma-separated.
    subject : str
        Email subject line
    body : str
        Email body content
    from_address : str, optional
        Sender's email address (defaults to environment variable EMAIL_ADDRESS)
    password : str, optional
        Sender's email password or app password (defaults to environment variable EMAIL_PASSWORD)
    smtp_server : str, optional
        SMTP server address (default: Gmail)
    smtp_port : int, optional
        SMTP server port (default: 587 for TLS)
    
    Returns:
    --------
    bool
        True if email sent successfully, False otherwise
    
    Example:
    --------
    # Set environment variables first:
    # export EMAIL_ADDRESS="your_email@gmail.com"
    # export EMAIL_PASSWORD="your_app_password"
    
    send_email(
        to_address="recipient@example.com",
        subject="Test Email",
        body="This is a test email."
    )
    
    # Multiple recipients:
    send_email(
        to_address="user1@example.com, user2@example.com",
        subject="Test Email",
        body="This is a test email."
    )
    """
    
    # Get credentials from parameters or environment variables
    from_address = from_address or os.getenv('EMAIL_ADDRESS')
    password = password or os.getenv('EMAIL_PASSWORD')
    
    if not from_address or not password:
        raise ValueError("Email credentials not provided. Set EMAIL_ADDRESS and EMAIL_PASSWORD environment variables or pass them as parameters.")
    
    # Parse to_address
    if isinstance(to_address, str):
        to_list = [addr.strip() for addr in to_address.split(',') if addr.strip()]
    else:
        to_list = list(to_address)
    
    if not to_list:
        raise ValueError("No valid recipient addresses provided.")
    
    try:
        # Create message
        msg = MIMEMultipart()
        msg['From'] = from_address
        msg['To'] = ", ".join(to_list)
        msg['Subject'] = subject
        
        # Attach body to email
        msg.attach(MIMEText(body, 'plain'))
        
        # Create SMTP session
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()  # Enable TLS encryption
            server.login(from_address, password)
            
            # Send email
            text = msg.as_string()
            server.sendmail(from_address, to_list, text)
        
        print(f"Email sent successfully to {', '.join(to_list)}")
        return True
        
    except smtplib.SMTPAuthenticationError:
        print("Error: Authentication failed. Check your email and password.")
        return False
    except smtplib.SMTPException as e:
        print(f"SMTP error occurred: {e}")
        return False
    except Exception as e:
        print(f"Error sending email: {e}")
        return False


