from dataclasses import dataclass
import os

MODE_DOCUMENT = "document"
MODE_AGENT = "agent"
VALID_MODES = {MODE_DOCUMENT, MODE_AGENT}
DEFAULT_AGENT_ROOT_DIR = "_agent"


def _normalize_root_dir(path: str) -> str:
    normalized = str(path).replace("\\", "/").strip().strip("/")
    if normalized == "":
        raise ValueError("OBSIDIAN_AGENT_ROOT_DIR must not be empty")

    parts: list[str] = []
    for part in normalized.split("/"):
        if part in ("", "."):
            continue
        if part == "..":
            raise ValueError("OBSIDIAN_AGENT_ROOT_DIR cannot include '..'")
        parts.append(part)

    if not parts:
        raise ValueError("OBSIDIAN_AGENT_ROOT_DIR must contain at least one valid segment")

    return "/".join(parts)


@dataclass(frozen=True)
class RuntimeConfig:
    mode: str
    agent_root_dir: str

    @property
    def is_agent_mode(self) -> bool:
        return self.mode == MODE_AGENT


def load_runtime_config(mode: str | None = None, agent_root_dir: str | None = None) -> RuntimeConfig:
    raw_mode = str(mode or os.getenv("OBSIDIAN_MODE", MODE_DOCUMENT)).strip().lower()
    if raw_mode not in VALID_MODES:
        valid_modes = ", ".join(sorted(VALID_MODES))
        raise ValueError(f"Invalid OBSIDIAN_MODE '{raw_mode}'. Valid values: {valid_modes}")

    raw_agent_root_dir = str(agent_root_dir or os.getenv("OBSIDIAN_AGENT_ROOT_DIR", DEFAULT_AGENT_ROOT_DIR))
    normalized_agent_root_dir = _normalize_root_dir(raw_agent_root_dir)

    return RuntimeConfig(
        mode=raw_mode,
        agent_root_dir=normalized_agent_root_dir,
    )
