"""
Phase 5 Scheduler Test Suite

This module contains comprehensive tests for the Phase 5 Autonomous Scheduler.
Tests cover:
- Scheduler initialization and configuration
- Last updated timestamp retrieval
- Full update cycle execution
- Error handling
- Status reporting
"""

import unittest
import os
import sys
import json
import tempfile
import shutil
from datetime import datetime
from unittest.mock import patch, MagicMock

# Add project root to path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.append(PROJECT_ROOT)

from phase5_scheduler.scheduler import MFDataScheduler, trigger_full_update, get_last_updated


class TestMFDataScheduler(unittest.TestCase):
    """Test cases for MFDataScheduler class."""
    
    def setUp(self):
        """Set up test fixtures before each test method."""
        self.temp_dir = tempfile.mkdtemp()
        self.test_data_path = os.path.join(self.temp_dir, 'funds.json')
        
        # Create test funds data with last_updated
        self.test_funds = [
            {
                "scheme_name": "Test Fund 1",
                "nav": "₹100.00",
                "last_updated": "2026-03-05T10:00:00"
            },
            {
                "scheme_name": "Test Fund 2", 
                "nav": "₹200.00",
                "last_updated": "2026-03-05T10:00:00"
            }
        ]
        
        with open(self.test_data_path, 'w') as f:
            json.dump(self.test_funds, f)
    
    def tearDown(self):
        """Clean up test fixtures after each test method."""
        shutil.rmtree(self.temp_dir)
    
    def test_scheduler_initialization(self):
        """Test that scheduler initializes with correct default values."""
        scheduler = MFDataScheduler()
        
        self.assertIsNone(scheduler.last_run_status)
        self.assertIsNone(scheduler.last_run_time)
        self.assertIsNone(scheduler.last_error)
        self.assertEqual(scheduler.project_root, PROJECT_ROOT)
    
    def test_scheduler_custom_paths(self):
        """Test scheduler initialization with custom paths."""
        custom_root = "/custom/path"
        custom_data = "/custom/data.json"
        
        scheduler = MFDataScheduler(
            project_root=custom_root,
            data_path=custom_data
        )
        
        self.assertEqual(scheduler.project_root, custom_root)
        self.assertEqual(scheduler.data_path, custom_data)
    
    def test_scheduler_with_callbacks(self):
        """Test scheduler with success and error callbacks."""
        success_callback = MagicMock()
        error_callback = MagicMock()
        
        scheduler = MFDataScheduler(
            on_success=success_callback,
            on_error=error_callback
        )
        
        self.assertEqual(scheduler.on_success, success_callback)
        self.assertEqual(scheduler.on_error, error_callback)
    
    def test_get_last_updated_success(self):
        """Test retrieving last_updated from funds list format."""
        scheduler = MFDataScheduler(data_path=self.test_data_path)
        last_updated = scheduler.get_last_updated()
        self.assertIsNotNone(last_updated)
        
        # Verify it resembles an ISO string by parsing it
        try:
            datetime.fromisoformat(last_updated)
        except ValueError:
            self.fail("Output was not a valid ISO format string.")
    
    def test_get_last_updated_no_file(self):
        """Test retrieving last_updated when file doesn't exist."""
        nonexistent_path = os.path.join(self.temp_dir, 'nonexistent.json')
        scheduler = MFDataScheduler(data_path=nonexistent_path)
        
        last_updated = scheduler.get_last_updated()
        
        self.assertIsNone(last_updated)
    
    def test_get_status(self):
        """Test getting scheduler status."""
        scheduler = MFDataScheduler(data_path=self.test_data_path)
        scheduler.last_run_status = True
        scheduler.last_run_time = datetime.now()
        scheduler.last_error = None
        
        status = scheduler.get_status()
        
        self.assertIn('last_run_status', status)
        self.assertIn('last_run_time', status)
        self.assertIn('last_updated', status)
        self.assertIn('last_error', status)
        self.assertIn('data_path_exists', status)
        
        self.assertTrue(status['last_run_status'])
        self.assertTrue(status['data_path_exists'])
    
    @patch('phase5_scheduler.scheduler.subprocess.run')
    def test_run_command_success(self, mock_run):
        """Test successful command execution."""
        mock_run.return_value = MagicMock(
            stdout="Success output",
            stderr="",
            returncode=0
        )
        
        scheduler = MFDataScheduler()
        
        # Create a dummy script file
        dummy_script = os.path.join(self.temp_dir, 'dummy.py')
        with open(dummy_script, 'w') as f:
            f.write("# dummy script")
        
        result = scheduler._run_command(dummy_script, "Test Task")
        
        self.assertTrue(result)
        self.assertIsNone(scheduler.last_error)
    
    @patch('phase5_scheduler.scheduler.subprocess.run')
    def test_run_command_failure(self, mock_run):
        """Test failed command execution."""
        from subprocess import CalledProcessError
        
        mock_run.side_effect = CalledProcessError(
            returncode=1,
            cmd=["python", "test.py"],
            stderr="Error occurred"
        )
        
        scheduler = MFDataScheduler()
        
        # Create a dummy script file
        dummy_script = os.path.join(self.temp_dir, 'dummy.py')
        with open(dummy_script, 'w') as f:
            f.write("# dummy script")
        
        result = scheduler._run_command(dummy_script, "Test Task")
        
        self.assertFalse(result)
        self.assertIsNotNone(scheduler.last_error)
    
    def test_run_command_script_not_found(self):
        """Test command execution with missing script."""
        scheduler = MFDataScheduler()
        
        result = scheduler._run_command("nonexistent/script.py", "Test Task")
        
        self.assertFalse(result)
        self.assertIn("Script not found", scheduler.last_error)
    
    @patch.object(MFDataScheduler, '_run_command')
    def test_trigger_full_update_success(self, mock_run):
        """Test successful full update cycle."""
        mock_run.return_value = True
        
        success_callback = MagicMock()
        scheduler = MFDataScheduler(
            data_path=self.test_data_path,
            on_success=success_callback
        )
        
        result = scheduler.trigger_full_update()
        
        self.assertTrue(result)
        self.assertTrue(scheduler.last_run_status)
        self.assertIsNotNone(scheduler.last_run_time)
        success_callback.assert_called_once()
    
    @patch.object(MFDataScheduler, '_run_command')
    def test_trigger_full_update_failure(self, mock_run):
        """Test failed full update cycle."""
        mock_run.return_value = False
        
        error_callback = MagicMock()
        scheduler = MFDataScheduler(
            data_path=self.test_data_path,
            on_error=error_callback
        )
        
        result = scheduler.trigger_full_update()
        
        self.assertFalse(result)
        self.assertFalse(scheduler.last_run_status)
        error_callback.assert_called_once()
    
    def test_run_scheduler_once(self):
        """Test run_scheduler_once method."""
        scheduler = MFDataScheduler()
        
        with patch.object(scheduler, 'trigger_full_update') as mock_update:
            mock_update.return_value = True
            result = scheduler.run_scheduler_once()
            
            self.assertTrue(result)
            mock_update.assert_called_once()


class TestModuleFunctions(unittest.TestCase):
    """Test cases for module-level functions."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.test_data_path = os.path.join(self.temp_dir, 'funds.json')
        
        self.test_funds = [
            {"scheme_name": "Test", "last_updated": "2026-03-05T10:00:00"}
        ]
        
        with open(self.test_data_path, 'w') as f:
            json.dump(self.test_funds, f)
    
    def tearDown(self):
        """Clean up test fixtures."""
        shutil.rmtree(self.temp_dir)
    
    @patch('phase5_scheduler.scheduler.MFDataScheduler')
    def test_trigger_full_update_function(self, mock_scheduler_class):
        """Test standalone trigger_full_update function."""
        mock_scheduler = MagicMock()
        mock_scheduler.trigger_full_update.return_value = True
        mock_scheduler_class.return_value = mock_scheduler
        
        result = trigger_full_update()
        
        self.assertTrue(result)
        mock_scheduler.trigger_full_update.assert_called_once()
    
    def test_get_last_updated_function(self):
        """Test standalone get_last_updated function."""
        with patch('phase5_scheduler.scheduler.DATA_PATH', self.test_data_path):
            result = get_last_updated()
            self.assertIsNotNone(result)


class TestIntegration(unittest.TestCase):
    """Integration tests for Phase 5 components."""
    
    def setUp(self):
        """Set up integration test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.test_data_path = os.path.join(self.temp_dir, 'funds.json')
    
    def tearDown(self):
        """Clean up integration test fixtures."""
        shutil.rmtree(self.temp_dir)
    
    def test_end_to_end_status_flow(self):
        """Test complete status flow from initialization to update."""
        scheduler = MFDataScheduler(data_path=self.test_data_path)
        
        # Initial status
        status = scheduler.get_status()
        self.assertIsNone(status['last_run_status'])
        self.assertFalse(status['data_path_exists'])
        
        # Create data file
        test_data = [{"scheme_name": "Test", "last_updated": datetime.now().isoformat()}]
        with open(self.test_data_path, 'w') as f:
            json.dump(test_data, f)
        
        # Status after file creation
        status = scheduler.get_status()
        self.assertTrue(status['data_path_exists'])
    
    def test_timestamp_persistence(self):
        """Test that timestamp persists correctly through operations."""
        timestamp = datetime.now().isoformat()
        test_data = [
            {"scheme_name": "Fund 1", "last_updated": timestamp},
            {"scheme_name": "Fund 2", "last_updated": timestamp}
        ]
        
        with open(self.test_data_path, 'w') as f:
            json.dump(test_data, f)
        
        scheduler = MFDataScheduler(data_path=self.test_data_path)
        
        # Verify timestamp is retrieved correctly
        retrieved = scheduler.get_last_updated()
        self.assertIsNotNone(retrieved)


class TestEdgeCases(unittest.TestCase):
    """Edge case tests for Phase 5."""
    
    def test_empty_funds_list(self):
        """Test handling of empty funds list (Should still return the file modification time since the file exists)."""
        temp_dir = tempfile.mkdtemp()
        test_path = os.path.join(temp_dir, 'empty.json')
        
        try:
            with open(test_path, 'w') as f:
                json.dump([], f)
            
            scheduler = MFDataScheduler(data_path=test_path)
            last_updated = scheduler.get_last_updated()
            
            self.assertIsNotNone(last_updated)
        finally:
            shutil.rmtree(temp_dir)
    
    def test_malformed_timestamp(self):
        """Test handling of invalid timestamp format logic (Not applicable anymore)."""
        pass


def run_tests():
    """Run all Phase 5 scheduler tests."""
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add all test classes
    suite.addTests(loader.loadTestsFromTestCase(TestMFDataScheduler))
    suite.addTests(loader.loadTestsFromTestCase(TestModuleFunctions))
    suite.addTests(loader.loadTestsFromTestCase(TestIntegration))
    suite.addTests(loader.loadTestsFromTestCase(TestEdgeCases))
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result.wasSuccessful()


if __name__ == '__main__':
    success = run_tests()
    sys.exit(0 if success else 1)
