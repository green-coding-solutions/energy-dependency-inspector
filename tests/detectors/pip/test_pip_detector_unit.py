"""Unit tests for multi-venv pip detection."""

from typing import Optional

from energy_dependency_inspector.detectors.pip_detector import PipDetector


class FakeExecutor:
    """Minimal executor stub for pip detector unit tests."""

    def __init__(self, command_results: dict[str, tuple[str, str, int]], paths: set[str]):
        self.command_results = command_results
        self.paths = paths

    def execute_command(self, command: str, working_dir: Optional[str] = None) -> tuple[str, str, int]:
        return self.command_results.get(command, ("", "", 1))

    def path_exists(self, path: str) -> bool:
        return path in self.paths


def test_pip_multiple_venvs_and_system_result_in_mixed_output() -> None:
    detector = PipDetector()
    executor = FakeExecutor(
        command_results={
            "find '/' -path '*/site-packages/*' -prune -o -path '*/dist-packages/*' -prune -o -name 'pyvenv.cfg' -type f -print 2>/dev/null | LC_COLLATE=C sort -u": (
                "/opt/app1/pyvenv.cfg\n/opt/app2/pyvenv.cfg\n",
                "",
                0,
            ),
            "/opt/app1/bin/pip list --format=freeze": ("requests==2.31.0\n", "", 0),
            "/opt/app1/bin/pip show pip": ("Location: /opt/app1/lib/python3.11/site-packages\n", "", 0),
            "cd '/opt/app1/lib/python3.11/site-packages' && find . -name '__pycache__' -prune -o -name '__editable__*' -prune -o -name 'pip*' -prune -o -name 'setuptools*' -prune -o -name 'pkg_resources' -prune -o -name '*distutils*' -prune -o -path '*/pip/_vendor' -prune -o -not -name '*.pyc' -not -name '*.pyo' -not -name 'INSTALLER' -not -name 'RECORD' \\( -type f -o -type l \\) -printf '%s %p %l\\n' | LC_COLLATE=C sort -n -k1,1 -k2,2": (
                "10 ./requests/__init__.py \n",
                "",
                0,
            ),
            "/opt/app2/bin/pip list --format=freeze": ("click==8.1.7\n", "", 0),
            "/opt/app2/bin/pip show pip": ("Location: /opt/app2/lib/python3.11/site-packages\n", "", 0),
            "cd '/opt/app2/lib/python3.11/site-packages' && find . -name '__pycache__' -prune -o -name '__editable__*' -prune -o -name 'pip*' -prune -o -name 'setuptools*' -prune -o -name 'pkg_resources' -prune -o -name '*distutils*' -prune -o -path '*/pip/_vendor' -prune -o -not -name '*.pyc' -not -name '*.pyo' -not -name 'INSTALLER' -not -name 'RECORD' \\( -type f -o -type l \\) -printf '%s %p %l\\n' | LC_COLLATE=C sort -n -k1,1 -k2,2": (
                "8 ./click/__init__.py \n",
                "",
                0,
            ),
            "unset VIRTUAL_ENV && unset PYTHONPATH && /usr/bin/python3 -m pip list --format=freeze 2>/dev/null || /usr/bin/pip3 list --format=freeze 2>/dev/null || pip list --format=freeze": (
                "pip==24.0\n",
                "",
                0,
            ),
            "unset VIRTUAL_ENV && unset PYTHONPATH && /usr/bin/python3 -m pip show pip 2>/dev/null || /usr/bin/pip3 show pip 2>/dev/null || pip show pip": (
                "Location: /usr/lib/python3/dist-packages\n",
                "",
                0,
            ),
            "cd '/usr/lib/python3/dist-packages' && find . -name '__pycache__' -prune -o -name '__editable__*' -prune -o -name 'pip*' -prune -o -name 'setuptools*' -prune -o -name 'pkg_resources' -prune -o -name '*distutils*' -prune -o -path '*/pip/_vendor' -prune -o -not -name '*.pyc' -not -name '*.pyo' -not -name 'INSTALLER' -not -name 'RECORD' \\( -type f -o -type l \\) -printf '%s %p %l\\n' | LC_COLLATE=C sort -n -k1,1 -k2,2": (
                "6 ./site.py \n",
                "",
                0,
            ),
        },
        paths={
            "/opt/app1/pyvenv.cfg",
            "/opt/app1/bin/pip",
            "/opt/app2/pyvenv.cfg",
            "/opt/app2/bin/pip",
        },
    )

    result = detector.get_dependencies(executor)

    assert result["scope"] == "mixed"
    assert "/opt/app1/lib/python3.11/site-packages" in result["locations"]
    assert "/opt/app2/lib/python3.11/site-packages" in result["locations"]
    assert "/usr/lib/python3/dist-packages" in result["locations"]
