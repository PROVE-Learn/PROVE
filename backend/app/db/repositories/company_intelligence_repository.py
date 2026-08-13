from motor.motor_asyncio import AsyncIOMotorDatabase

from app.db.collections import COMPANIES, EVIDENCE_CLAIMS, JOB_POSTINGS
from app.db.repositories.base import serialize_doc, to_object_id
from app.models.company_intelligence import Company, EvidenceClaim, JobPosting


class CompanyRepository:
    def __init__(self, db: AsyncIOMotorDatabase): self._collection = db[COMPANIES]
    async def ensure_indexes(self): await self._collection.create_index("company_id", unique=True)
    async def upsert(self, company: Company) -> Company:
        await self._collection.update_one({"company_id": company.company_id}, {"$set": company.model_dump(by_alias=False, exclude={"id"})}, upsert=True)
        return Company.model_validate(serialize_doc(await self._collection.find_one({"company_id": company.company_id})))
    async def get(self, company_id: str) -> Company | None:
        doc = await self._collection.find_one({"company_id": company_id}); return Company.model_validate(serialize_doc(doc)) if doc else None
    async def lookup(self, query: str) -> list[Company]:
        cursor = self._collection.find({"$or": [{"company_id": {"$regex": query, "$options": "i"}}, {"name": {"$regex": query, "$options": "i"}}, {"aliases": {"$regex": query, "$options": "i"}}]})
        return [Company.model_validate(serialize_doc(doc)) async for doc in cursor]


class JobPostingRepository:
    def __init__(self, db: AsyncIOMotorDatabase): self._collection = db[JOB_POSTINGS]
    async def ensure_indexes(self): await self._collection.create_index([("company_id", 1), ("active", 1)])
    async def create(self, job: JobPosting) -> JobPosting:
        doc = job.model_dump(by_alias=False, exclude={"id"}); result = await self._collection.insert_one(doc); doc["_id"] = result.inserted_id; return JobPosting.model_validate(serialize_doc(doc))
    async def list_for_company(self, company_id: str) -> list[JobPosting]:
        cursor = self._collection.find({"company_id": company_id, "active": True}); return [JobPosting.model_validate(serialize_doc(doc)) async for doc in cursor]
    async def get(self, job_id: str) -> JobPosting | None:
        doc = await self._collection.find_one({"_id": to_object_id(job_id)}); return JobPosting.model_validate(serialize_doc(doc)) if doc else None


class EvidenceClaimRepository:
    def __init__(self, db: AsyncIOMotorDatabase): self._collection = db[EVIDENCE_CLAIMS]
    async def ensure_indexes(self): await self._collection.create_index([("company_id", 1), ("role_id", 1), ("claim_key", 1)])
    async def create(self, claim: EvidenceClaim) -> EvidenceClaim:
        doc = claim.model_dump(by_alias=False, exclude={"id"}); result = await self._collection.insert_one(doc); doc["_id"] = result.inserted_id; return EvidenceClaim.model_validate(serialize_doc(doc))
    async def list_for_company(self, company_id: str, role_id: str | None = None) -> list[EvidenceClaim]:
        query = {"company_id": company_id};
        if role_id: query["role_id"] = role_id
        cursor = self._collection.find(query); return [EvidenceClaim.model_validate(serialize_doc(doc)) async for doc in cursor]
