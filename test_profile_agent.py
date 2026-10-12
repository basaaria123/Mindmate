
from app.agents.profile_agent import extract_user_profile


def test_extract_user_profile():
    user_message = (
        "I am a second-year engineering student. "
        "My goal is to learn AI development. "
        "I know basic Python and am interested in artificial intelligence. "
        "I can spend one hour every day learning. "
        "I prefer step-by-step explanations."
    )

    profile = extract_user_profile(user_message)

    assert profile.education
    assert any(
    "learn ai development" in goal.lower()
    for goal in profile.goals
)
    assert any("Python" in skill for skill in profile.skills)
    assert profile.daily_available_minutes == 60
    assert any(
        "step-by-step" in preference.lower()
        for preference in profile.learning_preferences
    )
