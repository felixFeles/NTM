import json
import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
VALIDATOR = REPO_ROOT / "plugins/novel-to-manhwa/scripts/validate_generation_requests.py"
INITIALIZER = REPO_ROOT / "plugins/novel-to-manhwa/scripts/init_project.py"


def test_generation_request_filename_and_chapter_directory_are_enforced(tmp_path):
    requests = tmp_path / "generation/requests"
    request_path = requests / "chapter_001/request_panel_001.json"
    request_path.parent.mkdir(parents=True)
    request_path.write_text(
        json.dumps({"request_id": "request_panel_001", "chapter_id": "chapter_001"}),
        encoding="utf-8",
    )

    valid = subprocess.run(
        [sys.executable, str(VALIDATOR), str(requests)], capture_output=True, text=True, check=False
    )
    assert valid.returncode == 0, valid.stdout

    request_path.rename(request_path.with_name("wrong_name.json"))
    invalid = subprocess.run(
        [sys.executable, str(VALIDATOR), str(requests)], capture_output=True, text=True, check=False
    )
    assert invalid.returncode == 1
    assert "filename must be request_panel_001.json" in invalid.stdout


def test_initializer_installs_generation_request_storage_guidance(tmp_path):
    project = tmp_path / "series"
    result = subprocess.run(
        [sys.executable, str(INITIALIZER), str(project)], capture_output=True, text=True, check=False
    )

    assert result.returncode == 0, result.stdout
    assert (project / "tools/validate_generation_requests.py").is_file()
    guidance = (project / "generation/requests/README.md").read_text(encoding="utf-8")
    assert "<chapter_id>/<request_id>.json" in guidance
