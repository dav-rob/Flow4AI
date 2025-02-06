from pydantic import BaseModel
from typing import List, Optional

class UserProfile(BaseModel):
    """User profile data model"""
    username: str
    email: str
    full_name: str
    age: Optional[int] = None

class JobMetadata(BaseModel):
    """Job metadata model"""
    job_id: str
    status: str
    created_at: str
    updated_at: Optional[str] = None
    tags: List[str] = []

class TaskConfig(BaseModel):
    """Task configuration model"""
    task_name: str
    priority: int
    max_retries: int = 3
    timeout_seconds: int = 300
    dependencies: List[str] = []
