from app.schemas.fit import FitAssessment


sample_assessment = FitAssessment(
    opportunity_title="AI Engineering Intern",
    overall_fit="Moderate",
    matching_skills=[
        {
            "skill_name": "Python",
            "user_level": "Intermediate",
            "required_level": "Intermediate",
            "match_status": "Match",
            "explanation": "The user has demonstrated Python skills at the expected level.",
        }
    ],
    partial_matches=[
        {
            "skill_name": "Machine Learning",
            "user_level": "Beginner",
            "required_level": "Intermediate",
            "match_status": "Partial match",
            "explanation": "The user has some machine learning knowledge but needs further practice.",
        }
    ],
    missing_skills=[
        {
            "skill_name": "Model Deployment",
            "user_level": "Not demonstrated",
            "required_level": "Intermediate",
            "match_status": "Missing",
            "explanation": "The provided profile contains no evidence of model deployment experience.",
        }
    ],
    strengths=[
        "Python programming",
        "Interest in artificial intelligence",
    ],
    improvement_areas=[
        "Develop machine learning skills",
        "Learn model deployment",
    ],
    summary=(
        "The user has a foundation in Python but needs to develop "
        "additional skills relevant to the opportunity."
    ),
)


print("Fit schema validation successful!")
print(sample_assessment.model_dump_json(indent=2))