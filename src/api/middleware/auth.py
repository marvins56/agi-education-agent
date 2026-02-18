"""Auth middleware — re-exports from dependencies for backward compatibility."""

from src.api.dependencies import get_current_user

# Alias for student-facing endpoints
get_current_student = get_current_user

__all__ = ["get_current_user", "get_current_student"]
