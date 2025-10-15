import asyncio
from playwright.sync_api import sync_playwright
import time

# Import everything needed from your main script
from SmartFindScript import (
    WEBSITE_URL, USERNAME, PASSWORD,
    USERNAME_SELECTOR, PASSWORD_SELECTOR, LOGIN_BUTTON_SELECTOR,
    TEXT_TO_READ_SELECTOR, AVAILABLE_JOBS_TAB_SELECTOR, ACTIVE_JOBS_TAB_SELECTOR,
    DATE_RANGE_SELECTOR, JOBS_TABLE_SELECTOR, BUTTON_TO_CLICK_SELECTOR,
    TEXT_TO_COPY_SELECTOR, JOB_CLASSIFICATION_INDEX_DEFAULT, JOB_LOCATION_INDEX_DEFAULT,
    ACTIVE_TABLE_ID,
    process_row, rank_jobs, accept_job, decline_job, active_jobs_tab, verify_job_active
)

def automate_website():
    """
    Automates a series of web interactions using Playwright.
    """
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context()
        page = context.new_page()

        print("Navigating to the login page...")
        page.goto(WEBSITE_URL)

        # --- Log into the page ---
        print("Logging in...")
        page.locator(USERNAME_SELECTOR).fill(USERNAME)
        page.locator(PASSWORD_SELECTOR).fill(PASSWORD)
        page.locator(LOGIN_BUTTON_SELECTOR).click()

        # --- Read text from the page ---
        print("Reading text from the page...")
        welcome_text = page.locator(TEXT_TO_READ_SELECTOR).inner_text()
        print(f"Read text: '{welcome_text}'")

        # --- Click a button to navigate ---
        print("Clicking the Available jobs tab...")
        page.locator(AVAILABLE_JOBS_TAB_SELECTOR).click()

        # --- "Copy" text by storing it in a variable ---
        print("Locating and 'copying' current date range...")
        copied_text = page.locator(DATE_RANGE_SELECTOR).inner_text()
        print(f"Date Range': '{copied_text}'")

        # --- Interact with a table ---
        print("Interacting with the jobs table...")
        page.wait_for_selector(JOBS_TABLE_SELECTOR + " tbody tr")
        jobs_table = page.locator(JOBS_TABLE_SELECTOR)
        rows = jobs_table.locator("tbody tr").all()
        if rows:
            print(f"Found {len(rows)} rows in the jobs table.")
            possible_jobs = []
            for index, row in enumerate(rows):
                cell_texts = process_row(row)
                if cell_texts:  # Only add non-empty rows
                    possible_jobs.append(cell_texts)
                else:
                    # Job was rejected based on criteria
                    # Let's decline the job by clicking on the decline button
                    # decline_job(driver, row, index)
                    print(f"Rejected job at row {index + 1}.")
            print("Possible jobs collected:", possible_jobs)
            if possible_jobs:
                # Rank the possible jobs and select the top one
                top_job = rank_jobs(possible_jobs)
                if top_job:
                    print(f"Top ranked job: {top_job}")
                    # Find the row corresponding to the top job and accept it
                    for index, row in enumerate(rows):
                        cell_texts = process_row(row)
                        if cell_texts == top_job:
                            accept_job(page, row, index)
                            active_jobs_tab(page)
                            verify_job_active(page, top_job ACTIVE_TABLE_ID)
                            break
                else:
                    print("No jobs to rank or accept.")
        else:
            print("No acceptable jobs found in the jobs table.")

        print("Closing the browser.")
        context.close()
        browser.close()

if __name__ == "__main__":
    automate_website()