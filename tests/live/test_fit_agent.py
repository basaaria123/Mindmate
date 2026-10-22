
from app.agents.fit_agent import assess_fit
from app.schemas.opportunity import OpportunitySpec
from app.schemas.profile import UserProfile


def test_assess_fit():
    user_profile = UserProfile(
        education="Computer Science student",
        goals=[
            "Become an AI engineer",
            "Build practical AI projects",
        ],
        skills=[
            "Python",
            "Basic machine learning",
        ],
        interests=[
            "Artificial intelligence",
            "AI application development",
        ],
        daily_available_minutes=60,
        learning_preferences=[
            "Hands-on projects",
            "Step-by-step learning",
        ],
    )

    opportunity = OpportunitySpec(
        opportunity_title="AI Engineering Intern",
        organization="Example Technologies",
        opportunity_type="internship",
        required_skills=[
            {
                "skill_name": "Python",
                "importance": "High",
                "is_mandatory": True,
                "description": "Python programming is mandatory.",
            },
            {
                "skill_name": "Machine Learning",
                "importance": "High",
                "is_mandatory": True,
                "description": "Knowledge of machine learning is required.",
            },
            {
                "skill_name": "Model Deployment",
                "importance": "Medium",
                "is_mandatory": False,
                "description": "Experience deploying AI models is desirable.",
            },
        ],
        preferred_skills=["Git", "Communication"],
        experience_level="Beginner",
        summary=(
            "An internship for beginners interested in AI engineering "
            "and application development."
        ),
    )

    result = assess_fit(user_profile, opportunity)

    assert result.opportunity_title == "AI Engineering Intern"
    assert result.overall_fit in {"Strong", "Moderate", "Low"}
    assert isinstance(result.matching_skills, list)
    assert isinstance(result.partial_matches, list)
    assert isinstance(result.missing_skills, list)
    assert result.summary
