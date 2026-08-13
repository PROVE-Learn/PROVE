from abc import ABC, abstractmethod

from app.models.company_intelligence import EvidenceClaim


class CompanyResearchProvider(ABC):
    @abstractmethod
    async def research(self, company_id: str, role_id: str | None = None) -> list[EvidenceClaim]:
        """Return source-backed claims; callers perform verification separately."""
