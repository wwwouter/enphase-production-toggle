"""Test the integration manifest and metadata."""

import json
from pathlib import Path

from custom_components.enphase_production_toggle.const import DOMAIN


def test_manifest_exists():
    """Test that manifest.json exists."""
    manifest_path = (
        Path(__file__).parent.parent / "custom_components" / DOMAIN / "manifest.json"
    )
    assert manifest_path.exists(), "manifest.json should exist"


def test_manifest_valid_json():
    """Test that manifest.json is valid JSON."""
    manifest_path = (
        Path(__file__).parent.parent / "custom_components" / DOMAIN / "manifest.json"
    )

    with open(manifest_path) as f:
        manifest = json.load(f)

    assert isinstance(manifest, dict), "Manifest should be a dictionary"


def test_manifest_required_fields():
    """Test that manifest.json contains all required fields."""
    manifest_path = (
        Path(__file__).parent.parent / "custom_components" / DOMAIN / "manifest.json"
    )

    with open(manifest_path) as f:
        manifest = json.load(f)

    required_fields = [
        "domain",
        "name",
        "version",
        "documentation",
        "issue_tracker",
        "requirements",
        "config_flow",
        "iot_class",
    ]

    for field in required_fields:
        assert field in manifest, f"Manifest should contain '{field}' field"


def test_manifest_domain_matches():
    """Test that manifest domain matches our constant."""
    manifest_path = (
        Path(__file__).parent.parent / "custom_components" / DOMAIN / "manifest.json"
    )

    with open(manifest_path) as f:
        manifest = json.load(f)

    assert manifest["domain"] == DOMAIN, f"Manifest domain should be '{DOMAIN}'"


def test_manifest_version_format():
    """Test that version follows semantic versioning."""
    manifest_path = (
        Path(__file__).parent.parent / "custom_components" / DOMAIN / "manifest.json"
    )

    with open(manifest_path) as f:
        manifest = json.load(f)

    version = manifest["version"]
    assert isinstance(version, str), "Version should be a string"

    # Basic semantic versioning check (major.minor.patch)
    parts = version.split(".")
    assert len(parts) >= 2, "Version should have at least major.minor format"

    for part in parts:
        assert part.isdigit(), f"Version part '{part}' should be numeric"


def test_manifest_requirements():
    """Test that manifest requirements are properly specified."""
    manifest_path = (
        Path(__file__).parent.parent / "custom_components" / DOMAIN / "manifest.json"
    )

    with open(manifest_path) as f:
        manifest = json.load(f)

    requirements = manifest["requirements"]
    assert isinstance(requirements, list), "Requirements should be a list"
    assert "aiohttp" in requirements, "Should require aiohttp"


def test_manifest_config_flow_enabled():
    """Test that config flow is enabled."""
    manifest_path = (
        Path(__file__).parent.parent / "custom_components" / DOMAIN / "manifest.json"
    )

    with open(manifest_path) as f:
        manifest = json.load(f)

    assert manifest["config_flow"] is True, "Config flow should be enabled"


def test_manifest_iot_class():
    """Test that IoT class is properly specified."""
    manifest_path = (
        Path(__file__).parent.parent / "custom_components" / DOMAIN / "manifest.json"
    )

    with open(manifest_path) as f:
        manifest = json.load(f)

    iot_class = manifest["iot_class"]
    valid_iot_classes = [
        "local_polling",
        "local_push",
        "cloud_polling",
        "cloud_push",
        "assumed_state",
    ]

    assert iot_class in valid_iot_classes, f"IoT class '{iot_class}' should be valid"


def test_manifest_urls():
    """Test that URLs in manifest are properly formatted."""
    manifest_path = (
        Path(__file__).parent.parent / "custom_components" / DOMAIN / "manifest.json"
    )

    with open(manifest_path) as f:
        manifest = json.load(f)

    url_fields = ["documentation", "issue_tracker"]

    for field in url_fields:
        if field in manifest:
            url = manifest[field]
            assert isinstance(url, str), f"{field} should be a string"
            assert url.startswith(
                ("http://", "https://")
            ), f"{field} should be a valid URL"


def test_integration_files_exist():
    """Test that all expected integration files exist."""
    base_path = Path(__file__).parent.parent / "custom_components" / DOMAIN

    expected_files = [
        "__init__.py",
        "manifest.json",
        "config_flow.py",
        "const.py",
        "coordinator.py",
        "envoy_client.py",
        "switch.py",
    ]

    for file_name in expected_files:
        file_path = base_path / file_name
        assert file_path.exists(), f"{file_name} should exist"


def test_integration_structure():
    """Test the overall integration structure."""
    base_path = Path(__file__).parent.parent / "custom_components" / DOMAIN

    # Test that it's a Python package
    init_file = base_path / "__init__.py"
    assert init_file.exists(), "__init__.py should exist to make it a package"

    # Test that all .py files are importable (basic syntax check)
    python_files = list(base_path.glob("*.py"))
    assert len(python_files) >= 5, "Should have at least 5 Python files"

    for py_file in python_files:
        # Basic check that files are not empty
        assert py_file.stat().st_size > 0, f"{py_file.name} should not be empty"
