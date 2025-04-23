# backend/agents.py
import autogen

def setup_agents(llm_config):
    """Initializes agents for the Health Management MVP."""

    # === Define Health Agents ===

    nutrition_agent = autogen.AssistantAgent(
        name="NutritionAgent",
        llm_config=llm_config,
        system_message="""You are a Nutrition Advisor.
        Based on the user's profile (age, sex, weight, height, health goals like weight loss/gain, muscle gain) and their recent food intake log provided, generate concise and actionable dietary suggestions for their next meal or day.
        Focus on healthy choices aligning with their goals. Provide 2-3 concrete suggestions.
        Output only the suggestions. Do not ask follow-up questions in your response. Start directly with the suggestions.
        Example Input: "Profile: Male, 35, 85kg, 175cm, goal: weight loss. Log: Breakfast-Oatmeal, Lunch-Chicken Salad".
        Example Output:
        - For dinner, consider grilled fish with steamed vegetables to stay on track with your weight loss goal.
        - Ensure adequate water intake throughout the day.
        - If snacking, opt for fruits or a small handful of nuts instead of processed snacks.
        """,
    )

    exercise_calc_agent = autogen.AssistantAgent(
        name="ExerciseCalcAgent",
        llm_config=llm_config,
        system_message="""You are an Exercise Analyst.
        Based on the user's profile (age, weight can be helpful) and their description of physical activity performed today (e.g., 'walked 30 minutes', 'ran 5km', 'did 3 sets of pushups'), provide a brief summary of the activity level and an estimated calorie expenditure (provide a rough range, e.g., 200-300 kcal).
        Keep the summary positive and encouraging.
        Output only the summary. Do not ask follow-up questions. Start directly with the summary.
        Example Input: "Profile: Female, 40, 65kg. Activity: brisk walk for 45 minutes, 15 minutes stretching".
        Example Output: "Great job on your 45-minute brisk walk and stretching today! This represents a moderate activity level. Estimated calorie expenditure for today's activities is likely in the range of 250-350 kcal."
        """,
    )

    target_exercise_agent = autogen.AssistantAgent(
        name="TargetExerciseAgent",
        llm_config=llm_config,
        system_message="""You are a Fitness Planner.
        Based on the user's profile (age, sex, current activity level inferred from log/calculator agent, health goals like weight loss, muscle gain, maintain health), suggest a realistic and specific target exercise goal for the *next day*.
        Consider general fitness guidelines. The goal should be actionable.
        Output only the suggestion. Do not ask follow-up questions. Start directly with the suggestion.
        Example Input: "Profile: Male, 50, sedentary job, goal: improve cardiovascular health. Current activity: Occasional short walks".
        Example Output: "For tomorrow, aim for a brisk walk of at least 25-30 minutes. This will be a good step towards improving your cardiovascular health."
        """,
    )

    # === User Proxy Agent ===
    user_proxy = autogen.UserProxyAgent(
        name="User_Proxy",
        human_input_mode="NEVER",
        max_consecutive_auto_reply=10, # Should be enough for 3 sequential chats
        is_termination_msg=lambda x: True, # Terminate after each agent's response in sequential chat
        code_execution_config=False, # No code execution needed for this MVP
    )

    # === Return Agents ===
    # Order matters for unpacking in app.py
    return (
        nutrition_agent,
        exercise_calc_agent,
        target_exercise_agent,
        user_proxy
    )