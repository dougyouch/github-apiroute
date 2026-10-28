"""Python clients for GitHub's REST and GraphQL APIs, generated with apiroute.

    from github_apiroute.rest import GitHubRestApi
    from github_apiroute.graphql import GitHubGraphQLApi

    rest = GitHubRestApi(token=os.environ["GITHUB_TOKEN"])
    rest.repos.get(owner="octocat", repo="hello-world")

    gh = GitHubGraphQLApi(token=os.environ["GITHUB_TOKEN"])
    gh.models.viewer().viewer.login

Each client is imported on its own, and its sections and models load on first use.
"""
