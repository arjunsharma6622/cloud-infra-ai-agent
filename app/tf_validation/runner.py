import asyncio
import subprocess
from pathlib import Path

TF_TIMEOUT = 120


def _run_sync(
    command: list[str],
    cwd: Path,
    timeout: int = TF_TIMEOUT,
) -> tuple[int, str]:
    """
    Executes a command synchronously.

    Returns:
        (
            return_code,
            combined_stdout_stderr,
        )
    """

    try:
        result = subprocess.run(
            command,
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=timeout,
        )

        # print("\n" + "=" * 80)
        
        # print(f"Running: {' '.join(command)}")
        # print("RETURN CODE:", result.returncode)

        # if result.stdout:
        #     print("\nSTDOUT:")
        #     print(result.stdout)

        # if result.stderr:
        #     print("\nSTDERR:")
        #     print(result.stderr)

        # print("=" * 80)

        output = result.stdout
        if result.stderr:
            output += result.stderr

        return (
            result.returncode,
            output,
        )

    except subprocess.TimeoutExpired:
        return (
            -1,
            f"Command timed out after {timeout} seconds.",
        )

    except FileNotFoundError:
        return (
            -1,
            "Terraform executable not found. Ensure Terraform is installed and available in PATH.",
        )

    except Exception as e:
        return (
            -1,
            f"Unexpected error: {e}",
        )


async def _run(
    command: list[str],
    cwd: Path,
    timeout: int = TF_TIMEOUT,
) -> tuple[int, str]:
    """
    Executes a command in a background thread so the event loop
    remains responsive.
    """

    return await asyncio.to_thread(
        _run_sync,
        command,
        cwd,
        timeout,
    )


async def terraform_init(
    workspace: Path,
) -> tuple[int, str]:
    """
    Runs:
        terraform init -backend=false -input=false
    """

    return await _run(
        [
            "terraform",
            "init",
            "-backend=false",
            "-input=false",
            "-no-color"
        ],
        workspace,
    )


async def terraform_validate(
    workspace: Path,
) -> tuple[int, str]:
    """
    Runs:
        terraform validate -json
    """

    return await _run(
        [
            "terraform",
            "validate",
            "-json",
            "-no-color"
        ],
        workspace,
    )