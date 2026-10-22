"""Offline analysis behind the AI endpoints when Nemotron is not available.

Same response schemas as the agents, built from keyword extraction and the
deterministic fit rules in ``app/scoring/fit.py``, so onboarding, the
opportunity analyser, fit, gaps and suggestions keep working without a key.
``main.py`` marks these responses with ``X-MindMate-Source: offline`` and logs
a ``model_fallback`` event, so they are never presented as model output.
"""

from __future__ import annotations

import re

from app.schemas.fit import FitAssessment, SkillMatch
from app.schemas.gap import GapVectorJSON, SkillGap
from app.schemas.opportunity import OpportunityRequirement, OpportunitySpec
from app.schemas.profile import UserProfile
from app.schemas.suggestions import OpportunitySuggestion, SuggestionsResponse
from app.scoring.fit import WEIGHTS, band_for, normalize_weight, skill_matches

# General skills first, so a posting's "machine learning" is named as such rather than
# as a curated requirement such as "Machine learning fundamentals".
BASE_SKILLS = [
    "Python", "SQL", "Git", "Docker", "Kubernetes", "Linux", "Statistics", "Machine learning",
    "Deep learning", "Model evaluation", "Data structures", "Algorithms", "Data visualisation",
    "Data analysis", "Pandas", "NumPy", "scikit-learn", "PyTorch", "TensorFlow",
    "Large language models", "AI agents", "Natural language processing", "Computer vision",
    "REST APIs", "JSON", "FastAPI", "Flask", "Cloud", "AWS", "Azure", "GCP", "C++", "Java",
    "JavaScript", "TypeScript", "React", "Node.js", "HTML", "CSS", "Excel", "Power BI",
    "Tableau", "Spark", "MLOps", "Technical writing", "Communication", "Problem solving",
]

# Short forms that the phrase matcher cannot connect to the full name.
ALIASES = {
    "llm": "Large language models", "llms": "Large language models", "sklearn": "scikit-learn",
    "nlp": "Natural language processing", "ml": "Machine learning", "dl": "Deep learning",
    "k8s": "Kubernetes", "rest api": "REST APIs", "restful": "REST APIs", "apis": "REST APIs",
    "dsa": "Data structures", "data visualization": "Data visualisation",
    "google cloud": "GCP", "amazon web services": "AWS", "problem-solving": "Problem solving",
}

MANDATORY_HINTS = ("required", "require", "must", "mandatory", "essential", "need", "should have")
PREFERRED_HINTS = ("preferred", "nice to have", "good to have", "bonus", "plus", "desirable", "advantage",
                   "familiarity", "optional")
ROLE_NOUNS = ("Engineer", "Intern", "Internship", "Developer", "Scientist", "Analyst", "Researcher",
              "Designer", "Manager", "Fellow", "Fellowship", "Associate", "Architect", "Consultant",
              "Specialist", "Hackathon", "Trainee", "Apprentice")
GENERIC_HEADINGS = {"about", "about the role", "about us", "role", "overview", "description", "job description",
                    "responsibilities", "requirements", "qualifications", "skills", "success criteria",
                    "educational qualifications", "who we are", "what you will do", "benefits"}


def curated_skill_names() -> list[str]:
    from app.services.opportunity_service import curated_opportunities

    return [req["name"] for data in curated_opportunities() for req in data["requirements"]]


def vocabulary(extra: list[str] | None = None) -> list[str]:
    names = BASE_SKILLS + curated_skill_names() + list(extra or [])
    return list(dict.fromkeys(n for n in names if n))


def sentences(text: str) -> list[str]:
    """Lines and sentences, without bullets and heading marks."""

    parts: list[str] = []
    for line in text.splitlines():
        line = line.strip().strip("-*•#\t ").strip()
        if not line:
            continue
        parts.extend(p.strip() for p in re.split(r"(?<=[.;!?])\s+", line) if p.strip())
    return parts


def _mentions(name: str, sentence: str) -> bool:
    if skill_matches(name, sentence):
        return True
    lowered = f" {sentence.lower()} "
    return any(
        target == name and re.search(rf"(?<![a-z0-9+#]){re.escape(alias)}(?![a-z0-9+#])", lowered)
        for alias, target in ALIASES.items()
    )


def find_skills(text: str, extra_vocabulary: list[str] | None = None) -> list[tuple[str, list[str]]]:
    """``(skill, sentences mentioning it)`` for every vocabulary skill in the text, in order of first mention."""

    found: list[tuple[int, str, list[str]]] = []
    parts = sentences(text)
    for name in vocabulary(extra_vocabulary):
        indexes = [i for i, s in enumerate(parts) if _mentions(name, s)]
        if indexes and not any(skill_matches(name, other) for _, other, _ in found):
            found.append((indexes[0], name, [parts[i] for i in indexes]))
    found.sort(key=lambda item: (item[0], _position(item[1], item[2][0])))
    return [(name, mentions) for _, name, mentions in found]


def _position(name: str, sentence: str) -> int:
    position = sentence.lower().find(name.lower())
    return position if position >= 0 else len(sentence)


def extract_requirements(text: str, extra_vocabulary: list[str] | None = None) -> list[dict]:
    """Mandatory when any sentence naming the skill says so, preferred (Low) when it is only named as optional."""

    def has(hints: tuple[str, ...], sentence: str) -> bool:
        return any(hint in sentence.lower() for hint in hints)

    requirements = []
    for name, mentions in find_skills(text, extra_vocabulary):
        required = [s for s in mentions if has(MANDATORY_HINTS, s) and not has(PREFERRED_HINTS, s)]
        preferred = [s for s in mentions if has(PREFERRED_HINTS, s)]
        if required:
            weight, mandatory, note = "High", True, "Listed as required"
        elif preferred:
            weight, mandatory, note = "Low", False, "Listed as preferred or an advantage"
        else:
            weight, mandatory, note = "Medium", False, "Mentioned in the posting"
        requirements.append({"name": name, "weight": weight, "mandatory": mandatory,
                             "description": f"{note} (keyword match)."})
    return requirements


def guess_title(text: str) -> str:
    """A short first line ("ML Intern at Acme"), else a role phrase in the text, else the first line cut short."""

    lines = [line.strip().strip("#*-•\t ").strip() for line in text.splitlines()]
    lines = [line for line in lines if line and line.lower().rstrip(":") not in GENERIC_HEADINGS]
    if lines and len(lines[0]) <= 80 and not re.search(r"[.!?]\s", lines[0] + " "):
        return lines[0]
    nouns = "|".join(ROLE_NOUNS)
    match = re.search(rf"((?:[A-Z][\w/&+.\-]*\s+){{0,5}}(?:{nouns})s?)\b", text)
    if match:
        words = match.group(1).split()
        while words and words[0].lower() in {"a", "an", "the", "we", "our", "seeking", "hiring", "join"}:
            words.pop(0)
        if words:
            return " ".join(words)
    if lines:
        return lines[0] if len(lines[0]) <= 80 else lines[0][:77].rstrip() + "..."
    return "Untitled opportunity"


def guess_type(text: str) -> str:
    lowered = text.lower()
    for kind in ("internship", "hackathon", "fellowship", "scholarship", "competition"):
        if kind in lowered or (kind == "internship" and re.search(r"\bintern\b", lowered)):
            return kind
    return "job"


def guess_organization(text: str) -> str | None:
    labelled = re.search(r"(?im)^\s*(?:company|organi[sz]ation|employer)\s*[:\-]\s*(.+)$", text)
    if labelled:
        return labelled.group(1).strip()[:120]
    at = re.search(r"\bat[ \t]+([A-Z][\w&.]*(?:[ \t]+[A-Z][\w&.]*){0,3})", text)
    return at.group(1).strip() if at else None


def guess_experience(text: str) -> str:
    years = re.search(r"(\d+\s*(?:[–-]|to)\s*\d+|\d+\+?)\s*years?", text, re.IGNORECASE)
    lowered = text.lower()
    if years:
        return f"{' '.join(years.group(1).split())} years"
    if any(word in lowered for word in ("fresher", "entry level", "entry-level", "junior", "student", "graduate")):
        return "entry level"
    if "senior" in lowered:
        return "experienced"
    return "not specified"


def opportunity_from_text(text: str) -> OpportunitySpec:
    requirements = extract_requirements(text)
    parts = sentences(text)
    summary = " ".join(parts[:2])[:400] if parts else ""
    return OpportunitySpec(
        opportunity_title=guess_title(text),
        organization=guess_organization(text),
        opportunity_type=guess_type(text),
        required_skills=[
            OpportunityRequirement(skill_name=r["name"], importance=r["weight"], is_mandatory=r["mandatory"],
                                   description=r["description"])
            for r in requirements
        ],
        preferred_skills=[r["name"] for r in requirements if r["weight"] == "Low"],
        experience_level=guess_experience(text),
        summary=summary or "No description given.",
    )


_PREFERENCES = {
    "projects": "Hands-on projects", "hands-on": "Hands-on projects", "video": "Videos", "videos": "Videos",
    "reading": "Reading", "articles": "Reading", "books": "Reading", "practice": "Practice questions",
    "mentor": "Mentoring", "course": "Structured courses", "courses": "Structured courses",
}


def profile_from_text(message: str) -> UserProfile:
    parts = sentences(message)
    lowered = message.lower()
    education = next(
        (s for s in parts if re.search(r"\b(b\.?\s?tech|b\.?e\b|bsc|b\.sc|bachelor|master|m\.?tech|msc|phd|degree|"
                                       r"student|university|college|year)\b", s, re.IGNORECASE)),
        "",
    )
    goals = [s for s in parts if re.search(r"\b(want to|goal|aim|become|hoping to|looking for|plan to|"
                                            r"would like to|land)\b", s, re.IGNORECASE)]
    interests = []
    for s in parts:
        match = re.search(r"\binterested in\s+(.+)", s, re.IGNORECASE)
        if match:
            interests.extend(i.strip(" .") for i in re.split(r",|\band\b", match.group(1)) if i.strip(" ."))
    minutes = None
    time = re.search(r"(\d+(?:\.\d+)?)\s*(hours?|hrs?|h|minutes?|mins?)\b(?:\s*(?:a|per|each|every)\s*day|\s*daily)?",
                     lowered)
    if time:
        value = float(time.group(1))
        minutes = int(value * 60) if time.group(2).startswith("h") else int(value)
    preferences = list(dict.fromkeys(label for word, label in _PREFERENCES.items()
                                     if re.search(rf"\b{re.escape(word)}\b", lowered)))
    return UserProfile(
        education=education[:200] or "Not stated",
        goals=goals[:5],
        skills=[name for name, _ in find_skills(" ".join(s for s in parts if s not in goals and not re.search(
            r"\b(interested in|want to learn|hope to learn|learn more)\b", s, re.IGNORECASE)))],
        interests=interests[:8],
        daily_available_minutes=minutes,
        learning_preferences=preferences,
    )


def _match(profile: UserProfile, requirement: str) -> str | None:
    return next((skill for skill in profile.skills if skill_matches(requirement, skill)), None)


def fit_for(profile: UserProfile, opportunity: OpportunitySpec) -> FitAssessment:
    """Each requirement the profile names counts as covered; the score uses the fit weights."""

    matching, missing = [], []
    covered = total = 0
    for req in opportunity.required_skills:
        weight = WEIGHTS[normalize_weight(req.importance)]
        total += weight
        skill = _match(profile, req.skill_name)
        required_level = "required" if req.is_mandatory else req.importance.lower()
        if skill:
            covered += weight
            matching.append(SkillMatch(skill_name=req.skill_name, user_level="listed in profile",
                                       required_level=required_level, match_status="match",
                                       explanation=f"Your profile lists {skill}. Add evidence (a project or result) "
                                                   "to make this count in the evidence-based fit score."))
        else:
            missing.append(SkillMatch(skill_name=req.skill_name, user_level="not listed",
                                      required_level=required_level, match_status="missing",
                                      explanation=f"{req.skill_name} is not in your profile."))
    score = round(100 * covered / total) if total else 0
    band = band_for(score) if total else "Not enough detail"
    title = opportunity.opportunity_title
    summary = (f"Offline estimate: your profile lists {len(matching)} of {len(opportunity.required_skills)} "
               f"skills this opportunity asks for ({score}%, {band.lower()} by skill weight).")
    if not opportunity.required_skills:
        summary = "No skill requirements were found in this opportunity, so fit could not be estimated."
    return FitAssessment(
        opportunity_title=title,
        overall_fit=band,
        matching_skills=matching,
        partial_matches=[],
        missing_skills=missing,
        strengths=[f"{m.skill_name} is listed in your profile" for m in matching][:5],
        improvement_areas=[f"Build and show evidence of {m.skill_name}" for m in missing][:5],
        summary=summary,
    )


def gaps_for(profile: UserProfile, opportunity: OpportunitySpec, fit: FitAssessment) -> GapVectorJSON:
    by_name = {req.skill_name: req for req in opportunity.required_skills}
    gaps = []
    for item in fit.missing_skills + fit.partial_matches:
        req = by_name.get(item.skill_name)
        weight = WEIGHTS[normalize_weight(req.importance)] if req else 2
        mandatory = bool(req and req.is_mandatory)
        impact = min(100, weight * 25 + (25 if mandatory else 0))
        gaps.append(SkillGap(
            skill_name=item.skill_name,
            career_impact_score=impact,
            gap_type="missing skill" if item in fit.missing_skills else "partial skill",
            missing_evidence=f"No project, result or certificate showing {item.skill_name}.",
            rationale=f"{opportunity.opportunity_title} lists {item.skill_name} as "
                      f"{'mandatory' if mandatory else (req.importance.lower() if req else 'medium') + ' importance'}.",
            recommended_focus=f"Complete a small project that uses {item.skill_name} and record the result.",
        ))
    gaps.sort(key=lambda gap: -gap.career_impact_score)
    return GapVectorJSON(opportunity_title=opportunity.opportunity_title, gaps=gaps)


def suggestions_for(profile: UserProfile) -> SuggestionsResponse:
    """Three suggestions per category from the curated list and the profile's own skills and goals."""

    from app.services.opportunity_service import curated_opportunities

    words = {w for text in profile.goals + profile.interests + profile.skills for w in re.findall(r"[a-z+#]+", text.lower())}

    def overlap(data: dict) -> float:
        names = [req["name"] for req in data["requirements"]]
        have = sum(1 for name in names if any(skill_matches(name, skill) for skill in profile.skills))
        title_words = set(re.findall(r"[a-z+#]+", data["title"].lower()))
        return have / max(1, len(names)) + 0.2 * len(title_words & words)

    curated = sorted(curated_opportunities(), key=lambda data: -overlap(data))

    def explain(data: dict) -> str:
        names = [req["name"] for req in data["requirements"]]
        have = [n for n in names if any(skill_matches(n, s) for s in profile.skills)]
        missing = [n for n in names if n not in have]
        if have:
            text = f"Uses skills you listed ({', '.join(have[:3])})"
            return text + (f"; you would still need {', '.join(missing[:2])}." if missing else ".")
        return f"Asks for {', '.join(names[:3])}, which would extend your current skills."

    jobs = [d for d in curated if d.get("type") == "internship"][:3]
    other = [d for d in curated if d.get("type") != "internship"][:3]
    other += [d for d in curated if d not in jobs and d not in other][: 3 - len(other)]

    focus = [req["name"] for d in curated[:4] for req in d["requirements"]
             if not any(skill_matches(req["name"], s) for s in profile.skills)]
    fallback = ["Model evaluation", "Statistics", "Git", "SQL", "Data structures", "Docker"]
    focus = [name for name in dict.fromkeys(focus + fallback)
             if not any(skill_matches(name, s) for s in profile.skills)][:3]
    focus += [name for name in fallback if name not in focus][: 3 - len(focus)]
    strongest = (profile.skills or ["Python"])[:3]

    def card(data: dict, category: str) -> OpportunitySuggestion:
        return OpportunitySuggestion(title=data["title"], organization=data.get("org"),
                                     opportunity_type=data.get("type", "internship"), category=category,
                                     explanation=explain(data))

    suggestions = [card(d, "Jobs") for d in jobs]
    suggestions += [
        OpportunitySuggestion(title=f"Portfolio project: {skill}", organization=None, opportunity_type="project",
                              category="Projects",
                              explanation=f"A small, finished project would give you evidence of {skill}"
                                          f"{', combined with ' + strongest[0] if strongest[0] != skill else ''}.")
        for skill in focus
    ]
    suggestions += [
        OpportunitySuggestion(title=f"Study guide: {skill}", organization=None, opportunity_type="learning resource",
                              category="Resources",
                              explanation=f"{skill} appears in the opportunities that best match your profile.")
        for skill in focus
    ]
    suggestions += [card(d, "Other") for d in other]
    return SuggestionsResponse(suggestions=suggestions)
