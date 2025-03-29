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
        inputs = self.get_inputs()
        task_id = inputs.get('task_id', 'unknown')
        logging.info(f"[TASK_TRACK] TextCapitalizeJob START task_id: {task_id}")
        logging.debug(f"TextCapitalizeJob full task: {inputs}")
        
        input_text = inputs.get('text', '')
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
        inputs = self.get_inputs()
        logging.debug(f"TextReverseJob full task: {inputs}")
        
        # Get task data from previous job
        input_data = next(iter(inputs.values())) if inputs else {}
        logging.debug(f"TextReverseJob task_data: {input_data}")
        
        # Check for task_pass_through key in task_data
        task = self.get_task()
        if not task:
            logging.error(f"[TASK_TRACK] TextReverseJob missing task_pass_through")
            raise KeyError("Required key 'task_pass_through' not found in task")
            
        input_text = input_data.get('text', '')
        logging.debug(f"TextReverseJob input text: {input_text}")
        
        # Simulate some processing time
        await asyncio.sleep(0.01)
        
        result = {
            'text': input_text[::-1],
            'processing_stage': 'reversal'
        }
        logging.info(f"[TASK_TRACK] TextReverseJob END")
        logging.debug(f"TextReverseJob result: {result}")
        return result


class TextWrapJob(JobABC):
    """Wraps the text in brackets and adds stage info"""
    
    def __init__(self, name: Optional[str] = None, properties: Dict[str, Any] = {}):
        super().__init__(name, properties)
    
    async def run(self, task: Dict[str, Any]) -> Dict[str, Any]:
        inputs = self.get_inputs()
        logging.debug(f"TextWrapJob full task: {inputs}")
        
        # Get task data from previous job
        input_data = next(iter(inputs.values())) if inputs else {}
        logging.debug(f"TextWrapJob task_data: {input_data}")
        
        # Check for task_pass_through key in task_data
        task = self.get_task()
        if not task:
            logging.error(f"[TASK_TRACK] TextWrapJob missing task_pass_through")
            raise KeyError("Required key 'task_pass_through' not found in task")
            
        input_text = input_data.get('text', '')
        logging.debug(f"TextWrapJob input text: {input_text}")
        
        # Simulate some processing time
        await asyncio.sleep(0.01)
        
        result = {
            'text': f"[{input_text}]",
            'processing_stage': 'wrapping'
        }
        logging.info(f"[TASK_TRACK] TextWrapJob END")
        logging.debug(f"TextWrapJob result: {result}")
        return result
