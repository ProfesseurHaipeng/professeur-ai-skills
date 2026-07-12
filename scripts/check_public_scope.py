#!/usr/bin/env python3
"""Fail closed when a public Skill repository contains risky release material."""

from __future__ import annotations

import argparse
from dataclasses import asdict, dataclass
import json
import os
from pathlib import Path
import re
import sys
from typing import Iterable, Pattern


DEFAULT_MAX_BYTES = 1_000_000
SKIP_DIRECTORIES = {".git", ".mypy_cache", ".pytest_cache", "__pycache__"}
BLOCKED_DIRECTORIES = {
    ".aws",
    ".gnupg",
    ".ssh",
    ".venv",
    "build",
    "dist",
    "htmlcov",
    "node_modules",
    "venv",
}
BLOCKED_FILENAMES = {
    ".DS_Store",
    ".npmrc",
    ".pypirc",
    "credentials",
    "credentials.json",
    "id_rsa",
    "id_ed25519",
}
BLOCKED_SUFFIXES = {
    ".7z",
    ".db",
    ".doc",
    ".docx",
    ".gz",
    ".heic",
    ".jpeg",
    ".jpg",
    ".key",
    ".numbers",
    ".pages",
    ".pdf",
    ".pem",
    ".pkl",
    ".png",
    ".ppt",
    ".pptx",
    ".sqlite",
    ".tar",
    ".tgz",
    ".xls",
    ".xlsx",
    ".zip",
}


@dataclass(frozen=True)
class Finding:
    code: str
    path: str
    line: int | None
    message: str


@dataclass(frozen=True)
class TextRule:
    code: str
    pattern: Pattern[str]
    message: str


def _compile_rules() -> tuple[TextRule, ...]:
    token_prefixes = (
        "gh" + "p_",
        "github" + "_pat_",
        "sk" + "-",
        "xox" + "b-",
    )
    prefixed_token = r"(?:" + "|".join(re.escape(item) for item in token_prefixes) + r")[A-Za-z0-9_-]{16,}"
    cloud_access_key = r"\b(?:AKIA|ASIA)[0-9A-Z]{16}\b|\bAIza[0-9A-Za-z_-]{30,}\b"
    private_key = "BEGIN " + r"(?:RSA |EC |OPENSSH )?PRIVATE KEY"
    formula_word = "form" + r"(?:ula|ulation)"
    customer_word = "cust" + "omer"
    client_word = "cli" + "ent"
    chinese_formula = "配" + "方"
    chinese_household = "日" + "化"
    chinese_customer = "客" + "户"

    return (
        TextRule(
            "secret-token",
            re.compile(rf"(?:{prefixed_token}|{cloud_access_key})"),
            "Credential-like token found; remove it and rotate any real credential.",
        ),
        TextRule(
            "private-key",
            re.compile(private_key, re.IGNORECASE),
            "Private-key material must not be published.",
        ),
        TextRule(
            "secret-assignment",
            re.compile(
                r"(?i)\b(?:api[_-]?key|access[_-]?token|auth[_-]?token|client[_-]?secret|password)"
                r"\s*[:=]\s*['\"][^'\"\s]{8,}['\"]"
            ),
            "Secret-like assignment found; examples must use unmistakable placeholders.",
        ),
        TextRule(
            "personal-email",
            re.compile(r"(?i)\b(?![^@\s]+@(?:example\.com|users\.noreply\.github\.com)\b)[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b"),
            "Personal or operational email address found.",
        ),
        TextRule(
            "personal-phone",
            re.compile(r"(?<!\d)(?:\+?86[- ]?)?1[3-9]\d{9}(?!\d)|(?<!\d)\+?[1-9]\d{0,2}[- .]\d{3}[- .]\d{3}[- .]\d{4}(?!\d)"),
            "Phone-number-like value found.",
        ),
        TextRule(
            "government-id",
            re.compile(r"(?<!\d)\d{17}[0-9Xx](?!\d)|(?<!\d)\d{3}-\d{2}-\d{4}(?!\d)"),
            "Government-identifier-like value found.",
        ),
        TextRule(
            "local-path",
            re.compile((r"(?:/Us" + r"ers/[^\s'\"]+|[A-Za-z]:\\Users\\[^\s'\"]+)")),
            "Machine-specific home path found; use a repository-relative placeholder.",
        ),
        TextRule(
            "private-network-address",
            re.compile(r"\b(?:127\.0\.0\.1|10\.\d{1,3}(?:\.\d{1,3}){2}|192\.168(?:\.\d{1,3}){2}|172\.(?:1[6-9]|2\d|3[01])(?:\.\d{1,3}){2})\b"),
            "Private or loopback network address found.",
        ),
        TextRule(
            "restricted-interactive-domain",
            re.compile(
                ("game" + r"(?:play| design| mechanic| level| character| battle| combat| quest| boss)")
                + r"|(?:battle|combat) system|玩家.{0,12}(?:关卡|战斗|角色)|游戏.{0,16}(?:玩法|关卡|角色|战斗|地图)",
                re.IGNORECASE,
            ),
            "Scope-restricted interactive-product material found.",
        ),
        TextRule(
            "restricted-formulation-domain",
            re.compile(
                rf"\b{formula_word}\b.{{0,30}}\b(?:ingredient|concentration|batch|recipe|surfactant|preservative|spray)\b"
                rf"|\b(?:ingredient|batch|recipe)\b.{{0,30}}\b{formula_word}\b"
                rf"|(?:{chinese_formula}|{chinese_household}).{{0,24}}(?:原料|浓度|批次|工艺|成分|喷雾)",
                re.IGNORECASE,
            ),
            "Scope-restricted formulation or household-product material found.",
        ),
        TextRule(
            "restricted-commercial-record",
            re.compile(
                rf"\b(?:{customer_word}|{client_word})\s+(?:list|record|dataset|data|name|email|account|brief|contract|order|project)\b"
                rf"|{chinese_customer}.{{0,16}}(?:名单|资料|数据|邮箱|电话|合同|订单|项目|需求)",
                re.IGNORECASE,
            ),
            "Customer, client, or commercial record material found.",
        ),
        TextRule(
            "restricted-professional-pet-advice",
            re.compile(
                r"\b(?:pet|animal|dog|cat)\b.{0,50}\b(?:diagnos(?:e|is)|treat(?:ment)?|prescri(?:be|ption)|dosage|disease)\b"
                r"|\b(?:diagnos(?:e|is)|treat(?:ment)?|prescri(?:be|ption)|dosage|disease)\b.{0,50}\b(?:pet|animal|dog|cat)\b"
                r"|(?:宠物|猫|狗).{0,24}(?:诊断|治疗|处方|剂量|疾病)",
                re.IGNORECASE,
            ),
            "Professional animal-health advice is outside the public scope.",
        ),
        TextRule(
            "unverified-network-claim",
            re.compile(r"(?i)\b(?:100%\s+offline|completely private|guaranteed secure|zero data leaves|never uses (?:the )?network)\b"),
            "Absolute network, privacy, or security claim requires narrower tested wording.",
        ),
        TextRule(
            "unverified-compatibility-claim",
            re.compile(r"(?i)\b(?:works with (?:all|every) agents?|supports (?:all|every) (?:agent|model|platform)s?|universal compatibility)\b"),
            "Universal compatibility claim is not permitted without an exhaustive test contract.",
        ),
    )


TEXT_RULES = _compile_rules()
RULE_DEFINITION_PATHS = {"scripts/check_public_scope.py"}


def _line_number(text: str, offset: int) -> int:
    return text.count("\n", 0, offset) + 1


def scan_text(text: str, relative_path: str) -> list[Finding]:
    findings: list[Finding] = []
    seen: set[tuple[str, int]] = set()
    for rule in TEXT_RULES:
        if relative_path in RULE_DEFINITION_PATHS and rule.code.startswith(("restricted-", "unverified-")):
            continue
        for match in rule.pattern.finditer(text):
            line = _line_number(text, match.start())
            if rule.code.startswith("unverified-"):
                line_start = text.rfind("\n", 0, match.start()) + 1
                line_end = text.find("\n", match.end())
                if line_end == -1:
                    line_end = len(text)
                line_text = text[line_start:line_end].casefold()
                prefix = line_text[: max(match.start() - line_start, 0)]
                if re.search(r"\b(?:no|not|avoid|without|reject|prohibit|claims? of|must not)\b", prefix):
                    continue
            identity = (rule.code, line)
            if identity in seen:
                continue
            seen.add(identity)
            findings.append(Finding(rule.code, relative_path, line, rule.message))
    return findings


def _blocked_suffix(name: str) -> bool:
    lowered = name.casefold()
    return any(lowered.endswith(suffix) for suffix in BLOCKED_SUFFIXES)


def _blocked_filename(name: str) -> bool:
    lowered = name.casefold()
    return lowered in {item.casefold() for item in BLOCKED_FILENAMES} or lowered == ".env" or lowered.startswith(".env.")


def scan_repository(root: Path, max_bytes: int = DEFAULT_MAX_BYTES) -> tuple[list[Finding], int]:
    root = root.expanduser().resolve()
    if not root.is_dir():
        raise ValueError(f"scan root is not a directory: {root}")

    findings: list[Finding] = []
    scanned_files = 0
    for current, directories, filenames in os.walk(root, topdown=True, followlinks=False):
        current_path = Path(current)
        kept_directories: list[str] = []
        for directory in sorted(directories):
            candidate = current_path / directory
            relative = candidate.relative_to(root).as_posix()
            normalized_directory = directory.casefold()
            if normalized_directory in {item.casefold() for item in SKIP_DIRECTORIES}:
                continue
            if candidate.is_symlink():
                findings.append(Finding("symlink", relative, None, "Symbolic links are not allowed in a public release tree."))
                continue
            if normalized_directory in {item.casefold() for item in BLOCKED_DIRECTORIES}:
                findings.append(Finding("blocked-directory", relative, None, "Generated, dependency, cache, or private configuration directory is not publishable."))
                continue
            kept_directories.append(directory)
        directories[:] = kept_directories

        for filename in sorted(filenames):
            path = current_path / filename
            relative = path.relative_to(root).as_posix()
            if path.is_symlink():
                findings.append(Finding("symlink", relative, None, "Symbolic links are not allowed in a public release tree."))
                continue
            if _blocked_filename(filename):
                findings.append(Finding("blocked-file", relative, None, "Credential, machine, or environment file is not publishable."))
                continue
            if _blocked_suffix(filename):
                findings.append(Finding("blocked-artifact", relative, None, "Binary, archive, database, or office artifact is outside the source allowlist."))
                continue
            try:
                size = path.stat().st_size
            except OSError as exc:
                findings.append(Finding("read-error", relative, None, f"Could not stat file: {exc}"))
                continue
            if size > max_bytes:
                findings.append(Finding("oversized-file", relative, None, f"File exceeds the {max_bytes}-byte public source limit."))
                continue
            try:
                raw = path.read_bytes()
            except OSError as exc:
                findings.append(Finding("read-error", relative, None, f"Could not read file: {exc}"))
                continue
            scanned_files += 1
            if b"\x00" in raw:
                findings.append(Finding("binary-content", relative, None, "Binary content is not allowed in the source release."))
                continue
            try:
                text = raw.decode("utf-8")
            except UnicodeDecodeError:
                findings.append(Finding("non-utf8-content", relative, None, "Source files must be valid UTF-8 text."))
                continue
            findings.extend(scan_text(text, relative))

    findings.sort(key=lambda item: (item.path, item.line or 0, item.code))
    return findings, scanned_files


def _render_text(findings: Iterable[Finding], root: Path, scanned_files: int) -> None:
    findings = list(findings)
    if not findings:
        print(f"PASS: scanned {scanned_files} UTF-8 source files under {root}.")
        return
    for item in findings:
        location = f"{item.path}:{item.line}" if item.line else item.path
        print(f"ERROR [{item.code}] {location}: {item.message}")
    print(f"FAIL: {len(findings)} finding(s) across {scanned_files} scanned files.")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("root", nargs="?", default=".", type=Path, help="Repository root to scan")
    parser.add_argument("--max-bytes", type=int, default=DEFAULT_MAX_BYTES, help="Maximum allowed source file size")
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    root = args.root.expanduser().resolve()
    try:
        findings, scanned_files = scan_repository(root, args.max_bytes)
    except (OSError, ValueError) as exc:
        if args.json:
            print(json.dumps({"ok": False, "root": str(root), "scanned_files": 0, "findings": [{"code": "scan-error", "path": str(root), "line": None, "message": str(exc)}]}, indent=2))
        else:
            print(f"ERROR [scan-error] {root}: {exc}", file=sys.stderr)
        return 2

    payload = {
        "ok": not findings,
        "root": str(root),
        "scanned_files": scanned_files,
        "findings": [asdict(item) for item in findings],
    }
    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        _render_text(findings, root, scanned_files)
    if any(item.code == "read-error" for item in findings):
        return 2
    return 1 if findings else 0


if __name__ == "__main__":
    raise SystemExit(main())
