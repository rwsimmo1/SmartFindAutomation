"""
Unit tests for rank_jobs and should_accept_job functions.

Run with: pytest test_rank_and_accept_jobs.py -v
"""

from datetime import datetime, timedelta

import pytest
from SmartFindScripts import rank_jobs, should_accept_job


def _smartfind_date(days_ahead: int = 0) -> str:
    """Return a SmartFind-style date string (e.g., 'Tuesday 04/07/2026')."""
    target = datetime.today() + timedelta(days=days_ahead)
    return target.strftime("%A %m/%d/%Y")


def _mid_job_date_within_window() -> str:
    """Return a date guaranteed to be within the 7-day middle-school window."""
    # Use tomorrow so datetime comparisons against "now" do not fail by time-of-day.
    return _smartfind_date(days_ahead=1)


def _mid_job_date_outside_window() -> str:
    """Return a date guaranteed to be outside the 7-day middle-school window."""
    return _smartfind_date(days_ahead=8)


def _mid_job_date_at_upper_boundary() -> str:
    """Return a date at the inclusive 7-day upper boundary for middle-school jobs."""
    return _smartfind_date(days_ahead=7)


def _mid_job_date_in_past() -> str:
    """Return a date before today, which should fail middle-school date checks."""
    return _smartfind_date(days_ahead=-1)


class TestRankJobs:
    """Test cases for the rank_jobs function."""
    
    def test_high_location_high_classification(self):
        """Test that a job with high location and high classification gets top ranking."""
        jobs = [
            ['Monday 03/02/2026', '09:00 AM  04:30 PM', 'John Doe', 'HS HISTORY', 'JOHN CHAMPE HIGH'],
            ['Tuesday 03/03/2026', '08:00 AM  03:00 PM', 'Jane Smith', 'MS MATH', 'WILLARD MIDDLE']
        ]
        result = rank_jobs(jobs)
        assert result == jobs[0], "High location + high classification should rank highest"
    
    def test_mid_location_mid_classification(self):
        """Test that mid-tier jobs rank lower than high-tier jobs."""
        jobs = [
            ['Monday 03/02/2026', '09:00 AM  04:30 PM', 'John Doe', 'MUSIC', 'WILLARD MIDDLE'],
            ['Tuesday 03/03/2026', '08:00 AM  03:00 PM', 'Jane Smith', 'HS HISTORY', 'JOHN CHAMPE HIGH']
        ]
        result = rank_jobs(jobs)
        assert result == jobs[1], "High tier should beat mid tier"
    
    def test_low_location_low_classification(self):
        """Test that low-tier jobs rank lowest."""
        jobs = [
            ['Monday 03/02/2026', '09:00 AM  04:30 PM', 'John Doe', 'OTHER SUBJECT', 'SOME OTHER SCHOOL'],
            ['Tuesday 03/03/2026', '08:00 AM  03:00 PM', 'Jane Smith', 'HS HISTORY', 'JOHN CHAMPE HIGH']
        ]
        result = rank_jobs(jobs)
        assert result == jobs[1], "High tier should beat low tier"
    
    def test_empty_jobs_list(self):
        """Test that empty list returns None."""
        result = rank_jobs([])
        assert result is None, "Empty list should return None"
    
    def test_job_with_insufficient_columns(self):
        """Test that jobs with < 5 columns are skipped."""
        jobs = [
            ['Monday 03/02/2026', '09:00 AM  04:30 PM'],  # Only 2 columns - should be skipped
            ['Tuesday 03/03/2026', '08:00 AM  03:00 PM', 'Jane Smith', 'HS HISTORY', 'JOHN CHAMPE HIGH']
        ]
        result = rank_jobs(jobs)
        assert result == jobs[1], "Job with insufficient columns should be skipped"

    def test_all_jobs_with_insufficient_columns_returns_none(self):
        """Test that rank_jobs returns None when all rows are invalid."""
        jobs = [
            ['Monday 03/02/2026'],
            ['Tuesday 03/03/2026', '08:00 AM  03:00 PM'],
            ['Wednesday 03/04/2026', '09:00 AM  04:30 PM', 'John Doe', 'HS HISTORY'],
        ]
        result = rank_jobs(jobs)
        assert result is None, "All invalid rows should produce no ranked job"
    
    def test_multiple_high_tier_jobs_sorted_correctly(self):
        """Test that multiple high-tier jobs are sorted by score."""
        jobs = [
            ['Monday 03/02/2026', '09:00 AM  04:30 PM', 'John Doe', 'HS HISTORY', 'JOHN CHAMPE HIGH'],  # Score: 6
            ['Tuesday 03/03/2026', '08:00 AM  03:00 PM', 'Jane Smith', 'HS MATH', 'FREEDOM HIGH'],      # Score: 6
            ['Wednesday 03/04/2026', '09:00 AM  04:30 PM', 'Bob Jones', 'OTHER', 'WILLARD MIDDLE']      # Score: 4
        ]
        result = rank_jobs(jobs)
        # Should return one of the first two (both have score 6)
        assert result in [jobs[0], jobs[1]], "Should return a high-scoring job"
        assert result != jobs[2], "Should not return the lower-scoring job"
    
    def test_high_location_names(self):
        """Test that all high location names are recognized."""
        high_locations = [
            'JOHN CHAMPE HIGH', 'FREEDOM HIGH', 'LIGHTRIDGE HIGH', 
            'BRIAR WOODS HIGH', 'INDEPENDENCE HIGH', 'PARK VIEW HIGH',
            'RIVERSIDE HIGH'
        ]
        
        for location in high_locations:
            jobs = [
                ['Monday 03/02/2026', '09:00 AM  04:30 PM', 'John Doe', 'HS HISTORY', location],
                ['Tuesday 03/03/2026', '08:00 AM  03:00 PM', 'Jane Smith', 'OTHER', 'SOME OTHER SCHOOL']
            ]
            result = rank_jobs(jobs)
            assert result == jobs[0], f"High location '{location}' should be recognized"
    
    def test_high_classification_names(self):
        """Test that high classification names are recognized."""
        high_classifications = [
            'HS HISTORY', 'HS GOVERNMENT', 'HS ENGLISH', 'HS MATH', 
            'HS SCIENCE', 'HS DRAMA', 'HS GERMAN'
        ]
        
        for classification in high_classifications:
            jobs = [
                ['Monday 03/02/2026', '09:00 AM  04:30 PM', 'John Doe', classification, 'JOHN CHAMPE HIGH'],
                ['Tuesday 03/03/2026', '08:00 AM  03:00 PM', 'Jane Smith', 'OTHER', 'SOME OTHER SCHOOL']
            ]
            result = rank_jobs(jobs)
            assert result == jobs[0], f"High classification '{classification}' should be recognized"


class TestShouldAcceptJob:
    """Test cases for the should_accept_job function."""
    
    def test_job_meets_all_high_criteria(self):
        """Test that a job meeting all high criteria returns True."""
        job = ['Monday 03/02/2026', '09:00 AM  04:30 PM', 'John Doe', 'HS HISTORY', 'JOHN CHAMPE HIGH']
        assert should_accept_job(job) is True, "Job meeting all high criteria should be accepted"
    
    def test_job_with_high_location_but_wrong_classification(self):
        """Test that high location + wrong classification returns False."""
        job = ['Monday 03/02/2026', '09:00 AM  04:30 PM', 'John Doe', 'OTHER SUBJECT', 'JOHN CHAMPE HIGH']
        assert should_accept_job(job) is False, "Job without high classification should not be accepted"
    
    def test_job_with_high_classification_but_wrong_location(self):
        """Test that high classification + wrong location returns False."""
        job = ['Monday 03/02/2026', '09:00 AM  04:30 PM', 'John Doe', 'HS HISTORY', 'SOME OTHER SCHOOL']
        assert should_accept_job(job) is False, "Job without high location should not be accepted"
    
    def test_job_with_high_criteria_but_wrong_time(self):
        """Test that high location + classification but wrong time returns False."""
        job = ['Monday 03/02/2026', '08:00 AM  03:00 PM', 'John Doe', 'HS HISTORY', 'JOHN CHAMPE HIGH']
        assert should_accept_job(job) is False, "Job without correct time range should not be accepted"
    
    def test_job_with_insufficient_columns(self):
        """Test that job with < 5 columns returns False."""
        job = ['Monday 03/02/2026', '09:00 AM  04:30 PM']
        assert should_accept_job(job) is False, "Job with < 5 columns should not be accepted"
    
    def test_job_with_partial_time_match(self):
        """Test that time range must be exact."""
        job = ['Monday 03/02/2026', '09:00 AM  03:30 PM', 'John Doe', 'HS HISTORY', 'JOHN CHAMPE HIGH']
        assert should_accept_job(job) is False, "Partial time match should not be accepted"
    
    def test_all_high_locations_accepted(self):
        """Test that all high locations work with should_accept_job."""
        high_locations = [
            'JOHN CHAMPE HIGH', 'FREEDOM HIGH', 'LIGHTRIDGE HIGH', 
            'BRIAR WOODS HIGH', 'INDEPENDENCE HIGH', 'PARK VIEW HIGH',
            'RIVERSIDE HIGH'
        ]
        
        for location in high_locations:
            job = ['Monday 03/02/2026', '09:00 AM  04:30 PM', 'John Doe', 'HS HISTORY', location]
            assert should_accept_job(job) is True, f"Job at '{location}' should be accepted"
    
    def test_all_high_classifications_accepted(self):
        """Test that all high classifications work with should_accept_job."""
        high_classifications = [
            'HS HISTORY', 'HS GOVERNMENT', 'HS ENGLISH', 'HS MATH', 
            'HS SCIENCE', 'HS DRAMA', 'HS INSTRUMENTAL MUSIC', 
            'HS CHORAL MUSIC', 'HS MARKETING', 'HS BUSINESS', 'HS GERMAN',
            'HS LIBRARY ASSISTANT', 'HS LIBRARIAN/MEDIA SPECIALIST',
            'HS FAMILY & CONSUMER SCIENCE', 'HS TECHNOLOGY ED'
        ]
        
        for classification in high_classifications:
            job = ['Monday 03/02/2026', '09:00 AM  04:30 PM', 'John Doe', classification, 'JOHN CHAMPE HIGH']
            assert should_accept_job(job) is True, f"Job with '{classification}' should be accepted"
    
    def test_all_mid_classifications_accepted(self):
        """Test that all mid-tier classifications work with should_accept_job."""
        mid_classifications = [
            'MS CHORAL MUSIC', 'MS MATH', 'MS LIBRARIAN', 'MS LIBRARY ASSISTANT', 'MS GERMAN',
                       'MS ENGLISH', 'MS WORLD HISTORY AND GLOBAL STUDIES'
        ]
        mid_date = _mid_job_date_within_window()
        
        for classification in mid_classifications:
            job = [mid_date, '08:00 AM  03:30 PM', 'John Doe', classification, 'WILLARD MIDDLE']
            assert should_accept_job(job) is True, f"Job with '{classification}' should be accepted"

    
    def test_time_range_with_extra_spaces(self):
        """Test that exact time format matters (extra spaces)."""
        # The function checks for exact match "09:00 AM  04:30 PM" (2 spaces)
        job = ['Monday 03/02/2026', '09:00 AM 04:30 PM', 'John Doe', 'HS HISTORY', 'JOHN CHAMPE HIGH']  # 1 space
        assert should_accept_job(job) is False, "Time range must match exactly"
    
    def test_empty_time_range(self):
        """Test that empty or missing time range returns False."""
        job = ['Monday 03/02/2026', '', 'John Doe', 'HS HISTORY', 'JOHN CHAMPE HIGH']
        assert should_accept_job(job) is False, "Empty time range should not be accepted"
    
    def test_mid_tier_not_accepted(self):
        """Test that mid-tier location/classification doesn't meet acceptance criteria."""
        job = ['Monday 03/02/2026', '09:00 AM  04:30 PM', 'John Doe', 'MUSIC', 'WILLARD MIDDLE']
        assert should_accept_job(job) is False, "Middle school job should not be auto-accepted with high school time criteria"

    def test_all_mid_locations_accepted(self):
        """Test that all high locations work with should_accept_job."""
        mid_locations = [
            'WILLARD MIDDLE', 'GUM SPRING MIDDLE', 'LUNSFORD MIDDLE'
        ]
        mid_date = _mid_job_date_within_window()
        
        for location in mid_locations:
            job = [mid_date, '08:00 AM  03:30 PM', 'John Doe', 'MS MATH', location]
            assert should_accept_job(job) is True, f"Job at '{location}' should be accepted"

    def test_mid_job_outside_date_window_rejected(self):
        """Test that a middle-school job outside the 7-day window is rejected."""
        job = [
            _mid_job_date_outside_window(),
            '08:00 AM  03:30 PM',
            'John Doe',
            'MS MATH',
            'WILLARD MIDDLE',
        ]
        assert should_accept_job(job) is False, (
            "Middle-school jobs beyond the 7-day window should be rejected"
        )

    def test_mid_job_today_is_accepted(self):
        """Test that middle-school jobs dated today are accepted."""
        job = [
            _smartfind_date(days_ahead=0),
            '08:00 AM  03:30 PM',
            'John Doe',
            'MS MATH',
            'WILLARD MIDDLE',
        ]
        assert should_accept_job(job) is True, "Today should be inside the inclusive mid-date window"

    def test_mid_job_at_upper_boundary_is_accepted(self):
        """Test that middle-school jobs dated exactly 7 days ahead are accepted."""
        job = [
            _mid_job_date_at_upper_boundary(),
            '08:00 AM  03:30 PM',
            'John Doe',
            'MS MATH',
            'WILLARD MIDDLE',
        ]
        assert should_accept_job(job) is True, "Upper boundary day should be included"

    def test_mid_job_in_past_is_rejected(self):
        """Test that middle-school jobs dated before today are rejected."""
        job = [
            _mid_job_date_in_past(),
            '08:00 AM  03:30 PM',
            'John Doe',
            'MS MATH',
            'WILLARD MIDDLE',
        ]
        assert should_accept_job(job) is False, "Past dates should be outside the mid-date window"

    def test_mid_job_with_mmddyyyy_date_format_is_accepted(self):
        """Test that middle-school jobs using MM/DD/YYYY format are accepted when in range."""
        date_str = (datetime.today() + timedelta(days=1)).strftime("%m/%d/%Y")
        job = [date_str, '08:00 AM  03:30 PM', 'John Doe', 'MS MATH', 'WILLARD MIDDLE']
        assert should_accept_job(job) is True, "MM/DD/YYYY format should be parsed correctly"

    def test_mid_job_with_invalid_date_format_is_rejected(self):
        """Test that invalid date formats are rejected for middle-school jobs."""
        job = ['2026-04-03', '08:00 AM  03:30 PM', 'John Doe', 'MS MATH', 'WILLARD MIDDLE']
        assert should_accept_job(job) is False, "Invalid date format should not be accepted"

    def test_mid_job_wrong_time_even_with_valid_date_is_rejected(self):
        """Test that middle-school jobs fail when time does not match."""
        job = [
            _mid_job_date_within_window(),
            '08:00 AM  03:00 PM',
            'John Doe',
            'MS MATH',
            'WILLARD MIDDLE',
        ]
        assert should_accept_job(job) is False, "Mid-tier jobs still require exact middle-school time"

    def test_high_tier_job_acceptance_does_not_depend_on_date(self):
        """Test that high-tier acceptance ignores date window constraints."""
        job = ['Monday 01/01/1990', '09:00 AM  04:30 PM', 'John Doe', 'HS HISTORY', 'JOHN CHAMPE HIGH']
        assert should_accept_job(job) is True, "High-tier path should not require mid-date window"


class TestIntegration:
    """Integration tests combining rank_jobs and should_accept_job."""
    
    def test_top_ranked_job_should_be_accepted(self):
        """Test that the top-ranked job from a list should be accepted."""
        jobs = [
            ['Monday 03/02/2026', '09:00 AM  04:30 PM', 'John Doe', 'HS HISTORY', 'JOHN CHAMPE HIGH'],
            ['Tuesday 03/03/2026', '08:00 AM  03:00 PM', 'Jane Smith', 'OTHER', 'SOME SCHOOL'],
            ['Wednesday 03/04/2026', '09:00 AM  04:30 PM', 'Bob Jones', 'MUSIC', 'WILLARD MIDDLE']
        ]
        
        top_job = rank_jobs(jobs)
        assert top_job is not None, "Should return a top job"
        assert should_accept_job(top_job) is True, "Top job should meet acceptance criteria"
    
    def test_top_ranked_without_full_criteria(self):
        """Test that top-ranked job may not always meet acceptance criteria."""
        jobs = [
            ['Monday 03/02/2026', '08:00 AM  03:00 PM', 'John Doe', 'HS HISTORY', 'JOHN CHAMPE HIGH'],  # Wrong time
            ['Tuesday 03/03/2026', '09:00 AM  04:30 PM', 'Jane Smith', 'OTHER', 'SOME SCHOOL']
        ]
        
        top_job = rank_jobs(jobs)
        assert top_job == jobs[0], "Should rank first job higher"
        assert should_accept_job(top_job) is False, "But it shouldn't be auto-accepted due to wrong time"


if __name__ == "__main__":
    # Allow running tests directly with: python test_rank_and_accept_jobs.py
    pytest.main([__file__, "-v", "--tb=short"])
