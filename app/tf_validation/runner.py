import asyncio
from pathlib import Path

TF_TIMEOUT = 120


async def _run(
    command: list[str],
    cwd: Path,
    timeout: int = TF_TIMEOUT,
) -> tuple[int, str]:
    """
    Executes a command and returns:

    (
        return_code,
        combined_stdout_stderr
    )
    """

    process = await asyncio.create_subprocess_exec(
        *command,
        cwd=cwd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.STDOUT,
    )

    try:
        stdout, _ = await asyncio.wait_for(
            process.communicate(),
            timeout=timeout,
        )

    except asyncio.TimeoutError:
        process.kill()
        await process.wait()

        return (
            -1,
            f"Command timed out after {timeout} seconds.",
        )

    return (
        process.returncode,
        stdout.decode(errors="replace"),
    )


async def terraform_init(
    workspace: Path,
) -> tuple[int, str]:
    """
    Runs:
        terraform init
    """

    return await _run(
        [
            "terraform",
            "init",
            "-backend=false",
            "-input=false",
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
        ],
        workspace,
    )
