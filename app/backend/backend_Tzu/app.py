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

# Define OpenAI / AutoGen LLM config
llm_config = {
    "config_list": [{
        "model": os.getenv("OPENAI_API_MODEL", "gpt-4o-mini"),
        "api_key": os.getenv("OPENAI_API_KEY"),
        "base_url": os.getenv("OPENAI_API_BASE", "https://api.openai.com/v1"),
        "api_type": "openai"
    }],
    "timeout": 60,
    "max_tokens": 400
}

# Set up Flask app
app = Flask(__name__)

# Setup agents once at launch
agents = setup_agents(llm_config)

@app.route('/analyze_activity', methods=['POST'])
def analyze_activity_route():
    data = request.get_json()
    if not data:
        return jsonify({"error": "Missing JSON payload"}), 400

    try:
        result = agents["activity_agent"](data, agents["user_proxy"], agents["activity_llm"])
        return jsonify({"activity_analysis": result})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/analyze_sleep', methods=['POST'])
def analyze_sleep_route():
    data = request.get_json()
    if not data:
        return jsonify({"error": "Missing JSON payload"}), 400

    try:
        result = agents["sleep_agent"](data, agents["user_proxy"], agents["sleep_llm"])
        return jsonify({"sleep_analysis": result})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/analyze_stress', methods=['POST'])
def analyze_stress_route():
    data = request.get_json()
    if not data:
        return jsonify({"error": "Missing JSON payload"}), 400

    try:
        result = agents["stress_agent"](data, agents["user_proxy"], agents["stress_llm"])
        return jsonify({"stress_analysis": result})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/detect_anomaly', methods=['POST'])
def detect_anomaly_route():
    data = request.get_json()
    if not data:
        return jsonify({"error": "Missing JSON payload"}), 400

    # 確保包含三個結果欄位
    required_keys = ["stress_result", "sleep_result", "activity_result"]
    if not all(k in data for k in required_keys):
        return jsonify({"error": f"Missing one or more required fields: {required_keys}"}), 400

    try:
        result = agents["anomaly_agent"](
            data["stress_result"],
            data["sleep_result"],
            data["activity_result"],
            agents["user_proxy"],
            agents["anomaly_llm"]
        )
        return jsonify({"anomaly_analysis": result})
    except Exception as e:
        return jsonify({"error": str(e)}), 500



@app.route('/group_summary', methods=['POST'])
def group_summary():
    try:
        data = request.get_json()
        summary = run_group_health_chat(
            data["activity_data"],
            data["sleep_data"],
            data["stress_data"],
            llm_config
        )
        return jsonify({"group_health_summary": summary})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# Main server startup
if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5001, debug=True)
