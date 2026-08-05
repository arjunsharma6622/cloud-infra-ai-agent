from pathlib import Path


LINE = "=" * 90


def log_attempt(
    run_id: str,
    attempt: int,
    workspace: Path,
):
    print()
    print(LINE)
    print(f"Validation Run : {run_id}")
    print(f"Attempt        : {attempt}")
    print(f"Workspace      : {workspace}")
    print(LINE)


def log_stage(stage: str):
    print(f"\n[{stage}]")


def log_success(message: str):
    print(f"✅ {message}")


def log_failure(message: str):
    print(f"❌ {message}")


def log_output(output: str):
    print("-" * 90)
    print(output)
    print("-" * 90)