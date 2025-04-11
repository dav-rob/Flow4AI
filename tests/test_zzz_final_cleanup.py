"""
Final cleanup module that runs after all other tests to ensure test artifacts are removed.
The 'zzz' prefix in the filename ensures this runs last in alphabetical order.
"""
import os
import time
import pytest

from jobchain import jc_logging as logging
from tests.test_opentelemetry import force_cleanup_all_trace_files

logger = logging.getLogger(__name__)

def test_zzz_ensure_all_trace_files_cleaned():
    """
    This test ensures all trace files are properly cleaned up after all other tests have run.
    The 'zzz' prefix in the test name ensures it runs last even within this file.
    """
    logger.info("Running final OpenTelemetry trace file cleanup")
    
    # First delay to allow any pending async operations to complete
    time.sleep(2.0)
    
    # Perform the aggressive cleanup
    force_cleanup_all_trace_files()
    
    # Verify all files were actually removed
    test_dir = "tests"
    remaining = [f for f in os.listdir(test_dir) if f.startswith("temp_otel_trace")]
    
    if remaining:
        logger.warning(f"Found {len(remaining)} trace files after cleanup: {remaining}")
        # Do a second attempt with longer delay
        logger.info("Attempting final cleanup again with longer delay")
        time.sleep(5.0)
        force_cleanup_all_trace_files()
        
        # Final verification
        remaining = [f for f in os.listdir(test_dir) if f.startswith("temp_otel_trace")]
        assert len(remaining) == 0, f"Cleanup failed, {len(remaining)} trace files still remain: {remaining}"
    
    logger.info("All OpenTelemetry trace files successfully cleaned up")
