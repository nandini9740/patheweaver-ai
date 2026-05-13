from pydantic import BaseModel
from typing import List, Optional

class CourseInput(BaseModel):
    topic: str
    skill_level: str
    hours_per_week: int
    learning_style: str
    goal: str

class ModuleSchema(BaseModel):
    module_number: int
    title: str
    duration: str
    objectives: List[str]
    topics: List[str]
    resources: List[str]
    exercise: str
    mini_project: Optional[str] = None
    visual_aid: Optional[str] = None # Description or URL for a mind map, diagram, etc.
    quiz_questions: List[str]

class CourseOutput(BaseModel):
    course_title: str
    overview: str
    estimated_duration: str
    modules: List[ModuleSchema]

class CourseResponse(BaseModel):
    status: str
    id: str
    course: CourseOutput
    is_fallback: bool = False
    fallback_type: Optional[str] = None
