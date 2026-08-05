from pathlib import Path
import json
from datetime import datetime

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

class ValidationLogger:
    def __init__(self, workspace: Path):
        self.workspace = workspace
        self.logs_dir = workspace / "logs"
        self.logs_dir.mkdir(exist_ok=True)

    # GENERIC HELPERS

    def _write_text(self, filename: str, content: str):
        (self.logs_dir / filename).write_text(
            content,
            encoding="utf-8",
        )

    def _write_json(self, filename: str, data):
        (self.logs_dir / filename).write_text(
            json.dumps(
                data,
                indent=2,
                ensure_ascii=False,
            ),
            encoding="utf-8"
        )

    # LLM

    def save_prompt(self, prompt: str):
        self._write_text(
            "llm_prompt.md",
            prompt
        )

    def save_llm_response(self, response):
        self._write_json(
            "llm_response.json",
            response
        )

    # TERRAFORM

    def save_command_output(
        self,
        command: str,
        return_code: int,
        output: str,
    ):
        self._write_text(
            f"{command}.log",
            f"""COMMAND      : {command}
RETURN CODE  : {return_code}
TIME         : {datetime.now()}

OUTPUT
============================================================

{output}
""",
        )

    def save_validation_json(
        self, 
        validation_json
    ):
        self._write_json(
            "terraform_validate.json",
            validation_json
        )

    # SUMMARY

    def save_summary(
        self,
        attempt: int,
        stage: str,
        passed: bool
    ):
        status = "SUCCESS" if passed else "FAILED"

        self._write_text(
            "summary.log",

                    f"""
Validation Attempt : {attempt}

Stage              : {stage}

Status             : {status}

Timestamp          : {datetime.now()}
""",
        )

        