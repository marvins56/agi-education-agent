"""Tests for Role-Based Access Control (RBAC)."""

from unittest.mock import MagicMock

import pytest
from fastapi import HTTPException

from src.auth.rbac import Role, ROLE_HIERARCHY, require_role


class TestRoleEnum:
    def test_role_values(self):
        assert Role.student == "student"
        assert Role.teacher == "teacher"
        assert Role.parent == "parent"
        assert Role.admin == "admin"

    def test_role_from_string(self):
        assert Role("student") is Role.student
        assert Role("admin") is Role.admin


class TestRoleHierarchy:
    def test_admin_includes_all_roles(self):
        assert ROLE_HIERARCHY[Role.admin] == {
            Role.admin, Role.teacher, Role.parent, Role.student
        }

    def test_teacher_only_includes_teacher(self):
        assert ROLE_HIERARCHY[Role.teacher] == {Role.teacher}

    def test_student_only_includes_student(self):
        assert ROLE_HIERARCHY[Role.student] == {Role.student}


class TestRequireRole:
    async def test_student_allowed_on_student_route(self):
        mock_user = MagicMock()
        mock_user.role = "student"
        checker = require_role(Role.student)
        result = await checker(current_user=mock_user)
        assert result is mock_user

    async def test_student_denied_on_teacher_route(self):
        mock_user = MagicMock()
        mock_user.role = "student"
        checker = require_role(Role.teacher)
        with pytest.raises(HTTPException) as exc_info:
            await checker(current_user=mock_user)
        assert exc_info.value.status_code == 403
        assert "not authorized" in exc_info.value.detail

    async def test_admin_access_all_routes(self):
        mock_user = MagicMock()
        mock_user.role = "admin"

        for target_role in [Role.student, Role.teacher, Role.parent, Role.admin]:
            checker = require_role(target_role)
            result = await checker(current_user=mock_user)
            assert result is mock_user

    async def test_teacher_denied_on_parent_route(self):
        mock_user = MagicMock()
        mock_user.role = "teacher"
        checker = require_role(Role.parent)
        with pytest.raises(HTTPException) as exc_info:
            await checker(current_user=mock_user)
        assert exc_info.value.status_code == 403

    async def test_parent_denied_on_student_route(self):
        mock_user = MagicMock()
        mock_user.role = "parent"
        checker = require_role(Role.student)
        with pytest.raises(HTTPException) as exc_info:
            await checker(current_user=mock_user)
        assert exc_info.value.status_code == 403

    async def test_multiple_allowed_roles(self):
        """When multiple roles are allowed, any matching role should pass."""
        mock_user = MagicMock()
        mock_user.role = "teacher"
        checker = require_role(Role.teacher, Role.parent)
        result = await checker(current_user=mock_user)
        assert result is mock_user

    async def test_invalid_role_raises(self):
        mock_user = MagicMock()
        mock_user.role = "invalid_role"
        checker = require_role(Role.student)
        with pytest.raises(HTTPException) as exc_info:
            await checker(current_user=mock_user)
        assert exc_info.value.status_code == 403
