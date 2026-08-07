from fastapi import Depends, HTTPException, status

from app.middleware.auth_middleware import get_current_user
from app.models.user_model import User

# Role hierarchy: Super Admin > Admin > Engineer > Viewer
ROLE_LEVELS = {
    "Super Admin": 4,
    "Admin": 3,
    "Engineer": 2,
    "Viewer": 1,
}


def require_role(min_role: str):
    """Dependency factory: restricts an endpoint to users with >= min_role level."""

    def checker(current_user: User = Depends(get_current_user)) -> User:
        user_role = current_user.role.name if current_user.role else "Viewer"
        if ROLE_LEVELS.get(user_role, 0) < ROLE_LEVELS.get(min_role, 0):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to perform this action.",
            )
        return current_user

    return checker
