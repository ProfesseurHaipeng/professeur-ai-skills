#!/usr/bin/env python3
"""Audit a source release archive without extracting it."""

from __future__ import annotations

import argparse
from dataclasses import asdict, dataclass
import json
from pathlib import Path, PurePosixPath
import re
import stat
import sys
import tarfile
import zipfile

from check_public_scope import DEFAULT_MAX_BYTES, scan_text


MAX_ENTRIES = 1_024
MAX_TOTAL_BYTES = 10_000_000
MAX_COMPRESSION_RATIO = 200
ALLOWED_ROOT_FILES = {
    ".gitignore",
    "CHANGELOG.md",
    "CODE_OF_CONDUCT.md",
    "CONTRIBUTING.md",
    "LICENSE",
    "README.md",
    "SECURITY.md",
    "THIRD_PARTY_NOTICES.md",
}
ALLOWED_PREFIXES = (".github/", "docs/", "evals/", "scripts/", "skills/", "tests/")
ALLOWED_SUFFIXES = {".json", ".lock", ".md", ".py", ".toml", ".txt", ".yaml", ".yml"}


@dataclass(frozen=True)
class ArchiveFinding:
    code: str
    path: str
    message: str


@dataclass(frozen=True)
class Entry:
    raw_path: str
    is_directory: bool
    is_symlink: bool
    is_special: bool
    encrypted: bool
    size: int
    compressed_size: int | None
    read: object


def _safe_raw_path(raw_path: str) -> bool:
    if not raw_path or "\\" in raw_path or "\x00" in raw_path or "//" in raw_path:
        return False
    if raw_path.startswith("/") or re.match(r"^[A-Za-z]:", raw_path):
        return False
    path = PurePosixPath(raw_path)
    return all(part not in {"", ".", ".."} for part in path.parts)


def _common_prefix(entries: list[Entry]) -> str | None:
    files = [PurePosixPath(item.raw_path) for item in entries if not item.is_directory and _safe_raw_path(item.raw_path)]
    if not files or any(len(path.parts) < 2 for path in files):
        return None
    first = files[0].parts[0]
    return first if all(path.parts[0] == first for path in files) else None


def _relative_path(raw_path: str, prefix: str | None) -> str:
    parts = PurePosixPath(raw_path).parts
    if prefix and parts and parts[0] == prefix:
        parts = parts[1:]
    return PurePosixPath(*parts).as_posix() if parts else ""


def _allowed_file(path: str) -> bool:
    if path in ALLOWED_ROOT_FILES:
        return True
    if not any(path.startswith(prefix) for prefix in ALLOWED_PREFIXES):
        return False
    return PurePosixPath(path).suffix.casefold() in ALLOWED_SUFFIXES


def _zip_entries(archive: zipfile.ZipFile) -> list[Entry]:
    entries: list[Entry] = []
    for info in archive.infolist():
        mode = (info.external_attr >> 16) & 0xFFFF
        file_type = stat.S_IFMT(mode)
        is_symlink = stat.S_ISLNK(mode)
        is_directory = info.is_dir()
        entries.append(
            Entry(
                raw_path=info.filename.rstrip("/") if is_directory else info.filename,
                is_directory=is_directory,
                is_symlink=is_symlink,
                is_special=file_type not in {0, stat.S_IFREG, stat.S_IFDIR, stat.S_IFLNK},
                encrypted=bool(info.flag_bits & 0x1),
                size=info.file_size,
                compressed_size=info.compress_size,
                read=lambda item=info: archive.read(item),
            )
        )
    return entries


def _tar_entries(archive: tarfile.TarFile) -> list[Entry]:
    entries: list[Entry] = []
    for member in archive.getmembers():
        is_directory = member.isdir()
        is_symlink = member.issym() or member.islnk()
        is_special = not (member.isfile() or is_directory or is_symlink)

        def read_member(item: tarfile.TarInfo = member) -> bytes:
            stream = archive.extractfile(item)
            return stream.read() if stream is not None else b""

        entries.append(
            Entry(
                raw_path=member.name.rstrip("/") if is_directory else member.name,
                is_directory=is_directory,
                is_symlink=is_symlink,
                is_special=is_special,
                encrypted=False,
                size=member.size,
                compressed_size=None,
                read=read_member,
            )
        )
    return entries


def _open_entries(path: Path) -> tuple[list[Entry], object]:
    if zipfile.is_zipfile(path):
        archive = zipfile.ZipFile(path, "r")
        return _zip_entries(archive), archive
    if tarfile.is_tarfile(path):
        archive = tarfile.open(path, "r:*")
        return _tar_entries(archive), archive
    raise ValueError("archive must be a readable .zip, .tar, .tar.gz, or .tgz file")


def audit_archive(
    path: Path,
    *,
    max_entry_bytes: int = DEFAULT_MAX_BYTES,
    max_total_bytes: int = MAX_TOTAL_BYTES,
    max_entries: int = MAX_ENTRIES,
) -> tuple[list[ArchiveFinding], int, int]:
    path = path.expanduser().resolve()
    if not path.is_file():
        raise ValueError(f"archive is not a file: {path}")

    entries, archive = _open_entries(path)
    findings: list[ArchiveFinding] = []
    try:
        if len(entries) > max_entries:
            findings.append(ArchiveFinding("entry-count", "<archive>", f"Archive has {len(entries)} entries; limit is {max_entries}."))
            total_bytes = sum(max(item.size, 0) for item in entries if not item.is_directory)
            return findings, len(entries), total_bytes
        prefix = _common_prefix(entries)
        total_bytes = sum(max(item.size, 0) for item in entries if not item.is_directory)
        read_contents = total_bytes <= max_total_bytes
        if total_bytes > max_total_bytes:
            findings.append(ArchiveFinding("archive-size", "<archive>", f"Uncompressed size {total_bytes} exceeds {max_total_bytes} bytes."))

        seen: set[str] = set()
        seen_casefolded: set[str] = set()
        for item in entries:
            raw_path = item.raw_path
            if not _safe_raw_path(raw_path):
                findings.append(ArchiveFinding("unsafe-path", raw_path or "<empty>", "Absolute, parent, Windows, empty, or NUL archive path found."))
                continue
            relative = _relative_path(raw_path, prefix)
            if not relative:
                continue
            normalized_key = relative.casefold()
            if relative in seen or normalized_key in seen_casefolded:
                findings.append(ArchiveFinding("duplicate-entry", relative, "Duplicate or case-colliding archive entry found."))
                continue
            seen.add(relative)
            seen_casefolded.add(normalized_key)
            if item.is_symlink:
                findings.append(ArchiveFinding("link-entry", relative, "Symbolic and hard links are not allowed in a release archive."))
                continue
            if item.is_special:
                findings.append(ArchiveFinding("special-entry", relative, "Device, FIFO, socket, or other special entry is not allowed."))
                continue
            if item.encrypted:
                findings.append(ArchiveFinding("encrypted-entry", relative, "Encrypted entries cannot be audited and are not allowed."))
                continue
            if item.is_directory:
                continue
            if not _allowed_file(relative):
                findings.append(ArchiveFinding("disallowed-entry", relative, "Entry is outside the public source allowlist."))
                continue
            if item.size < 0 or item.size > max_entry_bytes:
                findings.append(ArchiveFinding("entry-size", relative, f"Entry size {item.size} exceeds the {max_entry_bytes}-byte limit."))
                continue
            if item.compressed_size is not None and item.size > 65_536:
                ratio = item.size / max(item.compressed_size, 1)
                if ratio > MAX_COMPRESSION_RATIO:
                    findings.append(ArchiveFinding("compression-ratio", relative, f"Compression ratio {ratio:.1f}:1 exceeds the safe limit."))
                    continue
            if not read_contents:
                continue
            try:
                raw = item.read()
            except (OSError, RuntimeError, tarfile.TarError, zipfile.BadZipFile) as exc:
                findings.append(ArchiveFinding("read-error", relative, f"Could not read archive entry: {exc}"))
                continue
            if len(raw) != item.size:
                findings.append(ArchiveFinding("size-mismatch", relative, "Declared and decoded entry sizes do not match."))
                continue
            if b"\x00" in raw:
                findings.append(ArchiveFinding("binary-content", relative, "Binary content is not allowed in the source release."))
                continue
            try:
                text = raw.decode("utf-8")
            except UnicodeDecodeError:
                findings.append(ArchiveFinding("non-utf8-content", relative, "Source entries must be valid UTF-8 text."))
                continue
            for item_finding in scan_text(text, relative):
                findings.append(ArchiveFinding(item_finding.code, relative, item_finding.message))
    finally:
        archive.close()

    findings.sort(key=lambda item: (item.path, item.code))
    return findings, len(entries), sum(max(item.size, 0) for item in entries if not item.is_directory)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("archive", type=Path, help="Source archive to audit")
    parser.add_argument("--max-entry-bytes", type=int, default=DEFAULT_MAX_BYTES)
    parser.add_argument("--max-total-bytes", type=int, default=MAX_TOTAL_BYTES)
    parser.add_argument("--max-entries", type=int, default=MAX_ENTRIES)
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    archive_path = args.archive.expanduser().resolve()
    try:
        findings, entries, total_bytes = audit_archive(
            archive_path,
            max_entry_bytes=args.max_entry_bytes,
            max_total_bytes=args.max_total_bytes,
            max_entries=args.max_entries,
        )
    except (OSError, ValueError, tarfile.TarError, zipfile.BadZipFile) as exc:
        payload = {"ok": False, "archive": str(archive_path), "entries": 0, "total_uncompressed_bytes": 0, "findings": [{"code": "archive-error", "path": str(archive_path), "message": str(exc)}]}
        if args.json:
            print(json.dumps(payload, ensure_ascii=False, indent=2))
        else:
            print(f"ERROR [archive-error] {archive_path}: {exc}", file=sys.stderr)
        return 2

    payload = {
        "ok": not findings,
        "archive": str(archive_path),
        "entries": entries,
        "total_uncompressed_bytes": total_bytes,
        "findings": [asdict(item) for item in findings],
    }
    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    elif findings:
        for item in findings:
            print(f"ERROR [{item.code}] {item.path}: {item.message}")
        print(f"FAIL: {len(findings)} finding(s) across {entries} entries.")
    else:
        print(f"PASS: audited {entries} entries and {total_bytes} uncompressed bytes.")
    if any(item.code == "read-error" for item in findings):
        return 2
    return 1 if findings else 0


if __name__ == "__main__":
    raise SystemExit(main())
