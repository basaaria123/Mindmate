from app.agents.opportunity_agent import extract_opportunity


def test_extract_opportunity():
    opportunity_description = """
    AI Engineering Intern at Example Technologies.

    We are looking for a beginner interested in artificial intelligence.

    Required skills:
    - Python programming is mandatory.
    - Knowledge of machine learning is preferred.

    The candidate should be interested in developing AI applications.
    """

    result = extract_opportunity(opportunity_description)

    assert result.opportunity_title
    assert result.organization
    assert isinstance(result.required_skills, list)
    assert result.summary
