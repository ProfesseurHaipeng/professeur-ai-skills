#!/usr/bin/env python3
"""Offline, non-executing compatibility audit for Agent Skills.

The auditor treats the target skill as untrusted input.  It never imports or
executes bundled scripts, never follows directory symlinks while walking, and
never performs network requests.
"""

from __future__ import annotations

import argparse
import json
import os
from dataclasses import dataclass, field
from pathlib import Path
import re
import stat
import sys
from typing import Any, Iterator, Sequence
from urllib.parse import unquote, urlsplit


TOOL_NAME = "portable-skill-doctor"
TOOL_VERSION = "0.1.0"
REPORT_SCHEMA = "urn:professeur-ai-skills:portable-skill-doctor:report:v1"
SARIF_SCHEMA = "https://json.schemastore.org/sarif-2.1.0.json"

EXIT_OK = 0
EXIT_FINDINGS = 1
EXIT_USAGE = 2
EXIT_INTERNAL = 3

MAX_TEXT_BYTES = 2 * 1024 * 1024
VALID_TARGETS = ("codex", "copilot", "all")
VALID_FORMATS = ("text", "json", "sarif")
SEVERITIES = ("error", "warning", "info")
SEVERITY_ORDER = {name: index for index, name in enumerate(SEVERITIES)}

SKILL_NAME_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
TOP_LEVEL_KEY_RE = re.compile(r"^([A-Za-z][A-Za-z0-9_-]*):(?:[ \t]*(.*))?$")
WINDOWS_ABSOLUTE_RE = re.compile(r"^[A-Za-z]:[\\/]")
WINDOWS_UNC_RE = re.compile(r"^(?:\\\\|//)")
SAFE_FRONTMATTER_FIELDS = {
    "name",
    "description",
    "license",
    "compatibility",
    "metadata",
    "allowed-tools",
}

MARKDOWN_LINK_RE = re.compile(
    r"!?\[[^\]\r\n]*\]\(\s*(?P<target><[^>\r\n]+>|[^)\r\n]+?)\s*\)"
)
INLINE_RESOURCE_RE = re.compile(
    r"`(?P<target>(?:scripts|references|assets|agents)/[^`\r\n]+)`"
)
TOOL_TOKEN_RE = re.compile(r"[A-Za-z][A-Za-z0-9_.-]*(?:\([^()]*\))?")
UNSAFE_YAML_TOKEN_RE = re.compile(r"(?:^|\s)(?:!![^\s]+|!<[^>]+>|&[A-Za-z0-9_-]+|\*[A-Za-z0-9_-]+)")

SUSPICIOUS_CONTENT_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    (
        "instruction override",
        re.compile(
            r"\b(?:ignore|disregard|override)\s+(?:all\s+)?"
            r"(?:previous|prior|system|developer)\s+(?:instructions?|messages?)\b",
            re.IGNORECASE,
        ),
    ),
    (
        "credential collection",
        re.compile(
            r"\b(?:reveal|exfiltrate|upload|send|collect)\b[^\r\n]{0,100}"
            r"\b(?:secret|token|credential|private[ -]?key|\.ssh|environment variable)\b",
            re.IGNORECASE,
        ),
    ),
    (
        "download piped to a shell",
        re.compile(
            r"\b(?:curl|wget)\b[^\r\n|]{0,300}\|\s*(?:sh|bash|zsh)\b",
            re.IGNORECASE,
        ),
    ),
)

RUNTIME_BY_SUFFIX: dict[str, tuple[str, tuple[str, ...]]] = {
    ".py": ("python", ("python",)),
    ".sh": ("shell", ("sh", "bash", "zsh", "shell")),
    ".bash": ("shell", ("bash", "shell")),
    ".zsh": ("shell", ("zsh", "shell")),
    ".js": ("node", ("node", "node.js", "javascript")),
    ".mjs": ("node", ("node", "node.js", "javascript")),
    ".cjs": ("node", ("node", "node.js", "javascript")),
    ".ts": ("typescript", ("typescript", "node", "deno", "bun", "tsx", "ts-node")),
    ".rb": ("ruby", ("ruby",)),
    ".ps1": ("powershell", ("powershell", "pwsh")),
    ".php": ("php", ("php",)),
}

SHEBANG_RUNTIME_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("python", re.compile(r"(?:^|[/ ])python(?:3(?:\.\d+)?)?(?:\s|$)")),
    ("node", re.compile(r"(?:^|[/ ])node(?:\s|$)")),
    ("typescript", re.compile(r"(?:^|[/ ])(?:deno|bun|tsx|ts-node)(?:\s|$)")),
    ("powershell", re.compile(r"(?:^|[/ ])(?:pwsh|powershell)(?:\s|$)")),
    ("ruby", re.compile(r"(?:^|[/ ])ruby(?:\s|$)")),
    ("php", re.compile(r"(?:^|[/ ])php(?:\s|$)")),
    ("shell", re.compile(r"(?:^|[/ ])(?:sh|bash|zsh|dash|ksh)(?:\s|$)")),
)

TEXT_SUFFIXES = {
    ".md",
    ".markdown",
    ".txt",
    ".yaml",
    ".yml",
    ".json",
    ".toml",
    ".py",
    ".sh",
    ".bash",
    ".zsh",
    ".js",
    ".mjs",
    ".cjs",
    ".ts",
    ".rb",
    ".ps1",
    ".php",
}


@dataclass(frozen=True)
class Finding:
    """One deterministic audit observation."""

    id: str
    severity: str
    title: str
    message: str
    path: str = "."
    line: int | None = None
    targets: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "severity": self.severity,
            "title": self.title,
            "message": self.message,
            "path": self.path,
            "line": self.line,
            "targets": list(self.targets),
        }


@dataclass
class Frontmatter:
    values: dict[str, Any] = field(default_factory=dict)
    value_types: dict[str, str] = field(default_factory=dict)
    lines: dict[str, int] = field(default_factory=dict)
    body: str = ""
    body_start_line: int = 1


@dataclass
class AuditReport:
    input_path: str
    root: str | None
    target: str
    strict: bool
    skill_name: str | None = None
    findings: list[Finding] = field(default_factory=list)
    _seen: set[tuple[Any, ...]] = field(default_factory=set, init=False, repr=False)

    def add(
        self,
        rule_id: str,
        severity: str,
        title: str,
        message: str,
        path: str = ".",
        line: int | None = None,
        targets: Sequence[str] = (),
    ) -> None:
        if severity not in SEVERITY_ORDER:
            raise ValueError(f"unsupported severity: {severity}")
        normalized_targets = tuple(sorted(set(targets)))
        key = (rule_id, severity, message, path, line, normalized_targets)
        if key in self._seen:
            return
        self._seen.add(key)
        self.findings.append(
            Finding(
                id=rule_id,
                severity=severity,
                title=title,
                message=message,
                path=path,
                line=line,
                targets=normalized_targets,
            )
        )

    def sorted_findings(self) -> list[Finding]:
        return sorted(
            self.findings,
            key=lambda item: (
                SEVERITY_ORDER[item.severity],
                item.id,
                item.path,
                item.line if item.line is not None else 0,
                item.message,
                item.targets,
            ),
        )

    def counts(self) -> dict[str, int]:
        result = {severity: 0 for severity in SEVERITIES}
        for finding in self.findings:
            result[finding.severity] += 1
        result["total"] = len(self.findings)
        return result

    def passed(self) -> bool:
        counts = self.counts()
        return counts["error"] == 0 and (not self.strict or counts["warning"] == 0)

    def exit_code(self) -> int:
        return EXIT_OK if self.passed() else EXIT_FINDINGS

    def to_dict(self) -> dict[str, Any]:
        counts = self.counts()
        return {
            "schema": REPORT_SCHEMA,
            "tool": {"name": TOOL_NAME, "version": TOOL_VERSION},
            "audit": {
                "input_path": self.input_path,
                "root": self.root,
                "target": self.target,
                "strict": self.strict,
                "skill_name": self.skill_name,
            },
            "summary": {
                **counts,
                "passed": self.passed(),
                "exit_code": self.exit_code(),
            },
            "findings": [item.to_dict() for item in self.sorted_findings()],
        }


def _relative_path(path: Path, root: Path) -> str:
    try:
        return path.relative_to(root).as_posix() or "."
    except ValueError:
        return "."


def _is_within(path: Path, root: Path) -> bool:
    try:
        return os.path.commonpath((str(path), str(root))) == str(root)
    except ValueError:
        return False


def _line_number(text: str, offset: int) -> int:
    return text.count("\n", 0, offset) + 1


def _unquote_scalar(value: str) -> Any:
    value = value.strip()
    if not value:
        return ""
    if value.startswith('"') and value.endswith('"'):
        try:
            decoded = json.loads(value)
            return decoded if isinstance(decoded, str) else value
        except json.JSONDecodeError:
            return value[1:-1]
    if value.startswith("'") and value.endswith("'"):
        return value[1:-1].replace("''", "'")
    if value.startswith("[") and value.endswith("]"):
        body = value[1:-1].strip()
        if not body:
            return []
        return [_unquote_scalar(part.strip()) for part in body.split(",")]
    lowered = value.lower()
    if lowered in {"true", "false"}:
        return lowered == "true"
    if lowered in {"null", "~"}:
        return None
    if re.fullmatch(r"-?[0-9]+", value):
        try:
            return int(value)
        except ValueError:
            pass
    if " #" in value:
        value = value.split(" #", 1)[0].rstrip()
    return value


def _parse_frontmatter(text: str, report: AuditReport) -> Frontmatter | None:
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        report.add(
            "PSD-FM-001",
            "error",
            "Missing frontmatter",
            "SKILL.md must begin with a YAML frontmatter delimiter (---).",
            "SKILL.md",
            1,
        )
        return None

    closing_index = next(
        (index for index in range(1, len(lines)) if lines[index].strip() == "---"),
        None,
    )
    if closing_index is None:
        report.add(
            "PSD-FM-002",
            "error",
            "Unterminated frontmatter",
            "SKILL.md frontmatter has no closing --- delimiter.",
            "SKILL.md",
            1,
        )
        return None

    parsed = Frontmatter(
        body="\n".join(lines[closing_index + 1 :]),
        body_start_line=closing_index + 2,
    )
    index = 1
    while index < closing_index:
        raw = lines[index]
        line_number = index + 1
        stripped = raw.strip()
        if not stripped or stripped.startswith("#"):
            index += 1
            continue
        if "\t" in raw:
            report.add(
                "PSD-FM-003",
                "error",
                "Tab in frontmatter",
                "Use spaces for YAML indentation; tabs are rejected for portable parsing.",
                "SKILL.md",
                line_number,
            )
        if stripped.startswith("%") or stripped.startswith("---") or stripped.startswith("..."):
            report.add(
                "PSD-FM-004",
                "error",
                "Unsupported YAML directive",
                "Additional YAML documents and directives are not allowed in SKILL.md frontmatter.",
                "SKILL.md",
                line_number,
            )
            index += 1
            continue

        indentation = len(raw) - len(raw.lstrip(" "))
        if indentation:
            report.add(
                "PSD-FM-005",
                "error",
                "Orphan nested frontmatter value",
                "Nested YAML content must belong to a top-level field.",
                "SKILL.md",
                line_number,
            )
            index += 1
            continue

        match = TOP_LEVEL_KEY_RE.match(raw)
        if not match or raw.startswith("<<:"):
            report.add(
                "PSD-FM-006",
                "error",
                "Invalid frontmatter syntax",
                "Expected a top-level 'key: value' entry.",
                "SKILL.md",
                line_number,
            )
            index += 1
            continue

        key = match.group(1)
        raw_value = (match.group(2) or "").strip()
        if key in parsed.values:
            report.add(
                "PSD-FM-007",
                "error",
                "Duplicate frontmatter key",
                f"The '{key}' field is declared more than once.",
                "SKILL.md",
                line_number,
            )
            index += 1
            continue
        if UNSAFE_YAML_TOKEN_RE.search(raw_value):
            report.add(
                "PSD-FM-008",
                "error",
                "Unsafe YAML feature",
                f"The '{key}' field uses a YAML tag, anchor, or alias; portable skills must use data-only values.",
                "SKILL.md",
                line_number,
            )

        parsed.lines[key] = line_number
        if raw_value in {"|", ">"}:
            block_lines: list[str] = []
            index += 1
            while index < closing_index:
                candidate = lines[index]
                candidate_indent = len(candidate) - len(candidate.lstrip(" "))
                if candidate.strip() and candidate_indent == 0:
                    break
                block_lines.append(candidate)
                index += 1
            nonempty_indents = [
                len(item) - len(item.lstrip(" ")) for item in block_lines if item.strip()
            ]
            trim = min(nonempty_indents) if nonempty_indents else 0
            trimmed = [item[trim:] if len(item) >= trim else "" for item in block_lines]
            parsed.values[key] = (
                "\n".join(trimmed).strip() if raw_value == "|" else " ".join(item.strip() for item in trimmed).strip()
            )
            parsed.value_types[key] = "scalar"
            continue

        if raw_value == "":
            nested: list[str] = []
            index += 1
            while index < closing_index:
                candidate = lines[index]
                candidate_indent = len(candidate) - len(candidate.lstrip(" "))
                if candidate.strip() and candidate_indent == 0:
                    break
                nested.append(candidate)
                index += 1
            nonempty = [item.strip() for item in nested if item.strip() and not item.strip().startswith("#")]
            if nonempty and all(item.startswith("-") for item in nonempty):
                parsed.values[key] = [_unquote_scalar(item[1:].strip()) for item in nonempty]
                parsed.value_types[key] = "list"
            else:
                parsed.values[key] = {"_raw": "\n".join(nested)} if nonempty else ""
                parsed.value_types[key] = "mapping" if nonempty else "scalar"
            continue

        value = _unquote_scalar(raw_value)
        parsed.values[key] = value
        parsed.value_types[key] = "list" if isinstance(value, list) else "scalar"
        index += 1

    return parsed


def _validate_frontmatter(frontmatter: Frontmatter, root: Path, report: AuditReport) -> None:
    values = frontmatter.values
    for key in sorted(set(values) - SAFE_FRONTMATTER_FIELDS):
        report.add(
            "PSD-FM-009",
            "warning",
            "Unknown frontmatter field",
            f"The top-level '{key}' field is outside the portable Agent Skills field set.",
            "SKILL.md",
            frontmatter.lines.get(key),
        )

    name = values.get("name")
    if not isinstance(name, str) or not name.strip():
        report.add(
            "PSD-FM-010",
            "error",
            "Missing skill name",
            "Frontmatter requires a non-empty string 'name'.",
            "SKILL.md",
            frontmatter.lines.get("name", 1),
        )
    else:
        name = name.strip()
        report.skill_name = name
        if len(name) > 64 or not SKILL_NAME_RE.fullmatch(name):
            report.add(
                "PSD-FM-011",
                "error",
                "Invalid skill name",
                "Skill names must be 1-64 lowercase ASCII letters, digits, or single hyphens, without leading or trailing hyphens.",
                "SKILL.md",
                frontmatter.lines.get("name"),
            )
        if name != root.name:
            report.add(
                "PSD-FM-012",
                "error",
                "Directory name mismatch",
                f"Frontmatter name '{name}' does not match directory '{root.name}'.",
                "SKILL.md",
                frontmatter.lines.get("name"),
            )

    description = values.get("description")
    if isinstance(description, list) and any(
        isinstance(item, str) and re.search(r"\bTODO\b", item, re.IGNORECASE)
        for item in description
    ):
        report.add(
            "PSD-TRIGGER-001",
            "error",
            "Placeholder description",
            "Replace template text with a concrete description before publishing.",
            "SKILL.md",
            frontmatter.lines.get("description"),
        )
    if not isinstance(description, str) or not description.strip():
        report.add(
            "PSD-FM-013",
            "error",
            "Missing skill description",
            "Frontmatter requires a non-empty string 'description'.",
            "SKILL.md",
            frontmatter.lines.get("description", 1),
        )
    else:
        description = description.strip()
        if len(description) > 1024:
            report.add(
                "PSD-FM-014",
                "error",
                "Description is too long",
                f"Description length is {len(description)} characters; the portable limit is 1024.",
                "SKILL.md",
                frontmatter.lines.get("description"),
            )
        if re.search(r"\[?TODO\]?|replace with|complete and informative", description, re.IGNORECASE):
            report.add(
                "PSD-TRIGGER-001",
                "error",
                "Placeholder description",
                "Replace template text with a concrete description before publishing.",
                "SKILL.md",
                frontmatter.lines.get("description"),
            )
        if len(description) < 40:
            report.add(
                "PSD-TRIGGER-002",
                "warning",
                "Description is too vague",
                "Describe both the capability and the situations that should activate it.",
                "SKILL.md",
                frontmatter.lines.get("description"),
            )
        trigger_window = description[:500].lower()
        trigger_markers = (
            "use when",
            "use for",
            "when ",
            "whenever",
            "trigger",
            "用于",
            "当用户",
            "适用于",
            "utiliser lorsque",
            "quand ",
        )
        if not any(marker in trigger_window for marker in trigger_markers):
            report.add(
                "PSD-TRIGGER-003",
                "warning",
                "Activation context is unclear",
                "Add explicit task or user-language cues that explain when the skill should activate.",
                "SKILL.md",
                frontmatter.lines.get("description"),
            )

    compatibility = values.get("compatibility")
    if compatibility is not None:
        if not isinstance(compatibility, str):
            report.add(
                "PSD-FM-015",
                "error",
                "Invalid compatibility field",
                "The optional 'compatibility' field must be a string.",
                "SKILL.md",
                frontmatter.lines.get("compatibility"),
            )
        elif not compatibility.strip() or len(compatibility) > 500:
            report.add(
                "PSD-FM-016",
                "error",
                "Invalid compatibility length",
                "Compatibility must contain 1-500 characters when provided.",
                "SKILL.md",
                frontmatter.lines.get("compatibility"),
            )


def _read_text_file(path: Path, root: Path, report: AuditReport) -> str | None:
    rel = _relative_path(path, root)
    try:
        resolved = path.resolve(strict=True)
    except (FileNotFoundError, OSError) as error:
        report.add(
            "PSD-FILE-001",
            "error",
            "Unreadable file",
            f"Cannot resolve file: {error}.",
            rel,
        )
        return None
    if not _is_within(resolved, root):
        report.add(
            "PSD-PATH-004",
            "error",
            "Symlink escapes skill root",
            "The file resolves outside the audited skill directory.",
            rel,
        )
        return None
    try:
        size = resolved.stat().st_size
        if size > MAX_TEXT_BYTES:
            report.add(
                "PSD-FILE-002",
                "error",
                "Text file is too large",
                f"File size {size} bytes exceeds the offline audit limit of {MAX_TEXT_BYTES} bytes.",
                rel,
            )
            return None
        data = resolved.read_bytes()
    except (OSError, PermissionError) as error:
        report.add(
            "PSD-FILE-001",
            "error",
            "Unreadable file",
            f"Cannot read file: {error}.",
            rel,
        )
        return None

    if b"\x00" in data:
        report.add(
            "PSD-TEXT-001",
            "error",
            "NUL byte in text file",
            "Portable text resources must not contain NUL bytes.",
            rel,
        )
        return None
    if data.startswith(b"\xef\xbb\xbf"):
        report.add(
            "PSD-TEXT-002",
            "warning",
            "UTF-8 BOM present",
            "Remove the byte-order mark to avoid parser differences across runtimes.",
            rel,
            1,
        )
    if b"\r\n" in data:
        report.add(
            "PSD-TEXT-003",
            "warning",
            "CRLF line endings",
            "Use LF line endings for consistent parsing across agent runtimes.",
            rel,
            1,
        )
    residual_cr = data.replace(b"\r\n", b"")
    if b"\r" in residual_cr:
        report.add(
            "PSD-TEXT-004",
            "error",
            "Bare carriage return",
            "Classic Mac line endings are not portable.",
            rel,
            1,
        )
    try:
        return data.decode("utf-8-sig")
    except UnicodeDecodeError as error:
        report.add(
            "PSD-TEXT-005",
            "error",
            "Invalid UTF-8",
            f"Text resources must be UTF-8: byte {error.start} is invalid.",
            rel,
        )
        return None


def _iter_entries(root: Path, report: AuditReport) -> Iterator[Path]:
    stack = [root]
    while stack:
        directory = stack.pop()
        try:
            entries = sorted(os.scandir(directory), key=lambda item: item.name)
        except (OSError, PermissionError) as error:
            report.add(
                "PSD-FILE-003",
                "error",
                "Unreadable directory",
                f"Cannot enumerate directory: {error}.",
                _relative_path(directory, root),
            )
            continue
        child_directories: list[Path] = []
        for entry in entries:
            path = Path(entry.path)
            yield path
            try:
                if entry.is_dir(follow_symlinks=False) and not entry.is_symlink():
                    child_directories.append(path)
            except OSError as error:
                report.add(
                    "PSD-FILE-004",
                    "error",
                    "Unreadable directory entry",
                    f"Cannot inspect entry: {error}.",
                    _relative_path(path, root),
                )
        stack.extend(reversed(child_directories))


def _check_symlink(path: Path, root: Path, report: AuditReport) -> None:
    rel = _relative_path(path, root)
    try:
        resolved = path.resolve(strict=False)
    except (OSError, RuntimeError) as error:
        report.add(
            "PSD-PATH-005",
            "error",
            "Invalid symlink",
            f"Cannot resolve symlink: {error}.",
            rel,
        )
        return
    if not _is_within(resolved, root):
        report.add(
            "PSD-PATH-004",
            "error",
            "Symlink escapes skill root",
            f"Symlink target resolves outside the skill root: {os.readlink(path)!r}.",
            rel,
        )
    elif not path.exists():
        report.add(
            "PSD-PATH-006",
            "error",
            "Broken symlink",
            "Symlink target does not exist.",
            rel,
        )


def _check_permissions(path: Path, root: Path, report: AuditReport) -> None:
    if os.name == "nt":
        return
    rel = _relative_path(path, root)
    try:
        mode = path.lstat().st_mode
    except OSError as error:
        report.add(
            "PSD-PERM-001",
            "error",
            "Unreadable permissions",
            f"Cannot read permission bits: {error}.",
            rel,
        )
        return
    if mode & (stat.S_ISUID | stat.S_ISGID):
        report.add(
            "PSD-PERM-002",
            "error",
            "Privileged permission bit",
            "Setuid and setgid bits are not appropriate in a portable skill package.",
            rel,
        )
    if mode & stat.S_IWOTH:
        report.add(
            "PSD-PERM-003",
            "error",
            "World-writable entry",
            "Remove world-write permission before distributing the skill.",
            rel,
        )
    is_executable = bool(mode & (stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH))
    relative = Path(rel)
    in_scripts = bool(relative.parts and relative.parts[0] == "scripts")
    if path.is_file() and is_executable and not in_scripts:
        report.add(
            "PSD-PERM-004",
            "warning",
            "Executable outside scripts directory",
            "Executable files should live under scripts/ so their purpose is explicit.",
            rel,
        )
    if path.is_file() and in_scripts and path.suffix.lower() in {".sh", ".bash", ".zsh"} and not is_executable:
        report.add(
            "PSD-PERM-005",
            "warning",
            "Shell script is not executable",
            "Add an execute bit or document that the script must be invoked through an interpreter.",
            rel,
        )


def _strip_markdown_title(target: str) -> str:
    target = target.strip()
    if target.startswith("<") and target.endswith(">"):
        return target[1:-1]
    match = re.match(r"^(\S+)(?:\s+[\"'][^\"']*[\"'])$", target)
    return match.group(1) if match else target


def _decode_reference(target: str) -> str:
    decoded = target
    for _ in range(3):
        next_value = unquote(decoded)
        if next_value == decoded:
            break
        decoded = next_value
    return decoded


def _validate_reference(
    raw_target: str,
    source: Path,
    source_text: str,
    offset: int,
    root: Path,
    report: AuditReport,
) -> None:
    source_rel = _relative_path(source, root)
    line = _line_number(source_text, offset)
    target = _decode_reference(_strip_markdown_title(raw_target)).strip()
    if not target or target.startswith("#"):
        return
    if any(ord(character) < 32 for character in target):
        report.add(
            "PSD-PATH-001",
            "error",
            "Control character in resource path",
            "Resource references must not contain control characters.",
            source_rel,
            line,
        )
        return
    if WINDOWS_ABSOLUTE_RE.match(target) or WINDOWS_UNC_RE.match(target) or target.startswith(("/", "~", "\\")):
        report.add(
            "PSD-PATH-002",
            "error",
            "Absolute resource path",
            f"Absolute resource reference is forbidden: {raw_target!r}.",
            source_rel,
            line,
        )
        return

    split = urlsplit(target)
    if split.scheme:
        if split.scheme.lower() in {"http", "https", "mailto", "tel", "data"}:
            return
        report.add(
            "PSD-PATH-002",
            "error",
            "Unsafe resource scheme",
            f"Only portable relative paths or normal web links are allowed; found scheme '{split.scheme}'.",
            source_rel,
            line,
        )
        return

    normalized_path = split.path.replace("\\", "/")
    parts = tuple(part for part in normalized_path.split("/") if part not in {"", "."})
    if ".." in parts:
        report.add(
            "PSD-PATH-003",
            "error",
            "Parent traversal in resource path",
            f"Parent traversal is forbidden even when it would resolve inside the skill: {raw_target!r}.",
            source_rel,
            line,
        )
        return
    if not normalized_path:
        return

    candidate = source.parent.joinpath(*parts)
    try:
        resolved = candidate.resolve(strict=False)
    except (OSError, RuntimeError) as error:
        report.add(
            "PSD-PATH-005",
            "error",
            "Invalid resource path",
            f"Cannot resolve resource reference {raw_target!r}: {error}.",
            source_rel,
            line,
        )
        return
    if not _is_within(resolved, root):
        report.add(
            "PSD-PATH-004",
            "error",
            "Resource escapes skill root",
            f"Resource reference resolves outside the audited skill: {raw_target!r}.",
            source_rel,
            line,
        )
        return
    if not os.path.lexists(candidate):
        report.add(
            "PSD-RESOURCE-001",
            "error",
            "Missing resource",
            f"Referenced resource does not exist: {normalized_path!r}.",
            source_rel,
            line,
        )
        return
    try:
        strict_resolved = candidate.resolve(strict=True)
    except (FileNotFoundError, OSError, RuntimeError):
        report.add(
            "PSD-PATH-006",
            "error",
            "Broken resource link",
            f"Referenced path cannot be resolved: {normalized_path!r}.",
            source_rel,
            line,
        )
        return
    if not _is_within(strict_resolved, root):
        report.add(
            "PSD-PATH-004",
            "error",
            "Resource symlink escapes skill root",
            f"Referenced resource resolves outside the audited skill: {raw_target!r}.",
            source_rel,
            line,
        )
    elif strict_resolved.is_dir():
        report.add(
            "PSD-RESOURCE-002",
            "warning",
            "Resource reference points to a directory",
            f"Reference a specific file instead of directory {normalized_path!r}.",
            source_rel,
            line,
        )


def _scan_resource_references(path: Path, text: str, root: Path, report: AuditReport) -> None:
    seen_offsets: set[tuple[int, str]] = set()
    for pattern in (MARKDOWN_LINK_RE, INLINE_RESOURCE_RE):
        for match in pattern.finditer(text):
            target = match.group("target")
            key = (match.start("target"), target)
            if key in seen_offsets:
                continue
            seen_offsets.add(key)
            _validate_reference(target, path, text, match.start("target"), root, report)


def _scan_suspicious_content(
    path: Path,
    text: str,
    root: Path,
    report: AuditReport,
    line_offset: int = 0,
) -> None:
    rel = _relative_path(path, root)
    for label, pattern in SUSPICIOUS_CONTENT_PATTERNS:
        for match in pattern.finditer(text):
            report.add(
                "PSD-CONTENT-001",
                "warning",
                "Suspicious instruction requires review",
                f"Detected a possible {label}; confirm that this text documents a threat rather than instructing the agent to perform it.",
                rel,
                _line_number(text, match.start()) + line_offset,
            )


def _infer_shebang_runtime(shebang: str) -> str | None:
    lowered = shebang.lower()
    for runtime, pattern in SHEBANG_RUNTIME_PATTERNS:
        if pattern.search(lowered):
            return runtime
    return None


def _runtime_is_compatible(expected: str, observed: str) -> bool:
    if expected == observed:
        return True
    return {expected, observed} <= {"node", "typescript"}


def _scan_scripts(
    files: Sequence[Path],
    root: Path,
    frontmatter: Frontmatter | None,
    report: AuditReport,
) -> None:
    script_files = [
        path
        for path in files
        if _relative_path(path, root).split("/", 1)[0] == "scripts"
        and not path.is_dir()
        and not path.is_symlink()
    ]
    if not script_files:
        return
    compatibility_value = frontmatter.values.get("compatibility") if frontmatter else ""
    compatibility = compatibility_value.lower() if isinstance(compatibility_value, str) else ""
    body = frontmatter.body if frontmatter else ""
    body_runtime = re.search(
        r"(?im)^(?:#{1,6}\s*)?(?:runtime|requirements?)\b[^\n]*"
        r"(?:python|node(?:\.js)?|javascript|typescript|shell|bash|zsh|powershell|ruby|php)",
        body,
    )
    declared_environment = compatibility or (body_runtime.group(0).lower() if body_runtime else "")
    if not declared_environment:
        report.add(
            "PSD-SCRIPT-001",
            "warning",
            "Script compatibility is undeclared",
            "The skill bundles scripts but does not declare required runtimes or system packages in frontmatter compatibility or a Runtime/Requirements section.",
            "SKILL.md",
            frontmatter.lines.get("compatibility") if frontmatter else 1,
        )

    for path in sorted(script_files, key=lambda item: _relative_path(item, root)):
        rel = _relative_path(path, root)
        suffix = path.suffix.lower()
        runtime_info = RUNTIME_BY_SUFFIX.get(suffix)
        text = _read_text_file(path, root, report) if suffix in TEXT_SUFFIXES else None
        shebang = ""
        if text:
            first_line = text.splitlines()[0] if text.splitlines() else ""
            shebang = first_line[2:].strip() if first_line.startswith("#!") else ""
        observed_runtime = _infer_shebang_runtime(shebang) if shebang else None
        declaration_window = "\n".join(text.splitlines()[:12]) if text else ""
        local_declaration = re.search(
            r"(?:requires?|runtime)\s*:\s*([^\r\n]+)",
            declaration_window,
            re.IGNORECASE,
        )

        if runtime_info:
            expected, keywords = runtime_info
            declared = observed_runtime is not None or local_declaration is not None or any(
                keyword in declared_environment for keyword in keywords
            )
            if not declared:
                report.add(
                    "PSD-SCRIPT-002",
                    "warning",
                    "Script runtime is undeclared",
                    f"Declare the {expected} runtime for {rel} in compatibility, a shebang, or a leading Runtime/Requires comment.",
                    rel,
                    1,
                )
            if observed_runtime and not _runtime_is_compatible(expected, observed_runtime):
                report.add(
                    "PSD-SCRIPT-003",
                    "error",
                    "Script runtime conflict",
                    f"File extension implies {expected}, but the shebang selects {observed_runtime}.",
                    rel,
                    1,
                )
        else:
            try:
                executable = bool(path.stat().st_mode & (stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH))
            except OSError:
                executable = False
            if executable and not observed_runtime:
                report.add(
                    "PSD-SCRIPT-004",
                    "warning",
                    "Unknown executable runtime",
                    "An extensionless or unfamiliar executable requires a portable shebang and compatibility declaration.",
                    rel,
                    1,
                )


def _validate_allowed_tools(frontmatter: Frontmatter | None, report: AuditReport) -> None:
    if not frontmatter or "allowed-tools" not in frontmatter.values:
        return
    value = frontmatter.values.get("allowed-tools")
    line = frontmatter.lines.get("allowed-tools")
    if not isinstance(value, str):
        report.add(
            "PSD-TOOL-001",
            "error",
            "allowed-tools must be a string",
            "The portable specification defines allowed-tools as a space-delimited string, not a YAML list.",
            "SKILL.md",
            line,
        )
        return
    if not value.strip():
        report.add(
            "PSD-TOOL-002",
            "error",
            "allowed-tools is empty",
            "Remove the field or declare one or more explicit tool expressions.",
            "SKILL.md",
            line,
        )
        return
    if re.search(r"[;|`\r\n]|\$\(|&&|\|\|", value):
        report.add(
            "PSD-TOOL-003",
            "error",
            "Unsafe tool declaration",
            "allowed-tools contains shell control syntax; declare data-only tool expressions.",
            "SKILL.md",
            line,
        )
        return
    tokens = TOOL_TOKEN_RE.findall(value)
    remainder = TOOL_TOKEN_RE.sub("", value)
    if remainder.strip():
        report.add(
            "PSD-TOOL-004",
            "error",
            "Malformed tool declaration",
            f"Could not parse allowed-tools near {remainder.strip()!r}.",
            "SKILL.md",
            line,
        )
    lowered = [token.lower() for token in tokens]
    if len(lowered) != len(set(lowered)):
        report.add(
            "PSD-TOOL-005",
            "warning",
            "Duplicate tool declaration",
            "Remove duplicate allowed-tools entries.",
            "SKILL.md",
            line,
        )
    if any(token.lower() in {"bash", "shell", "execute"} or token.endswith("(*)") for token in tokens):
        report.add(
            "PSD-TOOL-006",
            "warning",
            "Broad execution permission",
            "Prefer command-scoped tool permissions over unrestricted shell execution.",
            "SKILL.md",
            line,
        )
    selected_targets = ("codex", "copilot") if report.target == "all" else (report.target,)
    report.add(
        "PSD-TOOL-007",
        "info",
        "Experimental tool field",
        "allowed-tools support and tool names vary by agent runtime; verify each selected target.",
        "SKILL.md",
        line,
        selected_targets,
    )


def _parse_openai_tool_dependencies(text: str) -> list[tuple[dict[str, str], int]]:
    lines = text.splitlines()
    dependencies_indent: int | None = None
    tools_indent: int | None = None
    entries: list[tuple[dict[str, str], int]] = []
    current: dict[str, str] | None = None
    current_line = 1

    for index, raw in enumerate(lines):
        stripped = raw.strip()
        if not stripped or stripped.startswith("#"):
            continue
        indent = len(raw) - len(raw.lstrip(" "))
        if dependencies_indent is None:
            if stripped == "dependencies:":
                dependencies_indent = indent
            continue
        if indent <= dependencies_indent and stripped != "dependencies:":
            break
        if tools_indent is None:
            if stripped == "tools:" and indent > dependencies_indent:
                tools_indent = indent
            continue
        if indent <= tools_indent:
            if current is not None:
                entries.append((current, current_line))
            break
        if stripped.startswith("-"):
            if current is not None:
                entries.append((current, current_line))
            current = {}
            current_line = index + 1
            remainder = stripped[1:].strip()
            if remainder and ":" in remainder:
                key, value = remainder.split(":", 1)
                current[key.strip()] = str(_unquote_scalar(value.strip()))
            continue
        if current is not None and ":" in stripped:
            key, value = stripped.split(":", 1)
            current[key.strip()] = str(_unquote_scalar(value.strip()))
    else:
        if current is not None:
            entries.append((current, current_line))
    return entries


def _validate_openai_dependencies(
    root: Path,
    files: Sequence[Path],
    report: AuditReport,
) -> None:
    metadata_path = root / "agents" / "openai.yaml"
    if not metadata_path.exists() or metadata_path.is_symlink():
        return
    text = _read_text_file(metadata_path, root, report)
    if text is None:
        return
    entries = _parse_openai_tool_dependencies(text)
    if not entries:
        return
    for entry, line in entries:
        dep_type = entry.get("type", "").strip()
        value = entry.get("value", "").strip()
        if not dep_type:
            report.add(
                "PSD-TOOL-008",
                "error",
                "Tool dependency type is missing",
                "Every agents/openai.yaml tool dependency needs a type.",
                "agents/openai.yaml",
                line,
                ("codex",),
            )
        elif dep_type != "mcp":
            report.add(
                "PSD-TOOL-009",
                "warning",
                "Unknown OpenAI tool dependency type",
                f"Dependency type {dep_type!r} is not the documented portable MCP type.",
                "agents/openai.yaml",
                line,
                ("codex",),
            )
        if not value:
            report.add(
                "PSD-TOOL-010",
                "error",
                "Tool dependency value is missing",
                "Every agents/openai.yaml tool dependency needs a stable value identifier.",
                "agents/openai.yaml",
                line,
                ("codex",),
            )
        elif re.search(r"[;|`\r\n]|\$\(|&&|\|\|", value):
            report.add(
                "PSD-TOOL-011",
                "error",
                "Unsafe tool dependency value",
                "Tool dependency identifiers must not contain shell control syntax.",
                "agents/openai.yaml",
                line,
                ("codex",),
            )
        url = entry.get("url", "").strip()
        if url:
            parsed = urlsplit(url)
            if parsed.scheme not in {"http", "https"} or not parsed.netloc or parsed.username or parsed.password:
                report.add(
                    "PSD-TOOL-012",
                    "error",
                    "Invalid MCP dependency URL",
                    "MCP dependency URLs must be credential-free HTTP(S) URLs with a host.",
                    "agents/openai.yaml",
                    line,
                    ("codex",),
                )
    if report.target in {"copilot", "all"}:
        report.add(
            "PSD-TOOL-013",
            "warning",
            "OpenAI-only dependency metadata",
            "GitHub Copilot may ignore agents/openai.yaml; declare required tools in portable compatibility metadata as well.",
            "agents/openai.yaml",
            entries[0][1],
            ("copilot",),
        )


def _contains_directory_pair(parts: Sequence[str], first: str, second: str) -> bool:
    return any(parts[index] == first and parts[index + 1] == second for index in range(len(parts) - 1))


def _direct_discovery_targets(root: Path) -> tuple[set[str], set[str]]:
    parts = tuple(root.parts)
    direct: set[str] = set()
    legacy: set[str] = set()
    if _contains_directory_pair(parts, ".agents", "skills"):
        direct.update(("codex", "copilot"))
    if _contains_directory_pair(parts, ".github", "skills") or _contains_directory_pair(parts, ".claude", "skills"):
        direct.add("copilot")
    if _contains_directory_pair(parts, ".copilot", "skills"):
        direct.add("copilot")
    if _contains_directory_pair(parts, ".codex", "skills"):
        legacy.add("codex")
    return direct, legacy


def _is_publish_layout(root: Path) -> bool:
    runtime_roots = {".agents", ".github", ".claude", ".copilot", ".codex"}
    if root.parent.name == "skills" and root.parent.parent.name not in runtime_roots:
        return True
    parts = root.parts
    return any(
        parts[index] == "plugins" and parts[index + 2] == "skills"
        for index in range(max(0, len(parts) - 3))
    )


def _check_discovery_layout(root: Path, report: AuditReport) -> None:
    selected = {"codex", "copilot"} if report.target == "all" else {report.target}
    direct, legacy = _direct_discovery_targets(root)
    for target in sorted(selected):
        if target in direct:
            continue
        if target in legacy:
            report.add(
                "PSD-DISCOVERY-001",
                "warning",
                "Legacy discovery path",
                "This path is recognized for compatibility, but .agents/skills is the current cross-runtime location.",
                ".",
                targets=(target,),
            )
            continue
        if _is_publish_layout(root):
            report.add(
                "PSD-DISCOVERY-002",
                "info",
                "Distribution layout",
                f"The skill is publishable but must be installed into a {target} discovery directory before runtime use.",
                ".",
                targets=(target,),
            )
            continue
        report.add(
            "PSD-DISCOVERY-003",
            "info",
            "Staging discovery path",
            f"The audited source is outside a documented {target} discovery or GitHub publication layout; install it into a documented location before expecting runtime discovery.",
            ".",
            targets=(target,),
        )


def audit_skill(skill_dir: str | os.PathLike[str], target: str = "all", strict: bool = False) -> AuditReport:
    """Audit one skill directory without executing any of its content."""

    if target not in VALID_TARGETS:
        raise ValueError(f"target must be one of: {', '.join(VALID_TARGETS)}")
    raw_input = os.fspath(skill_dir)
    report = AuditReport(input_path=raw_input, root=None, target=target, strict=strict)
    input_path = Path(raw_input).expanduser()
    try:
        root = input_path.resolve(strict=True)
    except (FileNotFoundError, OSError) as error:
        report.add(
            "PSD-INPUT-001",
            "error",
            "Skill directory does not exist",
            f"Cannot resolve audit target: {error}.",
        )
        return report
    if not root.is_dir():
        report.add(
            "PSD-INPUT-002",
            "error",
            "Audit target is not a directory",
            "Pass the directory that directly contains SKILL.md.",
        )
        return report
    report.root = str(root)

    _check_permissions(root, root, report)
    entries = list(_iter_entries(root, report))
    files: list[Path] = []
    for path in entries:
        if path.is_symlink():
            _check_symlink(path, root, report)
            continue
        _check_permissions(path, root, report)
        try:
            if path.is_file():
                files.append(path)
        except OSError:
            continue

    skill_path = root / "SKILL.md"
    if not os.path.lexists(skill_path):
        report.add(
            "PSD-FILE-005",
            "error",
            "SKILL.md is missing",
            "The audited directory must contain SKILL.md at its root.",
            "SKILL.md",
        )
        _check_discovery_layout(root, report)
        return report
    if skill_path.is_symlink():
        _check_symlink(skill_path, root, report)
        try:
            if not _is_within(skill_path.resolve(strict=True), root):
                _check_discovery_layout(root, report)
                return report
        except (OSError, RuntimeError):
            _check_discovery_layout(root, report)
            return report

    skill_text = _read_text_file(skill_path, root, report)
    frontmatter: Frontmatter | None = None
    if skill_text is not None:
        frontmatter = _parse_frontmatter(skill_text, report)
        if frontmatter is not None:
            _validate_frontmatter(frontmatter, root, report)
            _scan_suspicious_content(
                skill_path,
                frontmatter.body,
                root,
                report,
                line_offset=frontmatter.body_start_line - 1,
            )

    for path in sorted(files, key=lambda item: _relative_path(item, root)):
        if path == skill_path:
            text = skill_text
        elif path.suffix.lower() in TEXT_SUFFIXES:
            text = _read_text_file(path, root, report)
        else:
            text = None
        if text is None:
            continue
        if path.suffix.lower() in {".md", ".markdown"}:
            _scan_resource_references(path, text, root, report)
            if path != skill_path:
                _scan_suspicious_content(path, text, root, report)

    _validate_allowed_tools(frontmatter, report)
    _validate_openai_dependencies(root, files, report)
    _scan_scripts(files, root, frontmatter, report)
    _check_discovery_layout(root, report)
    return report


def render_text(report: AuditReport) -> str:
    counts = report.counts()
    status = "PASS" if report.passed() else "FAIL"
    lines = [
        f"{TOOL_NAME} {TOOL_VERSION}",
        f"Skill: {report.skill_name or '(unknown)'}",
        f"Root: {report.root or report.input_path}",
        f"Target: {report.target} | Strict: {'yes' if report.strict else 'no'} | Result: {status}",
        f"Findings: {counts['error']} error, {counts['warning']} warning, {counts['info']} info",
    ]
    findings = report.sorted_findings()
    if not findings:
        lines.append("No findings.")
    for finding in findings:
        location = finding.path
        if finding.line is not None:
            location += f":{finding.line}"
        target_suffix = f" [{','.join(finding.targets)}]" if finding.targets else ""
        lines.append(
            f"{finding.severity.upper():7} {finding.id} {location}{target_suffix} - {finding.message}"
        )
    return "\n".join(lines)


def render_json(report: AuditReport) -> str:
    return json.dumps(report.to_dict(), ensure_ascii=False, indent=2, sort_keys=True)


def render_sarif(report: AuditReport) -> str:
    findings = report.sorted_findings()
    rules_by_id: dict[str, Finding] = {}
    for finding in findings:
        rules_by_id.setdefault(finding.id, finding)
    rules = [
        {
            "id": rule_id,
            "name": re.sub(r"[^A-Za-z0-9]+", "_", finding.title).strip("_"),
            "shortDescription": {"text": finding.title},
            "defaultConfiguration": {"level": _sarif_level(finding.severity)},
        }
        for rule_id, finding in sorted(rules_by_id.items())
    ]
    results: list[dict[str, Any]] = []
    for finding in findings:
        result: dict[str, Any] = {
            "ruleId": finding.id,
            "level": _sarif_level(finding.severity),
            "message": {"text": finding.message},
            "properties": {
                "severity": finding.severity,
                "targets": list(finding.targets),
            },
        }
        if finding.path and finding.path != ".":
            physical_location: dict[str, Any] = {
                "artifactLocation": {"uri": finding.path, "uriBaseId": "%SRCROOT%"}
            }
            if finding.line is not None:
                physical_location["region"] = {"startLine": finding.line}
            result["locations"] = [{"physicalLocation": physical_location}]
        results.append(result)
    sarif = {
        "$schema": SARIF_SCHEMA,
        "version": "2.1.0",
        "runs": [
            {
                "tool": {
                    "driver": {
                        "name": TOOL_NAME,
                        "version": TOOL_VERSION,
                        "informationUri": "https://github.com/ProfesseurHaipeng/professeur-ai-skills",
                        "rules": rules,
                    }
                },
                "originalUriBaseIds": {
                    "%SRCROOT%": {"uri": Path(report.root or ".").as_uri() + "/" if report.root else "file:///"}
                },
                "properties": {
                    "target": report.target,
                    "strict": report.strict,
                    "passed": report.passed(),
                },
                "results": results,
            }
        ],
    }
    return json.dumps(sarif, ensure_ascii=False, indent=2, sort_keys=True)


def _sarif_level(severity: str) -> str:
    return {"error": "error", "warning": "warning", "info": "note"}[severity]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog=TOOL_NAME,
        description="Offline compatibility and safety audit for Agent Skills.",
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {TOOL_VERSION}")
    subparsers = parser.add_subparsers(dest="command", required=True)
    audit = subparsers.add_parser("audit", help="audit one directory containing SKILL.md")
    audit.add_argument("skill_dir", help="directory that directly contains SKILL.md")
    audit.add_argument("--target", choices=VALID_TARGETS, default="all")
    audit.add_argument("--format", dest="output_format", choices=VALID_FORMATS, default="text")
    audit.add_argument(
        "--strict",
        action="store_true",
        help="return exit 1 for warnings as well as errors",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.command != "audit":
        parser.error("an audit command is required")
        return EXIT_USAGE
    try:
        report = audit_skill(args.skill_dir, target=args.target, strict=args.strict)
        if args.output_format == "json":
            output = render_json(report)
        elif args.output_format == "sarif":
            output = render_sarif(report)
        else:
            output = render_text(report)
        print(output)
        return report.exit_code()
    except BrokenPipeError:
        return EXIT_OK
    except Exception as error:  # pragma: no cover - last-resort CLI boundary
        print(f"{TOOL_NAME}: internal error: {error}", file=sys.stderr)
        return EXIT_INTERNAL


if __name__ == "__main__":
    raise SystemExit(main())
