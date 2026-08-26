from fastapi import APIRouter, Depends
from pydantic import BaseModel

from kamla_api.auth import get_current_user
from kamla_api.db.models import User

router = APIRouter()


class MeResponse(BaseModel):
    id: str
    clerk_user_id: str
    email: str | None
    timezone: str | None
    onboarding_completed: bool


@router.get("/me", response_model=MeResponse)
def read_me(user: User = Depends(get_current_user)) -> MeResponse:
    return MeResponse(
        id=str(user.id),
        clerk_user_id=user.clerk_user_id,
        email=user.email,
        timezone=user.timezone,
        onboarding_completed=user.onboarding_completed_at is not None,
    )
