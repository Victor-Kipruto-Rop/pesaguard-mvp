from uuid import UUID

from sqlalchemy.orm import Session

from app.models.organization import Organization
from app.models.membership import OrganizationMembership
from app.models.role import Role
from app.models.user import User
from app.schemas.organization import OrganizationCreate, OrganizationResponse


class OrganizationService:
    def __init__(self, db: Session):
        self.db = db

    def create_organization(self, owner: User, payload: OrganizationCreate) -> Organization:
        organization = Organization(name=payload.name, slug=payload.slug, owner_id=owner.id)
        self.db.add(organization)
        self.db.flush()

        role = Role(organization_id=organization.id, name="Owner", slug="owner", description="Organization owner", is_system=True)
        self.db.add(role)
        self.db.flush()

        membership = OrganizationMembership(organization_id=organization.id, user_id=owner.id, role_id=role.id)
        self.db.add(membership)
        self.db.commit()
        self.db.refresh(organization)
        return organization

    def get_organization(self, organization_id: UUID) -> Organization | None:
        return self.db.query(Organization).filter(Organization.id == organization_id).first()

    def to_response(self, organization: Organization) -> OrganizationResponse:
        return OrganizationResponse.model_validate(organization)
