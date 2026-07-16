"""Daily brief HTTP routes."""

from fastapi import APIRouter

from mydash.core.services.brief import BriefService, DailyBrief

router = APIRouter(tags=["brief"])


@router.get("/brief", response_model=DailyBrief)
async def get_brief() -> DailyBrief:
    """Return the full daily brief as JSON."""
    return await BriefService().build()
