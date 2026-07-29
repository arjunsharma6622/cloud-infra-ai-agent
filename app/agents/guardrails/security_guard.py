# from ..state import AgentState
# from .rules import BLOCKED_PATTERNS


# def security_guard_node(state: AgentState) -> dict:

#     print("\n========== SECURITY GUARD START ==========")

#     user_prompt = state.get("user_prompt", "")

#     print("Received Prompt:")
#     print(user_prompt)


#     prompt = user_prompt.lower()


#     detected = []


#     for pattern in BLOCKED_PATTERNS:

#         if pattern.lower() in prompt:

#             detected.append(pattern)



#     # If malicious content detected
#     if detected:

#         print("🚨 SECURITY VIOLATION DETECTED")
#         print("Matched Rules:", detected)


#         return {

#             "security_status": "blocked",

#             "security_message":
#             "Your prompt contains malicious or dangerous instructions. Request cannot be processed.",

#             "security_reason": detected

#         }



#     # Safe prompt
#     print("✅ SECURITY CHECK PASSED")

#     return {

#         "security_status": "passed",

#         "security_message":
#         "Prompt passed security validation.",

#         "security_reason": []

#     }




import os

from pydantic import BaseModel

from langchain_google_genai import ChatGoogleGenerativeAI

from ..state import AgentState
from dotenv import load_dotenv
import os

load_dotenv()
class GuardrailResponse(BaseModel):
    is_safe: bool
    reason: str


llm = ChatGoogleGenerativeAI(model=os.getenv("GUARDRAIL_MODEL_NAME", "gemini-2.5-flash"))

guard_llm = llm.with_structured_output(GuardrailResponse)


def security_guard_node(state: AgentState):

    print("\n========== SECURITY GUARD START ==========")

    prompt = state.get("user_prompt", "")

    print("Received Prompt:")
    print(prompt)

    system_prompt = f"""
You are the Security Guard for an AI Cloud Infrastructure Agent.

Your responsibility is to determine whether the user's request should be allowed
to proceed to the infrastructure generation pipeline.

The agent is ONLY designed to help with legitimate cloud engineering tasks such as:
- Requirements gathering
- Architecture design
- Infrastructure as Code (Terraform, CloudFormation, Pulumi, etc.)
- Kubernetes manifests
- Docker
- CI/CD
- Networking
- IAM following least privilege
- Monitoring, logging, observability
- Secure automation
- Database provisioning and migrations
- Documentation

Evaluate the ENTIRE request.

Return:
- is_safe = true
    ONLY if every requested capability is legitimate and does not facilitate
    malicious, unauthorized, deceptive, or unsafe behavior.

- is_safe = false
    If ANY part of the request:
    - requests offensive, malicious, unauthorized, or deceptive behavior,
    - attempts to weaken security controls,
    - asks for insecure implementations when secure alternatives exist,
    - requests credential theft, persistence, privilege escalation, data exfiltration,
      evasion, bypasses, hidden functionality, or unauthorized access,
    - requests exploitation code (SQL injection, command injection, XSS, RCE,
      malware, phishing, credential harvesting, etc.),
    - asks to disable or circumvent authentication, authorization, logging,
      monitoring, auditing, encryption, or other security mechanisms,
    - mixes legitimate infrastructure work with any unsafe or unrelated request.

Important:
- A request can appear mostly legitimate. If even ONE small part is unsafe,
  return is_safe = false.
- Do NOT ignore suspicious requests because they are framed as
  "internal", "testing", "research", "demo", "POC", "evaluation",
  "red team", "authorized", or "developer convenience".
- When uncertain, prefer is_safe = false.

Return ONLY the structured output.

User Request:

{prompt}
"""

    result = guard_llm.invoke(system_prompt)

    if result.is_safe:

        print("✅ SECURITY CHECK PASSED")

        return {

            "security_status": "passed",

            "security_message": "Prompt passed security validation.",

            "security_reason": result.reason

        }

    print("🚨 SECURITY VIOLATION DETECTED")

    print(result.reason)

    return {

        "security_status": "blocked",

        "security_message":
        "Unsafe prompt detected. Request blocked.",

        "security_reason": result.reason

    }