# core/abnormaly_agent.py

def build_abnormal_prompt(activity_result: str, sleep_result: str, stress_result: str) -> str:
    """
    Builds a strict prompt for AbnormalyDetectionAgent focused ONLY on detecting anomalies and rating severity.
    """

    prompt = f"""
You are a health anomaly detection agent.

Review the following sensor analysis results:
---
🏃 Activity Analysis:
{activity_result}

😴 Sleep Analysis:
{sleep_result}

⚠️ Stress Analysis:
{stress_result}
---

Your ONLY tasks:
1. Identify if there are any abnormal indicators based on the data provided.
2. Classify the overall severity as one of the following levels:
   - Mild
   - Warning
   - Critical

Rules:
- DO NOT give any health advice, suggestions, or wellness summaries.
- DO NOT recommend any future actions.
- ONLY detect and classify anomalies objectively.
- Keep your response extremely concise.

Output Format (strictly follow):
- **Anomaly Detection**: (State "No anomaly detected" OR briefly list any detected anomalies.)
- **Severity Level**: (Mild / Warning / Critical)

Important:
- After you finish your response, **pass the conversation to NutritionAgent**.
- DO NOT terminate the chat yourself.

Stay professional and to the point.
"""
    return prompt.strip()


def run_anomaly_agent(activity_result: str, sleep_result: str, stress_result: str, user_proxy, agent) -> str:
    """
    Executes anomaly analysis by prompting the agent with strictly structured content.
    """
    prompt = build_abnormal_prompt(activity_result, sleep_result, stress_result)

    user_proxy.initiate_chat(
        agent,
        message=prompt,
        max_turns=1,
        clear_history=True
    )

    return user_proxy.last_message(agent).get("content", "No response.")
