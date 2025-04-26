# backend/group_summary_chat.py

from autogen import GroupChat, GroupChatManager
from backend.agents import setup_agents



def run_group_health_chat(activity_data, sleep_data, stress_data, llm_config):
    agents = setup_agents(llm_config)

    # 1️⃣ 個別分析 activity, sleep, stress
    activity_result = agents["activity_agent"](activity_data, agents["user_proxy"], agents["activity_llm"])
    sleep_result = agents["sleep_agent"](sleep_data, agents["user_proxy"], agents["sleep_llm"])
    stress_result = agents["stress_agent"](stress_data, agents["user_proxy"], agents["stress_llm"])

    # 2️⃣ GroupChat 開場訊息
    opening_message = f"""
You are now in a group chat.

🏃 ActivityAgent Result:
{activity_result}

😴 SleepAgent Result:
{sleep_result}

😟 StressAgent Result:
{stress_result}

🔎 AbnormalyDetectionAgent:
Your ONLY tasks:
1. Carefully review the ActivityAgent, SleepAgent, and StressAgent results.
2. Identify any abnormalities detected based on the data.
3. Write a very short, concise list of the anomalies found (if any).
4. Classify the overall severity: Mild / Warning / Critical.

Strict Rules:
- You MUST ONLY focus on anomaly detection.
- DO NOT generate any nutrition advice.
- DO NOT mention meal suggestions or transition to other topics.
- DO NOT write about NutritionAgent.
- After you finish, STOP and PASS the turn to NutritionAgent automatically.
- DO NOT continue writing beyond your assigned task.

Output Format (strictly follow):
- **Anomaly Detection**: (State "No anomaly detected" OR briefly list the anomalies.)
- **Severity Level**: (Mild / Warning / Critical)

Important:
- After you finish your response, **pass the conversation to NutritionAgent**.
- DO NOT terminate the chat yourself.
- Stay professional and to the point.

🥗 NutritionAgent:
Please carefully analyze the user's condition based on ActivityAgent, SleepAgent, and StressAgent.

Rules:
- DO NOT repeat previous activity, sleep, or stress analysis.
- DO NOT terminate immediately — finish your meal recommendations and advice first.
- **Even if AbnormalyDetectionAgent detects no anomaly, you MUST still complete the full meal recommendation.**
- Include full nutrition facts: calories, protein, fat, and carbohydrates for each food item.
- Add a short friendly note for each food about its benefit.
- Write clearly, friendly, practical, and encouraging.
- After you complete your meal suggestions, clearly send a final termination message to GroupChatManager to end the discussion immediately.


Output Format (Strict):
- Meal Time: (Breakfast / Lunch / Dinner)
- Menu Option 1:
  - Food 1:
    - Calories: xx kcal
    - Protein: xx g
    - Fat: xx g
    - Carbohydrates: xx g
    - Note: (Short benefit description)
  - Food 2:
    - Calories: xx kcal
    - Protein: xx g
    - Fat: xx g
    - Carbohydrates: xx g
    - Note: (Short benefit description)
- Total Calories: xxx kcal
- Menu Option 2: (same structure)
- (Optional) Menu Option 3: (same structure)
- Advice: (One supportive advice for tomorrow.)

Tone:
- Supportive
- Caring
- Professional
- Easy to follow

Important:
- After completing your full structured response, you may terminate.
- Until then, please complete all parts as required.
"""

    # 3️⃣ 建立 GroupChat
    group_chat = GroupChat(
        agents=[
            agents["user_proxy"],
            agents["abnormaly_detection_llm"],
            agents["nutrition_llm"]
        ],
        messages=[],
        speaker_selection_method="auto"  # 正常使用 auto，讓 agent 自己順序流動
    )

    manager = GroupChatManager(
        groupchat=group_chat,
        llm_config=llm_config
    )

    # 4️⃣ 啟動 GroupChat
    agents["user_proxy"].initiate_chat(
        recipient=manager,
        message=opening_message,
        send_termination_message=True  # 讓 NutritionAgent 完成後結束
    )

    messages = manager.groupchat.messages

    abnormaly_detection_result = None
    nutrition_result = None

    for m in messages:
        sender = m.get("name", "")
        content = m.get("content", "")
        
        if not content:
            continue  # 沒內容就跳過

        # 如果是異常偵測 Agent 的訊息
        if sender == "AbnormalyDetectionAgent" and abnormaly_detection_result is None:
            abnormaly_detection_result = content.strip()

        # 如果是營養建議 Agent 的訊息
        if sender == "NutritionAgent" and nutrition_result is None:
            nutrition_result = content.strip()

    # 防止空值
    if abnormaly_detection_result is None:
        abnormaly_detection_result = "No abnormaly detection result."

    if nutrition_result is None:
        nutrition_result = "No nutrition suggestion."




    # 6️⃣ GroupChat結束後，送去 HealthSummaryAgent
    summary_message = f"""
    🏃 Activity Summary:
    {activity_result}

    😴 Sleep Summary:
    {sleep_result}

    😟 Stress Summary:
    {stress_result}

    📋 GroupChat Discussion Completed.

    Now summarize the user's overall health status, and suggest ONE specific improvement for tomorrow.
    - Be friendly and professional.
    - Do NOT repeat previous analysis.
    - Do NOT generate code.
    - Respond like a caring personal health coach.
    - After you complete your reply, you must add a single line TERMINATE at the end. Only after doing so the session will end.
    """

    # 🔥 [重點] 這邊開新的 chat, 但只跑一輪！
    agents["user_proxy"].initiate_chat(
        recipient=agents["health_summary_llm"],
        message=summary_message,
        max_turns=1,  # <<< 加這個！強制只讓 HealthSummaryAgent 回一次
        clear_history=True,  # <<< 不帶舊的訊息
        send_termination_message=True
    )

    # 🔥 這時候就可以直接收訊息了
    health_summary_result = agents["user_proxy"].last_message(agents["health_summary_llm"]).get("content", "No health summary.")

    # 最後 🔥 強制終止 UserProxy 避免死循環
    #agents["user_proxy"].stop_replying()

    # 7️⃣ 收集結果
    results = {
        "activity_result": activity_result,
        "sleep_result": sleep_result,
        "stress_result": stress_result,
        "abnormaly_detection_result": abnormaly_detection_result,
        "nutrition_result": nutrition_result,
        "health_summary_result": health_summary_result
    }

    return results
