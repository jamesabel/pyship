"""
The launcher's self-update against a fake update feed served from a local HTTP server.

The real feed (www.abel.co/updates/<app>) answers GET <url>/versions with JSON and GET
<url>/<app>_<version>.clip with a redirect to a signed S3 URL; here a stdlib server plays
both parts (the redirect included), so the launcher's stdlib-only urllib path is exercised
end to end without the network.
"""

import io
import json
import logging
import shutil
import threading
import zipfile
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

import pytest

from pyship.launcher.launcher import _check_for_update, _compare_versions
from pyship.launcher.metadata import calculate_metadata
from pyship import AppInfo, get_app_info_py_project

APP = "tstupdateapp"


def _clip_bytes(version: str) -> bytes:
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as zf:
        zf.writestr("python.exe", b"not really")
        zf.writestr(f"{APP}_{version}.txt", version)
    return buffer.getvalue()


class _Feed(BaseHTTPRequestHandler):
    versions = ["0.0.1", "0.0.2"]
    clips = {}  # path -> bytes
    fail_versions = False
    hits = []

    def do_GET(self):
        _Feed.hits.append(self.path)
        if self.path == f"/updates/{APP}/versions":
            if _Feed.fail_versions:
                self.send_error(500)
                return
            body = json.dumps({"app": APP, "versions": _Feed.versions, "latest": _Feed.versions[-1]}).encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(body)
        elif self.path.startswith(f"/updates/{APP}/") and self.path.endswith(".clip"):
            # Like the real feed: redirect to the "signed" location.
            self.send_response(302)
            self.send_header("Location", f"http://{self.headers['Host']}/signed{self.path}")
            self.end_headers()
        elif self.path.startswith("/signed/"):
            body = _Feed.clips.get(self.path[len("/signed") :])
            if body is None:
                self.send_error(404)
                return
            self.send_response(200)
            self.send_header("Content-Type", "application/zip")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
        else:
            self.send_error(404)

    def log_message(self, *args):
        pass


@pytest.fixture
def feed():
    server = HTTPServer(("127.0.0.1", 0), _Feed)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    _Feed.versions = ["0.0.1", "0.0.2"]
    _Feed.clips = {f"/updates/{APP}/{APP}_{v}.clip": _clip_bytes(v) for v in _Feed.versions}
    _Feed.fail_versions = False
    _Feed.hits = []
    yield f"http://127.0.0.1:{server.server_port}/updates/{APP}"
    server.shutdown()
    server.server_close()


def _log():
    return logging.getLogger("test_launcher_update")


def test_installs_newer_version(feed, tmp_path):
    user_data_dir = tmp_path / "user_data"
    assert _check_for_update(feed, APP, _compare_versions("0.0.1"), user_data_dir, _log())
    installed = user_data_dir / f"{APP}_0.0.2"
    assert (installed / f"{APP}_0.0.2.txt").read_text() == "0.0.2"
    assert (installed / "python.exe").exists()
    assert not list(user_data_dir.glob("*.clip*")), "the downloaded clip is removed after unpacking"
    assert not list(user_data_dir.glob("*.tmp")), "no unpack scratch dir is left behind"
    assert f"/updates/{APP}/{APP}_0.0.2.clip" in _Feed.hits, "the clip is fetched by its exact key"


def test_up_to_date_does_nothing(feed, tmp_path):
    user_data_dir = tmp_path / "user_data"
    assert not _check_for_update(feed, APP, _compare_versions("0.0.2"), user_data_dir, _log())
    assert not user_data_dir.exists()
    assert _Feed.hits == [f"/updates/{APP}/versions"], "only the listing is fetched"


def test_two_part_versions_compare_numerically(feed, tmp_path):
    # The real bup bucket has 0.11.9 and 0.13 side by side; 0.13 must win over 0.11.9,
    # and 0.13 installed must not be "older" than a padded 0.13.0.
    _Feed.versions = ["0.11.9", "0.13"]
    _Feed.clips[f"/updates/{APP}/{APP}_0.13.clip"] = _clip_bytes("0.13")
    user_data_dir = tmp_path / "user_data"
    assert _check_for_update(feed, APP, _compare_versions("0.11.9"), user_data_dir, _log())
    assert (user_data_dir / f"{APP}_0.13").exists()
    assert not _check_for_update(feed, APP, _compare_versions("0.13"), user_data_dir, _log())


def test_already_staged_is_not_downloaded_again(feed, tmp_path):
    user_data_dir = tmp_path / "user_data"
    (user_data_dir / f"{APP}_0.0.2").mkdir(parents=True)
    assert not _check_for_update(feed, APP, _compare_versions("0.0.1"), user_data_dir, _log())
    assert not any(h.endswith(".clip") for h in _Feed.hits)


def test_feed_failure_is_harmless(feed, tmp_path):
    _Feed.fail_versions = True
    user_data_dir = tmp_path / "user_data"
    assert not _check_for_update(feed, APP, _compare_versions("0.0.1"), user_data_dir, _log())


def test_bad_clip_leaves_nothing_behind(feed, tmp_path):
    _Feed.clips[f"/updates/{APP}/{APP}_0.0.2.clip"] = b"this is not a zip"
    user_data_dir = tmp_path / "user_data"
    assert not _check_for_update(feed, APP, _compare_versions("0.0.1"), user_data_dir, _log())
    assert not (user_data_dir / f"{APP}_0.0.2").exists()
    assert not list(user_data_dir.glob("*.tmp")) and not list(user_data_dir.glob("*.clip*"))


def test_stale_partial_files_are_cleaned_up(feed, tmp_path):
    user_data_dir = tmp_path / "user_data"
    user_data_dir.mkdir()
    (user_data_dir / f"{APP}_0.0.9.clip.part").write_bytes(b"partial")
    (user_data_dir / f"{APP}_0.0.9.tmp").mkdir()
    _check_for_update(feed, APP, _compare_versions("0.0.2"), user_data_dir, _log())
    assert not (user_data_dir / f"{APP}_0.0.9.clip.part").exists()
    assert not (user_data_dir / f"{APP}_0.0.9.tmp").exists()


def test_update_url_flows_from_pyproject_to_metadata(tmp_path):
    (tmp_path / "pyproject.toml").write_text(
        '[project]\nname = "myapp"\nversion = "1.0.0"\n\n[tool.pyship]\nui = "cli"\nupdate_url = "https://www.abel.co/updates/myapp/"\n',
        encoding="utf-8",
    )
    app_info = get_app_info_py_project(AppInfo(), tmp_path)
    assert app_info.update_url == "https://www.abel.co/updates/myapp", "trailing slash is normalised away"

    icon = tmp_path / "icon.ico"
    icon.write_bytes(b"icon")
    launcher_dir = tmp_path / "launcher"
    launcher_dir.mkdir()
    from semver import VersionInfo

    metadata = calculate_metadata("myapp", "abel", VersionInfo.parse("1.0.0"), launcher_dir, icon, "cli", app_info.update_url)
    assert metadata["update_url"] == "https://www.abel.co/updates/myapp"
    without = calculate_metadata("myapp", "abel", VersionInfo.parse("1.0.0"), launcher_dir, icon, "cli")
    assert "update_url" not in without, "apps with no feed carry no key, so the launcher skips the check"
