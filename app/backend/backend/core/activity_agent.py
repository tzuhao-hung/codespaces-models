# core/activity_agent.py

def build_activity_prompt(data: dict) -> str:
    """
    Builds a user-friendly prompt for the ActivityAgent to analyze wearable sensor data.

    Expected input keys in `data`:
    - acceleration (3-axis list)
    - time (string, e.g., 'morning', 'evening')
    - weight (kg)
    - duration (minutes)
    """
    acc = data.get("acceleration", [])
    time = data.get("time", "unspecified")
    weight = data.get("weight", "unknown")
    duration = data.get("duration", "unknown")

    prompt = f"""
You are a physical activity coach. Based on the user's wearable sensor data below, determine their recent activity level.

Sensor Input:
- Acceleration (3-axis): {acc}
- Time of Day: {time}
- Body Weight: {weight} kg
- Duration: {duration} minutes

Please respond with:
1. Estimated activity type (Sedentary / Walking / Running)
2. Approximate step count
3. Estimated calories burned
4. One short comment on how this activity supports or needs improvement for the user's fitness

Use clear bullet points. Speak like a friendly fitness advisor.
"""
    return prompt


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
