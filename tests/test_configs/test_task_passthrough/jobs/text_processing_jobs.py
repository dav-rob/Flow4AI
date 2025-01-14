from typing import Any, Dict, Optional

from jobchain.job import JobABC

#Head Job in test
class TextCapitalizeJob(JobABC):
    """Capitalizes input text and adds stage info"""
    
    def __init__(self, name: Optional[str] = None, properties: Dict[str, Any] = {}):
        super().__init__(name, properties)
    
    async def run(self, task: Dict[str, Any]) -> Dict[str, Any]:
        self.logger.info(f"TextCapitalizeJob received task: {task}")
        input_text = task.get('text', '')
        result = {
            'text': input_text.upper(),
            'processing_stage': 'capitalization'
        }
        self.logger.info(f"TextCapitalizeJob returning: {result}")
        return result

#Middle job in test
class TextReverseJob(JobABC):
    """Reverses the capitalized text and adds stage info"""
    
    def __init__(self, name: Optional[str] = None, properties: Dict[str, Any] = {}):
        super().__init__(name, properties)
    
    async def run(self, task: Dict[str, Any]) -> Dict[str, Any]:
        self.logger.info(f"TextReverseJob received task: {task}")
        
        # Get task data from previous job
        task_data = next(iter(task.values())) if task else {}
        
        # Check for task_pass_through key in task_data
        if 'task_pass_through' not in task_data:
            raise KeyError("Required key 'task_pass_through' not found in task")
            
        input_text = task_data.get('text', '')
        result = {
            'text': input_text[::-1],
            'processing_stage': 'reversal'
        }
        self.logger.info(f"TextReverseJob returning: {result}")
        return result


class TextWrapJob(JobABC):
    """Wraps the text in brackets and adds stage info"""
    
    def __init__(self, name: Optional[str] = None, properties: Dict[str, Any] = {}):
        super().__init__(name, properties)
    
    async def run(self, task: Dict[str, Any]) -> Dict[str, Any]:
        self.logger.info(f"TextWrapJob received task: {task}")
        
        # Get task data from previous job
        task_data = next(iter(task.values())) if task else {}
        
        # Check for task_pass_through key in task_data
        if 'task_pass_through' not in task_data:
            raise KeyError("Required key 'task_pass_through' not found in task")
            
        input_text = task_data.get('text', '')
        result = {
            'text': f"[{input_text}]",
            'processing_stage': 'wrapping'
        }
        self.logger.info(f"TextWrapJob returning: {result}")
        return result
