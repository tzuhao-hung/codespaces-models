# core/stress_agent.py

def build_stress_prompt(data: dict) -> str:
    """
    Generate a prompt to analyze stress level using only HR, TEMP, EDA, ACCEL data.
    """
    hr = data.get("HR")
    temp = data.get("TEMP")
    eda = data.get("EDA")
    accel = data.get("ACCEL")  # Expected to be a 3-axis list

    return f"""
You are a stress monitoring assistant. Based on the following sensor readings, assess the user's current stress level:

- Heart Rate: {hr} bpm
- Skin Temperature: {temp} °C
- Electrodermal Activity (EDA): {eda} µS
- Movement (Acceleration): {accel}

Please provide:
1. Estimated stress level (Low, Medium, High)
2. Short reasoning based on the physiological signals
3. One quick suggestion to help the user reduce stress if needed

Be empathetic, concise, and supportive in your tone.
"""

def run_stress_agent(user_input: dict, user_proxy, agent) -> str:
    """
    Use GPT to analyze stress level from provided physiological input.
    """
    prompt = build_stress_prompt(user_input)

    user_proxy.initiate_chat(
        agent,
        message=prompt,
        max_turns=1,
        clear_history=True
    )

    return user_proxy.last_message(agent).get("content", "No response.")
