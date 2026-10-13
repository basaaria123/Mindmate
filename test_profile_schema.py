
from app.schemas.profile import UserProfile


def test_user_profile_schema():
    profile = UserProfile(
        education="Second-year engineering student",
        goals=["Learn AI development"],
        skills=["Basic Python"],
        interests=["Artificial Intelligence"],
        daily_available_minutes=60,
        learning_preferences=["Step-by-step explanations"],
    )

    assert profile.education == "Second-year engineering student"
    assert profile.goals == ["Learn AI development"]
    assert profile.skills == ["Basic Python"]
    assert profile.interests == ["Artificial Intelligence"]
    assert profile.daily_available_minutes == 60
    assert profile.learning_preferences == ["Step-by-step explanations"]
