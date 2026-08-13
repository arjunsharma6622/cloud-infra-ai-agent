
# # TEMP: generated files for validation
# from app.config import archi
# from app.tf_validation.workspace import create_workspace, write_files
# from app.tf_validation.runner import terraform_init, terraform_validate
# from app.tf_validation.parser import parse_validation_output
# from app.agents.services.terraform_generator import generate_terraform
# from uuid import uuid4
# from datetime import datetime
# from app.tf_validation.logger import (
#     log_attempt,
#     log_stage,
#     log_success,
#     log_failure,
# )
# from app.tf_validation.logger import ValidationLogger
# from fastapi import APIRouter
# from app.schemas import ArchitecturePlan

# router = APIRouter()

# @router.get("/validation", tags=["Testing/Validation"])
# async def validationRoute():

#     architecture_plan = ArchitecturePlan(
#         architecture_markdown=archi,
#         resources=[]
#     )

#     validation_run_id = (
#         f"{datetime.now():%Y%m%d-%H%M%S}-{uuid4().hex[:6]}"
#     )

#     # -------------------------------------------------------
#     # Initial Terraform Generation
#     # -------------------------------------------------------

#     generation_result = generate_terraform(
#         architecture_plan=architecture_plan,
#     )

#     generated_files = generation_result["generated_code"]

#     # -------------------------------------------------------
#     # Validation Loop
#     # -------------------------------------------------------

#     for attempt in range(5):

#         workspace = create_workspace(
#             validation_run_id,
#             attempt + 1,
#         )

#         validation_logger = ValidationLogger(workspace)

#         log_attempt(
#             validation_run_id,
#             attempt + 1,
#             workspace,
#         )

#         # Save everything that produced THIS attempt
#         validation_logger.save_prompt(
#             generation_result["generation_prompt"]
#         )

#         try:

#             # -------------------------------------------------------
#             # Write Terraform Files
#             # -------------------------------------------------------

#             log_stage("Writing Terraform files")

#             write_files(
#                 workspace,
#                 generated_files,
#             )

#             log_success("Terraform files written.")

#             # -------------------------------------------------------
#             # Terraform Init
#             # -------------------------------------------------------

#             log_stage("terraform init")

#             init_code, init_output = await terraform_init(
#                 workspace
#             )

#             if init_code != 0:

#                 log_failure("terraform init failed.")


#                 validation_logger.save_command_output(
#                     command="terraform_init",
#                     return_code=init_code,
#                     output=init_output,
#                 )

#                 validation_logger.save_summary(
#                     attempt=attempt + 1,
#                     stage="terraform_init",
#                     passed=False,
#                 )

#                 generation_result = generate_terraform(
#                     architecture_plan=architecture_plan,
#                     validation_attempts=attempt + 1,
#                     validation_stage="init",
#                     validation_errors=[
#                         {
#                             "file": "",
#                             "severity": "error",
#                             "summary": "Terraform init failed",
#                             "detail": init_output,
#                         }
#                     ],
#                     previous_code=generated_files,
#                 )

#                 generated_files = generation_result["generated_code"]

#                 continue

#             log_success("terraform init succeeded.")

#             # -------------------------------------------------------
#             # Terraform Validate
#             # -------------------------------------------------------

#             log_stage("terraform validate")

#             validate_code, validate_output = await terraform_validate(
#                 workspace,
#             )

#             passed, diagnostics = parse_validation_output(
#                 validate_output,
#             )

#             if passed and validate_code == 0:

#                 log_success("terraform validate succeeded.")

#                 validation_logger.save_summary(
#                     attempt=attempt + 1,
#                     stage="terraform_validate",
#                     passed=True,
#                 )

#                 return {
#                     "validation_passed": True,
#                     "attempts": attempt + 1,
#                     "generated_code": generated_files,
#                 }

#             log_failure("terraform validate failed.")

#             validation_logger.save_command_output(
#                 command="terraform_validate",
#                 return_code=validate_code,
#                 output=validate_output,
#             )

#             validation_logger.save_validation_json(
#                 diagnostics,
#             )

#             validation_logger.save_summary(
#                 attempt=attempt + 1,
#                 stage="terraform_validate",
#                 passed=False,
#             )

#             generation_result = generate_terraform(
#                 architecture_plan=architecture_plan,
#                 validation_attempts=attempt + 1,
#                 validation_stage="validate",
#                 validation_errors=diagnostics,
#                 previous_code=generated_files,
#             )

#             generated_files = generation_result["generated_code"]

#         finally:
#             print("DONE")
#     # -------------------------------------------------------
#     # Max Retries
#     # -------------------------------------------------------

#     validation_logger.save_summary(
#         attempt=5,
#         stage="max_retries",
#         passed=False,
#     )

#     return {
#         "validation_passed": False,
#         "attempts": 5,
#         "generated_code": generated_files,
#         "validation_errors": (
#             diagnostics
#             if "diagnostics" in locals()
#             else init_output
#         ),
#     }

