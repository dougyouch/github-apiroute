"""GitHubAuth: the token and API version on the wire, Enterprise hosts, and which calls are
retried after a read timeout."""

import httpx
import pytest
from apiroute import Retries
from apiroute.testing import MockTransport, graphql_response

from github_apiroute.auth import API_VERSION
from github_apiroute.graphql import GitHubGraphQLApi
from github_apiroute.rest import GitHubRestApi


def test_rest_sends_the_token_and_api_version():
    mock = MockTransport()
    mock.respond(httpx.Response(200, json={"full_name": "octocat/hello-world"}))
    rest = GitHubRestApi(token="ghp_secret", transport=mock)
    assert rest.repos.get("octocat", "hello-world")["full_name"] == "octocat/hello-world"
    request = mock.last
    assert str(request.url) == "https://api.github.com/repos/octocat/hello-world"
    assert request.headers["Authorization"] == "Bearer ghp_secret"
    assert request.headers["X-GitHub-Api-Version"] == API_VERSION
    assert request.operation == "repos/get"


def test_a_token_function_is_called_per_request():
    tokens = iter(["first", "second"])
    mock = MockTransport()
    mock.respond(httpx.Response(200, json={}), httpx.Response(200, json={}))
    rest = GitHubRestApi(token=lambda: next(tokens), transport=mock)
    rest.repos.get("o", "r")
    rest.repos.get("o", "r")
    assert [call.headers["Authorization"] for call in mock.calls] == [
        "Bearer first",
        "Bearer second",
    ]


def test_no_token_sends_no_authorization():
    mock = MockTransport()
    mock.respond(httpx.Response(200, json={}))
    GitHubRestApi(transport=mock).repos.get("o", "r")
    assert "Authorization" not in mock.last.headers


def test_enterprise_hosts():
    mock = MockTransport()
    mock.respond(httpx.Response(200, json={}), graphql_response(data={"viewer": {}}))
    GitHubRestApi(token="t", base_url="https://ghe.test/api/v3", transport=mock).repos.get("o", "r")
    assert str(mock.last.url) == "https://ghe.test/api/v3/repos/o/r"
    GitHubGraphQLApi(token="t", base_url="https://ghe.test/api", transport=mock).viewer()
    assert str(mock.last.url) == "https://ghe.test/api/graphql"


@pytest.mark.parametrize(
    "call, attempts",
    [
        (lambda rest: rest.repos.get("o", "r"), 2),  # GET
        (lambda rest: rest.activity.star_repo_for_authenticated_user("o", "r"), 2),  # PUT
        (lambda rest: rest.activity.unstar_repo_for_authenticated_user("o", "r"), 2),  # DELETE
        (lambda rest: rest.issues.create("o", "r", body={"title": "t"}), 1),  # POST
    ],
)
def test_rest_calls_safe_to_repeat_are_retried_after_a_read_timeout(call, attempts):
    mock = MockTransport()
    mock.respond(httpx.ReadTimeout("slow"), httpx.Response(200, json={}))
    rest = GitHubRestApi(token="t", transport=mock).with_options(
        retries=Retries(attempts=3, sleep=0)
    )
    try:
        call(rest)
    except httpx.ReadTimeout:
        pass
    assert len(mock.calls) == attempts


@pytest.mark.parametrize("operation, attempts", [("viewer", 2), ("mutations.add_star", 1)])
def test_graphql_queries_are_retried_and_mutations_are_not(operation, attempts):
    mock = MockTransport()
    mock.respond(httpx.ReadTimeout("slow"), graphql_response(data={}))

    class Retrying(GitHubGraphQLApi):
        retries = Retries(attempts=3, sleep=0)

    gh = Retrying(token="t", transport=mock)
    target = gh
    for part in operation.split("."):
        target = getattr(target, part)
    try:
        target() if operation == "viewer" else target(starrable_id="R_1")
    except httpx.ReadTimeout:
        pass
    assert len(mock.calls) == attempts
