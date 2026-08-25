"""Tests for the Jira ProjectsMixin."""

from typing import Any
from unittest.mock import MagicMock, call, patch

import pytest

from mcp_atlassian.jira import JiraFetcher
from mcp_atlassian.jira.config import JiraConfig
from mcp_atlassian.jira.projects import ProjectsMixin
from mcp_atlassian.models.jira.issue import JiraIssue
from mcp_atlassian.models.jira.search import JiraSearchResult


@pytest.fixture
def mock_config():
    """Fixture to create a mock JiraConfig instance."""
    config = MagicMock(spec=JiraConfig)
    config.url = "https://test.atlassian.net"
    config.username = "test@example.com"
    config.api_token = "test-token"
    config.auth_type = "pat"
    return config


@pytest.fixture
def projects_mixin(jira_fetcher: JiraFetcher) -> ProjectsMixin:
    """Fixture to create a ProjectsMixin instance for testing."""
    mixin = jira_fetcher
    return mixin


@pytest.fixture
def mock_projects():
    """Fixture to return mock project data."""
    return [
        {
            "id": "10000",
            "key": "PROJ1",
            "name": "Project One",
            "lead": {"name": "user1", "displayName": "User One"},
        },
        {
            "id": "10001",
            "key": "PROJ2",
            "name": "Project Two",
            "lead": {"name": "user2", "displayName": "User Two"},
        },
    ]


@pytest.fixture
def mock_components():
    """Fixture to return mock project components."""
    return [
        {"id": "10000", "name": "Component One"},
        {"id": "10001", "name": "Component Two"},
    ]


@pytest.fixture
def mock_versions():
    """Fixture to return mock project versions."""
    return [
        {"id": "10000", "name": "1.0", "released": True},
        {"id": "10001", "name": "2.0", "released": False},
    ]


@pytest.fixture
def mock_roles():
    """Fixture to return mock project roles."""
    return {
        "Administrator": {"id": "10000", "name": "Administrator"},
        "Developer": {"id": "10001", "name": "Developer"},
    }


@pytest.fixture
def mock_role_members():
    """Fixture to return mock project role members."""
    return {
        "actors": [
            {"id": "user1", "name": "user1", "displayName": "User One"},
            {"id": "user2", "name": "user2", "displayName": "User Two"},
        ]
    }


@pytest.fixture
def mock_issue_types():
    """Fixture to return mock issue types."""
    return [
        {"id": "10000", "name": "Bug", "description": "A bug"},
        {"id": "10001", "name": "Task", "description": "A task"},
    ]


def test_get_all_projects(projects_mixin: ProjectsMixin, mock_projects: list[dict]):
    """Test get_all_projects method."""
    projects_mixin.jira.projects.return_value = mock_projects

    # Test with default value (include_archived=False)
    result = projects_mixin.get_all_projects()
    assert result == mock_projects
    projects_mixin.jira.projects.assert_called_once_with(included_archived=False)

    # Reset mock and test with include_archived=True
    projects_mixin.jira.projects.reset_mock()
    projects_mixin.jira.projects.return_value = mock_projects

    result = projects_mixin.get_all_projects(include_archived=True)
    assert result == mock_projects
    projects_mixin.jira.projects.assert_called_once_with(included_archived=True)


def test_get_all_projects_exception(projects_mixin: ProjectsMixin):
    """Test get_all_projects method with exception."""
    projects_mixin.jira.projects.side_effect = Exception("API error")

    result = projects_mixin.get_all_projects()
    assert result == []
    projects_mixin.jira.projects.assert_called_once()


def test_get_all_projects_non_list_response(projects_mixin: ProjectsMixin):
    """Test get_all_projects method with non-list response."""
    projects_mixin.jira.projects.return_value = "not a list"

    result = projects_mixin.get_all_projects()
    assert result == []
    projects_mixin.jira.projects.assert_called_once()


def test_get_project(projects_mixin: ProjectsMixin, mock_projects: list[dict]):
    """Test get_project method."""
    project = mock_projects[0]
    projects_mixin.jira.project.return_value = project

    result = projects_mixin.get_project("PROJ1")
    assert result == project
    projects_mixin.jira.project.assert_called_once_with("PROJ1")


def test_get_project_exception(projects_mixin: ProjectsMixin):
    """Test get_project method with exception."""
    projects_mixin.jira.project.side_effect = Exception("API error")

    result = projects_mixin.get_project("PROJ1")
    assert result is None
    projects_mixin.jira.project.assert_called_once()


def test_get_project_issues(projects_mixin: ProjectsMixin):
    """Test get_project_issues method."""
    # Setup mock response
    # Mock the method that is actually called: search_issues
    # It should return a JiraSearchResult object
    mock_search_result = JiraSearchResult(
        issues=[], total=0, start_at=0, max_results=50
    )
    projects_mixin.search_issues = MagicMock(return_value=mock_search_result)

    # Call the method
    result = projects_mixin.get_project_issues("TEST")

    # Verify search_issues was called, not jira.jql
    projects_mixin.search_issues.assert_called_once_with(
        'project = "TEST"',
        start=0,
        limit=50,
    )
    assert isinstance(result, JiraSearchResult)
    assert len(result.issues) == 0


def test_get_project_issues_with_start(projects_mixin: ProjectsMixin) -> None:
    """Test getting project issues with a start index."""
    # Mock search_issues to return a result reflecting pagination
    mock_issue = JiraIssue(key="PROJ-2", summary="Issue 2", id="10002")
    mock_search_result = JiraSearchResult(
        issues=[mock_issue],
        total=1,
        start_at=3,
        max_results=5,
    )
    projects_mixin.search_issues = MagicMock(return_value=mock_search_result)

    project_key = "PROJ"
    start_index = 3

    # Call the method
    result = projects_mixin.get_project_issues(project_key, start=start_index, limit=5)

    assert len(result.issues) == 1
    # Note: Assertions on start_at, max_results, total should be based on the
    # JiraSearchResult object returned by the mocked search_issues
    assert result.start_at == 3  # Comes from the mocked JiraSearchResult
    assert result.max_results == 5  # Comes from the mocked JiraSearchResult
    assert result.total == 1  # Comes from the mocked JiraSearchResult

    # Verify search_issues was called with the correct arguments
    projects_mixin.search_issues.assert_called_once_with(
        f'project = "{project_key}"',
        start=start_index,
        limit=5,
    )


def test_project_exists(projects_mixin: ProjectsMixin, mock_projects: list[dict]):
    """Test project_exists method."""
    # Test with existing project
    project = mock_projects[0]
    projects_mixin.jira.project.return_value = project

    result = projects_mixin.project_exists("PROJ1")
    assert result is True
    projects_mixin.jira.project.assert_called_once_with("PROJ1")

    # Test with non-existing project
    projects_mixin.jira.project.reset_mock()
    projects_mixin.jira.project.return_value = None

    result = projects_mixin.project_exists("NONEXISTENT")
    assert result is False
    projects_mixin.jira.project.assert_called_once()


def test_project_exists_exception(projects_mixin: ProjectsMixin):
    """Test project_exists method with exception."""
    projects_mixin.jira.project.side_effect = Exception("API error")

    result = projects_mixin.project_exists("PROJ1")
    assert result is False
    projects_mixin.jira.project.assert_called_once()


def test_get_project_components(
    projects_mixin: ProjectsMixin, mock_components: list[dict]
):
    """Test get_project_components method."""
    projects_mixin.jira.get_project_components.return_value = mock_components

    result = projects_mixin.get_project_components("PROJ1")
    assert result == mock_components
    projects_mixin.jira.get_project_components.assert_called_once_with(key="PROJ1")


def test_get_project_components_exception(projects_mixin: ProjectsMixin):
    """Test get_project_components method with exception."""
    projects_mixin.jira.get_project_components.side_effect = Exception("API error")

    result = projects_mixin.get_project_components("PROJ1")
    assert result == []
    projects_mixin.jira.get_project_components.assert_called_once()


def test_get_project_components_non_list_response(projects_mixin: ProjectsMixin):
    """Test get_project_components method with non-list response."""
    projects_mixin.jira.get_project_components.return_value = "not a list"

    result = projects_mixin.get_project_components("PROJ1")
    assert result == []
    projects_mixin.jira.get_project_components.assert_called_once()


def test_get_project_versions(projects_mixin: ProjectsMixin, mock_versions: list[dict]):
    """Test get_project_versions method."""
    projects_mixin.jira.get_project_versions.return_value = mock_versions
    # Simplified dicts should include id, name, released and archived
    expected = [
        {
            "id": v["id"],
            "name": v["name"],
            "released": v.get("released", False),
            "archived": v.get("archived", False),
        }
        for v in mock_versions
    ]
    result = projects_mixin.get_project_versions("PROJ1")
    assert result == expected
    projects_mixin.jira.get_project_versions.assert_called_once_with(key="PROJ1")


def test_get_project_versions_exception(projects_mixin: ProjectsMixin):
    """Test get_project_versions method with exception."""
    projects_mixin.jira.get_project_versions.side_effect = Exception("API error")
    result = projects_mixin.get_project_versions("PROJ1")
    assert result == []
    projects_mixin.jira.get_project_versions.assert_called_once_with(key="PROJ1")


def test_get_project_versions_non_list_response(projects_mixin: ProjectsMixin):
    """Test get_project_versions method with non-list response."""
    projects_mixin.jira.get_project_versions.return_value = "not a list"
    result = projects_mixin.get_project_versions("PROJ1")
    assert result == []
    projects_mixin.jira.get_project_versions.assert_called_once_with(key="PROJ1")


def test_get_project_roles(
    projects_mixin: ProjectsMixin, mock_roles: dict[str, dict[str, str]]
):
    """Test get_project_roles method."""
    projects_mixin.jira.get_project_roles.return_value = mock_roles

    result = projects_mixin.get_project_roles("PROJ1")
    assert result == mock_roles
    projects_mixin.jira.get_project_roles.assert_called_once_with(project_key="PROJ1")


def test_get_project_roles_exception(projects_mixin: ProjectsMixin):
    """Test get_project_roles method with exception."""
    projects_mixin.jira.get_project_roles.side_effect = Exception("API error")

    result = projects_mixin.get_project_roles("PROJ1")
    assert result == {}
    projects_mixin.jira.get_project_roles.assert_called_once()


def test_get_project_roles_non_dict_response(projects_mixin: ProjectsMixin):
    """Test get_project_roles method with non-dict response."""
    projects_mixin.jira.get_project_roles.return_value = "not a dict"

    result = projects_mixin.get_project_roles("PROJ1")
    assert result == {}
    projects_mixin.jira.get_project_roles.assert_called_once()


def test_get_project_role_members(
    projects_mixin: ProjectsMixin, mock_role_members: dict[str, list[dict[str, str]]]
):
    """Test get_project_role_members method."""
    projects_mixin.jira.get_project_actors_for_role_project.return_value = (
        mock_role_members
    )

    result = projects_mixin.get_project_role_members("PROJ1", "10001")
    assert result == mock_role_members["actors"]
    projects_mixin.jira.get_project_actors_for_role_project.assert_called_once_with(
        project_key="PROJ1", role_id="10001"
    )


def test_get_project_role_members_exception(projects_mixin: ProjectsMixin):
    """Test get_project_role_members method with exception."""
    projects_mixin.jira.get_project_actors_for_role_project.side_effect = Exception(
        "API error"
    )

    result = projects_mixin.get_project_role_members("PROJ1", "10001")
    assert result == []
    projects_mixin.jira.get_project_actors_for_role_project.assert_called_once()


def test_get_project_role_members_invalid_response(projects_mixin: ProjectsMixin):
    """Test get_project_role_members method with invalid response."""
    # Response without actors
    projects_mixin.jira.get_project_actors_for_role_project.return_value = {}

    result = projects_mixin.get_project_role_members("PROJ1", "10001")
    assert result == []
    projects_mixin.jira.get_project_actors_for_role_project.assert_called_once()

    # Non-dict response
    projects_mixin.jira.get_project_actors_for_role_project.reset_mock()
    projects_mixin.jira.get_project_actors_for_role_project.return_value = "not a dict"

    result = projects_mixin.get_project_role_members("PROJ1", "10001")
    assert result == []


def test_get_project_permission_scheme(projects_mixin: ProjectsMixin):
    """Test get_project_permission_scheme method."""
    scheme = {"id": "10000", "name": "Default Permission Scheme"}
    projects_mixin.jira.get_project_permission_scheme.return_value = scheme

    result = projects_mixin.get_project_permission_scheme("PROJ1")
    assert result == scheme
    projects_mixin.jira.get_project_permission_scheme.assert_called_once_with(
        project_id_or_key="PROJ1"
    )


def test_get_project_permission_scheme_exception(projects_mixin: ProjectsMixin):
    """Test get_project_permission_scheme method with exception."""
    projects_mixin.jira.get_project_permission_scheme.side_effect = Exception(
        "API error"
    )

    result = projects_mixin.get_project_permission_scheme("PROJ1")
    assert result is None
    projects_mixin.jira.get_project_permission_scheme.assert_called_once()


def test_get_project_notification_scheme(projects_mixin: ProjectsMixin):
    """Test get_project_notification_scheme method."""
    scheme = {"id": "10000", "name": "Default Notification Scheme"}
    projects_mixin.jira.get_project_notification_scheme.return_value = scheme

    result = projects_mixin.get_project_notification_scheme("PROJ1")
    assert result == scheme
    projects_mixin.jira.get_project_notification_scheme.assert_called_once_with(
        project_id_or_key="PROJ1"
    )


def test_get_project_notification_scheme_exception(projects_mixin: ProjectsMixin):
    """Test get_project_notification_scheme method with exception."""
    projects_mixin.jira.get_project_notification_scheme.side_effect = Exception(
        "API error"
    )

    result = projects_mixin.get_project_notification_scheme("PROJ1")
    assert result is None
    projects_mixin.jira.get_project_notification_scheme.assert_called_once()


def test_get_project_issue_types(
    projects_mixin: ProjectsMixin, mock_issue_types: list[dict]
):
    """Test get_project_issue_types with new paginated values format."""
    createmeta = {
        "maxResults": 50,
        "startAt": 0,
        "total": len(mock_issue_types),
        "isLast": True,
        "values": mock_issue_types,
    }
    projects_mixin.jira.issue_createmeta_issuetypes.return_value = createmeta

    result = projects_mixin.get_project_issue_types("PROJ1")
    assert result == mock_issue_types
    projects_mixin.jira.issue_createmeta_issuetypes.assert_called_once_with(
        project="PROJ1"
    )


def test_get_project_issue_types_old_format(
    projects_mixin: ProjectsMixin, mock_issue_types: list[dict]
):
    """Test get_project_issue_types falls back to old projects format."""
    createmeta = {
        "projects": [
            {"key": "PROJ1", "name": "Project One", "issuetypes": mock_issue_types}
        ]
    }
    projects_mixin.jira.issue_createmeta_issuetypes.return_value = createmeta

    result = projects_mixin.get_project_issue_types("PROJ1")
    assert result == mock_issue_types


def test_get_project_issue_types_empty_response(projects_mixin: ProjectsMixin):
    """Test get_project_issue_types method with empty response."""
    # Empty values list
    projects_mixin.jira.issue_createmeta_issuetypes.return_value = {
        "values": [],
        "total": 0,
    }

    result = projects_mixin.get_project_issue_types("PROJ1")
    assert result == []
    projects_mixin.jira.issue_createmeta_issuetypes.assert_called_once()

    # Empty old format fallback
    projects_mixin.jira.issue_createmeta_issuetypes.reset_mock()
    projects_mixin.jira.issue_createmeta_issuetypes.return_value = {"projects": []}

    result = projects_mixin.get_project_issue_types("PROJ1")
    assert result == []


def test_get_project_issue_types_exception(projects_mixin: ProjectsMixin):
    """Test get_project_issue_types method with exception."""
    projects_mixin.jira.issue_createmeta_issuetypes.side_effect = Exception("API error")

    result = projects_mixin.get_project_issue_types("PROJ1")
    assert result == []
    projects_mixin.jira.issue_createmeta_issuetypes.assert_called_once()


def test_get_project_issues_count(projects_mixin: ProjectsMixin):
    """Test get_project_issues_count method."""
    jql_result = {"total": 42}
    projects_mixin.jira.jql.return_value = jql_result

    result = projects_mixin.get_project_issues_count("PROJ1")
    assert result == 42
    projects_mixin.jira.jql.assert_called_once_with(
        jql='project = "PROJ1"', fields="key", limit=1
    )


def test_get_project_issues_count__project_with_reserved_keyword(
    projects_mixin: ProjectsMixin,
):
    """Test get_project_issues_count method."""
    jql_result = {"total": 42}
    projects_mixin.jira.jql.return_value = jql_result

    result = projects_mixin.get_project_issues_count("AND")
    assert result == 42
    projects_mixin.jira.jql.assert_called_once_with(
        jql='project = "AND"', fields="key", limit=1
    )


def test_get_project_issues_count_invalid_response(projects_mixin: ProjectsMixin):
    """Test get_project_issues_count method with invalid response."""
    # No total field
    projects_mixin.jira.jql.return_value = {}

    result = projects_mixin.get_project_issues_count("PROJ1")
    assert result == 0
    projects_mixin.jira.jql.assert_called_once()

    # Non-dict response
    projects_mixin.jira.jql.reset_mock()
    projects_mixin.jira.jql.return_value = "not a dict"

    result = projects_mixin.get_project_issues_count("PROJ1")
    assert result == 0
    projects_mixin.jira.jql.assert_called_once()


def test_get_project_issues_count_exception(projects_mixin: ProjectsMixin):
    """Test get_project_issues_count method with exception."""
    projects_mixin.jira.jql.side_effect = Exception("API error")

    result = projects_mixin.get_project_issues_count("PROJ1")
    assert result == 0
    projects_mixin.jira.jql.assert_called_once()


def test_get_project_issues_with_search_mixin(projects_mixin: ProjectsMixin):
    """Test get_project_issues method with search_issues available."""
    # Mock the search_issues method
    mock_search_result = [MagicMock(), MagicMock()]
    projects_mixin.search_issues = MagicMock(return_value=mock_search_result)

    result = projects_mixin.get_project_issues("PROJ1", start=10, limit=20)
    assert result == mock_search_result
    projects_mixin.search_issues.assert_called_once_with(
        'project = "PROJ1"', start=10, limit=20
    )
    projects_mixin.jira.jql.assert_not_called()


def test_get_project_issues_invalid_response(projects_mixin: ProjectsMixin):
    """Test get_project_issues method with invalid response."""

    # Mock search_issues to simulate an empty result scenario
    mock_search_result = JiraSearchResult(
        issues=[], total=0, start_at=0, max_results=50
    )
    projects_mixin.search_issues = MagicMock(return_value=mock_search_result)

    result = projects_mixin.get_project_issues("PROJ1")
    assert result.issues == []
    projects_mixin.search_issues.assert_called_once()

    # Reset mock and test with non-JiraSearchResult response (this would be handled by the except block)
    projects_mixin.search_issues.reset_mock()
    projects_mixin.search_issues = MagicMock(
        side_effect=TypeError("Not a JiraSearchResult")
    )

    result = projects_mixin.get_project_issues("PROJ1")
    assert result.issues == []
    projects_mixin.search_issues.assert_called_once()


def test_get_project_issues_exception(projects_mixin: ProjectsMixin):
    """Test get_project_issues method with exception."""

    # Mock search_issues to raise an exception, simulating an API error during the search
    projects_mixin.search_issues = MagicMock(side_effect=Exception("API error"))

    result = projects_mixin.get_project_issues("PROJ1")
    assert result.issues == []
    # Verify that search_issues was called, even though it raised an exception
    # The except block in get_project_issues catches it and returns an empty result
    projects_mixin.search_issues.assert_called_once()


def test_get_project_keys(
    projects_mixin: ProjectsMixin, mock_projects: list[dict[str, Any]]
):
    """Test get_project_keys method."""
    # Mock the get_all_projects method
    with patch.object(projects_mixin, "get_all_projects", return_value=mock_projects):
        result = projects_mixin.get_project_keys()
        assert result == ["PROJ1", "PROJ2"]
        projects_mixin.get_all_projects.assert_called_once()


def test_get_project_keys_exception(projects_mixin: ProjectsMixin):
    """Test get_project_keys method with exception."""
    # Mock the get_all_projects method to raise an exception
    with patch.object(
        projects_mixin, "get_all_projects", side_effect=Exception("Error")
    ):
        result = projects_mixin.get_project_keys()
        assert result == []
        projects_mixin.get_all_projects.assert_called_once()


def test_get_project_leads(
    projects_mixin: ProjectsMixin, mock_projects: list[dict[str, Any]]
):
    """Test get_project_leads method."""
    # Mock the get_all_projects method
    with patch.object(projects_mixin, "get_all_projects", return_value=mock_projects):
        result = projects_mixin.get_project_leads()
        assert result == {"PROJ1": "user1", "PROJ2": "user2"}
        projects_mixin.get_all_projects.assert_called_once()


def test_get_project_leads_with_different_lead_formats(
    projects_mixin: ProjectsMixin, mock_projects: list[dict[str, Any]]
):
    """Test get_project_leads method with different lead formats."""
    mixed_projects = [
        # Project with lead as dictionary with name
        {"key": "PROJ1", "lead": {"name": "user1", "displayName": "User One"}},
        # Project with lead as dictionary with displayName but no name
        {"key": "PROJ2", "lead": {"displayName": "User Two"}},
        # Project with lead as string
        {"key": "PROJ3", "lead": "user3"},
        # Project without lead
        {"key": "PROJ4"},
    ]

    # Mock the get_all_projects method
    with patch.object(projects_mixin, "get_all_projects", return_value=mixed_projects):
        result = projects_mixin.get_project_leads()
        assert result == {"PROJ1": "user1", "PROJ2": "User Two", "PROJ3": "user3"}
        projects_mixin.get_all_projects.assert_called_once()


def test_get_project_leads_exception(projects_mixin: ProjectsMixin):
    """Test get_project_leads method with exception."""
    # Mock the get_all_projects method to raise an exception
    with patch.object(
        projects_mixin, "get_all_projects", side_effect=Exception("Error")
    ):
        result = projects_mixin.get_project_leads()
        assert result == {}
        projects_mixin.get_all_projects.assert_called_once()


def test_get_user_accessible_projects(
    projects_mixin: ProjectsMixin, mock_projects: list[dict[str, Any]]
):
    """Test get_user_accessible_projects method."""
    # Mock the get_all_projects method
    with patch.object(projects_mixin, "get_all_projects", return_value=mock_projects):
        # Set up the browse permission responses
        browse_users_responses = [
            [{"name": "test_user"}],  # User has access to PROJ1
            [],  # User doesn't have access to PROJ2
        ]
        projects_mixin.jira.get_users_with_browse_permission_to_a_project.side_effect = browse_users_responses

        result = projects_mixin.get_user_accessible_projects("test_user")

        # Only PROJ1 should be in the result
        assert len(result) == 1
        assert result[0]["key"] == "PROJ1"

        # Check that get_users_with_browse_permission_to_a_project was called for both projects
        assert (
            projects_mixin.jira.get_users_with_browse_permission_to_a_project.call_count
            == 2
        )
        projects_mixin.jira.get_users_with_browse_permission_to_a_project.assert_has_calls(
            [
                call(username="test_user", project_key="PROJ1", limit=1),
                call(username="test_user", project_key="PROJ2", limit=1),
            ]
        )


def test_get_user_accessible_projects_with_permissions_exception(
    projects_mixin: ProjectsMixin, mock_projects: list[dict[str, Any]]
):
    """Test get_user_accessible_projects method with exception in permissions check."""
    # Mock the get_all_projects method
    with patch.object(projects_mixin, "get_all_projects", return_value=mock_projects):
        # First call succeeds, second call raises exception
        projects_mixin.jira.get_users_with_browse_permission_to_a_project.side_effect = [
            [{"name": "test_user"}],  # User has access to PROJ1
            Exception("Permission error"),  # Error checking PROJ2
        ]

        result = projects_mixin.get_user_accessible_projects("test_user")

        # Only PROJ1 should be in the result (PROJ2 was skipped due to error)
        assert len(result) == 1
        assert result[0]["key"] == "PROJ1"


def test_get_user_accessible_projects_exception(projects_mixin: ProjectsMixin):
    """Test get_user_accessible_projects method with main exception."""
    # Mock the get_all_projects method to raise an exception
    with patch.object(
        projects_mixin, "get_all_projects", side_effect=Exception("Error")
    ):
        result = projects_mixin.get_user_accessible_projects("test_user")
        assert result == []
        projects_mixin.get_all_projects.assert_called_once()
        projects_mixin.jira.get_users_with_browse_permission_to_a_project.assert_not_called()


def test_create_project_version_minimal(projects_mixin: ProjectsMixin) -> None:
    """Test create_project_version with only required fields."""
    mock_response = {"id": "201", "name": "v4.0"}
    with patch.object(
        projects_mixin, "create_version", return_value=mock_response
    ) as mock_create_version:
        result = projects_mixin.create_project_version(project_key="PROJ2", name="v4.0")
        assert result == mock_response
        mock_create_version.assert_called_once_with(
            project="PROJ2",
            name="v4.0",
            start_date=None,
            release_date=None,
            description=None,
        )


def test_create_project_version_all_fields(projects_mixin: ProjectsMixin) -> None:
    """Test create_project_version with all fields."""
    mock_response = {
        "id": "202",
        "name": "v5.0",
        "description": "Release 5.0",
        "startDate": "2025-08-01",
        "releaseDate": "2025-08-15",
    }
    with patch.object(
        projects_mixin, "create_version", return_value=mock_response
    ) as mock_create_version:
        result = projects_mixin.create_project_version(
            project_key="PROJ3",
            name="v5.0",
            start_date="2025-08-01",
            release_date="2025-08-15",
            description="Release 5.0",
        )
        assert result == mock_response
        mock_create_version.assert_called_once_with(
            project="PROJ3",
            name="v5.0",
            start_date="2025-08-01",
            release_date="2025-08-15",
            description="Release 5.0",
        )


def test_create_project_version_error(projects_mixin: ProjectsMixin) -> None:
    """Test create_project_version propagates errors."""
    with patch.object(
        projects_mixin, "create_version", side_effect=Exception("API failure")
    ):
        with pytest.raises(Exception):
            projects_mixin.create_project_version("PROJ4", "v6.0")


# ── create_project: payload composition + smart default for template ──
#
# Regression suite for 2026-05-16 incident (production agent could not
# create Jira project JLP — 4 attempts all returned ``HTTP 400: Invalid
# request payload`` because Jira Cloud REQUIRES ``projectTemplateKey``
# but the tool description said it was optional).


def _ok_response(payload: dict) -> Any:
    """Helper: build a Jira ``advanced_mode`` response object."""
    resp = MagicMock()
    resp.status_code = 201
    resp.json.return_value = payload
    return resp


def _err_response(body_text: str, status: int = 400, json_body: dict | None = None) -> Any:
    resp = MagicMock()
    resp.status_code = status
    resp.text = body_text
    if json_body is not None:
        resp.json.return_value = json_body
    else:
        resp.json.side_effect = ValueError("not json")
    return resp


def test_create_project_fills_default_template_for_software(
    projects_mixin: ProjectsMixin,
) -> None:
    """When caller passes empty/None ``project_template_key``, the mixin
    MUST fill in the Cloud-required default for the given type. Without
    this, Jira Cloud returns HTTP 400.
    """
    posted = {}

    def _capture_post(path, json=None, advanced_mode=False):
        posted["path"] = path
        posted["json"] = json
        return _ok_response({"id": "10010", "key": "JLP", "name": "JLP"})

    projects_mixin.jira = MagicMock()
    projects_mixin.jira.post.side_effect = _capture_post
    projects_mixin._markdown_to_jira = lambda x: x  # bypass conversion

    projects_mixin.create_project(
        key="JLP",
        name="JLP",
        project_type_key="software",
        lead_account_id="5a0be2a37ae7bd77b1125ca8",
        project_template_key="",  # ← incident-shape: empty string
    )

    sent = posted["json"]
    assert sent["projectTemplateKey"] == (
        "com.pyxis.greenhopper.jira:gh-simplified-agility-scrum"
    ), (
        "Empty template_key should default to Scrum agility for software type. "
        f"Got: {sent.get('projectTemplateKey')!r}"
    )


def test_create_project_description_is_plain_string_not_adf(
    projects_mixin: ProjectsMixin,
) -> None:
    """Regression for 2026-05-16 09:32 ICT incident: project ``description``
    must be a plain string in the POST /rest/api/3/project payload —
    sending the ADF dict (which ``_markdown_to_jira`` returns on Cloud)
    triggers ``HTTP 400: Invalid request payload`` with no structured
    detail. The project create endpoint's schema documents ``description``
    as ``string``, unlike issue endpoints where it's ADF.
    """
    posted = {}
    projects_mixin.jira = MagicMock()
    projects_mixin.jira.post.side_effect = lambda *a, **kw: (
        posted.update({"json": kw.get("json")})
        or _ok_response({"id": "1", "key": "JLP", "name": "JLP"})
    )

    # The mixin's _markdown_to_jira would normally convert this to an ADF
    # dict on Cloud — verify create_project bypasses that conversion.
    projects_mixin._markdown_to_jira = MagicMock(return_value={
        "version": 1, "type": "doc", "content": [],
    })

    projects_mixin.create_project(
        key="JLP",
        name="JLP",
        project_type_key="software",
        lead_account_id="acc",
        description="# Heading\n\nMarkdown body with **bold**.",
    )

    sent = posted["json"]
    assert isinstance(sent["description"], str), (
        f"Project description MUST be plain string. Got {type(sent['description'])}: "
        f"{sent['description']!r}. ADF causes HTTP 400 on /rest/api/3/project."
    )
    assert sent["description"] == "# Heading\n\nMarkdown body with **bold**."
    # _markdown_to_jira must NOT be called for project description
    projects_mixin._markdown_to_jira.assert_not_called()


def test_create_project_respects_explicit_template_key(
    projects_mixin: ProjectsMixin,
) -> None:
    """Caller-provided template_key MUST NOT be overridden by the default."""
    posted = {}
    projects_mixin.jira = MagicMock()
    projects_mixin.jira.post.side_effect = lambda *a, **kw: (
        posted.update({"json": kw.get("json")})
        or _ok_response({"id": "1", "key": "OPS", "name": "OPS"})
    )
    projects_mixin._markdown_to_jira = lambda x: x

    projects_mixin.create_project(
        key="OPS",
        name="OPS",
        project_type_key="software",
        lead_account_id="acc",
        project_template_key="com.pyxis.greenhopper.jira:gh-simplified-agility-kanban",
    )
    assert posted["json"]["projectTemplateKey"] == (
        "com.pyxis.greenhopper.jira:gh-simplified-agility-kanban"
    )


def test_create_project_error_surfaces_payload_and_raw_response(
    projects_mixin: ProjectsMixin,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """On 400 with no structured Jira error detail, the exception text
    AND log line MUST include the sent payload + raw response body so
    callers can diagnose missing/wrong fields without re-running.
    """
    import logging as _logging
    projects_mixin.jira = MagicMock()
    projects_mixin.jira.post.return_value = _err_response(
        "Invalid request payload. Refer to the REST API documentation and try again."
    )
    projects_mixin._markdown_to_jira = lambda x: x

    with caplog.at_level(_logging.ERROR, logger="mcp-jira"):
        with pytest.raises(Exception) as exc_info:
            projects_mixin.create_project(
                key="JLP",
                name="JLP",
                project_type_key="software",
                lead_account_id="acc-id",
                project_template_key="",  # default-filled to scrum
            )

    msg = str(exc_info.value)
    assert "Sent payload" in msg, f"Exception text missing payload: {msg}"
    assert '"projectTemplateKey"' in msg, (
        "Sent payload must include the resolved template key so callers "
        "can see what was actually sent to Jira."
    )
    assert "Raw response" in msg
    assert "Invalid request payload" in msg

    # Log line also carries diagnostic context.
    error_records = [r for r in caplog.records if r.levelname == "ERROR"]
    assert error_records, "Expected at least one ERROR log on 400 response"
    log_text = " ".join(r.getMessage() for r in error_records)
    assert "JLP" in log_text and "payload=" in log_text


# ── create_project: trashed-key collision probe ──
#
# Regression for 2026-05-20 incident (agile-team_02cef7e8 / Jesse [PM]):
# project JLP was soft-deleted on 2026-05-19. Atlassian Cloud holds the
# key reserved for ~30 days. Agent kept retrying ``create_project(key=
# "JLP")`` and got the generic ``HTTP 400: ... uses this project key``
# 7 times in a row, because Atlassian's error gives no hint that the
# key is held by a trashed (vs live) project. The mixin must probe the
# trash and surface an actionable next-step error so the agent stops
# retrying.


def test_create_project_detects_trashed_key_collision(
    projects_mixin: ProjectsMixin,
) -> None:
    """When Atlassian returns 400 'uses this project key', the mixin
    MUST probe the trash and raise an actionable error explaining
    restore / purge / new-key options.
    """
    err_json = {
        "errors": {
            "projectKey": "Project 'Jarvis Product Landing Page' uses this project key.",
        }
    }
    err_resp = _err_response(
        "uses this project key",
        status=400,
        json_body=err_json,
    )

    trash_payload = {
        "total": 1,
        "values": [
            {
                "id": "10042",
                "key": "JLP",
                "name": "Jarvis Product Landing Page",
                "deletedDate": "2026-05-19T21:07:44.424+0700",
            }
        ],
    }

    projects_mixin.jira = MagicMock()
    projects_mixin.jira.post.return_value = err_resp
    projects_mixin.jira.get.return_value = trash_payload
    projects_mixin._markdown_to_jira = lambda x: x

    with pytest.raises(Exception) as exc_info:
        projects_mixin.create_project(
            key="JLP",
            name="JLP",
            project_type_key="software",
            lead_account_id="acc",
        )

    msg = str(exc_info.value)
    assert "soft-deleted" in msg, (
        f"Trash detection must surface in error message. Got: {msg}"
    )
    assert "2026-05-19" in msg, "Deleted date must be visible to caller"
    assert "RESTORE" in msg and "PURGE" in msg, (
        "Caller must see both restore and purge action options"
    )
    assert "DIFFERENT key" in msg, "Caller must see alternative-key option"
    assert "10042" in msg, "Project ID must be in error for purge URL"

    # Trash probe MUST hit the search endpoint with status=deleted
    projects_mixin.jira.get.assert_called_once()
    call_args = projects_mixin.jira.get.call_args
    assert "rest/api/3/project/search" in call_args[0][0]
    params = call_args[1].get("params") or call_args[0][1] if len(call_args[0]) > 1 else call_args[1].get("params")
    assert params.get("status") == "deleted"
    assert params.get("query") == "JLP"


def test_create_project_trash_probe_failure_falls_back_to_original_400(
    projects_mixin: ProjectsMixin,
) -> None:
    """If the trash-probe itself fails (network/permissions), the
    original ambiguous 400 must still surface — the probe is additive
    enrichment, not a hard dependency.
    """
    err_resp = _err_response(
        "uses this project key",
        status=400,
        json_body={"errors": {"projectKey": "uses this project key"}},
    )
    projects_mixin.jira = MagicMock()
    projects_mixin.jira.post.return_value = err_resp
    projects_mixin.jira.get.side_effect = RuntimeError("probe network error")
    projects_mixin._markdown_to_jira = lambda x: x

    with pytest.raises(Exception) as exc_info:
        projects_mixin.create_project(
            key="JLP",
            name="JLP",
            project_type_key="software",
            lead_account_id="acc",
        )

    msg = str(exc_info.value)
    # Falls through to the original generic error path
    assert "Failed to create project (HTTP 400)" in msg
    assert "Sent payload" in msg


def test_create_project_trash_probe_skipped_for_non_collision_400(
    projects_mixin: ProjectsMixin,
) -> None:
    """A 400 with a DIFFERENT error (not key-collision) must NOT trigger
    the trash probe — we only want the enrichment for the specific
    ambiguous case Atlassian surfaces for trashed keys.
    """
    err_resp = _err_response(
        "Invalid request payload",
        status=400,
        json_body={"errorMessages": ["Invalid request payload"]},
    )
    projects_mixin.jira = MagicMock()
    projects_mixin.jira.post.return_value = err_resp
    projects_mixin.jira.get.return_value = {"total": 0, "values": []}
    projects_mixin._markdown_to_jira = lambda x: x

    with pytest.raises(Exception):
        projects_mixin.create_project(
            key="JLP",
            name="JLP",
            project_type_key="software",
            lead_account_id="acc",
        )

    # Probe must be skipped to avoid wasted API calls
    projects_mixin.jira.get.assert_not_called()
