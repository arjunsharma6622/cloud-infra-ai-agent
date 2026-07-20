from ..state import AgentState
from .rules import BLOCKED_PATTERNS


def security_guard_node(state: AgentState) -> dict:

    print("\n========== SECURITY GUARD START ==========")

    user_prompt = state.get("user_prompt", "")

    print("Received Prompt:")
    print(user_prompt)


    prompt = user_prompt.lower()


    detected = []


    for pattern in BLOCKED_PATTERNS:

        if pattern.lower() in prompt:

            detected.append(pattern)



    # If malicious content detected
    if detected:

        print("🚨 SECURITY VIOLATION DETECTED")
        print("Matched Rules:", detected)


        return {

            "security_status": "blocked",

            "security_message":
            "⚠️ Your prompt contains malicious or dangerous instructions. Request cannot be processed.",

            "security_reason": detected

        }



    # Safe prompt
    print("✅ SECURITY CHECK PASSED")

    return {

        "security_status": "passed",

        "security_message":
        "Prompt passed security validation.",

        "security_reason": []

    }