from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database.session import get_db, get_settings
from app.models.user import User
from app.schemas.organization import OrganizationCreate, OrganizationResponse
from app.services.organization_service import OrganizationService

router = APIRouter(prefix="/organizations", tags=["organizations"])


@router.post("", response_model=OrganizationResponse, status_code=status.HTTP_201_CREATED)
def create_organization(payload: OrganizationCreate, db: Session = Depends(get_db)):
    owner = db.query(User).first()
    if not owner:
        raise HTTPException(status_code=404, detail="No user registered")
    service = OrganizationService(db)
    organization = service.create_organization(owner, payload)
    return service.to_response(organization)
