# backend/agents.py

from autogen import AssistantAgent, UserProxyAgent
from core.activity_agent import run_activity_agent
from core.sleep_agent import run_sleep_agent
from core.health_summary_agent import run_summary_agent
from core.stress_agent import run_stress_agent
from core.abnormaly_agent import run_anomaly_agent
from core.nutrition_agent import run_nutrition_agent

def setup_agents(llm_config):
    """
    Initializes all GPT-powered assistant agents and user proxy agent.
    """

    # GPT Assistant Agents
    activity_agent = AssistantAgent(name="ActivityAgent", llm_config=llm_config)
    sleep_agent = AssistantAgent(name="SleepAgent", llm_config=llm_config)
    stress_agent = AssistantAgent(name="StressAgent", llm_config=llm_config)
    health_summary_agent = AssistantAgent(
        name="HealthSummaryAgent",
        system_message="You summarize health based on activity and sleep insights. Provide 1–2 lines of summary and 1 clear suggestion for tomorrow. Be concise and encouraging.",
        llm_config=llm_config
    )
    abnormaly_detection_agent = AssistantAgent(name="AbnormalyDetectionAgent", llm_config=llm_config)
    nutrition_agent = AssistantAgent(name="NutritionAgent", llm_config=llm_config)

    # User Proxy
    user_proxy = UserProxyAgent(name="UserProxy", human_input_mode="NEVER")

    return {
        # Core agents (functions)
        "activity_agent": run_activity_agent,
        "sleep_agent": run_sleep_agent,
        "stress_agent": run_stress_agent,
        "health_summary_agent": run_summary_agent,
        "abnormaly_detection_agent": run_anomaly_agent,
        "nutrition_agent": run_nutrition_agent,

        # GPT model instances (LLMs)
        "activity_llm": activity_agent,
        "sleep_llm": sleep_agent,
        "stress_llm": stress_agent,
        "health_summary_llm": health_summary_agent,
        "abnormaly_detection_llm": abnormaly_detection_agent,
        "nutrition_llm": nutrition_agent,

        # Shared Proxy
        "user_proxy": user_proxy
    }
