# backend/agents.py

from autogen import AssistantAgent, UserProxyAgent
from core.activity_agent import run_activity_agent
from core.sleep_agent import run_sleep_agent
from core.health_summary_agent import run_summary_agent
from core.stress_agent import run_stress_agent
from core.abnormaly_agent import run_anomaly_agent

def setup_agents(llm_config):
    """
    Initializes the GPT-based ActivityAgent and UserProxyAgent for analysis.
    """
    
    #GPT powered agents
    activity_agent = AssistantAgent(name="ActivityAgent",llm_config=llm_config)
    
    sleep_agent = AssistantAgent(name="SleepAgent",llm_config=llm_config)

    stress_agent = AssistantAgent(name="StressAgent", llm_config=llm_config)

    anomaly_agent = AssistantAgent(name="AbnormalyDetectionAgent", llm_config=llm_config)


    summary_agent = AssistantAgent(
    name="HealthSummaryAgent",
    system_message="You summarize health based on activity and sleep insights. Provide 1–2 lines of summary and 1 clear suggestion for tomorrow. Be concise and encouraging.",
    llm_config=llm_config
    )
    #UserProxyAgent
    user_proxy = UserProxyAgent(name="UserProxy", human_input_mode="NEVER")

    return {
        # Activity Agent
        "activity_agent": run_activity_agent,
        "activity_llm": activity_agent,
        
        # Sleep Agent
        "sleep_agent": run_sleep_agent,
        "sleep_llm": sleep_agent,
        
        "stress_agent": run_stress_agent,
        "stress_llm": stress_agent,

        "anomaly_agent": run_anomaly_agent,
        "anomaly_llm": anomaly_agent,


        "summary_agent": run_summary_agent,
        "summary_llm": summary_agent,
        # Shared Proxy
        "user_proxy": user_proxy
    }
