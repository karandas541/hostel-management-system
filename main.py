"""Application entry point; prefer this project's isolated environment."""

from pathlib import Path
import subprocess
import sys


def _relaunch_with_project_environment():
    """Run with the project venv when `python main.py` uses global Python."""
    project_root = Path(__file__).resolve().parent
    environment = project_root / ".venv"
    if sys.platform.startswith("win"):
        project_python = environment / "Scripts" / "python.exe"
    else:
        project_python = environment / "bin" / "python"

    if not project_python.is_file() or Path(sys.prefix).resolve() == environment.resolve():
        return

    result = subprocess.run(
        [str(project_python), str(Path(__file__).resolve()), *sys.argv[1:]],
        cwd=project_root,
        check=False,
    )
    raise SystemExit(result.returncode)


def main():
    _relaunch_with_project_environment()

    import flet as ft
    from app_flet import main as flet_main
    ft.run(flet_main)


if __name__ == "__main__":
    main()
