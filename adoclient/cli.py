"""Command-line entry point for pulling info out of Azure DevOps on demand.

Usage:
    python -m adoclient.cli projects
    python -m adoclient.cli repos
    python -m adoclient.cli commits --repo <repo-id-or-name>
    python -m adoclient.cli prs [--repo <repo-id-or-name>]
    python -m adoclient.cli workitems --wiql "select [System.Id] from workitems"
    python -m adoclient.cli builds
    python -m adoclient.cli pipelines
"""

import argparse
import json
import sys

from dotenv import load_dotenv

from .client import AdoClient, AdoConfigError

DEFAULT_WIQL = (
    "select [System.Id], [System.Title], [System.State] "
    "from WorkItems where [System.AssignedTo] = @Me and [System.State] <> 'Closed' "
    "order by [System.ChangedDate] desc"
)


def build_parser():
    parser = argparse.ArgumentParser(description="Pull information from Azure DevOps using a PAT")
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("projects", help="List projects in the organization")
    sub.add_parser("teams", help="List teams in the current project")
    sub.add_parser("repos", help="List repositories in the current project")

    commits = sub.add_parser("commits", help="List recent commits for a repo")
    commits.add_argument("--repo", required=True, help="Repository id or name")
    commits.add_argument("--top", type=int, default=20)

    prs = sub.add_parser("prs", help="List pull requests")
    prs.add_argument("--repo", help="Repository id or name (omit for all repos in the project)")
    prs.add_argument("--status", default="active", choices=["active", "completed", "abandoned", "all"])

    workitems = sub.add_parser("workitems", help="Query work items with WIQL")
    workitems.add_argument("--wiql", default=DEFAULT_WIQL, help="WIQL query string")

    builds = sub.add_parser("builds", help="List recent pipeline builds")
    builds.add_argument("--top", type=int, default=20)

    sub.add_parser("pipelines", help="List pipeline definitions")

    return parser


def main(argv=None):
    load_dotenv()
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        client = AdoClient()
    except AdoConfigError as exc:
        print(f"Configuration error: {exc}", file=sys.stderr)
        print("Copy .env.example to .env and fill in ADO_ORG / ADO_PROJECT / ADO_PAT.", file=sys.stderr)
        return 1

    if args.command == "projects":
        result = client.list_projects()
    elif args.command == "teams":
        result = client.list_teams()
    elif args.command == "repos":
        result = client.list_repos()
    elif args.command == "commits":
        result = client.list_commits(args.repo, top=args.top)
    elif args.command == "prs":
        result = client.list_pull_requests(repo_id=args.repo, status=args.status)
    elif args.command == "workitems":
        result = client.query_work_items(args.wiql)
    elif args.command == "builds":
        result = client.list_builds(top=args.top)
    elif args.command == "pipelines":
        result = client.list_pipelines()
    else:
        parser.error(f"Unknown command: {args.command}")
        return 2

    print(json.dumps(result, indent=2, default=str))
    return 0


if __name__ == "__main__":
    sys.exit(main())
