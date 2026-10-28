"""Live tests: read-only calls against api.github.com, run only when GITHUB_TOKEN is set.

    GITHUB_TOKEN="$(gh auth token)" uv run pytest tests/live

They check the typed models against what GitHub actually sends, which the spec alone can't.
Every call reads; nothing is created, changed or starred. Lists are kept to a few items.
"""

import os

import pytest
from apiroute import UnexpectedResponse

from github_apiroute.graphql import GitHubGraphQLApi
from github_apiroute.rest import GitHubRestApi

TOKEN = os.environ.get("GITHUB_TOKEN")


def pytest_collection_modifyitems(items):
    skip = pytest.mark.skip(reason="live tests need GITHUB_TOKEN")
    for item in items:
        if "tests/live/" in item.nodeid and not TOKEN:
            item.add_marker(skip)


@pytest.fixture(scope="session")
def rest() -> GitHubRestApi:
    return GitHubRestApi(token=TOKEN)


@pytest.fixture(scope="session")
def gql() -> GitHubGraphQLApi:
    return GitHubGraphQLApi(token=TOKEN)


@pytest.fixture(scope="session")
def signed_in(rest) -> None:
    """Skips a test about the signed-in user when the token belongs to no user: the Actions
    GITHUB_TOKEN (an app installation token) gets 403 from GET /user."""
    try:
        rest.users.get_authenticated()
    except UnexpectedResponse as error:
        if error.response.status_code != 403:
            raise
        pytest.skip("the token belongs to no user (the Actions GITHUB_TOKEN)")
