"""Module for Jira project operations."""

import logging
from typing import Any

from ..models import JiraProject
from ..models.jira.search import JiraSearchResult
from ..models.jira.version import JiraVersion
from .client import JiraClient
from .protocols import SearchOperationsProto

logger = logging.getLogger("mcp-jira")


class ProjectsMixin(JiraClient, SearchOperationsProto):
    """Mixin for Jira project operations.

    This mixin provides methods for retrieving and working with Jira projects,
    including project details, components, versions, and other project-related operations.
    """

    def get_all_projects(self, include_archived: bool = False) -> list[dict[str, Any]]:
        """
        Get all projects visible to the current user.

        Args:
            include_archived: Whether to include archived projects

        Returns:
            List of project data dictionaries
        """
        try:
            params = {}
            if include_archived:
                params["includeArchived"] = "true"

            projects = self.jira.projects(included_archived=include_archived)
            return projects if isinstance(projects, list) else []

        except Exception as e:
            logger.error(f"Error getting all projects: {str(e)}")
            return []

    def get_project(self, project_key: str) -> dict[str, Any] | None:
        """
        Get project information by key.

        Args:
            project_key: The project key (e.g. 'PROJ')

        Returns:
            Project data or None if not found
        """
        try:
            project_data = self.jira.project(project_key)
            if not isinstance(project_data, dict):
                msg = f"Unexpected return value type from `jira.project`: {type(project_data)}"
                logger.error(msg)
                raise TypeError(msg)
            return project_data
        except Exception as e:
            logger.warning(f"Error getting project {project_key}: {e}")
            return None

    def get_project_model(self, project_key: str) -> JiraProject | None:
        """
        Get project information as a JiraProject model.

        Args:
            project_key: The project key (e.g. 'PROJ')

        Returns:
            JiraProject model or None if not found
        """
        project_data = self.get_project(project_key)
        if not project_data:
            return None

        return JiraProject.from_api_response(project_data)

    def project_exists(self, project_key: str) -> bool:
        """
        Check if a project exists.

        Args:
            project_key: The project key to check

        Returns:
            True if the project exists, False otherwise
        """
        try:
            project = self.get_project(project_key)
            return project is not None

        except Exception:
            return False

    def get_project_components(self, project_key: str) -> list[dict[str, Any]]:
        """
        Get all components for a project.

        Args:
            project_key: The project key

        Returns:
            List of component data dictionaries
        """
        try:
            components = self.jira.get_project_components(key=project_key)
            return components if isinstance(components, list) else []

        except Exception as e:
            logger.error(
                f"Error getting components for project {project_key}: {str(e)}"
            )
            return []

    def get_project_versions(self, project_key: str) -> list[dict[str, Any]]:
        """
        Get all versions for a project.

        Args:
            project_key: The project key.

        Returns:
            List of version data dictionaries
        """
        try:
            raw_versions = self.jira.get_project_versions(key=project_key)
            if not isinstance(raw_versions, list):
                return []
            versions: list[dict[str, Any]] = []
            for v in raw_versions:
                ver = JiraVersion.from_api_response(v)
                versions.append(ver.to_simplified_dict())
            return versions
        except Exception as e:
            logger.error(f"Error getting versions for project {project_key}: {str(e)}")
            return []

    def get_project_roles(self, project_key: str) -> dict[str, Any]:
        """
        Get all roles for a project.

        Args:
            project_key: The project key

        Returns:
            Dictionary of role names mapped to role details
        """
        try:
            roles = self.jira.get_project_roles(project_key=project_key)
            return roles if isinstance(roles, dict) else {}

        except Exception as e:
            logger.error(f"Error getting roles for project {project_key}: {str(e)}")
            return {}

    def get_project_role_members(
        self, project_key: str, role_id: str
    ) -> list[dict[str, Any]]:
        """
        Get members assigned to a specific role in a project.

        Args:
            project_key: The project key
            role_id: The role ID

        Returns:
            List of role members
        """
        try:
            members = self.jira.get_project_actors_for_role_project(
                project_key=project_key, role_id=role_id
            )
            # Extract the actors from the response
            actors = []
            if isinstance(members, dict) and "actors" in members:
                actors = members.get("actors", [])
            return actors

        except Exception as e:
            logger.error(
                f"Error getting role members for project {project_key}, role {role_id}: {str(e)}"
            )
            return []

    def get_project_permission_scheme(self, project_key: str) -> dict[str, Any] | None:
        """
        Get the permission scheme for a project.

        Args:
            project_key: The project key

        Returns:
            Permission scheme data if found, None otherwise
        """
        try:
            scheme = self.jira.get_project_permission_scheme(
                project_id_or_key=project_key
            )
            if not isinstance(scheme, dict):
                msg = f"Unexpected return value type from `jira.get_project_permission_scheme`: {type(scheme)}"
                logger.error(msg)
                raise TypeError(msg)
            return scheme

        except Exception as e:
            logger.error(
                f"Error getting permission scheme for project {project_key}: {str(e)}"
            )
            return None

    def get_project_notification_scheme(
        self, project_key: str
    ) -> dict[str, Any] | None:
        """
        Get the notification scheme for a project.

        Args:
            project_key: The project key

        Returns:
            Notification scheme data if found, None otherwise
        """
        try:
            scheme = self.jira.get_project_notification_scheme(
                project_id_or_key=project_key
            )
            if not isinstance(scheme, dict):
                msg = f"Unexpected return value type from `jira.get_project_notification_scheme`: {type(scheme)}"
                logger.error(msg)
                raise TypeError(msg)
            return scheme

        except Exception as e:
            logger.error(
                f"Error getting notification scheme for project {project_key}: {str(e)}"
            )
            return None

    def get_project_issue_types(self, project_key: str) -> list[dict[str, Any]]:
        """
        Get all issue types available for a project.

        Args:
            project_key: The project key

        Returns:
            List of issue type data dictionaries
        """
        try:
            meta = self.jira.issue_createmeta_issuetypes(project=project_key)
            if not isinstance(meta, dict):
                msg = f"Unexpected return value type from `jira.issue_createmeta_issuetypes`: {type(meta)}"
                logger.error(msg)
                raise TypeError(msg)

            # The new createmeta endpoint returns paginated "values" array
            issue_types = meta.get("values", [])
            if not issue_types:
                # Fallback for older response format
                projects = meta.get("projects", [])
                if projects and "issuetypes" in projects[0]:
                    issue_types = projects[0]["issuetypes"]

            return issue_types

        except Exception as e:
            logger.error(
                f"Error getting issue types for project {project_key}: {str(e)}"
            )
            return []

    def get_project_issues_count(self, project_key: str) -> int:
        """
        Get the total number of issues in a project.

        Args:
            project_key: The project key

        Returns:
            Count of issues in the project
        """
        try:
            # Use JQL to count issues in the project
            jql = f'project = "{project_key}"'
            result = self.jira.jql(jql=jql, fields="key", limit=1)
            if not isinstance(result, dict):
                msg = f"Unexpected return value type from `jira.jql`: {type(result)}"
                logger.error(msg)
                raise TypeError(msg)

            # Extract total from the response
            total = 0
            if isinstance(result, dict) and "total" in result:
                total = result.get("total", 0)

            return total

        except Exception as e:
            logger.error(
                f"Error getting issue count for project {project_key}: {str(e)}"
            )
            return 0

    def get_project_issues(
        self, project_key: str, start: int = 0, limit: int = 50
    ) -> JiraSearchResult:
        """
        Get issues for a specific project.

        Args:
            project_key: The project key
            start: Index of the first issue to return
            limit: Maximum number of issues to return

        Returns:
            List of JiraIssue models representing the issues
        """
        try:
            # Use JQL to get issues in the project
            jql = f'project = "{project_key}"'

            return self.search_issues(jql, start=start, limit=limit)

        except Exception as e:
            logger.error(f"Error getting issues for project {project_key}: {str(e)}")
            return JiraSearchResult(issues=[], total=0)

    def get_project_keys(self) -> list[str]:
        """
        Get all project keys.

        Returns:
            List of project keys
        """
        try:
            projects = self.get_all_projects()
            project_keys: list[str] = []
            for project in projects:
                key = project.get("key")
                if not isinstance(key, str):
                    msg = f"Unexpected return value type from `get_all_projects`: {type(key)}"
                    logger.error(msg)
                    raise TypeError(msg)
                project_keys.append(key)
            return project_keys

        except Exception as e:
            logger.error(f"Error getting project keys: {str(e)}")
            return []

    def get_project_leads(self) -> dict[str, str]:
        """
        Get all project leads mapped to their projects.

        Returns:
            Dictionary mapping project keys to lead usernames
        """
        try:
            projects = self.get_all_projects()
            leads = {}

            for project in projects:
                if "key" in project and "lead" in project:
                    key = project.get("key")
                    lead = project.get("lead", {})

                    # Handle different formats of lead information
                    lead_name = None
                    if isinstance(lead, dict):
                        lead_name = lead.get("name") or lead.get("displayName")
                    elif isinstance(lead, str):
                        lead_name = lead

                    if key and lead_name:
                        leads[key] = lead_name

            return leads

        except Exception as e:
            logger.error(f"Error getting project leads: {str(e)}")
            return {}

    def get_user_accessible_projects(self, username: str) -> list[dict[str, Any]]:
        """
        Get projects that a specific user can access.

        Args:
            username: The username to check access for

        Returns:
            List of accessible project data dictionaries
        """
        try:
            # This requires admin permissions
            # For non-admins, a different approach might be needed
            all_projects = self.get_all_projects()
            accessible_projects = []

            for project in all_projects:
                project_key = project.get("key")
                if not project_key:
                    continue

                try:
                    # Check if user has browse permission for this project
                    browse_users = (
                        self.jira.get_users_with_browse_permission_to_a_project(
                            username=username, project_key=project_key, limit=1
                        )
                    )

                    # If the user is in the list, they have access
                    user_has_access = False
                    if isinstance(browse_users, list):
                        for user in browse_users:
                            if isinstance(user, dict) and user.get("name") == username:
                                user_has_access = True
                                break

                    if user_has_access:
                        accessible_projects.append(project)

                except Exception:
                    # Skip projects that cause errors
                    continue

            return accessible_projects

        except Exception as e:
            logger.error(
                f"Error getting accessible projects for user {username}: {str(e)}"
            )
            return []

    def create_project_version(
        self,
        project_key: str,
        name: str,
        start_date: str | None = None,
        release_date: str | None = None,
        description: str | None = None,
    ) -> dict[str, Any]:
        """
        Create a new version in the specified Jira project.

        Args:
            project_key: The project key (e.g., 'PROJ')
            name: The name of the version
            start_date: The start date (YYYY-MM-DD, optional)
            release_date: The release date (YYYY-MM-DD, optional)
            description: Description of the version (optional)

        Returns:
            The created version object as returned by Jira
        """
        return self.create_version(
            project=project_key,
            name=name,
            start_date=start_date,
            release_date=release_date,
            description=description,
        )

    def create_project(
        self,
        key: str,
        name: str,
        project_type_key: str,
        lead_account_id: str,
        description: str | None = None,
        project_template_key: str | None = None,
        assignee_type: str = "UNASSIGNED",
    ) -> dict[str, Any]:
        """
        Create a new Jira project.

        Requires the 'Administer Jira' global permission.

        Args:
            key: The project key (2-10 uppercase characters, e.g., 'PROJ')
            name: The name of the project
            project_type_key: The type of project ('software', 'business', 'service_desk')
            lead_account_id: The account ID of the project lead
            description: Optional project description (markdown, converted to ADF for Cloud)
            project_template_key: Optional template key
                (e.g., 'com.pyxis.greenhopper.jira:gh-scrum-template')
            assignee_type: Default assignee type ('PROJECT_LEAD' or 'UNASSIGNED')

        Returns:
            The created project data as returned by Jira API

        Raises:
            ValueError: If the API returns an unexpected response
            Exception: If the API call fails (e.g., permission denied, invalid params)
        """
        # Jira Cloud REQUIRES ``projectTemplateKey`` on POST /rest/api/3/project
        # even when it's documented as "optional" by some older clients. When
        # the caller passes "" or None, the API returns generic
        # ``HTTP 400: Invalid request payload`` with no structured detail —
        # which is what blocked production attempts to create project JLP
        # at 2026-05-16 00:32:59 ICT (4 attempts, all 400). Pick a safe
        # default per ``project_type_key`` so an unknowing caller still
        # gets a project, and the agent doesn't have to learn Atlassian's
        # internal template-key naming scheme.
        _CLOUD_DEFAULT_TEMPLATE = {
            "software": "com.pyxis.greenhopper.jira:gh-simplified-agility-scrum",
            "business": "com.atlassian.jira-core-project-templates:jira-core-simplified-process-control",
            "service_desk": "com.atlassian.servicedesk:simplified-it-service-desk",
        }
        if not project_template_key:
            project_template_key = _CLOUD_DEFAULT_TEMPLATE.get(project_type_key)

        payload: dict[str, Any] = {
            "key": key.upper(),
            "name": name,
            "projectTypeKey": project_type_key,
            "leadAccountId": lead_account_id,
            "assigneeType": assignee_type,
        }

        if description:
            # ⚠️ Project description is PLAIN STRING, not ADF.
            # ``POST /rest/api/3/project`` schema says ``description: string``
            # — unlike issue ``description`` which is ADF on Cloud. Passing
            # an ADF dict here triggers ``HTTP 400: Invalid request payload``
            # (production incident 2026-05-16 09:32 ICT, jarvis.log:3765+).
            # If callers send markdown, strip to plain text — the project
            # screen renders it as plain text anyway.
            payload["description"] = description

        if project_template_key:
            payload["projectTemplateKey"] = project_template_key

        logger.info(
            f"Creating Jira project: key={key.upper()}, name={name}, "
            f"type={project_type_key}, lead={lead_account_id}, "
            f"template={project_template_key or '<none>'}"
        )

        try:
            response = self.jira.post(
                "/rest/api/3/project", json=payload, advanced_mode=True
            )
            if response.status_code in (200, 201):
                result = response.json()
                if not isinstance(result, dict):
                    error_message = f"Unexpected response from Jira API: {result}"
                    raise ValueError(error_message)
                logger.info(f"Successfully created Jira project: {key.upper()}")
                return result
            else:
                # Extract detailed error from Jira response. When Jira returns
                # a bare ``Invalid request payload`` with no structured detail
                # (common on Cloud for malformed bodies), surface the FULL
                # request body and raw response in the error message — that's
                # the only way to diagnose missing/wrong fields like the
                # 2026-05-16 JLP incident.
                try:
                    error_data = response.json()
                    errors = error_data.get("errors", {})
                    error_messages = error_data.get("errorMessages", [])
                    details = []
                    if error_messages:
                        details.extend(error_messages)
                    for field, msg in errors.items():
                        details.append(f"{field}: {msg}")
                    error_detail = "; ".join(details) if details else response.text
                except Exception:
                    error_detail = response.text
                # Make payload visible in logs + error so callers can diagnose
                # without re-running and dumping over the wire. ``json.dumps``
                # uses default spacing matching the Jira request.
                import json as _json
                payload_repr = _json.dumps(payload, ensure_ascii=False)[:1500]
                raw_response = (response.text or "")[:500]
                logger.error(
                    "Failed to create project key=%s (HTTP %d). "
                    "detail=%r payload=%s raw_response=%r",
                    key.upper(), response.status_code, error_detail,
                    payload_repr, raw_response,
                )
                # Atlassian Cloud holds soft-deleted projects in a trash
                # bin for ~30 days before purging. During that window
                # ``GET /rest/api/3/project/KEY`` returns 404 (project
                # appears gone), but ``POST /rest/api/3/project`` with the
                # same key fails with a generic 400 "uses this project key"
                # — Atlassian gives no hint that the key is reserved by a
                # trashed project, not a live one. Agents see this as a
                # mysterious conflict and retry forever (production
                # 2026-05-20: 7 identical retries against trashed JLP).
                # Probe the trash so the caller learns the actual cause
                # and gets an actionable next step.
                key_upper = key.upper()
                if (
                    response.status_code == 400
                    and "uses this project key" in (error_detail or "").lower()
                ):
                    trash_hint = self._probe_trashed_project_key(key_upper)
                    if trash_hint:
                        raise Exception(trash_hint)
                error_message = (
                    f"Failed to create project (HTTP {response.status_code}): "
                    f"{error_detail}. Sent payload: {payload_repr}. "
                    f"Raw response: {raw_response}"
                )
                raise Exception(error_message)
        except Exception as e:
            logger.error(f"Error creating Jira project {key}: {e}", exc_info=True)
            raise

    def _probe_trashed_project_key(self, key: str) -> str | None:
        """Check whether ``key`` is reserved by a soft-deleted (trashed)
        project on Atlassian Cloud.

        Returns an actionable error message if the key is in trash, else
        ``None``. The message tells the agent the three concrete next
        steps (restore / purge / different key) so it stops retrying.

        Best-effort: any exception during the probe returns ``None`` so
        the original ambiguous 400 still surfaces — the probe is purely
        additive enrichment.
        """
        try:
            response = self.jira.get(
                "rest/api/3/project/search",
                params={"query": key, "status": "deleted", "maxResults": 5},
            )
        except Exception as exc:
            logger.warning(
                "Trash-probe failed for project key=%s: %s. "
                "Falling back to ambiguous 400.", key, exc,
            )
            return None
        if not isinstance(response, dict):
            return None
        for project in response.get("values", []) or []:
            if not isinstance(project, dict):
                continue
            if (project.get("key") or "").upper() != key:
                continue
            deleted_date = project.get("deletedDate") or "<unknown>"
            project_id = project.get("id") or "<unknown>"
            return (
                f"Project key {key!r} is reserved by a soft-deleted project "
                f"(name={project.get('name')!r}, deleted={deleted_date}, "
                f"id={project_id}). Atlassian Cloud holds the key for ~30 "
                f"days before purging. Next steps: "
                f"(1) RESTORE the project — `PUT /rest/api/3/project/{key}/restore` — "
                f"if you want to keep its history; "
                f"(2) PURGE it now — `DELETE /rest/api/3/project/{project_id}?enableUndo=false` — "
                f"to free the key immediately (irreversible); "
                f"(3) Use a DIFFERENT key. Retrying with the same key will keep failing."
            )
        return None
