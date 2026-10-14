from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from application.automation.service import LocationNotFound
from application.overview.dto import LocationOverviewDto
from application.overview.facade import LocationOverviewFacade, build_overview_facade
from infrastructure.db import get_db

router = APIRouter(prefix="/api/locations", tags=["overview"])


def get_overview_facade(db: Session = Depends(get_db)) -> LocationOverviewFacade:
    return build_overview_facade(db)


@router.get("/{location_id}/overview", response_model=LocationOverviewDto)
def get_overview(
    location_id: UUID,
    facade: LocationOverviewFacade = Depends(get_overview_facade),
) -> LocationOverviewDto:
    try:
        return facade.get_overview(location_id)
    except LocationNotFound as exc:
        raise HTTPException(status_code=404, detail="Location not found") from exc
