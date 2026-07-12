from __future__ import annotations

import io
import os
from pathlib import Path
import stat
import sys
import tarfile
import tempfile
import unittest
import zipfile


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS))

import audit_release_archive  # noqa: E402
import check_public_scope  # noqa: E402


class PublicScopeTests(unittest.TestCase):
    def write(self, root: Path, relative: str, text: str) -> None:
        path = root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")

    def codes(self, root: Path) -> set[str]:
        findings, _ = check_public_scope.scan_repository(root)
        return {item.code for item in findings}

    def test_minimal_skill_tree_passes(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            self.write(
                root,
                "skills/example/SKILL.md",
                "---\nname: example\ndescription: Audit a selected directory and return a structured report.\n---\n\n# Example\n",
            )
            self.write(root, "LICENSE", "Synthetic test license.\n")
            findings, scanned = check_public_scope.scan_repository(root)
            self.assertEqual(findings, [])
            self.assertEqual(scanned, 2)

    def test_scope_restricted_material_is_detected(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            restricted = "form" + "ulation batch ingredient concentration table"
            self.write(root, "skills/example/reference.md", restricted)
            self.assertIn("restricted-formulation-domain", self.codes(root))

    def test_interactive_product_material_is_detected(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            restricted = "game" + "play " + "battle" + " system and character level design"
            self.write(root, "skills/example/reference.md", restricted)
            self.assertIn("restricted-interactive-domain", self.codes(root))

    def test_commercial_record_is_detected(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            restricted = "cust" + "omer list with account and project data"
            self.write(root, "examples/data.txt", restricted)
            self.assertIn("restricted-commercial-record", self.codes(root))

    def test_non_english_scope_material_is_detected(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            restricted = bytes.fromhex("e9858de696b9e58e9fe69699e6b593e5baa6e689b9e6aca1").decode("utf-8")
            self.write(root, "examples/sample.txt", restricted)
            self.assertIn("restricted-formulation-domain", self.codes(root))

    def test_professional_animal_advice_is_detected(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            subject = "pe" + "t"
            action = "diag" + "nosis and treatment dosage"
            self.write(root, "examples/sample.txt", f"{subject} {action}")
            self.assertIn("restricted-professional-pet-advice", self.codes(root))

    def test_identifying_and_secret_like_values_are_detected(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            email = "person" + "@mail.test"
            token = "gh" + "p_" + "A" * 24
            self.write(root, "examples/sample.txt", f"{email}\n{token}\n")
            codes = self.codes(root)
            self.assertIn("personal-email", codes)
            self.assertIn("secret-token", codes)

    def test_cloud_key_shape_is_detected(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            key = "AK" + "IA" + "A" * 16
            self.write(root, "examples/sample.txt", key)
            self.assertIn("secret-token", self.codes(root))

    def test_absolute_claim_is_detected(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            claim = "This tool " + "works with " + "every " + "agent."
            self.write(root, "README.md", claim)
            self.assertIn("unverified-compatibility-claim", self.codes(root))

    def test_negated_claim_is_allowed(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            claim = "Do not claim that this tool " + "works with " + "every " + "agent."
            self.write(root, "SECURITY.md", claim)
            self.assertNotIn("unverified-compatibility-claim", self.codes(root))

    def test_environment_file_is_blocked(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            self.write(root, ".env", "PLACEHOLDER=value\n")
            self.assertIn("blocked-file", self.codes(root))

    def test_symlink_is_blocked(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            target = root / "target.txt"
            target.write_text("safe synthetic text", encoding="utf-8")
            try:
                os.symlink(target, root / "linked.txt")
            except (OSError, NotImplementedError):
                self.skipTest("symlinks are unavailable")
            self.assertIn("symlink", self.codes(root))


class ArchiveAuditTests(unittest.TestCase):
    def make_zip(self, path: Path, entries: dict[str, str]) -> None:
        with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
            for name, text in entries.items():
                archive.writestr(name, text)

    def archive_codes(self, path: Path) -> set[str]:
        findings, _, _ = audit_release_archive.audit_archive(path)
        return {item.code for item in findings}

    def test_safe_single_root_zip_passes(self):
        with tempfile.TemporaryDirectory() as temp:
            archive_path = Path(temp) / "source.zip"
            self.make_zip(
                archive_path,
                {
                    "package/README.md": "# Synthetic Skill\n",
                    "package/LICENSE": "Synthetic license text.\n",
                    "package/skills/example/SKILL.md": "---\nname: example\ndescription: Produce a structured static report for one selected directory.\n---\n",
                },
            )
            findings, entries, total = audit_release_archive.audit_archive(archive_path)
            self.assertEqual(findings, [])
            self.assertEqual(entries, 3)
            self.assertGreater(total, 0)

    def test_parent_traversal_is_blocked(self):
        with tempfile.TemporaryDirectory() as temp:
            archive_path = Path(temp) / "source.zip"
            self.make_zip(archive_path, {"package/../escape.txt": "synthetic"})
            self.assertIn("unsafe-path", self.archive_codes(archive_path))

    def test_ambiguous_double_separator_is_blocked(self):
        with tempfile.TemporaryDirectory() as temp:
            archive_path = Path(temp) / "source.zip"
            self.make_zip(archive_path, {"package//README.md": "synthetic"})
            self.assertIn("unsafe-path", self.archive_codes(archive_path))

    def test_zip_symlink_is_blocked(self):
        with tempfile.TemporaryDirectory() as temp:
            archive_path = Path(temp) / "source.zip"
            with zipfile.ZipFile(archive_path, "w") as archive:
                info = zipfile.ZipInfo("package/skills/example/link.txt")
                info.create_system = 3
                info.external_attr = (stat.S_IFLNK | 0o777) << 16
                archive.writestr(info, "../../outside")
            self.assertIn("link-entry", self.archive_codes(archive_path))

    def test_tar_symlink_is_blocked(self):
        with tempfile.TemporaryDirectory() as temp:
            archive_path = Path(temp) / "source.tar"
            with tarfile.open(archive_path, "w") as archive:
                info = tarfile.TarInfo("package/skills/example/link.txt")
                info.type = tarfile.SYMTYPE
                info.linkname = "../../outside"
                archive.addfile(info)
            self.assertIn("link-entry", self.archive_codes(archive_path))

    def test_secret_like_archive_content_is_blocked(self):
        with tempfile.TemporaryDirectory() as temp:
            archive_path = Path(temp) / "source.zip"
            token = "gh" + "p_" + "B" * 24
            self.make_zip(archive_path, {"package/README.md": token})
            self.assertIn("secret-token", self.archive_codes(archive_path))

    def test_disallowed_binary_path_is_blocked(self):
        with tempfile.TemporaryDirectory() as temp:
            archive_path = Path(temp) / "source.zip"
            self.make_zip(archive_path, {"package/assets/preview.png": "not really an image"})
            self.assertIn("disallowed-entry", self.archive_codes(archive_path))

    def test_duplicate_case_colliding_entries_are_blocked(self):
        with tempfile.TemporaryDirectory() as temp:
            archive_path = Path(temp) / "source.zip"
            with zipfile.ZipFile(archive_path, "w") as archive:
                archive.writestr("package/README.md", "one")
                archive.writestr("package/readme.md", "two")
            self.assertIn("duplicate-entry", self.archive_codes(archive_path))

    def test_entry_count_limit_fails_closed(self):
        with tempfile.TemporaryDirectory() as temp:
            archive_path = Path(temp) / "source.zip"
            self.make_zip(
                archive_path,
                {"package/README.md": "one", "package/LICENSE": "two"},
            )
            findings, _, _ = audit_release_archive.audit_archive(archive_path, max_entries=1)
            self.assertIn("entry-count", {item.code for item in findings})

    def test_total_uncompressed_limit_fails_closed(self):
        with tempfile.TemporaryDirectory() as temp:
            archive_path = Path(temp) / "source.zip"
            self.make_zip(archive_path, {"package/README.md": "varied release content " * 20})
            findings, _, _ = audit_release_archive.audit_archive(archive_path, max_total_bytes=20)
            self.assertIn("archive-size", {item.code for item in findings})

    def test_extreme_compression_ratio_is_blocked(self):
        with tempfile.TemporaryDirectory() as temp:
            archive_path = Path(temp) / "source.zip"
            self.make_zip(archive_path, {"package/README.md": "A" * 200_000})
            self.assertIn("compression-ratio", self.archive_codes(archive_path))

    def test_tar_regular_file_is_read_without_extracting(self):
        with tempfile.TemporaryDirectory() as temp:
            archive_path = Path(temp) / "source.tar"
            data = b"# Synthetic Skill\n"
            with tarfile.open(archive_path, "w") as archive:
                info = tarfile.TarInfo("package/README.md")
                info.size = len(data)
                archive.addfile(info, io.BytesIO(data))
            self.assertEqual(self.archive_codes(archive_path), set())


class RepositoryPolicyTests(unittest.TestCase):
    def test_workflow_actions_are_pinned_and_read_only(self):
        workflows = sorted((ROOT / ".github" / "workflows").glob("*.yml"))
        self.assertGreaterEqual(len(workflows), 1)
        for workflow in workflows:
            text = workflow.read_text(encoding="utf-8")
            self.assertIn("permissions:\n  contents: read", text, workflow.name)
            self.assertNotIn("pull_request_target", text, workflow.name)
            self.assertNotRegex(text, r"permissions:\s*write")
            for line in text.splitlines():
                if "uses:" not in line:
                    continue
                reference = line.split("uses:", 1)[1].split("#", 1)[0].strip()
                self.assertRegex(reference, r"^[^\s@]+@[0-9a-f]{40}$", line)


if __name__ == "__main__":
    unittest.main()
