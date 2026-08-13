import re

from fastapi import HTTPException, status

from app.company_intelligence.verification import mark_conflicts, verify_claim
from app.config import Settings
from app.db.repositories.company_intelligence_repository import CompanyRepository, EvidenceClaimRepository, JobPostingRepository
from app.learning.catalog import ROLE_SKILL_REQUIREMENTS, SKILLS_BY_ID
from app.models.company_intelligence import Company, EvidenceClaim, JobPosting
from app.db.repositories.user_repository import UserRepository
from app.company_intelligence.research import CompanyResearchProvider


class CompanyIntelligenceService:
    def __init__(self, companies: CompanyRepository, jobs: JobPostingRepository, claims: EvidenceClaimRepository, settings: Settings):
        self.companies, self.jobs, self.claims, self.settings = companies, jobs, claims, settings

    @staticmethod
    def _extract_role_skills(claims: list[EvidenceClaim], role_id: str | None = None) -> list[str]:
        weighted: dict[str, int] = {}

        if role_id and role_id in ROLE_SKILL_REQUIREMENTS:
            for skill_id, weight in ROLE_SKILL_REQUIREMENTS[role_id].items():
                weighted[skill_id] = max(weighted.get(skill_id, 0), int(weight * 5))

        if not claims and weighted:
            ordered = sorted(weighted.items(), key=lambda item: (-item[1], item[0]))
            return [skill_id for skill_id, _ in ordered]

        for claim in claims:
            text = " ".join(part for part in (claim.claim_key, claim.claim_text, claim.evidence_text) if part).lower()
            for skill_id, skill in SKILLS_BY_ID.items():
                aliases = {skill_id.lower(), skill.name.lower().replace("&", " and ")}
                for token in re.split(r"[\s/_-]+", skill.name.lower()):
                    if token:
                        aliases.add(token)
                if skill_id == "machine_learning":
                    aliases.update({"ml", "machine learning", "deep learning", "neural network", "neural networks"})
                if skill_id == "statistics":
                    aliases.update({"stats", "statistical", "data science"})
                if skill_id == "sql":
                    aliases.update({"structured query language", "queries", "querying"})
                if skill_id == "databases":
                    aliases.update({"database", "db", "data storage"})
                if skill_id == "cloud":
                    aliases.update({"deployment", "deploy", "devops", "docker", "kubernetes"})
                if skill_id == "apis":
                    aliases.update({"api", "rest api", "rest", "http"})
                if skill_id == "testing":
                    aliases.update({"tests", "test", "qa", "unit tests"})
                if any(alias in text for alias in aliases):
                    weighted[skill_id] = max(weighted.get(skill_id, 0), 4)

        if not weighted and role_id and role_id in ROLE_SKILL_REQUIREMENTS:
            return list(ROLE_SKILL_REQUIREMENTS[role_id].keys())

        ordered = sorted(weighted.items(), key=lambda item: (-item[1], item[0]))
        return [skill_id for skill_id, _ in ordered]

    async def extract_role_skills(self, company_id: str, role_id: str | None = None) -> list[str]:
        await self.company(company_id)
        claims = await self.claims.list_for_company(company_id, role_id)
        return self._extract_role_skills(claims, role_id)

    async def lookup(self, query: str): return await self.companies.lookup(query)
    async def company(self, company_id: str) -> Company:
        result = await self.companies.get(company_id)
        if not result: raise HTTPException(status_code=404, detail="Company not found")
        return result
    async def jobs_for_company(self, company_id: str) -> list[JobPosting]:
        await self.company(company_id)
        return [job for job in await self.jobs.list_for_company(company_id) if not job.is_stale(self.settings.cache_ttl_job_posting_days)]
    async def evidence(self, company_id: str, role_id: str | None = None) -> list[EvidenceClaim]:
        await self.company(company_id)
        return mark_conflicts(await self.claims.list_for_company(company_id, role_id))
    async def add_company(self, company: Company): return await self.companies.upsert(company)
    async def add_job(self, job: JobPosting):
        await self.company(job.company_id); return await self.jobs.create(job)
    async def add_claim(self, claim: EvidenceClaim):
        await self.company(claim.company_id); return await self.claims.create(verify_claim(claim, self.settings.cache_ttl_question_reverify_days))
    async def target_companies(self, user_id: str, users: UserRepository) -> list[Company]:
        user = await users.get_by_id(user_id)
        return [company for company_id in user.profile.target_companies if (company := await self.companies.get(company_id))]
    async def add_target_company(self, user_id: str, company_id: str, users: UserRepository):
        await self.company(company_id); user = await users.get_by_id(user_id)
        if company_id in user.profile.target_companies: raise HTTPException(status_code=409, detail="Company already targeted")
        return await users.set_target_companies(user_id, user.profile.target_companies + [company_id])
    async def remove_target_company(self, user_id: str, company_id: str, users: UserRepository):
        user = await users.get_by_id(user_id)
        if company_id not in user.profile.target_companies: raise HTTPException(status_code=404, detail="Target company not found")
        return await users.set_target_companies(user_id, [item for item in user.profile.target_companies if item != company_id])
    async def research(self, company_id: str, role_id: str | None, provider: CompanyResearchProvider) -> list[EvidenceClaim]:
        await self.company(company_id)
        claims = await provider.research(company_id, role_id)
        if any(claim.company_id != company_id or claim.role_id != role_id for claim in claims):
            raise HTTPException(status_code=422, detail="Provider returned claims for another company or role")
        return [await self.add_claim(claim) for claim in claims]
