def build_abnormal_prompt(activity_result: str, sleep_result: str, stress_result: str) -> str:
    """
    Builds a prompt for AbnormalyDetectionAgent focused on detecting anomalies and severity levels only.

    Inputs:
    - activity_result: output from ActivityAgent
    - sleep_result: output from SleepAgent
    - stress_result: output from StressAgent

    Output:
    - A clear, focused prompt that asks the agent to detect anomalies in structured format.
    """
    return f"""
You are a health anomaly detection assistant. Your job is to review the following results from different health analysis agents and determine if any metrics indicate abnormal conditions.

---
📌 Activity Analysis:
{activity_result}

😴 Sleep Analysis:
{sleep_result}

⚠️ Stress Analysis:
{stress_result}
---

Please respond using the following format:
1. **Anomaly Detection Summary**: Mention whether any metrics are abnormal. Only state what's unusual.
2. **Severity Levels**: Categorize each anomaly as one of: Mild / Warning / Critical.
3. **Detailed Breakdown**:
   - For each detected anomaly, explain why it's abnormal and which metric triggered it.
4. **No Suggestion Needed**: Do not give health advice or future suggestions. Leave that to the HealthSummaryAgent.

Use bullet points and keep it clear and professional.
"""

def run_anomaly_agent(activity_result: str, sleep_result: str, stress_result: str, user_proxy, agent) -> str:
    """
    Executes anomaly analysis by prompting the agent with structured, focused content.
    """
    prompt = build_abnormal_prompt(activity_result, sleep_result, stress_result)

    user_proxy.initiate_chat(
        agent,
        message=prompt,
        max_turns=1,
        clear_history=True
    )

    return user_proxy.last_message(agent).get("content", "No response.")