import pytest
import pytest_asyncio
from fastapi.testclient import TestClient
from httpx import AsyncClient, ASGITransport

from main import app

#
# @pytest.fixture(scope="session")
# def client():
#     return TestClient(app)
#
#
# @pytest.fixture(scope="session", autouse=True)
# def setup_and_teardown():
#     print("Starting tests")
#     yield
#     print("finished tests")


### async version


@pytest_asyncio.fixture(scope="session")
async def client():
    async with AsyncClient(
        transport=ASGITransport(app),
        base_url="http://testserver",
    ) as client:
        yield client


@pytest.fixture(scope="session", autouse=True)
def setup_and_teardown():
    print("Starting tests")
    yield
    print("finished tests")
