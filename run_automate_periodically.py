#!/usr/bin/env python3
"""
run_automate_periodically.py

This script accepts two date arguments in MM/DD/YYYY format and runs the AutomateSmartFind.py script
with those dates as arguments, repeating every 20 seconds.

Usage:
    python run_automate_periodically.py "01/05/2026" "01/09/2026"

The script will run indefinitely until interrupted (Ctrl+C).
"""

import sys
import time
import subprocess
import datetime

def validate_date(date_str):
    """Validate that the date string is in MM/DD/YYYY format."""
    try:
        datetime.datetime.strptime(date_str, "%m/%d/%Y")
        return True
    except ValueError:
        return False

def main():
    if len(sys.argv) != 3:
        print("Usage: python run_automate_periodically.py \"MM/DD/YYYY\" \"MM/DD/YYYY\"")
        sys.exit(1)

    start_date = sys.argv[1]
    end_date = sys.argv[2]

    if not validate_date(start_date):
        print(f"Invalid start date format: {start_date}. Expected MM/DD/YYYY.")
        sys.exit(1)

    if not validate_date(end_date):
        print(f"Invalid end date format: {end_date}. Expected MM/DD/YYYY.")
        sys.exit(1)

    print(f"Starting periodic execution with dates: {start_date} to {end_date}")
    print("Press Ctrl+C to stop.")

    try:
        while True:
            print(f"Running: python .\\AutomateSmartFind.py \"{start_date}\" \"{end_date}\"")
            result = subprocess.run([
                "python", ".\\AutomateSmartFind.py", start_date, end_date
            ], capture_output=True, text=True)
            
            # Always print the output from AutomateSmartFind.py
            if result.stdout:
                print("STDOUT:")
                print(result.stdout)
            if result.stderr:
                print("STDERR:")
                print(result.stderr)
            
            if result.returncode != 0:
                print(f"Command failed with return code {result.returncode}")
            else:
                print("Command executed successfully.")
            
            print("Sleeping for 40 seconds...")
            time.sleep(40)
    except KeyboardInterrupt:
        print("\nStopped by user.")

if __name__ == "__main__":
    main()