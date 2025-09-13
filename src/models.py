import uuid
from typing import Optional
from pydantic import BaseModel, Field
from datetime import date

class employees(BaseModel):
    employee_id : str = Field(...,  example= "E123")
    name: str = Field(..., example="John Doe")
    department: str = Field(..., example="Engineering")
    salary: float = Field(..., example=75000.00)
    joining_date: date = Field(..., example="2023-01-15")
    skills: list[str] = Field(..., example=["Python", "FastAPI", "MongoDB"])
    
class employeeUpdate(BaseModel):
    name: Optional[str] = Field(None, examples="John Doe")
    department: Optional[str] = Field(None, example="Engineering")
    salary: Optional[float] = Field(None, example=75000.00)
    joining_date: Optional[date] = Field(None, example="2023-01-15")
    skills: Optional[list[str]] = Field(None, example=["Python", "FastAPI", "MongoDB"])

