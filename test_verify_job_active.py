import unittest
from unittest.mock import MagicMock
from SmartFindScript import verify_job_active

class TestVerifyJobActive(unittest.TestCase):
    job = ['Thursday  10/09/2025', '08:20 AM  03:50 PM', 'Tracey-Jane  Milligan-Orwig', 'MS ENGLISH', 'GUM SPRING MIDDLE']
    def test_verify_job_active_job_found(self):
        # Arrange
        mock_page = MagicMock()
        job = self.job
        table_id = 'parent-table-desktop-active'
        
        # Mock the table and rows
        mock_row = MagicMock()
        mock_cells = [MagicMock(), MagicMock(), MagicMock(), MagicMock(), MagicMock()]
        # Set up cell inner_texts to match job
        for i, cell in enumerate(mock_cells):
            cell.inner_text.return_value = job[i]
            cell.text_content.return_value = job[i]
        mock_row.locator.return_value.count.return_value = len(job)
        mock_row.locator.return_value.nth.side_effect = lambda i: mock_cells[i]
        mock_row.locator.return_value.__iter__.return_value = iter(mock_cells)
        
        mock_table = MagicMock()
        mock_table.locator.return_value.all.return_value = [mock_row]
        mock_page.locator.return_value = mock_table
        mock_page.wait_for_selector.return_value = None
        
        # Act
        verify_job_active(mock_page, job, table_id)
        
        # Assert
        mock_page.wait_for_selector.assert_called_with(f"#{table_id} tbody tr")
        mock_page.locator.assert_called_with(f"#{table_id}")
        self.assertTrue(any(cell.inner_text() == job[i] for i, cell in enumerate(mock_cells)))

    def test_verify_job_active_job_not_found(self):
        # Arrange
        mock_page = MagicMock()
        job = self.job
        table_id = 'parent-table-desktop-active'
        
        # Mock the table and rows with a different job
        mock_row = MagicMock()
        mock_cells = [MagicMock(), MagicMock(), MagicMock(), MagicMock(), MagicMock()]
        # Set up cell inner_texts to NOT match job
        for i, cell in enumerate(mock_cells):
            cell.inner_text.return_value = f"not_{job[i]}"
            cell.text_content.return_value = f"not_{job[i]}"
        mock_row.locator.return_value.count.return_value = len(job)
        mock_row.locator.return_value.nth.side_effect = lambda i: mock_cells[i]
        mock_row.locator.return_value.__iter__.return_value = iter(mock_cells)
        
        mock_table = MagicMock()
        mock_table.locator.return_value.all.return_value = [mock_row]
        mock_page.locator.return_value = mock_table
        mock_page.wait_for_selector.return_value = None
        
        # Act
        verify_job_active(mock_page, job, table_id)
        
        # Assert
        mock_page.wait_for_selector.assert_called_with(f"#{table_id} tbody tr")
        mock_page.locator.assert_called_with(f"#{table_id}")
        self.assertFalse(any(cell.inner_text() == job[i] for i, cell in enumerate(mock_cells)))

if __name__ == "__main__":
    unittest.main()
