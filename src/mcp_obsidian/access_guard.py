from dataclasses import dataclass
import re
from typing import Any

from .runtime_config import RuntimeConfig


def normalize_relative_path(path: str) -> str:
    normalized = str(path).replace("\\", "/").strip().lstrip("/")
    if normalized == "":
        return ""

    parts: list[str] = []
    for part in normalized.split("/"):
        if part in ("", "."):
            continue
        if part == "..":
            raise PermissionError("Path traversal ('..') is not allowed in this mode")
        parts.append(part)

    return "/".join(parts)


@dataclass(frozen=True)
class VaultAccessGuard:
    config: RuntimeConfig

    @property
    def is_agent_mode(self) -> bool:
        return self.config.is_agent_mode

    @property
    def agent_root_dir(self) -> str:
        return self.config.agent_root_dir

    def resolve_path(self, path: str) -> str:
        raw_path = "" if path is None else str(path)
        if not self.is_agent_mode:
            return raw_path

        normalized = normalize_relative_path(raw_path)

        if normalized == "":
            return self.agent_root_dir

        if normalized == self.agent_root_dir or normalized.startswith(f"{self.agent_root_dir}/"):
            return normalized

        return f"{self.agent_root_dir}/{normalized}"

    def scope_jsonlogic_query(self, query: dict[str, Any]) -> dict[str, Any]:
        if not self.is_agent_mode:
            return query

        path_regex = f"^{re.escape(self.agent_root_dir)}(/|$)"
        return {
            "and": [
                {"regexp": [path_regex, {"var": "path"}]},
                query,
            ]
        }

    def filter_search_results(self, results: Any) -> Any:
        if not self.is_agent_mode:
            return results

        if not isinstance(results, list):
            return []

        filtered_results: list[dict[str, Any]] = []
        for item in results:
            if not isinstance(item, dict):
                continue
            candidate_path = item.get("filename") or item.get("path")
            if isinstance(candidate_path, str) and self.is_allowed_response_path(candidate_path):
                filtered_results.append(item)

        return filtered_results

    def is_allowed_response_path(self, path: str) -> bool:
        normalized = normalize_relative_path(path)
        if not self.is_agent_mode:
            return True

        return normalized == self.agent_root_dir or normalized.startswith(f"{self.agent_root_dir}/")

    def ensure_feature_supported(self, feature_name: str) -> None:
        if not self.is_agent_mode:
            return

        unsupported_features = {
            "periodic_note",
            "recent_periodic_notes",
        }
        if feature_name in unsupported_features:
            raise PermissionError(
                f"'{feature_name}' is unavailable in agent mode because it cannot be safely scoped "
                f"to '{self.agent_root_dir}'"
            )
