# backend/app.py
import os
import autogen
import traceback
import openai # For OpenAI specific error handling
from dotenv import load_dotenv
from flask import Flask, request, jsonify

# --- Load Environment Variables ---
script_dir = os.path.dirname(os.path.abspath(__file__))
dotenv_path = os.path.join(script_dir, '.env')
print(f"Attempting to load .env from: {dotenv_path}")
if os.path.exists(dotenv_path):
    load_dotenv(dotenv_path=dotenv_path)
    print(".env file loaded successfully from backend directory.")
else:
    print(f".env file not found at {dotenv_path}, attempting load from current/parent dirs.")
    load_dotenv()

# --- Load LLM Configuration ---
AZURE_DEPLOYMENT_NAME = os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME")
AZURE_API_BASE = os.getenv("AZURE_OPENAI_API_BASE")
AZURE_API_KEY = os.getenv("AZURE_OPENAI_API_KEY")
AZURE_API_VERSION = os.getenv("AZURE_OPENAI_API_VERSION", "2024-02-01") # Default or check Azure docs

# --- Critical Configuration Check ---
if not AZURE_DEPLOYMENT_NAME or not AZURE_API_BASE or not AZURE_API_KEY:
    print("ERROR: Critical Azure OpenAI configuration missing.")
    print("Ensure .env file is correct and loaded.")
    print("WARNING: Proceeding without full config. API calls WILL fail.")

config_list = [
    {
        'model': AZURE_DEPLOYMENT_NAME,
        'api_key': AZURE_API_KEY,
        'api_type': 'azure',
        'base_url': AZURE_API_BASE,
        'api_version': AZURE_API_VERSION,
    }
]

llm_config = {
    "config_list": config_list,
    "timeout": 120, # Can likely be shorter now
    "cache_seed": None,
}
print(f"LLM Config loaded. Using Base URL: {AZURE_API_BASE}")

# --- Import Agent Setup ---
try:
    # Use relative import since agents.py is in the same package (backend)
    from .agents import setup_agents
except ImportError as e:
     print(f"ERROR importing agents: {e}.")
     import sys
     sys.exit("Exiting: Failed to import agents setup.")

# --- Flask App ---
app = Flask(__name__)

# --- Simple Alerting Logic ---
def check_for_alerts(user_input_text):
    """Basic keyword check for potential alerts."""
    alerts = []
    text_lower = user_input_text.lower()
    # Add keywords that might indicate an emergency
    alert_keywords = ["chest pain", "difficulty breathing", "severe pain", "sudden weakness", "slurred speech", "fainted", "unconscious", "暈倒", "胸痛", "呼吸困難", "劇痛"]
    for keyword in alert_keywords:
        if keyword in text_lower:
            alerts.append(f"Alert: Input mentioned '{keyword}'. If experiencing a medical emergency, please seek immediate medical attention (e.g., call emergency services).")
            break # Only add one alert for now
    return alerts


@app.route('/get_health_advice', methods=['POST'])
def get_health_advice_route():
    """ Endpoint for Health Agent MVP """
    try:
        data = request.get_json()
        if not data or 'user_input' not in data:
            return jsonify({"error": "Missing 'user_input' in JSON payload"}), 400

        user_input = data['user_input']
        print(f"\n--- Received User Input: ---\n{user_input}\n---------------------------")

        if not user_input.strip():
             return jsonify({"error": "User input cannot be empty"}), 400

        # --- Setup Agents ---
        try:
             nutrition_agent, exercise_calc_agent, target_exercise_agent, user_proxy = setup_agents(llm_config)
             print("--- Health Agents Setup Complete ---")
        except Exception as agent_setup_error:
             print(f"ERROR setting up agents: {agent_setup_error}")
             traceback.print_exc()
             return jsonify({"error": "Internal error: Failed to set up AI agents."}), 500

        # --- Agent Workflow Execution ---
        nutrition_response = "Could not get nutrition advice."
        exercise_calc_response = "Could not calculate exercise."
        target_exercise_response = "Could not determine target exercise."

        try:
            print("\n--- Phase 1: Nutrition Advice ---")
            # Construct a prompt focusing on info needed by NutritionAgent
            nutrition_prompt = f"Generate nutrition advice based on this user information: {user_input}"
            user_proxy.initiate_chat(nutrition_agent, message=nutrition_prompt, max_turns=1, clear_history=True)
            nutrition_response = user_proxy.last_message(nutrition_agent).get("content","Failed to get response.").strip()
            print(f"Nutrition Response:\n{nutrition_response}")

            print("\n--- Phase 2: Exercise Calculation ---")
            # Construct a prompt focusing on info needed by ExerciseCalcAgent
            ex_calc_prompt = f"Calculate exercise summary based on this user information: {user_input}"
            user_proxy.initiate_chat(exercise_calc_agent, message=ex_calc_prompt, max_turns=1, clear_history=True) # Start fresh chat
            exercise_calc_response = user_proxy.last_message(exercise_calc_agent).get("content","Failed to get response.").strip()
            print(f"Exercise Calc Response:\n{exercise_calc_response}")

            print("\n--- Phase 3: Target Exercise ---")
            # Construct a prompt focusing on info needed by TargetExerciseAgent
            target_ex_prompt = f"Suggest a target exercise goal based on this user information: {user_input}"
            user_proxy.initiate_chat(target_exercise_agent, message=target_ex_prompt, max_turns=1, clear_history=True) # Start fresh chat
            target_exercise_response = user_proxy.last_message(target_exercise_agent).get("content","Failed to get response.").strip()
            print(f"Target Exercise Response:\n{target_exercise_response}")

        except Exception as agent_workflow_error:
             print(f"ERROR during agent workflow execution: {agent_workflow_error}")
             traceback.print_exc()
             if isinstance(agent_workflow_error, openai.APIError):
                  raise agent_workflow_error # Re-raise to specific handlers below
             else:
                  # Keep the partial results if any, but indicate an error occurred
                  pass # Allow response synthesis below, it will show failed parts

        # --- Synthesize Responses & Check Alerts ---
        print("\n--- Synthesizing Final Response ---")
        recommendation = f"## Health & Wellness Suggestions\n\n"
        recommendation += f"**Nutrition Advice:**\n{nutrition_response}\n\n"
        recommendation += f"**Today's Activity Summary:**\n{exercise_calc_response}\n\n"
        recommendation += f"**Suggested Goal for Tomorrow:**\n{target_exercise_response}\n\n"
        recommendation += f"---\n*Disclaimer: This is AI-generated advice based on your input. It is not a substitute for professional medical consultation.*"

        alerts = check_for_alerts(user_input)
        print(f"Alerts generated: {alerts}")

        # --- Return JSON Response ---
        return jsonify({"recommendation": recommendation, "alerts": alerts})

    # --- Specific Exception Handling ---
    # (Keep relevant handlers like API errors)
    except openai.APIConnectionError as e:
        print(f"OpenAI API Connection Error: {e}")
        return jsonify({"error": f"Cannot connect to AI service endpoint. Check config/network. Error: {e}"}), 503
    except openai.AuthenticationError as e:
        print(f"OpenAI API Authentication Error: {e}")
        return jsonify({"error": f"AI service authentication failed. Check API key. Error: {e}"}), 401
    except openai.RateLimitError as e:
         print(f"OpenAI API Rate Limit Error: {e}")
         return jsonify({"error": f"AI service rate limit exceeded. Try again later. Error: {e}"}), 429
    except openai.NotFoundError as e:
         print(f"OpenAI API Not Found Error: {e}")
         return jsonify({"error": f"AI service resource not found. Check deployment name? Error: {e}"}), 404
    except openai.BadRequestError as e:
        print(f"OpenAI API Bad Request Error: {e}")
        error_detail = str(e)
        error_msg = f"Invalid request to AI service (check input/content filter?). Error: {error_detail}"
        print(error_msg)
        return jsonify({"error": error_msg}), 400
    except Exception as e: # General fallback
        print(f"Unexpected Error occurred: {e}")
        traceback.print_exc()
        return jsonify({"error": f"An internal server error occurred. Check backend logs."}), 500
    # --- End Exception Handling ---

# --- Main Execution ---
if __name__ == '__main__':
    # Check critical config again before starting
    if not AZURE_DEPLOYMENT_NAME or not AZURE_API_BASE or not AZURE_API_KEY:
         print("\nCRITICAL ERROR: Azure OpenAI Configuration is missing or incomplete.")
         print("The backend server will not start. Please fix your .env file loading and content.\n")
    else:
        print("Starting Flask server for Health Agent Backend...")
        # Ensure host is correct for accessibility from frontend
        app.run(host='0.0.0.0', port=5001, debug=True)