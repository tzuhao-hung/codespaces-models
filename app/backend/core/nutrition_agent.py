# core/nutrition_agent.py

def build_nutrition_prompt(activity_result: str, sleep_result: str, stress_result: str) -> str:
    """
    Builds a strong prompt for NutritionAgent to generate structured personalized meal suggestions
    based on prior agent outputs.
    """

    prompt = f"""
You are a certified nutritionist.

Based on the user's recent physiological condition, please design a personalized meal plan for today:

🏃 Activity Summary:
{activity_result}

😴 Sleep Summary:
{sleep_result}

😟 Stress Summary:
{stress_result}

Tasks:
1. Choose ONE meal time (Breakfast / Lunch / Dinner) to recommend meals for.
2. Provide **TWO to THREE complete meal options**:
    - List 2–4 food items per meal.
    - Add estimated calories per item.
    - Summarize total calories per meal.
3. Tailor suggestions based on the user's activity level, sleep quality, and stress level.
4. At the end, provide **one simple dietary advice for tomorrow**.

Rules:
- **DO NOT repeat** previous activity, sleep, or stress analysis.
- **DO NOT terminate immediately** — finish your meal recommendations and advice first.
- Write clearly, friendly, practical, and encouraging.

Output Format:
- **Meal Time**: (Breakfast / Lunch / Dinner)
- **Menu Option 1**:
  - Food 1 – xx kcal
  - Food 2 – xx kcal
- **Total Calories**: xxx kcal
- **Menu Option 2**:
  - Food 1 – xx kcal
  - Food 2 – xx kcal
- **Total Calories**: xxx kcal
- (Optional) **Menu Option 3**:
  - Food 1 – xx kcal
  - Food 2 – xx kcal
- **Total Calories**: xxx kcal
- **Advice**: (One friendly advice for tomorrow.)

Tone:
- Supportive
- Caring
- Professional
- Easy to follow

Important:
- After finishing your response, you may terminate.
- Until then, please complete all parts as required.
"""
    return prompt.strip()


def run_nutrition_agent(activity_result: str, sleep_result: str, stress_result: str, user_proxy, agent) -> str:
    """
    Executes the NutritionAgent GPT prompt based on the user's recent physiological data.
    """
    prompt = build_nutrition_prompt(activity_result, sleep_result, stress_result)

    user_proxy.initiate_chat(
        agent,
        message=prompt,
        max_turns=1,
        clear_history=True
    )

    return user_proxy.last_message(agent).get("content", "No nutrition suggestion returned.")
