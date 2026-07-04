import re
import tomllib
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parents[1]
PINNED_ACTION_REF = re.compile(r"^[^@\s]+@[0-9a-f]{40}$")


def load_workflow(path: Path) -> dict:
    return yaml.load(path.read_text(), Loader=yaml.BaseLoader)


def workflow_uses_refs(workflow: dict) -> list[str]:
    refs = []
    for job in workflow["jobs"].values():
        for step in job.get("steps", []):
            if "uses" in step:
                refs.append(step["uses"])
    return refs


def test_release_workflow_uses_least_privilege_permissions_and_pinned_actions():
    workflow = load_workflow(REPO_ROOT / ".github/workflows/release.yml")

    assert workflow["permissions"] == {}
    assert workflow["jobs"]["build"]["permissions"] == {"contents": "read"}
    assert workflow["jobs"]["publish"]["permissions"] == {
        "actions": "read",
        "id-token": "write",
    }

    refs = workflow_uses_refs(workflow)
    assert refs
    assert all(PINNED_ACTION_REF.fullmatch(ref) for ref in refs)


def test_example_pages_workflow_pins_package_version():
    project = tomllib.loads((REPO_ROOT / "pyproject.toml").read_text())
    expected_package = f"ics-to-static-site-themes=={project['project']['version']}"
    workflow = load_workflow(REPO_ROOT / "examples/deploy-github-pages.yml")

    generate_step = next(
        step
        for step in workflow["jobs"]["build"]["steps"]
        if step.get("name") == "Generate the site"
    )

    assert f"uvx --from {expected_package} " in generate_step["run"]
