def build_sleep_prompt(data: dict) -> str:
    hr = data.get("HR", "unknown")
    hrv = data.get("HRV", "unknown")
    temp = data.get("TEMP", "unknown")
    accel = data.get("ACCELERATION", [])
    gsr = data.get("GSR", "unknown")
    time = data.get("TIME", "unknown")

    return f"""
You are a sleep analysis expert. The following physiological data was recorded during the user's sleep:

- Heart Rate (HR): {hr} bpm
- Heart Rate Variability (HRV): {hrv} ms
- Skin Temperature: {temp} °C
- Acceleration (3-axis): {accel}
- Galvanic Skin Response (GSR): {gsr} µS
- Time of Night: {time}

Please provide:
1. Estimated sleep stage (Awake, Light, Deep, REM)
2. Sleep quality (Good, Fair, Poor)
3. 2–3 bullet points that explain your reasoning based on the physiological data
4. One friendly suggestion to improve future sleep

Keep it concise and supportive, like a helpful wellness coach.
"""

def run_sleep_agent(user_input: dict, user_proxy, agent) -> str:
    prompt = build_sleep_prompt(user_input)

    user_proxy.initiate_chat(
        agent,
        message=prompt,
        max_turns=1,
        clear_history=True
    )

    return user_proxy.last_message(agent).get("content", "No response.")
