from app.models.skill import SkillCreate

SKILL_CATALOG = [
    SkillCreate(skill_id="programming_fundamentals", name="Programming fundamentals", category="foundations", description="Variables, control flow, functions, and problem decomposition.", difficulty=1),
    SkillCreate(skill_id="html", name="HTML", category="frontend", prerequisites=["programming_fundamentals"], difficulty=1),
    SkillCreate(skill_id="css", name="CSS", category="frontend", prerequisites=["html"], difficulty=2),
    SkillCreate(skill_id="javascript", name="JavaScript", category="frontend", prerequisites=["programming_fundamentals", "html"], difficulty=2),
    SkillCreate(skill_id="python", name="Python", category="programming", prerequisites=["programming_fundamentals"], difficulty=2),
    SkillCreate(skill_id="java", name="Java", category="programming", prerequisites=["programming_fundamentals"], difficulty=2),
    SkillCreate(skill_id="data_structures", name="Data structures", category="foundations", prerequisites=["programming_fundamentals"], difficulty=3),
    SkillCreate(skill_id="databases", name="Databases", category="backend", prerequisites=["programming_fundamentals"], difficulty=2),
    SkillCreate(skill_id="sql", name="SQL", category="backend", prerequisites=["databases"], difficulty=2),
    SkillCreate(skill_id="http", name="HTTP", category="web", prerequisites=["programming_fundamentals"], difficulty=2),
    SkillCreate(skill_id="apis", name="REST APIs", category="backend", prerequisites=["http", "programming_fundamentals"], difficulty=3),
    SkillCreate(skill_id="authentication", name="Authentication", category="backend", prerequisites=["apis"], difficulty=3),
    SkillCreate(skill_id="testing", name="Testing", category="quality", prerequisites=["programming_fundamentals"], difficulty=2),
    SkillCreate(skill_id="git", name="Git", category="tools", difficulty=1),
    SkillCreate(skill_id="cloud", name="Deployment", category="operations", prerequisites=["git"], difficulty=3),
    SkillCreate(skill_id="statistics", name="Statistics", category="data", difficulty=2),
    SkillCreate(skill_id="machine_learning", name="Machine learning", category="data", prerequisites=["python", "statistics"], difficulty=4),
    SkillCreate(skill_id="user_research", name="User research", category="design", difficulty=2),
    SkillCreate(skill_id="prototyping", name="Prototyping", category="design", prerequisites=["user_research"], difficulty=2),
]

SKILLS_BY_ID = {skill.skill_id: skill for skill in SKILL_CATALOG}

ROLE_SKILL_REQUIREMENTS = {
    "frontend_developer": {"javascript": 3, "html": 3, "css": 3, "testing": 2, "git": 2},
    "backend_developer": {"python": 3, "apis": 3, "databases": 3, "testing": 2, "cloud": 2, "authentication": 2},
    "full_stack_developer": {"javascript": 3, "apis": 3, "databases": 3, "html": 2, "css": 2, "testing": 2},
    "python_developer": {"python": 3, "testing": 2, "apis": 2, "databases": 2},
    "java_developer": {"java": 3, "apis": 2, "databases": 2, "testing": 2},
    "data_analyst": {"sql": 3, "statistics": 3, "python": 2},
    "machine_learning_engineer": {"python": 3, "statistics": 3, "machine_learning": 3, "databases": 2},
    "ui_ux_designer": {"user_research": 3, "prototyping": 3},
}

def role_requirements(role_id: str) -> dict[str, int]:
    return dict(ROLE_SKILL_REQUIREMENTS.get(role_id, {}))

# Keep the existing CareerRole catalog as the source of role identity while
# exposing normalized skill IDs and deterministic proficiency expectations.
from app.career_discovery.catalog import ROLES
for _role in ROLES:
    _role.skill_requirements = role_requirements(_role.role_id) if _role.role_id in ROLE_SKILL_REQUIREMENTS else {}
    _role.expected_proficiency = dict(_role.skill_requirements)
