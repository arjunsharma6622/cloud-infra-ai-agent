from pathlib import Path
import shutil
import tempfile

PLAYGROUND_ROOT = Path("playground")


def create_workspace(attempt) -> Path:
    """
    Creates a unique temporary workspace for one validation run.
    """

    PLAYGROUND_ROOT.mkdir(exist_ok=True)

    workspace = Path(
        tempfile.mkdtemp(
            prefix=f"tf-{attempt}-",
            dir=PLAYGROUND_ROOT,
        )
    )

    return workspace


def write_files(
    workspace: Path,
    generated_files: dict[str, str],
) -> None:
    """
    Writes generated Terraform files into the workspace.
    """

    for filename, content in generated_files.items():
        filepath = workspace / filename

        filepath.parent.mkdir(parents=True, exist_ok=True)

        filepath.write_text(
            content,
            encoding="utf-8",
        )


def cleanup_workspace(workspace: Path) -> None:
    """
    Removes the temporary workspace.
    """

    shutil.rmtree(
        workspace,
        ignore_errors=True,
    )
    