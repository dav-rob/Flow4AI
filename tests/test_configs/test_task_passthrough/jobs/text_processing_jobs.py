import asyncio
from typing import Any, Dict, Optional

import jobchain.jc_logging as logging
from jobchain.job import JobABC


#Head Job in test
class TextCapitalizeJob(JobABC):
    """Capitalizes input text and adds stage info"""
    
    def __init__(self, name: Optional[str] = None, properties: Dict[str, Any] = {}):
        super().__init__(name, properties)
    
    async def run(self, task: Dict[str, Any]) -> Dict[str, Any]:
        task_id = task.get('task_id', 'unknown')
        logging.info(f"[TASK_TRACK] TextCapitalizeJob START task_id: {task_id}")
        logging.debug(f"TextCapitalizeJob full task: {task}")
        
        input_text = task.get('text', '')
        logging.debug(f"TextCapitalizeJob input text: {input_text}")
        
        # Simulate some processing time
        await asyncio.sleep(0.01)
        
        result = {
            'text': input_text.upper(),
            'processing_stage': 'capitalization'
        }
        logging.info(f"[TASK_TRACK] TextCapitalizeJob END task_id: {task_id}")
        logging.debug(f"TextCapitalizeJob result: {result}")
        return result

#Middle job in test
class TextReverseJob(JobABC):
    """Reverses the capitalized text and adds stage info"""
    
    def __init__(self, name: Optional[str] = None, properties: Dict[str, Any] = {}):
        super().__init__(name, properties)
    
    async def run(self, task: Dict[str, Any]) -> Dict[str, Any]:
        task_id = task.get('task_id', 'unknown')
        logging.info(f"[TASK_TRACK] TextReverseJob START task_id: {task_id}")
        logging.debug(f"TextReverseJob full task: {task}")
        
        # Get task data from previous job
        task_data = next(iter(task.values())) if task else {}
        logging.debug(f"TextReverseJob task_data: {task_data}")
        
        # Check for task_pass_through key in task_data
        if 'task_pass_through' not in task_data:
            logging.error(f"[TASK_TRACK] TextReverseJob task_id: {task_id} missing task_pass_through")
            raise KeyError("Required key 'task_pass_through' not found in task")
            
        input_text = task_data.get('text', '')
        logging.debug(f"TextReverseJob input text: {input_text}")
        
        # Simulate some processing time
        await asyncio.sleep(0.01)
        
        result = {
            'text': input_text[::-1],
            'processing_stage': 'reversal'
        }
        logging.info(f"[TASK_TRACK] TextReverseJob END task_id: {task_id}")
        logging.debug(f"TextReverseJob result: {result}")
        return result


class TextWrapJob(JobABC):
    """Wraps the text in brackets and adds stage info"""
    
    def __init__(self, name: Optional[str] = None, properties: Dict[str, Any] = {}):
        super().__init__(name, properties)
    
    async def run(self, task: Dict[str, Any]) -> Dict[str, Any]:
        task_id = task.get('task_id', 'unknown')
        logging.info(f"[TASK_TRACK] TextWrapJob START task_id: {task_id}")
        logging.debug(f"TextWrapJob full task: {task}")
        
        # Get task data from previous job
        task_data = next(iter(task.values())) if task else {}
        logging.debug(f"TextWrapJob task_data: {task_data}")
        
        # Check for task_pass_through key in task_data
        if 'task_pass_through' not in task_data:
            logging.error(f"[TASK_TRACK] TextWrapJob task_id: {task_id} missing task_pass_through")
            raise KeyError("Required key 'task_pass_through' not found in task")
            
        input_text = task_data.get('text', '')
        logging.debug(f"TextWrapJob input text: {input_text}")
        
        # Simulate some processing time
        await asyncio.sleep(0.01)
        
        result = {
            'text': f"[{input_text}]",
            'processing_stage': 'wrapping'
        }
        logging.info(f"[TASK_TRACK] TextWrapJob END task_id: {task_id}")
        logging.debug(f"TextWrapJob result: {result}")
        return result
