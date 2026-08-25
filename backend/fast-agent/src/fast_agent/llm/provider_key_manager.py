"""
Provider API key management for various LLM providers.
Centralizes API key handling logic to make provider implementations more generic.
"""

import os
from typing import Any

from pydantic import BaseModel

from fast_agent.core.exceptions import ProviderKeyError
from fast_agent.utils.huggingface_hub import get_huggingface_hub_token

PROVIDER_ENVIRONMENT_MAP: dict[str, str] = {
    # default behaviour in _get_env_key_name is to capitalize the
    # provider name and suffix "_API_KEY" - so no specific mapping needed unless overriding
    "hf": "HF_TOKEN",
    "responses": "OPENAI_API_KEY",  # Temporary workaround
    "openresponses": "OPENRESPONSES_API_KEY",
    "codexresponses": "CODEX_API_KEY",
}
PROVIDER_CONFIG_KEY_ALIASES: dict[str, tuple[str, ...]] = {
    # HuggingFace historically used "huggingface" (full name) in config files,
    # while the provider id is "hf". Support both spellings.
    "hf": ("hf", "huggingface"),
    "huggingface": ("huggingface", "hf"),
    # Responses shares OpenAI credentials; allow reading openai.api_key when
    # responses.api_key is omitted.
    "responses": ("openai",),
}
API_KEY_HINT_TEXT = "<your-api-key-here>"
API_KEYLESS_PROVIDERS: frozenset[str] = frozenset({"anthropic-vertex"})


class ProviderKeyManager:
    """
    Manages API keys for different providers centrally.
    This class abstracts away the provider-specific key access logic,
    making the provider implementations more generic.
    """
    _key_indices: dict[str, int] = {}

    @classmethod
    def get_all_keys(cls, provider_name: str, config: Any = None) -> list[str]:
        """Collect all configured API keys for a provider (config, primary, fallback, numbered keys)."""
        keys: list[str] = []
        provider_name = provider_name.lower()

        # Collect candidate names (e.g. ['hf', 'huggingface'])
        candidates = [provider_name]
        for alias in PROVIDER_CONFIG_KEY_ALIASES.get(provider_name, ()):
            if alias not in candidates:
                candidates.append(alias)

        for name in candidates:
            # 1. Check config file
            if config:
                cfg_key = cls.get_config_file_key(name, config)
                if cfg_key and cfg_key not in keys and cfg_key != API_KEY_HINT_TEXT:
                    keys.append(cfg_key)

            # 2. Check primary env var (e.g. GROQ_API_KEY or HF_TOKEN or HUGGINGFACE_API_KEY)
            primary = cls.get_env_var(name)
            if primary and primary not in keys and primary != API_KEY_HINT_TEXT:
                keys.append(primary)

            # 3. Check direct UPPER_API_KEY and UPPER_TOKEN env vars
            for suffix in ["_API_KEY", "_TOKEN"]:
                direct_key = os.getenv(f"{name.upper()}{suffix}")
                if direct_key and direct_key not in keys and direct_key != API_KEY_HINT_TEXT:
                    keys.append(direct_key)

                # Fallback
                fallback = os.getenv(f"{name.upper()}{suffix}_FALLBACK")
                if fallback and fallback not in keys and fallback != API_KEY_HINT_TEXT:
                    keys.append(fallback)

                # Numbered (2 through 9)
                for i in range(2, 10):
                    extra = os.getenv(f"{name.upper()}{suffix}_{i}")
                    if extra and extra not in keys and extra != API_KEY_HINT_TEXT:
                        keys.append(extra)

        return keys

    @classmethod
    def rotate_api_key(cls, provider_name: str, config: Any = None) -> str | None:
        """Rotate to the next API key in the pool for this provider."""
        provider_name = provider_name.lower()
        keys = cls.get_all_keys(provider_name, config)
        if len(keys) <= 1:
            return None

        current = cls._key_indices.get(provider_name, 0)
        new_index = (current + 1) % len(keys)
        cls._key_indices[provider_name] = new_index
        import logging
        logging.getLogger("fast_agent.llm.key_rotation").info(
            f"[KEY_ROTATION] Rotated {provider_name} to key #{new_index + 1}/{len(keys)}"
        )
        return keys[new_index]

    @staticmethod
    def get_env_var(provider_name: str) -> str | None:
        env_key_name = ProviderKeyManager.get_env_key_name(provider_name)
        if not env_key_name:
            return None
        return os.getenv(env_key_name)

    @staticmethod
    def get_env_key_name(provider_name: str) -> str | None:
        if provider_name.lower() in API_KEYLESS_PROVIDERS:
            return None
        return PROVIDER_ENVIRONMENT_MAP.get(provider_name, f"{provider_name.upper()}_API_KEY")

    @staticmethod
    def get_config_file_key(provider_name: str, config: Any) -> str | None:
        api_key = None
        if isinstance(config, BaseModel):
            config = config.model_dump()
        provider_name = provider_name.lower()
        provider_keys = ProviderKeyManager._get_provider_config_keys(provider_name)
        for key in provider_keys:
            provider_settings = config.get(key)
            if not provider_settings:
                continue
            api_key = provider_settings.get("api_key", API_KEY_HINT_TEXT)
            if api_key == API_KEY_HINT_TEXT:
                api_key = None
            break

        return api_key

    @staticmethod
    def _get_provider_config_keys(provider_name: str) -> list[str]:
        """Return config key candidates for a provider (provider id + aliases)."""
        keys = [provider_name]
        for alias in PROVIDER_CONFIG_KEY_ALIASES.get(provider_name, ()):
            if alias not in keys:
                keys.append(alias)
        return keys

    @staticmethod
    def get_api_key(
        provider_name: str,
        config: Any,
    ) -> str:
        """
        Gets the API key for the specified provider.

        Args:
            provider_name: Name of the provider (e.g., "anthropic", "openai")
            config: The application configuration object

        Returns:
            The API key as a string

        Raises:
            ProviderKeyError: If the API key is not found or is invalid
        """

        from fast_agent.llm.provider_types import Provider

        provider_name = provider_name.lower()

        # Fast-agent provider doesn't need external API keys
        if provider_name == "fast-agent":
            return ""

        # Check for request-scoped token first (token passthrough from MCP server)
        if provider_name in {"hf", "huggingface"}:
            from fast_agent.mcp.auth.context import request_bearer_token

            ctx_token = request_bearer_token.get()
            if ctx_token:
                return ctx_token

        # Google Vertex AI uses ADC/IAM and does not require an API key.
        if provider_name == "google":
            try:
                cfg = config.model_dump() if isinstance(config, BaseModel) else config
                if isinstance(cfg, dict) and bool(
                    (cfg.get("google") or {}).get("vertex_ai", {}).get("enabled")
                ):
                    return ""
            except Exception:
                pass

        if provider_name == "anthropic-vertex":
            return ""

        # Check multi-key pool first
        all_keys = ProviderKeyManager.get_all_keys(provider_name, config)
        if all_keys:
            idx = ProviderKeyManager._key_indices.get(provider_name, 0) % len(all_keys)
            return all_keys[idx]

        api_key = ProviderKeyManager.get_config_file_key(provider_name, config)
        if not api_key:
            api_key = ProviderKeyManager.get_env_var(provider_name)

        # Codex OAuth tokens stored in keyring (if no env/config key supplied)
        if not api_key and provider_name == "codexresponses":
            from fast_agent.llm.provider.openai.codex_oauth import get_codex_access_token

            api_key = get_codex_access_token()

        # HuggingFace
        if not api_key and provider_name in {"hf", "huggingface"}:
            api_key = get_huggingface_hub_token()

        if not api_key and provider_name == "generic":
            api_key = "ollama"

        if not api_key and provider_name == "codexresponses":
            raise ProviderKeyError(
                "Codex OAuth token not configured",
                "Run `fast-agent auth codex-login` to authenticate, or set the CODEX_API_KEY environment variable.",
            )

        if not api_key:
            try:
                provider_enum = Provider(provider_name)
                display_name = provider_enum.display_name
            except ValueError:
                raise ProviderKeyError(
                    f"Invalid provider: {provider_name}",
                    f"'{provider_name}' is not a valid provider name.",
                )

            env_key_name = ProviderKeyManager.get_env_key_name(provider_name)
            env_hint = (
                f" or set the {env_key_name} environment variable."
                if env_key_name
                else "."
            )
            raise ProviderKeyError(
                f"{display_name} API key not configured",
                f"The {display_name} API key is required but not set.\n"
                f"Add it to your configuration file under {provider_name}.api_key{env_hint}",
            )

        return api_key
