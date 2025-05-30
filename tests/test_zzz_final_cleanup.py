"""
Final cleanup module that runs after all other tests to ensure test artifacts are removed.
The 'zzz' prefix in the filename ensures this runs last in alphabetical order.
"""
import os
import time

import pytest

from flow4ai import f4a_logging as logging

logger = logging.getLogger(__name__)

def test_zzz_ensure_all_trace_files_cleaned():
    """
    This test ensures all trace files are properly cleaned up after all other tests have run.
    The 'zzz' prefix in the test name ensures it runs last even within this file.
    """
    logger.info("Running final OpenTelemetry trace file cleanup")
    
    # First delay to allow any pending async operations to complete
    time.sleep(2.0)
    
    # Perform direct cleanup of trace files
    test_dir = "tests"
    try:
        # Look for any temp_otel_trace files or rotated versions
        otel_files = [f for f in os.listdir(test_dir) 
                    if f.startswith("temp_otel_trace")]
        
        logger.info(f"Found {len(otel_files)} trace files to remove")
        
        for trace_file in otel_files:
            file_path = os.path.join(test_dir, trace_file)
            try:
                if os.path.exists(file_path):
                    os.unlink(file_path)
                    logger.info(f"Removed trace file: {trace_file}")
            except (FileNotFoundError, PermissionError) as e:
                logger.error(f"Error during cleanup of {trace_file}: {e}")
    except Exception as e:
        logger.error(f"Error during cleanup: {e}")
    
    # Verify all files were actually removed
    remaining = [f for f in os.listdir(test_dir) if f.startswith("temp_otel_trace")]
    
    if remaining:
        logger.warning(f"Found {len(remaining)} trace files after cleanup: {remaining}")
        # Do a second attempt with longer delay
        logger.info("Attempting final cleanup again with longer delay")
        time.sleep(5.0)
        
        # Second cleanup attempt for remaining files
        for trace_file in remaining:
            file_path = os.path.join(test_dir, trace_file)
            try:
                if os.path.exists(file_path):
                    os.unlink(file_path)
                    logger.info(f"Removed trace file in second pass: {trace_file}")
            except (FileNotFoundError, PermissionError) as e:
                logger.error(f"Error during second cleanup of {trace_file}: {e}")
        
        # Final verification
        remaining = [f for f in os.listdir(test_dir) if f.startswith("temp_otel_trace")]
        assert len(remaining) == 0, f"Cleanup failed, {len(remaining)} trace files still remain: {remaining}"
    
    logger.info("All OpenTelemetry trace files successfully cleaned up")
