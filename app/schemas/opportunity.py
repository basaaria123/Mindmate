from pydantic import BaseModel, Field

class OpportunityRequirement(BaseModel):
    skill_name: str = Field(description="A required skill for the opportunity")
    importance: str = Field(description="Importance of the skill: High, Medium, or Low")
    is_mandatory: bool = Field(description="Whether the skill is explicitly mandatory")
    description: str = Field(description="Why or how this skill is required")
    
class OpportunitySpec(BaseModel):
    opportunity_title: str = Field(description="Title of the job, internship, or other opportunity")
    organization: str | None = Field(default=None, description="Organization offering the opportunity")
    opportunity_type: str = Field(description="Type, such as job, internship, or hackathon")
    required_skills: list[OpportunityRequirement] = Field(description="Normalized requirements extracted from the source text")
    preferred_skills: list[str] = Field(description="Additional desirable skills")
    experience_level: str = Field(description="Experience level, such as beginner, intermediate, or experienced")
    summary: str = Field(description="Short summary of the opportunity")
