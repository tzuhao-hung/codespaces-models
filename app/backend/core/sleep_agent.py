# core/sleep_agent.py

def build_sleep_prompt(data: dict) -> str:
    """
    Builds a user-friendly prompt for the SleepAgent to analyze wearable sensor data.

    Expected input keys in `data`:
    - heart_rate (HR)
    - hrv (Heart Rate Variability)
    - skin_temperature (TEMP)
    - acceleration_samples (list of 3-axis lists)
    - gsr (Galvanic Skin Response)
    - time_of_night (time)
    """
    # 解析輸入
    hr = data.get("heart_rate", "unknown")
    hrv = data.get("hrv", "unknown")
    temp = data.get("skin_temperature", "unknown")
    acc_samples = data.get("acceleration", []) or data.get("acceleration_samples", [])
    gsr = data.get("gsr", "unknown")
    time_of_night = data.get("time_of_night", "unknown")

    # 把加速度 sample 整理成文字
    if isinstance(acc_samples, list) and len(acc_samples) > 0:
        acc_text = "\n".join([f"  - Sample {i+1}: {sample}" for i, sample in enumerate(acc_samples[:10])])
    else:
        acc_text = "No acceleration data available."

    # 組合 prompt
    prompt = f"""
You are a sleep analysis expert. The following physiological data was recorded during the user's sleep:

- Heart Rate (HR): {hr} bpm
- Heart Rate Variability (HRV): {hrv} ms
- Skin Temperature: {temp} °C
- Galvanic Skin Response (GSR): {gsr} µS
- Time of Night: {time_of_night}
- Acceleration Samples (showing up to 10):
{acc_text}

Each acceleration sample is a 3-axis [X, Y, Z] reading collected during sleep to detect body movements.

Please provide:
1. Estimated sleep stage (Awake, Light, Deep, REM)
2. Sleep quality (Good, Fair, Poor)
3. 2–3 bullet points that explain your reasoning based on the physiological data
4. One friendly suggestion to improve future sleep

Keep it concise and supportive, like a helpful wellness coach.
"""
    return prompt.strip()


def run_sleep_agent(user_input: dict, user_proxy, agent) -> str:
    """
    Executes the sleep analysis by prompting the GPT-based AssistantAgent via UserProxyAgent.

    Parameters:
    - user_input: Dictionary containing sleep-related sensor data
    - user_proxy: AutoGen's UserProxyAgent
    - agent: AutoGen's AssistantAgent (SleepAgent)

    Returns:
    - A string response containing GPT's structured analysis
    """
    prompt = build_sleep_prompt(user_input)

    user_proxy.initiate_chat(
        agent,
        message=prompt,
        max_turns=1,
        clear_history=True
    )

    return user_proxy.last_message(agent).get("content", "No response.")
