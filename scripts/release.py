"""Release gates for the prebuilt Android SDK. Uses only the Python standard library."""

import argparse
import hashlib
import io
import json
import os
from pathlib import Path
import re
import subprocess
import time
import urllib.error
import urllib.request
import xml.etree.ElementTree as ET
import zipfile

REPOSITORY = "REGALITECH/leeep-android-sdk"
GROUP = "com.github.REGALITECH"
ARTIFACT = "leeep-android-sdk"
MAVEN = f"https://jitpack.io/com/github/REGALITECH/{ARTIFACT}"


def validate_tag(tag):
    if not re.fullmatch(r"(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)", tag):
        raise ValueError("Tag must be x.y.z without a prefix, suffix or leading zero")
    return tag


def notes_path(tag):
    validate_tag(tag)
    path = Path("releases") / f"{tag}.md"
    text = path.read_text(encoding="utf-8")
    if not text.startswith(f"# {tag}\n"):
        raise ValueError(f"Release notes must start with '# {tag}'")
    for heading in ("## 変更内容", "## 更新時の対応"):
        if heading not in text:
            raise ValueError(f"Missing release notes section: {heading}")
        section = text.split(heading, 1)[1].split("\n## ", 1)[0].strip()
        if not section or re.search(r"\b(TODO|TBD)\b", section, re.I):
            raise ValueError(f"Write release-specific notes in {heading}")
    return path


def git(*args):
    return subprocess.check_output(["git", *args])


def resolve_tag(tag):
    validate_tag(tag)
    # Fetch the named remote tag, never create or replace a tag locally/remotely.
    git("fetch", "--no-tags", "origin", f"refs/tags/{tag}")
    return git("rev-parse", "FETCH_HEAD^{commit}").decode().strip()


def assert_no_release(tag):
    releases = []
    # The tag endpoint only finds published releases. The publish job repeats
    # this paginated lookup with contents:write so drafts are visible too.
    for page in range(1, 101):
        request = urllib.request.Request(
            f"https://api.github.com/repos/{REPOSITORY}/releases?per_page=100&page={page}",
            headers={"Accept": "application/vnd.github+json", "Authorization": f"Bearer {os.environ['GH_TOKEN']}"},
        )
        with urllib.request.urlopen(request, timeout=30) as response:
            entries = json.load(response)
        if not isinstance(entries, list) or len(entries) > 100:
            raise ValueError("Unexpected GitHub releases response")
        for entry in entries:
            if (not isinstance(entry, dict) or not isinstance(entry.get("tag_name"), str)
                    or not entry["tag_name"] or type(entry.get("draft")) is not bool
                    or type(entry.get("prerelease")) is not bool):
                raise ValueError("Unexpected GitHub release fields")
            if entry["tag_name"] == tag:
                raise ValueError("A release already exists for this tag; it will not be edited")
        releases.extend(entries)
        if len(entries) < 100:
            return releases
    raise ValueError("GitHub release pagination exceeded the safety limit")


def is_latest(tag, releases):
    version = tuple(map(int, validate_tag(tag).split(".")))
    for entry in releases:
        if entry["draft"] or entry["prerelease"]:
            continue
        try:
            existing = tuple(map(int, validate_tag(entry["tag_name"]).split(".")))
        except ValueError:
            continue
        if existing >= version:
            return False
    return True


def download(url, timeout=60):
    with urllib.request.urlopen(url, timeout=timeout) as response:
        return response.read()


def pom_dependencies(pom):
    dependencies = ET.fromstring(pom).findall("{http://maven.apache.org/POM/4.0.0}dependencies")
    if len(dependencies) != 1:
        raise ValueError("POM must contain one dependencies element")

    def normalized(node):
        return (node.tag, (node.text or "").strip(), tuple(sorted(node.attrib.items())),
                tuple(sorted(normalized(child) for child in node)))

    return normalized(dependencies[0])


def validate_distribution(tag, commit, status, pom, aar, metadata, expected_aar, licenses, expected_pom):
    if status.get("status") != "ok" or status.get("commit") != commit:
        raise ValueError("JitPack build must succeed at the resolved tag commit")
    root = ET.fromstring(pom)
    ns = {"m": "http://maven.apache.org/POM/4.0.0"}
    for field, expected in (("groupId", GROUP), ("artifactId", ARTIFACT), ("version", tag), ("packaging", "aar")):
        if root.findtext(f"m:{field}", namespaces=ns) != expected:
            raise ValueError(f"Unexpected published POM {field}")
    if pom_dependencies(pom) != pom_dependencies(expected_pom):
        raise ValueError("Published POM dependencies differ from the resolved tag")
    if tag not in [node.text for node in ET.fromstring(metadata).findall("./versioning/versions/version")]:
        raise ValueError("Version is not discoverable in JitPack Maven metadata yet")
    if hashlib.sha256(aar).digest() != hashlib.sha256(expected_aar).digest():
        raise ValueError("Downloaded AAR differs from the resolved tag")
    with zipfile.ZipFile(io.BytesIO(aar)) as archive:
        if archive.testzip() is not None or not archive.read("classes.jar"):
            raise ValueError("Invalid AAR")
        for name, contents in licenses.items():
            if archive.read(f"assets/leeep/licenses/{name}") != contents:
                raise ValueError(f"AAR license does not match the tag: {name}")


class JitPackBuildFailed(RuntimeError):
    pass


def build_status(body, tag):
    status = json.loads(body)
    # JitPack keeps a failed build and never rebuilds it on later requests, so
    # waiting cannot succeed. Stop with the log URL; the failed build has to be
    # deleted on jitpack.io before retrying (see RELEASING.md).
    if isinstance(status, dict) and status.get("status") == "Error":
        raise JitPackBuildFailed(f"JitPack build failed; see {MAVEN}/{tag}/build.log")
    return status


def verify_jitpack(tag, commit):
    expected_aar = git("show", f"{commit}:LeeepAndroidSdk.aar")
    expected_pom = git("show", f"{commit}:sdk-dependencies.pom")
    licenses = {name: git("show", f"{commit}:{name}") for name in ("LICENSE", "THIRD_PARTY_NOTICES.txt")}
    base = f"{MAVEN}/{tag}/{ARTIFACT}-{tag}"
    status_url = f"https://jitpack.io/api/builds/{GROUP}/{ARTIFACT}/{tag}"
    deadline = time.monotonic() + 12 * 60
    last_error = "JitPack not ready"
    # Requesting the POM can start a JitPack build. Only release preparation or
    # an explicitly requested existing-version check calls this, never PR CI.
    while time.monotonic() < deadline:
        try:
            def fetch(url):
                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    raise TimeoutError("JitPack verification timed out")
                return download(url, timeout=min(60, remaining))

            try:
                pom = fetch(base + ".pom")
            except urllib.error.HTTPError:
                # A failed build answers the POM with 404. Stop if the build has
                # already failed; otherwise keep waiting for it.
                build_status(fetch(status_url), tag)
                raise
            status = build_status(fetch(status_url), tag)
            aar = fetch(base + ".aar")
            metadata = fetch(MAVEN + "/maven-metadata.xml")
            validate_distribution(tag, commit, status, pom, aar, metadata, expected_aar, licenses, expected_pom)
            print(f"Verified {GROUP}:{ARTIFACT}:{tag} at {commit}")
            return
        except (urllib.error.URLError, TimeoutError, ValueError, KeyError, ET.ParseError, zipfile.BadZipFile) as error:
            last_error = str(error)
            print(f"Waiting for JitPack: {last_error}", flush=True)
            time.sleep(max(0, min(30, deadline - time.monotonic())))
    raise RuntimeError(f"JitPack distribution was not verified within 12 minutes: {last_error}")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("prepare", "publish", "verify-jitpack"))
    parser.add_argument("tag")
    parser.add_argument("expected_commit", nargs="?")
    args = parser.parse_args()
    validate_tag(args.tag)
    if args.command != "verify-jitpack":
        notes = notes_path(args.tag)
        releases = assert_no_release(args.tag)
    commit = resolve_tag(args.tag)
    if args.command == "publish":
        if commit != args.expected_commit:
            raise ValueError("Remote tag changed after validation; refusing to publish")
        subprocess.run([
            "gh", "release", "create", args.tag, "--repo", REPOSITORY,
            "--verify-tag", "--title", f"LEEEP Android SDK {args.tag}",
            f"--latest={str(is_latest(args.tag, releases)).lower()}",
            "--notes-file", str(notes),
        ], check=True)
    else:
        verify_jitpack(args.tag, commit)
        if args.command == "prepare":
            if resolve_tag(args.tag) != commit:
                raise ValueError("Remote tag changed during validation")
            with open(os.environ["GITHUB_OUTPUT"], "a", encoding="utf-8") as output:
                output.write(f"tag={args.tag}\ncommit={commit}\n")


if __name__ == "__main__":
    main()
