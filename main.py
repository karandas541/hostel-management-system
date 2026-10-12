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

    try:
        import customtkinter as ctk
    except ModuleNotFoundError as error:
        if error.name == "customtkinter":
            raise SystemExit(
                "Project dependencies are missing. Set up the environment with "
                "`.venv\\Scripts\\python.exe -m pip install -r requirements.txt`, "
                "then run `python main.py` again."
            ) from error
        raise

    # CustomTkinter falls back to its coarse circle renderer when Windows
    # cannot load the bundled OTF shapes font. Polygon rendering avoids that
    # fallback's visibly rough edges during resize and scroll repainting.
    if ctk.DrawEngine.preferred_drawing_method == "circle_shapes":
        ctk.DrawEngine.preferred_drawing_method = "polygon_shapes"

    from database import initialize_database
    from views.login import LoginWindow

    initialize_database()
    ctk.set_default_color_theme("blue")

    app = LoginWindow()

    app.mainloop()


if __name__ == "__main__":
    main()
