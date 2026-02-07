"""Role-based access control for EduAGI."""

from enum import Enum

from fastapi import Depends, HTTPException, status

from src.api.dependencies import get_current_user
from src.models.user import User


class Role(str, Enum):
    student = "student"
    teacher = "teacher"
    parent = "parent"
    admin = "admin"


ROLE_HIERARCHY = {
    Role.admin: {Role.admin, Role.teacher, Role.parent, Role.student},
    Role.teacher: {Role.teacher},
    Role.parent: {Role.parent},
    Role.student: {Role.student},
}


def require_role(*allowed_roles: Role):
    """Dependency that checks if the current user has one of the allowed roles."""

    async def _check_role(current_user: User = Depends(get_current_user)):
        try:
            user_role = Role(current_user.role)
        except ValueError:
            # F-30 fix: Unknown roles (e.g. guest) get 403 instead of 500
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="not authorized for this action",
            )
        # Admin can access everything
        if user_role == Role.admin:
            return current_user
        if user_role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                # F-34 fix: Don't leak user role in error message
                detail="not authorized for this action",
            )
        return current_user

    return _check_role
