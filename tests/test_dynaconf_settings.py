from dynaconf import settings


def test_dynaconf():
    """Test dynaconf setup settings."""
    assert settings.TESTING is True
