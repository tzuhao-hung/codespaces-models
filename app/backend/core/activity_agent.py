# core/activity_agent.py

def build_activity_prompt(data: dict) -> str:
    """
    Builds a user-friendly prompt for the ActivityAgent to analyze wearable sensor data.

    Expected input keys in `data`:
    - acceleration_samples (list of 3-axis lists)
    - time_of_day (string, e.g., 'morning', 'evening')
    - body_weight (kg)
    - duration_minutes (minutes)
    """
    # Parse input
    acc_samples = data.get("acceleration", []) or data.get("acceleration_samples", [])
    time_of_day = data.get("time_of_day", "unspecified")
    weight = data.get("body_weight", "unknown")
    duration = data.get("duration_minutes", "unknown")

    # Format acceleration samples
    if isinstance(acc_samples, list) and len(acc_samples) > 0:
        acc_text = "\n".join([f"  - Sample {i+1}: {sample}" for i, sample in enumerate(acc_samples[:10])])
    else:
        acc_text = "No acceleration data available."

    # Build upgraded prompt
    prompt = f"""
You are a professional physical activity coach. Based on the user's wearable sensor data below, directly determine their recent activity level.

Sensor Input:
- Time of Day: {time_of_day}
- Body Weight: {weight} kg
- Duration: {duration} minutes
- Acceleration Samples (showing up to 10):
{acc_text}

Each acceleration sample is a 3-axis [X, Y, Z] reading in g-force units, collected at regular intervals.

Please respond clearly and directly with:
1. **Estimated Activity Type**: (Sedentary / Walking / Running)
2. **Approximate Step Count**: (Give a reasonable number)
3. **Estimated Calories Burned**: (in kcal)
4. **Fitness Comment**: (One short friendly comment encouraging healthy habits.)

Rules:
- **DO NOT** describe your analysis process or calculations.
- **DO NOT** write Python code.
- **JUST** provide final results based on standard assumptions (e.g., MET values for typical activities).
- Keep your response **concise, friendly, and professional**, as if you are advising a real client.

Tone:
- Friendly
- Professional
- Easy to understand
- Supportive
"""
    return prompt.strip()


def run_activity_agent(user_input: dict, user_proxy, agent) -> str:
    """
    Executes the activity analysis by prompting the GPT-based AssistantAgent via UserProxyAgent.

    Parameters:
    - user_input: Dictionary containing activity-related sensor data
    - user_proxy: AutoGen's UserProxyAgent
    - agent: AutoGen's AssistantAgent (ActivityAgent)

    Returns:
    - A string response containing GPT's structured analysis
    """
    prompt = build_activity_prompt(user_input)

    user_proxy.initiate_chat(
        agent,
        message=prompt,
        max_turns=1,
        clear_history=True
    )

    return user_proxy.last_message(agent).get("content", "No response.")
