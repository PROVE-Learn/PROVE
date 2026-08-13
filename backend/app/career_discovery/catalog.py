from app.models.career_discovery import CareerRole, DiscoveryQuestion, QuestionOption


QUESTION_VERSION = "1.0"

QUESTIONS = [
    DiscoveryQuestion("interest_build", "interests", "What would you most enjoy building?", [
        QuestionOption("web", "Interactive web experiences", {"web": 2, "technical": 1}),
        QuestionOption("data", "Insights from data", {"data": 2, "analytical": 1}),
        QuestionOption("models", "Systems that learn from data", {"ml": 2, "analytical": 1}),
    ]),
    DiscoveryQuestion("strength_reason", "strengths", "Which strength do you rely on most?", [
        QuestionOption("analysis", "Breaking down complex problems", {"analytical": 2}),
        QuestionOption("design", "Making things clear and usable", {"design": 2}),
        QuestionOption("implementation", "Turning ideas into working software", {"technical": 2}),
    ]),
    DiscoveryQuestion("technical_orientation", "technical_orientation", "Which technical area interests you most?", [
        QuestionOption("ui", "Interfaces and user interaction", {"web": 2, "design": 1}),
        QuestionOption("services", "APIs, services, and databases", {"backend": 2, "technical": 1}),
        QuestionOption("statistics", "Data, statistics, and experimentation", {"data": 2, "analytical": 1}),
    ]),
    DiscoveryQuestion("problem_solving", "problem_solving", "What kind of problem is most satisfying?", [
        QuestionOption("systems", "Making systems reliable and scalable", {"backend": 2}),
        QuestionOption("patterns", "Finding patterns in information", {"data": 2, "ml": 1}),
        QuestionOption("flow", "Improving a user's task flow", {"design": 2, "web": 1}),
    ]),
    DiscoveryQuestion("work_preferences", "work_preferences", "Which work style appeals most?", [
        QuestionOption("product", "Iterating visibly with a product team", {"web": 1, "design": 1}),
        QuestionOption("depth", "Deep technical implementation", {"backend": 2, "technical": 1}),
        QuestionOption("research", "Experimenting and evaluating results", {"ml": 2, "data": 1}),
    ]),
    DiscoveryQuestion("communication_preferences", "communication_preferences", "How do you prefer to communicate your work?", [
        QuestionOption("visual", "Visual prototypes and explanations", {"design": 2, "web": 1}),
        QuestionOption("data_story", "Data-backed stories and findings", {"data": 2}),
        QuestionOption("technical_docs", "Technical designs and documentation", {"backend": 2}),
    ]),
    DiscoveryQuestion("learning_preferences", "learning_preferences", "What learning activity keeps you engaged?", [
        QuestionOption("projects", "Building small projects", {"web": 1, "backend": 1, "technical": 1}),
        QuestionOption("datasets", "Exploring datasets and examples", {"data": 2, "ml": 1}),
        QuestionOption("prototypes", "Sketching and testing prototypes", {"design": 2}),
    ]),
    DiscoveryQuestion("career_motivations", "career_motivations", "What outcome matters most in your next role?", [
        QuestionOption("impact", "Useful experiences for people", {"web": 1, "design": 2}),
        QuestionOption("systems", "Dependable technical systems", {"backend": 2}),
        QuestionOption("insight", "Better decisions from evidence", {"data": 2, "ml": 1}),
    ]),
]

ROLES = [
    CareerRole("frontend_developer", "Frontend Developer", "Builds accessible, interactive web experiences.", ["JavaScript", "HTML", "CSS"], ["UX", "testing"], ["web", "design"], ["product"], ["Basic programming"]),
    CareerRole("backend_developer", "Backend Developer", "Builds APIs, data services, and dependable systems.", ["Python", "APIs", "databases"], ["testing", "cloud"], ["backend", "technical"], ["depth"], ["Basic programming"]),
    CareerRole("full_stack_developer", "Full Stack Developer", "Builds product features across frontend and backend.", ["JavaScript", "APIs", "databases"], ["UX", "testing"], ["web", "backend"], ["product"], ["Basic programming"]),
    CareerRole("python_developer", "Python Developer", "Develops software and automation using Python.", ["Python", "testing"], ["APIs", "databases"], ["technical", "backend"], ["depth"], ["Basic programming"]),
    CareerRole("java_developer", "Java Developer", "Develops maintainable Java applications and services.", ["Java", "OOP"], ["APIs", "databases"], ["technical", "backend"], ["depth"], ["Basic programming"]),
    CareerRole("data_analyst", "Data Analyst", "Turns data into understandable findings and decisions.", ["SQL", "statistics"], ["Python", "visualization"], ["data", "analytical"], ["research"], ["Basic numeracy"]),
    CareerRole("machine_learning_engineer", "Machine Learning Engineer", "Builds and evaluates data-driven learning systems.", ["Python", "statistics", "machine learning"], ["data engineering", "experimentation"], ["ml", "analytical"], ["research"], ["Python and statistics fundamentals"]),
    CareerRole("ui_ux_designer", "UI/UX Designer", "Designs useful, understandable digital experiences.", ["user research", "prototyping"], ["visual design", "communication"], ["design", "web"], ["product"], ["Portfolio practice"]),
]

QUESTION_BY_ID = {question.id: question for question in QUESTIONS}
ROLE_BY_ID = {role.role_id: role for role in ROLES}
