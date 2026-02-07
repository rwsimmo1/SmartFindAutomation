"""
Unit tests for rank_jobs and should_accept_job functions.

Run with: pytest test_rank_and_accept_jobs.py -v
"""

import pytest
from SmartFindScripts import rank_jobs, should_accept_job


class TestRankJobs:
    """Test cases for the rank_jobs function."""
    
    def test_high_location_high_classification(self):
        """Test that a job with high location and high classification gets top ranking."""
        jobs = [
            ['12345', '09:00 AM  04:30 PM', 'John Doe', 'HS HISTORY', 'JOHN CHAMPE HIGH'],
            ['12346', '08:00 AM  03:00 PM', 'Jane Smith', 'MS MATH', 'WILLARD MIDDLE']
        ]
        result = rank_jobs(jobs)
        assert result == jobs[0], "High location + high classification should rank highest"
    
    def test_mid_location_mid_classification(self):
        """Test that mid-tier jobs rank lower than high-tier jobs."""
        jobs = [
            ['12345', '09:00 AM  04:30 PM', 'John Doe', 'MUSIC', 'WILLARD MIDDLE'],
            ['12346', '08:00 AM  03:00 PM', 'Jane Smith', 'HS HISTORY', 'JOHN CHAMPE HIGH']
        ]
        result = rank_jobs(jobs)
        assert result == jobs[1], "High tier should beat mid tier"
    
    def test_low_location_low_classification(self):
        """Test that low-tier jobs rank lowest."""
        jobs = [
            ['12345', '09:00 AM  04:30 PM', 'John Doe', 'OTHER SUBJECT', 'SOME OTHER SCHOOL'],
            ['12346', '08:00 AM  03:00 PM', 'Jane Smith', 'HS HISTORY', 'JOHN CHAMPE HIGH']
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
            ['12345', '09:00 AM  04:30 PM'],  # Only 2 columns - should be skipped
            ['12346', '08:00 AM  03:00 PM', 'Jane Smith', 'HS HISTORY', 'JOHN CHAMPE HIGH']
        ]
        result = rank_jobs(jobs)
        assert result == jobs[1], "Job with insufficient columns should be skipped"
    
    def test_multiple_high_tier_jobs_sorted_correctly(self):
        """Test that multiple high-tier jobs are sorted by score."""
        jobs = [
            ['12345', '09:00 AM  04:30 PM', 'John Doe', 'HS HISTORY', 'JOHN CHAMPE HIGH'],  # Score: 6
            ['12346', '08:00 AM  03:00 PM', 'Jane Smith', 'HS MATH', 'FREEDOM HIGH'],       # Score: 6
            ['12347', '09:00 AM  04:30 PM', 'Bob Jones', 'OTHER', 'WILLARD MIDDLE']         # Score: 4
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
            'LOUDOUN COUNTY HIGH', 'RIVERSIDE HIGH'
        ]
        
        for location in high_locations:
            jobs = [
                ['12345', '09:00 AM  04:30 PM', 'John Doe', 'HS HISTORY', location],
                ['12346', '08:00 AM  03:00 PM', 'Jane Smith', 'OTHER', 'SOME OTHER SCHOOL']
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
                ['12345', '09:00 AM  04:30 PM', 'John Doe', classification, 'JOHN CHAMPE HIGH'],
                ['12346', '08:00 AM  03:00 PM', 'Jane Smith', 'OTHER', 'SOME OTHER SCHOOL']
            ]
            result = rank_jobs(jobs)
            assert result == jobs[0], f"High classification '{classification}' should be recognized"


class TestShouldAcceptJob:
    """Test cases for the should_accept_job function."""
    
    def test_job_meets_all_high_criteria(self):
        """Test that a job meeting all high criteria returns True."""
        job = ['12345', '09:00 AM  04:30 PM', 'John Doe', 'HS HISTORY', 'JOHN CHAMPE HIGH']
        assert should_accept_job(job) is True, "Job meeting all high criteria should be accepted"
    
    def test_job_with_high_location_but_wrong_classification(self):
        """Test that high location + wrong classification returns False."""
        job = ['12345', '09:00 AM  04:30 PM', 'John Doe', 'OTHER SUBJECT', 'JOHN CHAMPE HIGH']
        assert should_accept_job(job) is False, "Job without high classification should not be accepted"
    
    def test_job_with_high_classification_but_wrong_location(self):
        """Test that high classification + wrong location returns False."""
        job = ['12345', '09:00 AM  04:30 PM', 'John Doe', 'HS HISTORY', 'SOME OTHER SCHOOL']
        assert should_accept_job(job) is False, "Job without high location should not be accepted"
    
    def test_job_with_high_criteria_but_wrong_time(self):
        """Test that high location + classification but wrong time returns False."""
        job = ['12345', '08:00 AM  03:00 PM', 'John Doe', 'HS HISTORY', 'JOHN CHAMPE HIGH']
        assert should_accept_job(job) is False, "Job without correct time range should not be accepted"
    
    def test_job_with_insufficient_columns(self):
        """Test that job with < 5 columns returns False."""
        job = ['12345', '09:00 AM  04:30 PM']
        assert should_accept_job(job) is False, "Job with < 5 columns should not be accepted"
    
    def test_job_with_partial_time_match(self):
        """Test that time range must be exact."""
        job = ['12345', '09:00 AM  03:30 PM', 'John Doe', 'HS HISTORY', 'JOHN CHAMPE HIGH']
        assert should_accept_job(job) is False, "Partial time match should not be accepted"
    
    def test_all_high_locations_accepted(self):
        """Test that all high locations work with should_accept_job."""
        high_locations = [
            'JOHN CHAMPE HIGH', 'FREEDOM HIGH', 'LIGHTRIDGE HIGH', 
            'BRIAR WOODS HIGH', 'INDEPENDENCE HIGH', 'PARK VIEW HIGH',
            'LOUDOUN COUNTY HIGH', 'RIVERSIDE HIGH'
        ]
        
        for location in high_locations:
            job = ['12345', '09:00 AM  04:30 PM', 'John Doe', 'HS HISTORY', location]
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
            job = ['12345', '09:00 AM  04:30 PM', 'John Doe', classification, 'JOHN CHAMPE HIGH']
            assert should_accept_job(job) is True, f"Job with '{classification}' should be accepted"
    
    def test_time_range_with_extra_spaces(self):
        """Test that exact time format matters (extra spaces)."""
        # The function checks for exact match "09:00 AM  04:30 PM" (2 spaces)
        job = ['12345', '09:00 AM 04:30 PM', 'John Doe', 'HS HISTORY', 'JOHN CHAMPE HIGH']  # 1 space
        assert should_accept_job(job) is False, "Time range must match exactly"
    
    def test_empty_time_range(self):
        """Test that empty or missing time range returns False."""
        job = ['12345', '', 'John Doe', 'HS HISTORY', 'JOHN CHAMPE HIGH']
        assert should_accept_job(job) is False, "Empty time range should not be accepted"
    
    def test_mid_tier_not_accepted(self):
        """Test that mid-tier location/classification doesn't meet acceptance criteria."""
        job = ['12345', '09:00 AM  04:30 PM', 'John Doe', 'MUSIC', 'WILLARD MIDDLE']
        assert should_accept_job(job) is False, "Mid-tier job should not be auto-accepted"


class TestIntegration:
    """Integration tests combining rank_jobs and should_accept_job."""
    
    def test_top_ranked_job_should_be_accepted(self):
        """Test that the top-ranked job from a list should be accepted."""
        jobs = [
            ['12345', '09:00 AM  04:30 PM', 'John Doe', 'HS HISTORY', 'JOHN CHAMPE HIGH'],
            ['12346', '08:00 AM  03:00 PM', 'Jane Smith', 'OTHER', 'SOME SCHOOL'],
            ['12347', '09:00 AM  04:30 PM', 'Bob Jones', 'MUSIC', 'WILLARD MIDDLE']
        ]
        
        top_job = rank_jobs(jobs)
        assert top_job is not None, "Should return a top job"
        assert should_accept_job(top_job) is True, "Top job should meet acceptance criteria"
    
    def test_top_ranked_without_full_criteria(self):
        """Test that top-ranked job may not always meet acceptance criteria."""
        jobs = [
            ['12345', '08:00 AM  03:00 PM', 'John Doe', 'HS HISTORY', 'JOHN CHAMPE HIGH'],  # Wrong time
            ['12346', '09:00 AM  04:30 PM', 'Jane Smith', 'OTHER', 'SOME SCHOOL']
        ]
        
        top_job = rank_jobs(jobs)
        assert top_job == jobs[0], "Should rank first job higher"
        assert should_accept_job(top_job) is False, "But it shouldn't be auto-accepted due to wrong time"


if __name__ == "__main__":
    # Allow running tests directly with: python test_rank_and_accept_jobs.py
    pytest.main([__file__, "-v", "--tb=short"])
