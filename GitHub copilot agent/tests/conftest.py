import pytest


@pytest.fixture
def tmp_project_dir(tmp_path):
    """Provide a temporary project directory."""
    return tmp_path
