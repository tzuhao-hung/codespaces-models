# core/health_summary_agent.py

def build_summary_prompt(activity_result: str, sleep_result: str, stress_result: str = None, abnormal_result: str = None) -> str:
    """
    Constructs a concise and user-friendly health summary prompt.
    Accepts outputs from other agents.
    """
    prompt = f"""
You are a health summary assistant. The following insights are collected from individual wellness agents:

🏃 Activity Summary:
{activity_result}

😴 Sleep Summary:
{sleep_result}
"""
    if stress_result:
        prompt += f"😟 Stress Summary:\n{stress_result}\n\n"
    if abnormal_result:
        prompt += f"🚨 Anomaly Report:\n{abnormal_result}\n\n"

    prompt += """
Please perform the following tasks:
1. Write a holistic, easy-to-understand summary of the user's current health condition.
2. Highlight any strengths and areas for improvement.
3. Suggest one practical action the user can do tomorrow to enhance their wellness.

Use a warm, motivating, supportive tone. Keep it short and encouraging.

Important:
- After you finish your response, **pass the conversation to AbnormalyDetectionAgent**.
- DO NOT terminate the chat. DO NOT pass to any other agent.
"""
    return prompt.strip()


def run_summary_agent(activity_result: str, sleep_result: str, user_proxy, agent, stress_result: str = None, abnormal_result: str = None) -> str:
    """
    Executes the HealthSummaryAgent GPT prompt to generate an overall health summary.
    """
    prompt = build_summary_prompt(activity_result, sleep_result, stress_result, abnormal_result)

    user_proxy.initiate_chat(
        agent,
        message=prompt,
        max_turns=1,
        clear_history=True
    )

    return user_proxy.last_message(agent).get("content", "No response.")
