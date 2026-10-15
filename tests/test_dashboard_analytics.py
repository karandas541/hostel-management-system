
import pytest

from analytics.dashboard_analytics import get_dashboard_statistics


def test_dashboard_rejects_missing_actor():
    """Dashboard statistics require an authenticated actor."""
    with pytest.raises(PermissionError):
        get_dashboard_statistics()


def test_dashboard_rejects_invalid_actor():
    """An invalid actor must not receive dashboard statistics."""
    with pytest.raises(PermissionError):
        get_dashboard_statistics({"id": None})


def test_dashboard_rejects_actor_without_session():
    """A user without a valid session must be rejected."""
    with pytest.raises(PermissionError):
        get_dashboard_statistics({
            "id": 1,
            "role": "admin",
        })
