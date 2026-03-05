"""
Phase 5: Autonomous Scheduler

Technology: APScheduler (Python) or GitHub Actions
Workflow: Automatically runs the Phase 1 scraper to ensure data freshness
and triggers RAG re-indexing.
"""

import subprocess
import sys
import os
import json
import logging
from datetime import datetime
from typing import Optional, Callable

# Get the project root directory
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_PATH = os.path.join(PROJECT_ROOT, 'data', 'funds.json')

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class MFDataScheduler:
    """
    Autonomous Scheduler for Mutual Fund Data Synchronization.
    
    This class manages the automated workflow of:
    1. Running the web scraper (Phase 1)
    2. Re-indexing the knowledge base (Phase 2)
    3. Tracking last update timestamps
    
    Attributes:
        project_root: Root directory of the project
        data_path: Path to the funds.json data file
        on_success: Optional callback function called on successful update
        on_error: Optional callback function called on error
    """
    
    def __init__(
        self,
        project_root: Optional[str] = None,
        data_path: Optional[str] = None,
        on_success: Optional[Callable] = None,
        on_error: Optional[Callable] = None
    ):
        self.project_root = project_root or PROJECT_ROOT
        self.data_path = data_path or DATA_PATH
        self.on_success = on_success
        self.on_error = on_error
        self.last_run_status: Optional[bool] = None
        self.last_run_time: Optional[datetime] = None
        self.last_error: Optional[str] = None
        
    def _run_command(self, script_rel_path: str, description: str) -> bool:
        """
        Execute a Python script and log the output.
        
        Args:
            script_rel_path: Relative path to the script from project root
            description: Human-readable description of the task
            
        Returns:
            bool: True if command succeeded, False otherwise
        """
        logger.info(f"--- Starting {description} at {datetime.now()} ---")
        script_path = os.path.join(self.project_root, script_rel_path)
        
        if not os.path.exists(script_path):
            error_msg = f"Script not found: {script_path}"
            logger.error(error_msg)
            self.last_error = error_msg
            return False
            
        try:
            result = subprocess.run(
                [sys.executable, script_path],
                check=True,
                capture_output=True,
                text=True,
                cwd=self.project_root
            )
            logger.info(result.stdout)
            logger.info(f"--- Completed {description} successfully ---")
            return True
        except subprocess.CalledProcessError as e:
            error_msg = f"Error during {description}: {e.stderr}"
            logger.error(error_msg)
            self.last_error = error_msg
            return False
    
    def get_last_updated(self) -> Optional[str]:
        """
        Get the last updated timestamp from funds.json using file modification time.
        
        Returns:
            ISO format timestamp string or None if not available
        """
        if not os.path.exists(self.data_path):
            return None
            
        try:
            mtime = os.path.getmtime(self.data_path)
            return datetime.fromtimestamp(mtime).isoformat()
        except Exception as e:
            logger.error(f"Error reading funds.json modification time: {e}")
            return None
    
    def trigger_full_update(self) -> bool:
        """
        Execute the full data synchronization cycle.
        
        This method:
        1. Runs the scraper to fetch latest fund data
        2. Re-indexes the knowledge base with new data
        
        Returns:
            bool: True if all steps completed successfully
        """
        logger.info(f"Initiating full data synchronization cycle...")
        self.last_run_time = datetime.now()
        
        # Step 1: Run Scraper (Phase 1)
        if not self._run_command("phase1_data_acquisition/scraper.py", "Phase 1: Data Scraping"):
            self.last_run_status = False
            if self.on_error:
                self.on_error(self.last_error)
            return False
            
        # Step 2: Run RAG Pipeline (Phase 2: Indexing)
        if not self._run_command("phase2_indexing/rag_pipeline.py", "Phase 2: KB Re-indexing"):
            self.last_run_status = False
            if self.on_error:
                self.on_error(self.last_error)
            return False
        
        logger.info(f"Full synchronization completed at {datetime.now()}.")
        self.last_run_status = True
        self.last_error = None
        
        if self.on_success:
            self.on_success(self.get_last_updated())
            
        return True
    
    def run_scheduler_once(self) -> bool:
        """
        Run the scheduler once (for manual or cron-based execution).
        
        Returns:
            bool: Success status of the update
        """
        return self.trigger_full_update()
    
    def get_status(self) -> dict:
        """
        Get current scheduler status.
        
        Returns:
            Dictionary with scheduler status information
        """
        return {
            "last_run_status": self.last_run_status,
            "last_run_time": self.last_run_time.isoformat() if self.last_run_time else None,
            "last_updated": self.get_last_updated(),
            "last_error": self.last_error,
            "data_path_exists": os.path.exists(self.data_path)
        }


# Legacy function for backward compatibility
def trigger_full_update() -> bool:
    """
    Standalone function to trigger a full update.
    
    Returns:
        bool: True if update succeeded
    """
    scheduler = MFDataScheduler()
    return scheduler.trigger_full_update()


def get_last_updated() -> Optional[str]:
    """
    Get the last updated timestamp from funds.json.
    
    Returns:
        ISO format timestamp or None
    """
    scheduler = MFDataScheduler()
    return scheduler.get_last_updated()


if __name__ == "__main__":
    # Run the scheduler when executed directly
    scheduler = MFDataScheduler()
    success = scheduler.trigger_full_update()
    
    # Print final status
    status = scheduler.get_status()
    print("\n" + "="*50)
    print("SCHEDULER STATUS")
    print("="*50)
    for key, value in status.items():
        print(f"{key}: {value}")
    
    sys.exit(0 if success else 1)
