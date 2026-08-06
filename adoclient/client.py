"""Thin client for pulling information out of Azure DevOps using a PAT.

Auth: Azure DevOps accepts HTTP Basic auth with an empty username and the
PAT as the password, so no OAuth flow is needed.
"""

import base64
import os

import requests

API_VERSION = "7.1"
DEFAULT_BASE_URL = "https://dev.azure.com"


class AdoConfigError(RuntimeError):
    pass


class AdoClient:
    def __init__(self, org=None, project=None, pat=None, base_url=None):
        self.org = org or os.environ.get("ADO_ORG")
        self.project = project or os.environ.get("ADO_PROJECT")
        self.pat = pat or os.environ.get("ADO_PAT")
        self.base_url = base_url or os.environ.get("ADO_BASE_URL") or DEFAULT_BASE_URL

        if not self.org:
            raise AdoConfigError("Missing Azure DevOps organization (set ADO_ORG)")
        if not self.pat:
            raise AdoConfigError("Missing Azure DevOps PAT (set ADO_PAT)")

        token = base64.b64encode(f":{self.pat}".encode()).decode()
        self._session = requests.Session()
        self._session.headers.update(
            {
                "Authorization": f"Basic {token}",
                "Accept": "application/json",
            }
        )

    def _org_url(self, path):
        return f"{self.base_url}/{self.org}/{path.lstrip('/')}"

    def _project_url(self, path, project=None):
        proj = project or self.project
        if not proj:
            raise AdoConfigError("This call requires a project (set ADO_PROJECT or pass project=)")
        return f"{self.base_url}/{self.org}/{proj}/{path.lstrip('/')}"

    def _get(self, url, params=None):
        params = dict(params or {})
        params.setdefault("api-version", API_VERSION)
        resp = self._session.get(url, params=params)
        resp.raise_for_status()
        return resp.json()

    def _post(self, url, json=None, params=None):
        params = dict(params or {})
        params.setdefault("api-version", API_VERSION)
        resp = self._session.post(url, params=params, json=json)
        resp.raise_for_status()
        return resp.json()

    # --- Org overview -----------------------------------------------------

    def list_projects(self):
        return self._get(self._org_url("_apis/projects")).get("value", [])

    def list_teams(self, project=None):
        return self._get(self._project_url("_apis/teams", project)).get("value", [])

    # --- Repos / commits / PRs --------------------------------------------

    def list_repos(self, project=None):
        return self._get(self._project_url("_apis/git/repositories", project)).get("value", [])

    def list_commits(self, repo_id, project=None, top=20):
        url = self._project_url(f"_apis/git/repositories/{repo_id}/commits", project)
        return self._get(url, params={"searchCriteria.top": top}).get("value", [])

    def list_pull_requests(self, repo_id=None, project=None, status="active"):
        if repo_id:
            url = self._project_url(f"_apis/git/repositories/{repo_id}/pullrequests", project)
        else:
            url = self._project_url("_apis/git/pullrequests", project)
        return self._get(url, params={"searchCriteria.status": status}).get("value", [])

    # --- Work items --------------------------------------------------------

    def query_work_items(self, wiql, project=None):
        url = self._project_url("_apis/wit/wiql", project)
        result = self._post(url, json={"query": wiql})
        ids = [item["id"] for item in result.get("workItems", [])]
        return self.get_work_items(ids) if ids else []

    def get_work_items(self, ids):
        if not ids:
            return []
        url = self._org_url("_apis/wit/workitems")
        return self._get(url, params={"ids": ",".join(str(i) for i in ids)}).get("value", [])

    # --- Pipelines / builds -------------------------------------------------

    def list_builds(self, project=None, top=20):
        url = self._project_url("_apis/build/builds", project)
        return self._get(url, params={"$top": top}).get("value", [])

    def list_pipelines(self, project=None):
        return self._get(self._project_url("_apis/pipelines", project)).get("value", [])
