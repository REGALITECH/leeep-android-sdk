import importlib.util
import io
import json
from pathlib import Path
import unittest
from unittest.mock import patch
import urllib.error
import xml.etree.ElementTree as ET
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
          <version>0.10.0</version><packaging>aar</packaging><dependencies>
            <dependency><groupId>example</groupId><artifactId>engine</artifactId>
              <version>1.2.3</version><scope>compile</scope><type>jar</type>
              <classifier>android</classifier><optional>false</optional>
              <exclusions><exclusion><groupId>excluded</groupId><artifactId>library</artifactId></exclusion></exclusions>
            </dependency>
            <dependency><groupId>example</groupId><artifactId>ui</artifactId>
              <version>2.0.0</version><scope>runtime</scope></dependency>
          </dependencies></project>'''
        self.expected_pom = self.pom.replace(b"<version>0.10.0</version>", b"<version>unspecified</version>")
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
                    aar=self.aar, metadata=self.metadata, expected_aar=self.aar,
                    licenses=self.licenses, expected_pom=self.expected_pom)
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

    def test_dependencies_ignore_xml_formatting_but_preserve_resolution_fields(self):
        ns = {"m": "http://maven.apache.org/POM/4.0.0"}
        root = ET.fromstring(self.pom)
        for node in root.find("m:dependencies", ns).iter():
            node[:] = reversed(list(node))
            if node.text and node.text.strip():
                node.text = "\n " + node.text.strip() + " "
        self.verify(pom=ET.tostring(root))
        for field in ("groupId", "artifactId", "version", "scope", "type", "classifier", "optional",
                      "exclusions/exclusion/groupId", "exclusions/exclusion/artifactId"):
            root = ET.fromstring(self.pom)
            path = "m:dependencies/m:dependency/" + "/".join("m:" + part for part in field.split("/"))
            root.find(path, ns).text = "changed"
            with self.subTest(field=field), self.assertRaisesRegex(ValueError, "dependencies differ"):
                self.verify(pom=ET.tostring(root))
        root = ET.fromstring(self.pom)
        dependencies = root.find("m:dependencies", ns)
        dependencies.clear()
        with self.assertRaisesRegex(ValueError, "dependencies differ"):
            self.verify(pom=ET.tostring(root))
        root.remove(dependencies)
        with self.assertRaisesRegex(ValueError, "dependencies element"):
            self.verify(pom=ET.tostring(root))

    def test_release_listing_paginates_and_rejects_a_draft_on_later_page(self):
        first_page = [{"tag_name": f"0.1.{i}", "draft": False, "prerelease": False} for i in range(100)]
        draft = {"tag_name": "0.10.0", "draft": True, "prerelease": False}
        for second_page in ([], [draft]):
            responses = [io.BytesIO(json.dumps(page).encode()) for page in (first_page, second_page)]
            with patch.dict(release.os.environ, {"GH_TOKEN": "test"}), \
                 patch.object(release.urllib.request, "urlopen", side_effect=responses) as lookup:
                if second_page:
                    with self.assertRaisesRegex(ValueError, "already exists"):
                        release.assert_no_release("0.10.0")
                else:
                    self.assertEqual(release.assert_no_release("0.10.0"), first_page)
                self.assertEqual([call.args[0].full_url for call in lookup.call_args_list], [
                    f"https://api.github.com/repos/{release.REPOSITORY}/releases?per_page=100&page={page}"
                    for page in (1, 2)
                ])

    def test_release_listing_errors_never_reach_publication(self):
        with patch.dict(release.os.environ, {"GH_TOKEN": "test"}):
            for status in (403, 404, 500):
                error = urllib.error.HTTPError("url", status, "error", {}, io.BytesIO())
                with error, self.subTest(status=status), \
                     patch("sys.argv", ["release.py", "publish", "0.10.0", self.commit]), \
                     patch.object(release.urllib.request, "urlopen", side_effect=error), \
                     patch.object(release.subprocess, "run") as create:
                    with self.assertRaises(urllib.error.HTTPError):
                        release.main()
                    create.assert_not_called()
            for payload in (b"not json", b"{}", b"[{}]", b'[{"tag_name":"0.9.1","draft":"false","prerelease":false}]'):
                with self.subTest(payload=payload), \
                     patch("sys.argv", ["release.py", "publish", "0.10.0", self.commit]), \
                     patch.object(release.urllib.request, "urlopen", return_value=io.BytesIO(payload)), \
                     patch.object(release.subprocess, "run") as create:
                    with self.assertRaises(ValueError):
                        release.main()
                    create.assert_not_called()

    def test_publish_rechecks_drafts_before_creation(self):
        draft = [{"tag_name": "0.10.0", "draft": True, "prerelease": False}]
        with patch.dict(release.os.environ, {"GH_TOKEN": "test"}), \
             patch("sys.argv", ["release.py", "publish", "0.10.0", self.commit]), \
             patch.object(release.urllib.request, "urlopen", return_value=io.BytesIO(json.dumps(draft).encode())), \
             patch.object(release.subprocess, "run") as create:
            with self.assertRaisesRegex(ValueError, "already exists"):
                release.main()
            create.assert_not_called()

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

    def test_failed_jitpack_build_stops_without_waiting(self):
        not_found = urllib.error.HTTPError("url", 404, "Not Found", {}, io.BytesIO())
        failed = json.dumps({"status": "Error", "commit": self.commit}).encode()
        with not_found, patch.object(release, "git", return_value=b"unused"), \
             patch.object(release, "download", side_effect=[not_found, failed]) as download, \
             patch.object(release.time, "sleep") as sleep:
            with self.assertRaisesRegex(release.JitPackBuildFailed, r"/0\.10\.0/build\.log"):
                release.verify_jitpack("0.10.0", self.commit)
            self.assertEqual(download.call_count, 2)
            sleep.assert_not_called()

    def test_unregistered_jitpack_build_keeps_waiting(self):
        elapsed = [0]

        def advance(seconds):
            elapsed[0] += seconds

        not_found = urllib.error.HTTPError("url", 404, "Not Found", {}, io.BytesIO())
        with not_found, patch.object(release, "git", return_value=b"unused"), \
             patch.object(release, "download", side_effect=not_found) as download, \
             patch.object(release.time, "monotonic", side_effect=lambda: elapsed[0]), \
             patch.object(release.time, "sleep", side_effect=advance), \
             patch("builtins.print"):
            with self.assertRaisesRegex(RuntimeError, "within 12 minutes"):
                release.verify_jitpack("0.10.0", self.commit)
            self.assertEqual(download.call_count, 48)

    def test_moved_tag_never_reaches_release_creation(self):
        with patch("sys.argv", ["release.py", "publish", "0.10.0", "b" * 40]), \
             patch.object(release, "assert_no_release", return_value=[]), \
             patch.object(release, "resolve_tag", return_value=self.commit), \
             patch.object(release.subprocess, "run") as create:
            with self.assertRaises(ValueError):
                release.main()
            create.assert_not_called()

    def test_publish_uses_verified_tag_and_authored_notes_without_editing(self):
        existing = {"tag_name": "0.9.9", "draft": False, "prerelease": False}
        cases = [([], True), ([existing], True), ([dict(existing, tag_name="0.10.1")], False),
                 ([dict(existing, tag_name="1.0.0", draft=True)], True),
                 ([dict(existing, tag_name="1.0.0", prerelease=True)], True),
                 ([dict(existing, tag_name="v99.0.0")], True)]
        for releases, latest in cases:
            with self.subTest(releases=releases), \
                 patch("sys.argv", ["release.py", "publish", "0.10.0", self.commit]), \
                 patch.object(release, "assert_no_release", return_value=releases), \
                 patch.object(release, "resolve_tag", return_value=self.commit), \
                 patch.object(release.subprocess, "run") as create:
                release.main()
                command = create.call_args.args[0]
                self.assertEqual(command[:4], ["gh", "release", "create", "0.10.0"])
                self.assertIn("--verify-tag", command)
                self.assertIn(f"--latest={str(latest).lower()}", command)
                self.assertEqual(command[-2:], ["--notes-file", "releases/0.10.0.md"])


if __name__ == "__main__":
    unittest.main()
