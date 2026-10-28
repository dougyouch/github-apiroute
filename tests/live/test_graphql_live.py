"""Every GraphQL query in operations/graphql against live data. Mutations aren't run."""

import asyncio
from itertools import islice

import pytest

MINE = {"owner": "dougyouch", "name": "apiroute"}
BUSY = {"owner": "pallets", "name": "flask"}


def test_viewer(gql, signed_in):
    viewer = gql.models.viewer().viewer
    assert viewer.login and viewer.created_at.year >= 2008


def test_rate_limit(gql):
    assert gql.models.rate_limit().rate_limit.limit > 0


def test_repository(gql):
    repo = gql.repos.models.repository(**BUSY).repository
    assert repo.name_with_owner == "pallets/flask" and repo.default_branch_ref


def test_issue(gql):
    assert gql.repos.models.issue(**BUSY, number=6175).repository.issue.number == 6175


@pytest.mark.parametrize(
    ("operation", "variables"),
    [
        ("issues", BUSY),
        ("pull_requests", BUSY),
        ("releases", BUSY),
        # GitHub lists no stargazers for large repositories
        ("stargazers", {"owner": "dougyouch", "name": "mappable"}),
    ],
)
def test_paginated_repository_connections(gql, operation, variables):
    items = list(islice(getattr(gql.repos.models, operation)(**variables), 120))
    assert items and len({id(item) for item in items}) == len(items)


def test_issues_cross_a_page_boundary(gql):
    issues = gql.repos.models.issues(**BUSY, states=["OPEN", "CLOSED"])
    numbers = [issue.number for issue in islice(issues, 120)]
    assert len(numbers) == 120 and len(set(numbers)) == 120  # pages hold 100 at most


def test_user(gql):
    user = gql.users.models.user(login="octocat").user
    assert user.login == "octocat" and user.followers.total_count > 0


def test_user_repositories(gql):
    assert list(islice(gql.users.models.user_repositories(login="octocat"), 5))


def test_search_repositories(gql):
    found = list(islice(gql.search.models.search_repositories(query="flask language:python"), 5))
    assert found and all(repo.name_with_owner for repo in found)


def test_search_issues_mixes_issues_and_pull_requests(gql):
    found = list(islice(gql.search.models.search_issues(query="repo:pallets/flask"), 60))
    kinds = {type(node).__name__ for node in found}
    assert {"SearchIssuesSearchNodesIssue", "SearchIssuesSearchNodesPullRequest"} <= kinds


def test_dict_layer_and_async(gql):
    assert gql.rate_limit()["rateLimit"]["limit"] > 0
    assert asyncio.run(gql.repos.models.aio.repository(**MINE)).repository.name_with_owner
