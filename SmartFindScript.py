
# First, you need to install the required libraries:
# pip install playwright python-dotenv
import time
import os
from dotenv import load_dotenv

load_dotenv()

# Define constants for the website and user credentials
WEBSITE_URL = "https://loudouncountyva.eschoolsolutions.com/"
USERNAME = os.getenv("USERNAME")
PASSWORD = os.getenv("PASSWORD")

# Define selectors for Playwright (as strings)
USERNAME_SELECTOR = "#userId"
PASSWORD_SELECTOR = "#userPin"
LOGIN_BUTTON_SELECTOR = "#submitBtn"
TEXT_TO_READ_SELECTOR = "#desktop-header.pds-page-head"
# MESSAGE_OVERLAY_SELECTOR = "div.pds-overlay"
MESSAGE_OVERLAY_SELECTOR = ".pds-message-content span"
AVAILABLE_JOBS_TAB_SELECTOR = "#available-tab-link"
ACTIVE_JOBS_TAB_SELECTOR = "#active-tab-link"
DATE_RANGE_SELECTOR = ".banner-custom.hide-buttons .text"
JOBS_TABLE_SELECTOR = "#parent-table-desktop-available"
BUTTON_TO_CLICK_SELECTOR = "button:has-text('Next Page')"
TEXT_TO_COPY_SELECTOR = ".article-content p:first-of-type"
ACTIVE_TABLE_ID = "parent-table-desktop-active"
JOB_CLASSIFICATION_INDEX_DEFAULT = 3
JOB_LOCATION_INDEX_DEFAULT = 4

def rank_jobs(possible_jobs):
    """
    Ranks jobs based on location and classification, and returns the top ranked job.
 
    Args:
        possible_jobs: List of job rows, where each row is a list of cell texts.

    Returns:
        The top ranked job (list of cell texts) or None if no jobs are available.
    """
    # Define ranking groups
    high_locations = {"CHAMPE", "FREEDOM", "LTGHTRIDGE"}
    mid_locations = {"WILLARD", "GUM SPRING", "LUNSFORD"}
    high_classifications = {"HISTORY"}
    mid_classifications = {"MUSIC", "DRAMA", "LIBRARY", "LIBRARIAN", "GERMAN"}

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
    if len(cell_texts) > job_classification_index and "SPED" in cell_texts[job_classification_index]:
        print("SPED Job.")
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
    print("Clicking the Active jobs tab...")
    page.locator(ACTIVE_JOBS_TAB_SELECTOR).click()

def verify_job_active(page, job, table_id):
    """
     Verifies that the specified job is now active.
     
     Args:
         top_job: The job (list of cell texts) to verify as active.

     Returns: None
     """
    print(f"Verifying that the job '{job}' is now active...")
    # Here you would add code to verify that the job is listed in the active jobs section.
    # This could involve checking for the presence of the job in a table or list.
    
    # Select the active jobs table
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
        print(f"Job '{job}' is now active.")
    else:
        print(f"Job '{job}' is NOT active.")
