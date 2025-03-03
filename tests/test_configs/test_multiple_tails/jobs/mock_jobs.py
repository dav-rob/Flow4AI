import jobchain.jc_logging as logging
from jobchain.job import JobABC
from typing import Dict, Any, Union

logger = logging.getLogger(__name__)

class DataIngestionJob(JobABC):
    """Job for ingesting data from a source."""
    async def run(self, task) -> Dict[str, Any]:
        """Execute the job on the given task."""
        logger.debug(f"{self.name}: Processing data from {self.properties.get('source')} with batch size {self.properties.get('batch')}")
        result = {
            "source": self.properties.get('source'),
            "batch": self.properties.get('batch'),
            "records_processed": 1000,
            "status": "success"
        }
        logger.info(f"{self.name}: Completed data ingestion with result: {result}")
        return result

class DataSamplingJob(JobABC):
    """Job for sampling data from a source."""
    async def run(self, task) -> Dict[str, Any]:
        """Execute the job on the given task."""
        logger.debug(f"{self.name}: Sampling data from {self.properties.get('source')} at rate {self.properties.get('rate')}")
        result = {
            "source": self.properties.get('source'),
            "rate": self.properties.get('rate'),
            "samples_collected": 250,
            "status": "success"
        }
        logger.info(f"{self.name}: Completed data sampling with result: {result}")
        return result

class ModelProcessorJob(JobABC):
    """Job for processing data through a model."""
    async def run(self, task) -> Dict[str, Any]:
        """Execute the job on the given task."""
        logger.debug(f"{self.name}: Processing with model {self.properties.get('model')} in {self.properties.get('validation_mode')} mode")
        # Include inputs from upstream jobs in the result
        result = {
            "model": self.properties.get('model'),
            "validation": self.properties.get('validation_mode'),
            "accuracy": 0.92,
            "status": "success"
        }
        logger.info(f"{self.name}: Completed model processing with result: {result}")
        return result

class ResultArchiverJob(JobABC):
    """Job for archiving results."""
    async def run(self, task) -> Dict[str, Any]:
        """Execute the job on the given task."""
        logger.debug(f"{self.name}: Archiving results to {self.properties.get('storage_url')}")
        result = {
            "storage_url": self.properties.get('storage_url'),
            "archived_items": 3,
            "timestamp": "2025-02-26T19:30:00Z",
            "status": "success"
        }
        logger.info(f"{self.name}: Completed archiving with result: {result}")
        return result
