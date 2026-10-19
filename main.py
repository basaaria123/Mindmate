
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from app.agents.profile_agent import extract_user_profile
from app.agents.opportunity_agent import extract_opportunity
from app.agents.fit_agent import assess_fit
from app.agents.suggestions_agent import generate_suggestions
from app.agents.gap_agent import identify_skill_gaps
from app.agents.planner_agent import generate_plan
from app.agents.practice_agent import evaluate_practice
from app.agents.memory_agent import create_and_store_memory
from app.services.memory_store import get_memories
from app.services import offline_ai
from app.services.agent_bridge import answer_with_fallback


def _answer(agent, live, offline):
    """Nemotron when available, otherwise offline analysis; the header says which answered."""

    result, source = answer_with_fallback(agent, live, offline)
    return JSONResponse(result.model_dump(), headers={"X-MindMate-Source": source})

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

class GapRequest(BaseModel):
    user_profile: dict
    opportunity: dict
    fit_assessment: dict

class PlanRequest(BaseModel):
    user_profile: dict
    opportunity: dict
    gap_vector: dict
    goal_id: str = Field(min_length=1)
    existing_decisions: list[str] = Field(default_factory=list)

class PracticeRequest(BaseModel):
    question: str = Field(min_length=1)
    user_answer: str = Field(min_length=1)
    topic: str = Field(min_length=1)

class SuggestionsRequest(BaseModel):
    user_profile: dict

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
    return _answer(
        "profile",
        lambda: extract_user_profile(request.user_message),
        lambda: offline_ai.profile_from_text(request.user_message),
    )

@app.post("/opportunity")
def create_opportunity(request: OpportunityRequest):
    return _answer(
        "opportunity",
        lambda: extract_opportunity(request.opportunity_text),
        lambda: offline_ai.opportunity_from_text(request.opportunity_text),
    )

@app.post("/fit")
def create_fit_assessment(request: FitRequest):
    from app.schemas.profile import UserProfile
    from app.schemas.opportunity import OpportunitySpec

    user_profile = UserProfile.model_validate(request.user_profile)
    opportunity = OpportunitySpec.model_validate(request.opportunity)

    return _answer(
        "fit",
        lambda: assess_fit(user_profile, opportunity),
        lambda: offline_ai.fit_for(user_profile, opportunity),
    )

@app.post("/suggestions")
def create_suggestions(request: SuggestionsRequest):
    from app.schemas.profile import UserProfile

    user_profile = UserProfile.model_validate(request.user_profile)
    return _answer(
        "suggestions",
        lambda: generate_suggestions(user_profile),
        lambda: offline_ai.suggestions_for(user_profile),
    )

@app.post("/gap")
def create_skill_gap_assessment(request: GapRequest):
    from app.schemas.profile import UserProfile
    from app.schemas.opportunity import OpportunitySpec
    from app.schemas.fit import FitAssessment

    user_profile = UserProfile.model_validate(request.user_profile)
    opportunity = OpportunitySpec.model_validate(request.opportunity)
    fit_assessment = FitAssessment.model_validate(
        request.fit_assessment
    )

    return _answer(
        "gap",
        lambda: identify_skill_gaps(user_profile, opportunity, fit_assessment),
        lambda: offline_ai.gaps_for(user_profile, opportunity, fit_assessment),
    )

@app.post("/plan")
def create_plan(request: PlanRequest):
    from app.schemas.profile import UserProfile
    from app.schemas.opportunity import OpportunitySpec
    from app.schemas.gap import GapVectorJSON

    user_profile = UserProfile.model_validate(request.user_profile)
    opportunity = OpportunitySpec.model_validate(request.opportunity)
    gap_vector = GapVectorJSON.model_validate(request.gap_vector)

    memories = get_memories()

    # Decisions and memory IDs from the database memory layer, so the planner
    # can cite them and its reference check accepts them.
    from app.services.agent_bridge import database_planner_context

    database_decisions, database_memories = database_planner_context()

    plan = generate_plan(
        user_profile=user_profile,
        opportunity=opportunity,
        gap_vector=gap_vector,
        goal_id=request.goal_id,
        existing_decisions=request.existing_decisions + database_decisions,
        existing_memories=[
            memory.model_dump() for memory in memories
        ] + database_memories,
    )

    return plan.model_dump()

@app.post("/practice")
def create_practice_evaluation(request: PracticeRequest):
    evaluation = evaluate_practice(
        question=request.question,
        user_answer=request.user_answer,
        topic=request.topic,
    )

    memory = create_and_store_memory(
        evaluation=evaluation,
        source=f"practice:{request.topic}",
    )

    response = evaluation.model_dump()
    response["memory_saved"] = memory is not None

    if memory is not None:
        response["memory_id"] = memory.memory_id

    # Mirror the evaluation into the database memory; weakness thresholds decide
    # what is remembered there. A database problem never breaks this endpoint.
    try:
        from app.services.agent_bridge import mirror_practice_evaluation

        response.update(
            mirror_practice_evaluation(
                question=request.question,
                topic=request.topic,
                answer=request.user_answer,
                evaluation=evaluation,
            )
        )
    except Exception:  # noqa: BLE001
        response["database_mirror"] = "unavailable"

    return response

@app.get("/memories")
def list_memories():
    memories = get_memories()

    return {
        "total": len(memories),
        "memories": [
            memory.model_dump()
            for memory in memories
        ],
    }


# Backend & Memory layer (memory, goals, plans, practice, trace, admin APIs).
from app.backend import register_backend  # noqa: E402

register_backend(app)
