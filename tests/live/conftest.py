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

# What GitHub answers a token that may not read a resource. The Actions GITHUB_TOKEN (an app
# installation token, which Build uses) gets it for the signed-in user, stargazers, watchers
# and gists: a limit of the token, not a fault in the client, so such a test is skipped.
NOT_ACCESSIBLE = "Resource not accessible by integration"


def pytest_collection_modifyitems(items):
    skip = pytest.mark.skip(reason="live tests need GITHUB_TOKEN")
    for item in items:
        if "tests/live/" in item.nodeid and not TOKEN:
            item.add_marker(skip)


@pytest.hookimpl(wrapper=True)
def pytest_runtest_call(item):
    try:
        return (yield)
    except Exception as error:
        if NOT_ACCESSIBLE in _detail(error):
            pytest.skip(f"the token can't read this: {NOT_ACCESSIBLE}")
        raise


def _detail(error: Exception) -> str:
    response = getattr(error, "response", None)
    return str(error) + (response.text if response is not None else "")


@pytest.fixture(scope="session")
def rest() -> GitHubRestApi:
    return GitHubRestApi(token=TOKEN)


@pytest.fixture(scope="session")
def gql() -> GitHubGraphQLApi:
    return GitHubGraphQLApi(token=TOKEN)


@pytest.fixture(scope="session")
def signed_in(rest) -> None:
    """Skips a test about the signed-in user when the token belongs to no user, as the Actions
    token doesn't: GitHub refuses it GET /user, and answers /user/issues with a plain 404."""
    try:
        rest.users.get_authenticated()
    except UnexpectedResponse as error:
        if NOT_ACCESSIBLE not in _detail(error):
            raise
        pytest.skip("the token belongs to no user")
