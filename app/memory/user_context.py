"""Request-scoped user_id for tools that cannot take explicit state."""
from __future__ import annotations

from contextvars import ContextVar

_current_user_id: ContextVar[str | None] = ContextVar("steadyfit_user_id", default=None)


def set_current_user_id(user_id: str | None) -> None:
    _current_user_id.set(user_id)


def get_current_user_id() -> str | None:
    return _current_user_id.get()


def require_current_user_id() -> str:
    uid = _current_user_id.get()
    if not uid:
        raise RuntimeError("user_id is not set in request context")
    return uid
