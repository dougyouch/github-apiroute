"""Typed REST calls against live GitHub data: each response must validate as its model."""

import asyncio

import pytest
from pydantic import BaseModel

OWNER, REPO = "pallets", "flask"  # a busy public repository: labels, milestones, releases, CI
MINE = ("dougyouch", "apiroute")
FEW = {"per_page": 3}

CALLS = {
    # repos
    "repos.get": lambda r: r.repos.models.get(OWNER, REPO),
    "repos.list_branches": lambda r: r.repos.models.list_branches(OWNER, REPO, **FEW),
    "repos.get_branch": lambda r: r.repos.models.get_branch(OWNER, REPO, "main"),
    "repos.list_commits": lambda r: r.repos.models.list_commits(OWNER, REPO, **FEW),
    "repos.get_commit": lambda r: r.repos.models.get_commit(OWNER, REPO, "main", **FEW),
    "repos.compare_commits": lambda r: r.repos.models.compare_commits(
        *MINE, "v2.2.0...v2.3.0", **FEW
    ),
    "repos.get_combined_status_for_ref": lambda r: r.repos.models.get_combined_status_for_ref(
        OWNER, REPO, "main", **FEW
    ),
    "repos.list_contributors": lambda r: r.repos.models.list_contributors(OWNER, REPO, **FEW),
    "repos.get_community_profile_metrics": lambda r: r.repos.models.get_community_profile_metrics(
        OWNER, REPO
    ),
    "repos.get_readme": lambda r: r.repos.models.get_readme(OWNER, REPO),
    "repos.get_content": lambda r: r.repos.models.get_content(OWNER, REPO, "pyproject.toml"),
    "repos.list_tags": lambda r: r.repos.models.list_tags(OWNER, REPO, **FEW),
    "repos.list_releases": lambda r: r.repos.models.list_releases(OWNER, REPO, **FEW),
    "repos.get_latest_release": lambda r: r.repos.models.get_latest_release(OWNER, REPO),
    "repos.list_for_user": lambda r: r.repos.models.list_for_user("octocat", **FEW),
    "repos.list_for_org": lambda r: r.repos.models.list_for_org("pallets", **FEW),
    "repos.list_languages": lambda r: r.repos.models.list_languages(OWNER, REPO),
    "repos.list_deployments": lambda r: r.repos.models.list_deployments(OWNER, REPO, **FEW),
    # issues
    "issues.list_for_repo": lambda r: r.issues.models.list_for_repo(
        OWNER, REPO, state="all", **FEW
    ),
    "issues.get": lambda r: r.issues.models.get(OWNER, REPO, 5000),
    "issues.list_comments": lambda r: r.issues.models.list_comments(OWNER, REPO, 5000, **FEW),
    "issues.list_events": lambda r: r.issues.models.list_events(OWNER, REPO, 5000, **FEW),
    "issues.list_events_for_timeline": lambda r: r.issues.models.list_events_for_timeline(
        OWNER, REPO, 5000, **FEW
    ),
    "issues.list_labels_for_repo": lambda r: r.issues.models.list_labels_for_repo(
        OWNER, REPO, per_page=50
    ),
    "issues.list_milestones": lambda r: r.issues.models.list_milestones(
        OWNER, REPO, state="all", **FEW
    ),
    # pulls
    "pulls.list": lambda r: r.pulls.models.list(OWNER, REPO, state="all", **FEW),
    "pulls.get": lambda r: r.pulls.models.get(OWNER, REPO, 5000),
    "pulls.list_commits": lambda r: r.pulls.models.list_commits(OWNER, REPO, 5000, **FEW),
    "pulls.list_files": lambda r: r.pulls.models.list_files(OWNER, REPO, 5000, **FEW),
    "pulls.list_reviews": lambda r: r.pulls.models.list_reviews(OWNER, REPO, 5000, **FEW),
    "pulls.list_review_comments_for_repo": lambda r: r.pulls.models.list_review_comments_for_repo(
        OWNER, REPO, **FEW
    ),
    # git
    "git.get_ref": lambda r: r.git.models.get_ref(OWNER, REPO, "heads/main"),
    "git.list_matching_refs": lambda r: r.git.models.list_matching_refs(OWNER, REPO, "tags/3."),
    "git.get_tree": lambda r: r.git.models.get_tree(OWNER, REPO, "main"),
    # actions and checks
    "actions.list_repo_workflows": lambda r: r.actions.models.list_repo_workflows(
        OWNER, REPO, **FEW
    ),
    "actions.list_workflow_runs_for_repo": lambda r: r.actions.models.list_workflow_runs_for_repo(
        OWNER, REPO, **FEW
    ),
    "actions.list_artifacts_for_repo": lambda r: r.actions.models.list_artifacts_for_repo(
        *MINE, **FEW
    ),
    "checks.list_for_ref": lambda r: r.checks.models.list_for_ref(OWNER, REPO, "main", **FEW),
    "checks.list_suites_for_ref": lambda r: r.checks.models.list_suites_for_ref(
        OWNER, REPO, "main", **FEW
    ),
    # activity
    "activity.list_public_events_for_user": lambda r: r.activity.models.list_public_events_for_user(
        "octocat", **FEW
    ),
    "activity.list_repo_events": lambda r: r.activity.models.list_repo_events(OWNER, REPO, **FEW),
    "activity.list_stargazers_for_repo": lambda r: r.activity.models.list_stargazers_for_repo(
        *MINE, **FEW
    ),
    # GitHub answers 404 for a large repository's watchers and stargazers, so use a small one
    "activity.list_watchers_for_repo": lambda r: r.activity.models.list_watchers_for_repo(
        *MINE, **FEW
    ),
    # users and orgs
    "users.get_by_username": lambda r: r.users.models.get_by_username("octocat"),
    "users.list_followers_for_user": lambda r: r.users.models.list_followers_for_user(
        "octocat", **FEW
    ),
    "users.list_public_keys_for_user": lambda r: r.users.models.list_public_keys_for_user(
        "octocat", **FEW
    ),
    "orgs.get": lambda r: r.orgs.models.get("pallets"),
    "orgs.list_public_members": lambda r: r.orgs.models.list_public_members("pallets", **FEW),
    # search
    "search.repos": lambda r: r.search.models.repos(q="flask language:python", **FEW),
    "search.issues_and_pull_requests": lambda r: r.search.models.issues_and_pull_requests(
        q="repo:pallets/flask is:issue", **FEW
    ),
    "search.users": lambda r: r.search.models.users(q="octocat", **FEW),
    "search.commits": lambda r: r.search.models.commits(q="repo:pallets/flask fix", **FEW),
    "search.topics": lambda r: r.search.models.topics(q="python", **FEW),
    # gists and reference data
    "gists.list_public": lambda r: r.gists.models.list_public(**FEW),
    "gists.list_for_user": lambda r: r.gists.models.list_for_user("octocat", **FEW),
    "licenses.get_all_commonly_used": lambda r: r.licenses.models.get_all_commonly_used(),
    "licenses.get_for_repo": lambda r: r.licenses.models.get_for_repo(OWNER, REPO),
    "codes_of_conduct.get_all_codes_of_conduct": lambda r: (
        r.codes_of_conduct.models.get_all_codes_of_conduct()
    ),
    "gitignore.get_template": lambda r: r.gitignore.models.get_template("Python"),
    "meta.get": lambda r: r.meta.models.get(),
    "rate_limit.get": lambda r: r.rate_limit.models.get(),
    "reactions.list_for_issue": lambda r: r.reactions.models.list_for_issue(
        OWNER, REPO, 5000, **FEW
    ),
}


# about the signed-in user: these need a user's token
USER_CALLS = {
    "repos.list_for_authenticated_user": lambda r: r.repos.models.list_for_authenticated_user(
        **FEW
    ),
    "issues.list_for_authenticated_user": lambda r: r.issues.models.list_for_authenticated_user(
        filter="all", state="all", **FEW
    ),
    "activity.list_notifications_for_authenticated_user": lambda r: (
        r.activity.models.list_notifications_for_authenticated_user(all=True, **FEW)
    ),
    "activity.list_repos_starred_by_authenticated_user": lambda r: (
        r.activity.models.list_repos_starred_by_authenticated_user(**FEW)
    ),
    "users.get_authenticated": lambda r: r.users.models.get_authenticated(),
    "orgs.list_for_authenticated_user": lambda r: r.orgs.models.list_for_authenticated_user(**FEW),
}


def _typed(value) -> bool:
    """A model, or a list or dict whose values are models (or plain JSON values)."""
    if isinstance(value, BaseModel):
        return True
    if isinstance(value, list):
        return all(_typed(v) or not isinstance(v, dict) for v in value)
    return isinstance(value, dict | str)


@pytest.mark.parametrize("name", list(CALLS))
def test_typed_rest_call(rest, name):
    assert _typed(CALLS[name](rest))


@pytest.mark.parametrize("name", list(USER_CALLS))
def test_typed_rest_call_for_the_signed_in_user(rest, signed_in, name):
    assert _typed(USER_CALLS[name](rest))


def test_async_typed_rest_call(rest):
    repo = asyncio.run(rest.repos.models.aio.get(OWNER, REPO))
    assert repo.full_name == f"{OWNER}/{REPO}"
