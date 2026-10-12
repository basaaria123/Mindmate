from app.agents.opportunity_agent import extract_opportunity


opportunity_description = """
AI Engineering Intern at Example Technologies.

We are looking for a beginner interested in artificial intelligence.

Required skills:
- Python programming is mandatory.
- Knowledge of machine learning is preferred.

The candidate should be interested in developing AI applications.
"""


try:
    result = extract_opportunity(opportunity_description)

    print("\nOpportunity Agent is working!")
    print(result.model_dump_json(indent=2))

except Exception as error:
    print("\nSomething went wrong:")
    print(type(error).__name__, "-", error)