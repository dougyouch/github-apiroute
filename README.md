# github-apiroute

[![CI](https://github.com/dougyouch/github-apiroute/actions/workflows/ci.yml/badge.svg)](https://github.com/dougyouch/github-apiroute/actions/workflows/ci.yml)
[![Build](https://github.com/dougyouch/github-apiroute/actions/workflows/build.yml/badge.svg)](https://github.com/dougyouch/github-apiroute/actions/workflows/build.yml)

Python clients for GitHub's REST and GraphQL APIs, generated with [apiroute](https://github.com/dougyouch/apiroute) and kept current by a weekly build. The REST client comes from [GitHub's published OpenAPI description](https://github.com/github/rest-api-description). The GraphQL client comes from GitHub's schema plus a set of operations written in this repository.

- **Two layers:** every call works with plain dicts (`gh.repos.get("octocat", "Hello-World")`), and `.models` takes and returns typed pydantic models (`gh.repos.models.get(...)`).
- **Sync and async:** add `.aio` to any call for the async version.
- **Lazy loading:** only the sections and models you use are imported. The REST client covers about 1,250 endpoints and 4,100 models, and a script that calls one of them stays fast.
- **Typed:** the package ships `py.typed`, and mypy checks the generated code.

## Installation

```bash
pip install github-apiroute    # or: uv add github-apiroute
```

It needs Python 3.10 or newer.

## Authentication

Both clients take a `token`: a personal access token, a GitHub App installation token, or a function that returns the current token (so a refreshing helper can be passed directly). It is sent as `Authorization: Bearer <token>`. Without a token, the REST API allows a few anonymous calls and the GraphQL API none.

For GitHub Enterprise Server, pass `base_url`: `https://HOST/api/v3` for REST and `https://HOST/api` for GraphQL.

## REST API

```python
import os
from github_apiroute.rest import GitHubRestApi

gh = GitHubRestApi(token=os.environ["GITHUB_TOKEN"])

repo = gh.repos.get("octocat", "Hello-World")  # a dict
repo = gh.repos.models.get("octocat", "Hello-World")  # FullRepository
print(repo.full_name, repo.stargazers_count)

issues = gh.issues.list_for_repo("octocat", "Hello-World", state="open", per_page=100)
issues = await gh.issues.aio.list_for_repo("octocat", "Hello-World")
```

Sections follow GitHub's REST documentation (`repos`, `issues`, `pulls`, `actions` and so on), and each method is named after its operation. Every call sends `X-GitHub-Api-Version: 2022-11-28`; pass `api_version=` to request another version. REST list endpoints are paged with `page` and `per_page`.

## GraphQL API

The GraphQL client runs the operations in [`operations/graphql/`](operations/graphql): a practical starter set. Each one becomes a typed method, and its result models contain exactly the fields the operation selects.

```python
from github_apiroute.graphql import GitHubGraphQLApi

gh = GitHubGraphQLApi(token=os.environ["GITHUB_TOKEN"])

me = gh.models.viewer().viewer
print(me.login, me.created_at)  # created_at is a datetime

for issue in gh.repos.models.issues(owner="octocat", name="Hello-World"):  # every page
    print(issue.number, issue.title)

for repo in gh.search.models.search_repositories(query="apiroute language:python"):
    print(repo.name_with_owner)

await gh.mutations.models.aio.add_star(starrable_id=repo.id)
```

| Section | Operations |
| --- | --- |
| (root) | `viewer`, `rate_limit` |
| `repos` | `repository`, `issue`, and paginated `issues`, `pull_requests`, `releases`, `stargazers` |
| `users` | `user`, paginated `user_repositories` |
| `search` | paginated `search_repositories`, `search_issues` |
| `mutations` | `create_issue`, `add_comment`, `add_star`, `remove_star` |

Paginated operations return an iterator that follows `pageInfo.endCursor` until the last page. A response with `errors` raises `apiroute.graphql.GraphQLError`.

To add an operation, write it in a `.graphql` file under `operations/graphql/` and regenerate (see [Development](#development)). The generator checks every operation against GitHub's schema.

## APIs

<!-- apis:start -->
| API | Import | Docs |
| --- | --- | --- |
| REST API | `from github_apiroute.rest import GitHubRestApi` | [docs](https://docs.github.com/en/rest) |
| GraphQL API | `from github_apiroute.graphql import GitHubGraphQLApi` | [docs](https://docs.github.com/en/graphql) |
<!-- apis:end -->

Errors raise `apiroute.UnexpectedResponse`, which carries the `.response`. For retries, transports and other client options, see [apiroute's README](https://github.com/dougyouch/apiroute#readme).

Retries are off unless you turn them on, for example with `gh.with_options(retries=3)`. Once on, failed connections are always retried. After a read timeout, though, only calls that are safe to repeat are retried: REST `GET`, `PUT` and `DELETE` (GitHub's `PUT`s set state, such as starring a repository), and GraphQL queries. REST `POST`s and GraphQL mutations aren't, so an issue or a comment can't be created twice.

## How this repository stays up to date

Nothing under `src/github_apiroute/` is written by hand except `auth.py` and `__init__.py`. Everything else is generated from the sources listed in [`apis.yaml`](apis.yaml):

1. Every Monday, the **[Build](.github/workflows/build.yml)** workflow does the following:
   - Upgrades apiroute to its newest release.
   - Downloads GitHub's REST description and introspects the GraphQL schema into [`specs/`](specs).
   - Regenerates the clients with `apiroute generate`.
   - Runs the lint and tests.
2. If anything changed, it commits the result to `main`:
   - `feat(specs): ...` when GitHub changed a spec or schema, which produces a minor release.
   - `fix(codegen): ...` when only a newer apiroute changed the generated code, which produces a patch release.
3. **[Release](.github/workflows/release.yml)** (release-please) then updates its release PR, tests it, merges it and publishes the new version to [PyPI](https://pypi.org/project/github-apiroute/). No one has to do anything.

[CI](.github/workflows/ci.yml) checks every push. It lints, runs the tests on Python 3.10 to 3.14, and regenerates from the committed specs to confirm the committed code matches them exactly.

Because `specs/` is committed, `git log -p specs/` shows exactly what GitHub changed and when.

## Development

```bash
uv sync
GITHUB_TOKEN="$(gh auth token)" uv run python scripts/generate.py --fetch   # latest specs, regenerate
uv run python scripts/generate.py --only graphql   # regenerate one API from its committed spec
uv run pytest
uv run ruff check . && uv run ruff format --check .
```

Fetching the GraphQL schema needs a token in `GITHUB_TOKEN`; regenerating from the committed specs doesn't. Auth lives in [`src/github_apiroute/auth.py`](src/github_apiroute/auth.py), which the generated clients extend.

## License

MIT
