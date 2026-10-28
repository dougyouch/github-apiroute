"""The GraphQL client: operations sent as written, typed results, and pagination."""

import asyncio
import datetime

from apiroute.testing import MockTransport, graphql_response

from github_apiroute.graphql import GitHubGraphQLApi

VIEWER = {
    "id": "U_1",
    "login": "octocat",
    "name": "The Octocat",
    "bio": None,
    "company": "@github",
    "location": None,
    "url": "https://github.com/octocat",
    "avatarUrl": "https://avatars.githubusercontent.com/u/583231",
    "createdAt": "2011-01-25T18:44:36Z",
}


def test_a_typed_query():
    mock = MockTransport()
    mock.respond(graphql_response(data={"viewer": VIEWER}))
    viewer = GitHubGraphQLApi(token="t", transport=mock).models.viewer().viewer
    assert viewer.login == "octocat"
    assert viewer.created_at == datetime.datetime(
        2011, 1, 25, 18, 44, 36, tzinfo=datetime.timezone.utc
    )
    sent = mock.last.json()
    assert sent["operationName"] == "Viewer" and sent["query"].startswith("query Viewer {")
    assert str(mock.last.url) == "https://api.github.com/graphql"
    assert mock.last.headers["Authorization"] == "Bearer t"


def issues_page(numbers, cursor=None, more=False):
    nodes = [
        {
            "id": f"I_{n}",
            "number": n,
            "title": f"Issue {n}",
            "state": "OPEN",
            "url": f"https://github.com/o/r/issues/{n}",
            "createdAt": "2026-01-01T00:00:00Z",
            "updatedAt": "2026-01-02T00:00:00Z",
            "closedAt": None,
            "author": {"login": "octocat", "url": "https://github.com/octocat", "avatarUrl": "x"},
            "labels": {"nodes": [{"name": "bug", "color": "d73a4a"}]},
            "comments": {"totalCount": 0},
        }
        for n in numbers
    ]
    connection = {"pageInfo": {"hasNextPage": more, "endCursor": cursor}, "nodes": nodes}
    return graphql_response(data={"repository": {"issues": connection}})


def test_paginated_issues_across_pages():
    mock = MockTransport()
    mock.respond(issues_page([3, 2], "c1", True), issues_page([1]))
    issues = list(
        GitHubGraphQLApi(token="t", transport=mock).repos.models.issues(owner="o", name="r")
    )
    assert [issue.number for issue in issues] == [3, 2, 1]
    assert issues[0].labels.nodes[0].name == "bug"
    assert [call.graphql_variables for call in mock.calls] == [
        {"owner": "o", "name": "r"},
        {"owner": "o", "name": "r", "after": "c1"},
    ]
    assert "@paginate" not in mock.last.json()["query"]


def test_async_and_a_mutation():
    mock = MockTransport()
    mock.respond(
        graphql_response(
            data={
                "addStar": {
                    "starrable": {"id": "R_1", "stargazerCount": 2, "viewerHasStarred": True}
                }
            }
        )
    )
    gh = GitHubGraphQLApi(token="t", async_transport=mock.aio)
    result = asyncio.run(gh.mutations.models.aio.add_star(starrable_id="R_1"))
    assert result.add_star.starrable.viewer_has_starred is True
    assert mock.last.graphql_variables == {"starrableId": "R_1"}
