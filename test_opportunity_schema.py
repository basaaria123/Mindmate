from app.schemas.opportunity import OpportunitySpec

sample_opportunity = OpportunitySpec(
opportunity_title="AI Engineering Intern",
organization="Example Technologies",
opportunity_type="internship",
required_skills=[
{
"skill_name": "Python",
"importance": "High",
"is_mandatory": True,
"description": "Required for developing AI applications",
},
{
"skill_name": "Machine Learning",
"importance": "Medium",
"is_mandatory": False,
"description": "Useful for building and evaluating AI models",
},
],
preferred_skills=["Communication", "Git"],
experience_level="Beginner",
summary="An internship for candidates interested in AI engineering.",
)

print("Opportunity schema validation successful!")
print(sample_opportunity.model_dump_json(indent=2))
