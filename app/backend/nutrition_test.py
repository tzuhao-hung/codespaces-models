# backend/app.py
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
from flask import Flask, request, jsonify
from backend.agents import setup_agents
from backend.group_summary_chat import run_group_health_chat
from core.activity_agent import run_activity_agent
from core.sleep_agent import run_sleep_agent

# Load environment variables
load_dotenv()

# 你的 llm_config
llm_config = {
    "config_list": [{
        "model": os.getenv("OPENAI_API_MODEL", "gpt-4.0-mini"),
        "api_key": os.getenv("OPENAI_API_KEY"),
        "base_url": os.getenv("OPENAI_API_BASE", "https://api.openai.com/v1"),
        "api_type": "openai"
    }],
    "timeout": 60,
    "max_tokens": 500
}

# 1️⃣ Setup agent
agents = setup_agents(llm_config)

# 2️⃣ 模擬 activity, sleep, stress agent的結果
activity_result = "User walked 20 minutes, burned about 100 calories, mostly sedentary."
sleep_result = "Light sleep, fair quality, HR 58 bpm, HRV 72."
stress_result = "Moderate stress detected, HR 90 bpm, elevated EDA 3.5 µS."

# 3️⃣ 單獨呼叫 NutritionAgent
nutrition_response = agents["nutrition_agent"](
    activity_result,
    sleep_result,
    stress_result,
    agents["user_proxy"],
    agents["nutrition_llm"]
)

print("\n📋 NutritionAgent Output:\n")
print(nutrition_response)
