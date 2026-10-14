
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from app.agents.profile_agent import extract_user_profile
from app.agents.opportunity_agent import extract_opportunity
from app.agents.fit_agent import assess_fit


class ProfileRequest(BaseModel):
    user_message: str = Field(
        min_length=1,
        description="The user's message for profile extraction."
    )


class OpportunityRequest(BaseModel):
    opportunity_text: str = Field(
        min_length=1,
        description="The job, internship, or opportunity description."
    )


class FitRequest(BaseModel):
    user_profile: dict
    opportunity: dict

app = FastAPI(
    title="MindMate API",
    description="AI-powered personal growth and career guidance",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def home():
    return {
        "message": "Welcome to MindMate API!",
        "status": "running",
    }


@app.get("/health")
def health_check():
    return {
        "status": "healthy",
    }


@app.post("/profile")
def create_profile(request: ProfileRequest):
    profile = extract_user_profile(request.user_message)

    return profile.model_dump()

@app.post("/opportunity")
def create_opportunity(request: OpportunityRequest):
    opportunity = extract_opportunity(request.opportunity_text)

    return opportunity.model_dump()

@app.post("/fit")
def create_fit_assessment(request: FitRequest):
    from app.schemas.profile import UserProfile
    from app.schemas.opportunity import OpportunitySpec

    user_profile = UserProfile.model_validate(request.user_profile)
    opportunity = OpportunitySpec.model_validate(request.opportunity)

    assessment = assess_fit(user_profile, opportunity)

    return assessment.model_dump()
