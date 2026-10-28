import pytest

from clmgr.tests.test_base import YEAR


@pytest.fixture(autouse=True)
def current_year(monkeypatch):
    """Keep the expected output valid after the year it is written in"""
    monkeypatch.setattr("clmgr.processor.current_year", lambda: YEAR)
