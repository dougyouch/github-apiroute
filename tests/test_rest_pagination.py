"""The REST client's _all methods page by GitHub's Link headers (over a mock transport)."""

import httpx
import pytest
from apiroute.testing import MockTransport

from github_apiroute.rest import GitHubRestApi

ISSUES = "https://api.github.com/repos/o/r/issues"


@pytest.fixture
def mock():
    return MockTransport()


@pytest.fixture
def rest(mock):
    return GitHubRestApi(token="t", transport=mock)


def test_array_lists_follow_the_link_header(rest, mock):
    mock.respond(
        httpx.Response(200, json=[{"n": 1}], headers={"Link": f'<{ISSUES}?page=2>; rel="next"'}),
        httpx.Response(200, json=[{"n": 2}]),
    )
    assert list(rest.issues.list_for_repo_all("o", "r", per_page=1)) == [{"n": 1}, {"n": 2}]
    assert mock.last.params["page"] == "2"
    assert all(call.headers["Authorization"] == "Bearer t" for call in mock.calls)


def test_wrapped_lists_yield_their_items(rest, mock):
    mock.respond(httpx.Response(200, json={"total_count": 1, "items": [{"name": "x"}]}))
    assert list(rest.search.repos_all(q="x")) == [{"name": "x"}]


def test_a_next_link_to_another_host_is_refused(rest, mock):
    mock.respond(
        httpx.Response(
            200, json=[{"n": 1}], headers={"Link": '<https://evil.test/?page=2>; rel="next"'}
        )
    )
    with pytest.raises(ValueError, match="evil.test"):
        list(rest.issues.list_for_repo_all("o", "r"))
    assert len(mock.calls) == 1
