# backend/group_summary_chat.py

from autogen import GroupChat, GroupChatManager
from backend.agents import setup_agents

def run_group_health_chat(activity_data, sleep_data, stress_data, llm_config):
    agents = setup_agents(llm_config)

    # 1️⃣ 各 agent 先獨立分析
    activity_result = agents["activity_agent"](activity_data, agents["user_proxy"], agents["activity_llm"])
    sleep_result = agents["sleep_agent"](sleep_data, agents["user_proxy"], agents["sleep_llm"])
    stress_result = agents["stress_agent"](stress_data, agents["user_proxy"], agents["stress_llm"])

    # 2️⃣ 建立 GroupChat 開場訊息，基於前面分析結果
    message = f"""
ActivityAgent: {activity_result}

SleepAgent: {sleep_result}

StressAgent: {stress_result}

HealthSummaryAgent: Please summarize the user's wellness condition in a human-friendly way. Provide one suggestion for tomorrow.

AbnormalyDetectionAgent: Please detect any anomalies based on the above analysis. Rate severity (Mild / Warning / Critical). Do not give suggestions or summary.
"""

    # 3️⃣ 建立群組並設定 summary agent
    group = GroupChat(
        agents=[
            agents["user_proxy"],
            agents["activity_llm"],
            agents["sleep_llm"],
            agents["stress_llm"],
            agents["summary_llm"],
            agents["anomaly_llm"]
        ],
        messages=[]
    )

    print("👥 GroupChat agents:")
    for agent in group.agents:
        print("-", agent.name)

    manager = GroupChatManager(groupchat=group, llm_config=llm_config)

    agents["user_proxy"].initiate_chat(
        manager,
        message=message,
        summary_agent=agents["summary_llm"]
    )

    final_msg = agents["user_proxy"].last_message(agents["summary_llm"])
    print("📤 Final summary message from HealthSummaryAgent:")
    print(final_msg)

    if isinstance(final_msg, dict) and "content" in final_msg:
        return final_msg["content"]
    elif isinstance(final_msg, str):
        return final_msg
    elif final_msg is None:
        return "⚠️ HealthSummaryAgent returned None."
    else:
        return f"⚠️ Unexpected final_msg type: {type(final_msg)}"
