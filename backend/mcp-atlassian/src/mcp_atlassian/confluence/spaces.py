"""Module for Confluence space operations."""

import logging
from typing import cast

import requests

from .client import ConfluenceClient

logger = logging.getLogger("mcp-atlassian")


class SpacesMixin(ConfluenceClient):
    """Mixin for Confluence space operations."""

    def get_spaces(self, start: int = 0, limit: int = 10) -> dict[str, object]:
        """
        Get all available spaces.

        Args:
            start: The starting index for pagination
            limit: Maximum number of spaces to return

        Returns:
            Dictionary containing space information with results and metadata
        """
        spaces = self.confluence.get_all_spaces(start=start, limit=limit)
        # Cast the return value to the expected type
        return cast(dict[str, object], spaces)

    def create_space(
        self,
        space_key: str,
        space_name: str,
        description: str = "",
        is_private: bool = False,
    ) -> dict:
        """Create a new Confluence space.

        Wraps ``atlassian-python-api``'s ``create_space`` /
        ``create_private_space`` helpers. The underlying API requires the
        caller to have the "Create Space" global permission.

        Args:
            space_key: Space key (2-10 uppercase letters, must be unique).
            space_name: Display name for the space.
            description: Plain-text description (optional).
            is_private: If True, create a private space visible only to the
                creator until they explicitly grant access.

        Returns:
            Raw API response with ``id``, ``key``, ``name``, ``description``.
        """
        method = (
            self.confluence.create_private_space
            if is_private
            else self.confluence.create_space
        )
        # ``atlassian-python-api`` signatures: create_space(space_key, space_name)
        # and create_private_space(space_key, space_name). Description is set
        # via a follow-up call since the underlying methods don't accept it
        # uniformly across Cloud vs Server/DC.
        result = method(space_key, space_name)
        if description and isinstance(result, dict) and result.get("id"):
            try:
                self.confluence.update_space(
                    space_key, space_name, description_plain=description
                )
                result["description"] = {"plain": {"value": description}}
            except Exception as e:
                # Space was created; description update is best-effort —
                # log and return the created-space payload so the caller
                # can decide whether to retry.
                logger.warning(
                    "create_space: space %s created but description update "
                    "failed: %s", space_key, e,
                )
        return cast(dict, result)

    def get_user_contributed_spaces(self, limit: int = 250) -> dict:
        """
        Get spaces the current user has contributed to.

        Args:
            limit: Maximum number of results to return

        Returns:
            Dictionary of space keys to space information
        """
        try:
            # Use CQL to find content the user has contributed to
            cql = "contributor = currentUser() order by lastmodified DESC"
            results = self.confluence.cql(cql=cql, limit=limit)

            # Extract and deduplicate spaces
            spaces = {}
            for result in results.get("results", []):
                space_key = None
                space_name = None

                # Try to extract space from container
                if "resultGlobalContainer" in result:
                    container = result.get("resultGlobalContainer", {})
                    space_name = container.get("title")
                    display_url = container.get("displayUrl", "")
                    if display_url and "/spaces/" in display_url:
                        space_key = display_url.split("/spaces/")[1].split("/")[0]

                # Try to extract from content expandable
                if (
                    not space_key
                    and "content" in result
                    and "_expandable" in result["content"]
                ):
                    expandable = result["content"].get("_expandable", {})
                    space_path = expandable.get("space", "")
                    if space_path and space_path.startswith("/rest/api/space/"):
                        space_key = space_path.split("/rest/api/space/")[1]

                # Try to extract from URL
                if not space_key and "url" in result:
                    url = result.get("url", "")
                    if url and url.startswith("/spaces/"):
                        space_key = url.split("/spaces/")[1].split("/")[0]

                # Only add if we found a space key and it's not already in our results
                if space_key and space_key not in spaces:
                    # Add some defaults if we couldn't extract all fields
                    space_name = space_name or f"Space {space_key}"
                    spaces[space_key] = {"key": space_key, "name": space_name}

            return spaces

        except KeyError as e:
            logger.error(f"Missing key in Confluence spaces data: {str(e)}")
            return {}
        except ValueError as e:
            logger.error(f"Invalid value in Confluence spaces: {str(e)}")
            return {}
        except TypeError as e:
            logger.error(f"Type error when processing Confluence spaces: {str(e)}")
            return {}
        except requests.RequestException as e:
            logger.error(f"Network error when fetching spaces: {str(e)}")
            return {}
        except Exception as e:  # noqa: BLE001 - Intentional fallback with logging
            logger.error(f"Unexpected error fetching Confluence spaces: {str(e)}")
            logger.debug("Full exception details for Confluence spaces:", exc_info=True)
            return {}
