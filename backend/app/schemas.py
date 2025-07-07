from pydantic import BaseModel

class JobBase(BaseModel):
    title: str
    company: str
    location: str
    salary: str | None = None
    link: str
    source: str
    date_posted: str | None = None

class JobResponse(JobBase):
    id: int
    class Config:
        orm_mode = True