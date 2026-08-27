"""Authorization helpers — defense-in-depth after index matching."""

from __future__ import annotations

from uuid import UUID

from app.models import Document, User, UserRole


def is_admin(user: User) -> bool:
    return user.role == UserRole.ADMIN and user.is_active


def can_read_document(user: User, document: Document) -> bool:
    if not user.is_active:
        return False
    if is_admin(user):
        return True
    return document.owner_id == user.id


def can_delete_document(user: User, document: Document) -> bool:
    return can_read_document(user, document)


def can_search_document(user: User, owner_id: UUID) -> bool:
    if not user.is_active:
        return False
    if is_admin(user):
        return True
    return owner_id == user.id
