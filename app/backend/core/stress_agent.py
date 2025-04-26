# core/stress_agent.py

def build_stress_prompt(data: dict) -> str:
    """
    Generate a prompt to analyze stress level using HR, TEMP, EDA, and movement data.
    
    Expected input keys:
    - heart_rate
    - skin_temperature
    - eda (Electrodermal Activity)
    - acceleration_samples (list of 3-axis)
    """
    hr = data.get("heart_rate", "unknown")
    temp = data.get("skin_temperature", "unknown")
    eda = data.get("eda", "unknown")
    acc_samples = data.get("acceleration", []) or data.get("acceleration_samples", [])

    # Format acceleration samples
    if isinstance(acc_samples, list) and len(acc_samples) > 0:
        acc_text = "\n".join([f"  - Sample {i+1}: {sample}" for i, sample in enumerate(acc_samples[:10])])
    else:
        acc_text = "No acceleration data available."

    prompt = f"""
You are a stress monitoring assistant. Based on the following wearable sensor readings, assess the user's current stress level:

- Heart Rate: {hr} bpm
- Skin Temperature: {temp} °C
- Electrodermal Activity (EDA): {eda} µS
- Acceleration Samples (showing up to 10):
{acc_text}

Each acceleration sample is a 3-axis [X, Y, Z] vector recorded during the day to monitor movement and restlessness.

Please provide:
1. Estimated stress level (Low, Medium, High)
2. A short reasoning based on the physiological signals
3. One friendly and practical suggestion to help the user reduce stress if needed

Be empathetic, concise, and supportive in your tone.
"""
    return prompt.strip()


def run_stress_agent(user_input: dict, user_proxy, agent) -> str:
    """
    Use GPT to analyze stress level from provided physiological input.

    Parameters:
    - user_input: Dictionary with stress-related data
    - user_proxy: AutoGen's UserProxyAgent
    - agent: AutoGen's AssistantAgent (StressAgent)

    Returns:
    - GPT-generated string with stress analysis
    """
    prompt = build_stress_prompt(user_input)

    user_proxy.initiate_chat(
        agent,
        message=prompt,
        max_turns=1,
        clear_history=True
    )

    return user_proxy.last_message(agent).get("content", "No response.")
