# Crowe-Claude: Azure DevOps PAT client

A small Python client + CLI for pulling information out of Azure DevOps on
demand, authenticated with a Personal Access Token (PAT).

## Setup

```bash
pip install -r requirements.txt
cp .env.example .env
```

Fill in `.env`:

- `ADO_ORG` — your Azure DevOps organization name (from `https://dev.azure.com/<org>`)
- `ADO_PROJECT` — default project to query
- `ADO_PAT` — a Personal Access Token, created at
  `https://dev.azure.com/<org>/_usersSettings/tokens`. Scope it read-only
  (Work Items, Code, Build, Project and Team) unless you need write access.

`.env` is gitignored — never commit a real PAT.

## Usage

```bash
python -m adoclient.cli projects
python -m adoclient.cli teams
python -m adoclient.cli repos
python -m adoclient.cli commits --repo <repo-id-or-name>
python -m adoclient.cli prs --status active
python -m adoclient.cli workitems --wiql "select [System.Id] from workitems where [System.AssignedTo] = @Me"
python -m adoclient.cli builds
python -m adoclient.cli pipelines
```

Each command prints JSON to stdout, so it composes with `jq` or redirection.

## Using it as a library

```python
from adoclient import AdoClient

client = AdoClient()  # reads ADO_ORG / ADO_PROJECT / ADO_PAT from the environment
projects = client.list_projects()
repos = client.list_repos()
```
