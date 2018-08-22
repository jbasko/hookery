import pytest

from tests.helpers import Calls


@pytest.fixture
def calls():
    return Calls()
