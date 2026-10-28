"""Authentication for the generated GitHub clients.

This file is written by hand: the generated clients extend GitHubAuth (through the
`base_class` entries in apis.yaml), so regenerating never touches it.
"""

from collections.abc import Callable
from typing import Any

from apiroute import Client, RequestSpec

Token = str | Callable[[], str]

# The REST API version requested with every call: https://docs.github.com/en/rest/about-the-rest-api/api-versions
API_VERSION = "2022-11-28"

# REST methods GitHub implements so that repeating them is harmless: PUT sets (star a repo,
# add a collaborator, merge a pull request once) and DELETE removes
SAFE_TO_REPEAT = frozenset({"PUT", "DELETE"})


class GitHubAuth(Client):
    """A token for GitHub's REST and GraphQL APIs.

        rest = GitHubRestApi(token=os.environ["GITHUB_TOKEN"])
        gh = GitHubGraphQLApi(token=app.installation_token)  # or a function returning one

    token is a personal access token, a GitHub App installation token, or a function returning
    the current one (so a refreshing helper can be passed directly); without one, the REST API
    allows a few anonymous calls and the GraphQL API none. For GitHub Enterprise Server, pass
    base_url: "https://HOST/api/v3" for REST, "https://HOST/api" for GraphQL. With retries on,
    GET, PUT and DELETE calls (and GraphQL queries) are retried after a read timeout; POSTs and
    GraphQL mutations aren't.
    """

    headers = {
        "Authorization": lambda self: f"Bearer {self.current_token()}" if self._token else None,
        "X-GitHub-Api-Version": lambda self: self.api_version,
    }

    def __init__(
        self, token: Token | None = None, *, api_version: str = API_VERSION, **kwargs: Any
    ):
        super().__init__(**kwargs)
        self._token = token
        self.api_version = api_version

    def current_token(self) -> str | None:
        return self._token() if callable(self._token) else self._token

    def idempotent(self, request: RequestSpec) -> bool | None:
        return True if request.method in SAFE_TO_REPEAT else None
