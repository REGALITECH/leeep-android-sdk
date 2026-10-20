import importlib.util
import io
from pathlib import Path
import unittest
from unittest.mock import patch
import urllib.error
import zipfile

spec = importlib.util.spec_from_file_location("release", Path(__file__).parents[1] / "scripts/release.py")
release = importlib.util.module_from_spec(spec)
spec.loader.exec_module(release)


class ReleaseGatesTest(unittest.TestCase):
    def setUp(self):
        self.commit = "a" * 40
        self.status = {"status": "ok", "commit": self.commit}
        self.pom = b'''<project xmlns="http://maven.apache.org/POM/4.0.0">
          <groupId>com.github.REGALITECH</groupId><artifactId>leeep-android-sdk</artifactId>
          <version>0.10.0</version><packaging>aar</packaging></project>'''
        self.metadata = b"<metadata><versioning><versions><version>0.10.0</version></versions></versioning></metadata>"
        self.licenses = {"LICENSE": b"sdk terms", "THIRD_PARTY_NOTICES.txt": b"third party notices"}
        buffer = io.BytesIO()
        with zipfile.ZipFile(buffer, "w") as archive:
            archive.writestr("classes.jar", b"classes")
            for name, contents in self.licenses.items():
                archive.writestr(f"assets/leeep/licenses/{name}", contents)
        self.aar = buffer.getvalue()

    def verify(self, **changes):
        args = dict(tag="0.10.0", commit=self.commit, status=self.status, pom=self.pom,
                    aar=self.aar, metadata=self.metadata, expected_aar=self.aar, licenses=self.licenses)
        args.update(changes)
        release.validate_distribution(**args)

    def test_only_stable_numeric_tags_are_accepted(self):
        release.validate_tag("0.10.0")
        for tag in ("v0.10.0", "0.10.0-rc.1", "01.2.3", "../notes", "0.10.0\n", "1.2"):
            with self.subTest(tag=tag), self.assertRaises(ValueError):
                release.validate_tag(tag)

    def test_authored_notes_required_on_workflow_checkout(self):
        self.assertEqual(release.notes_path("0.10.0"), Path("releases/0.10.0.md"))
        with self.assertRaises(FileNotFoundError):
            release.notes_path("99.99.99")
        with patch.object(Path, "read_text", return_value="# 0.10.0\n## 変更内容\nTODO\n## 更新時の対応\nなし"):
            with self.assertRaises(ValueError):
                release.notes_path("0.10.0")

    def test_distribution_requires_commit_coordinates_discovery_and_exact_binary(self):
        self.verify()
        failures = [
            {"status": {"status": "ok", "commit": "b" * 40}},
            {"status": {"status": "building", "commit": self.commit}},
            {"pom": self.pom.replace(b"0.10.0", b"0.9.1")},
            {"metadata": self.metadata.replace(b"0.10.0", b"0.9.1")},
            {"expected_aar": b"different binary"},
            {"licenses": {"LICENSE": b"different terms"}},
        ]
        for change in failures:
            with self.subTest(change=change.keys()), self.assertRaises(ValueError):
                self.verify(**change)

    def test_only_explicit_404_allows_new_release(self):
        with patch.dict(release.os.environ, {"GH_TOKEN": "test"}):
            for status in (403, 500):
                error = urllib.error.HTTPError("url", status, "error", {}, io.BytesIO())
                with error, self.subTest(status=status), patch.object(release.urllib.request, "urlopen", side_effect=error):
                    with self.assertRaises(urllib.error.HTTPError):
                        release.assert_no_release("0.10.0")
            error = urllib.error.HTTPError("url", 404, "missing", {}, io.BytesIO())
            with error, patch.object(release.urllib.request, "urlopen", side_effect=error):
                release.assert_no_release("0.10.0")
            with patch.object(release.urllib.request, "urlopen"):
                with self.assertRaises(ValueError):
                    release.assert_no_release("0.10.0")

    def test_unavailable_jitpack_stops_after_bounded_wait(self):
        elapsed = [0]

        def advance(seconds):
            elapsed[0] += seconds

        with patch.object(release, "git", return_value=b"unused"), \
             patch.object(release, "download", side_effect=urllib.error.URLError("unavailable")) as download, \
             patch.object(release.time, "monotonic", side_effect=lambda: elapsed[0]), \
             patch.object(release.time, "sleep", side_effect=advance), \
             patch("builtins.print"):
            with self.assertRaisesRegex(RuntimeError, "within 12 minutes"):
                release.verify_jitpack("0.10.0", self.commit)
            self.assertEqual(elapsed[0], 720)
            self.assertEqual(download.call_count, 24)

    def test_moved_tag_never_reaches_release_creation(self):
        with patch("sys.argv", ["release.py", "publish", "0.10.0", "b" * 40]), \
             patch.object(release, "assert_no_release"), \
             patch.object(release, "resolve_tag", return_value=self.commit), \
             patch.object(release.subprocess, "run") as create:
            with self.assertRaises(ValueError):
                release.main()
            create.assert_not_called()

    def test_publish_uses_verified_tag_and_authored_notes_without_editing(self):
        with patch("sys.argv", ["release.py", "publish", "0.10.0", self.commit]), \
             patch.object(release, "assert_no_release"), \
             patch.object(release, "resolve_tag", return_value=self.commit), \
             patch.object(release.subprocess, "run") as create:
            release.main()
            command = create.call_args.args[0]
            self.assertEqual(command[:4], ["gh", "release", "create", "0.10.0"])
            self.assertIn("--verify-tag", command)
            self.assertEqual(command[-2:], ["--notes-file", "releases/0.10.0.md"])


if __name__ == "__main__":
    unittest.main()
