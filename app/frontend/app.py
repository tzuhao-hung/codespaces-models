# frontend/app.py
import streamlit as st
import requests
import traceback
import time

# --- Configuration ---
# Point to the NEW backend endpoint
BACKEND_URL = "http://localhost:5001/get_health_advice"

# --- Streamlit App Layout ---
st.set_page_config(layout="wide")

st.title("🏠 Smart Home Health Advisor (MVP)")
st.markdown("""
Describe your profile, health goals, and today's food/activity below.
The AI agents will provide personalized suggestions.
*(MVP uses text input to simulate data from smart devices)*
""")

# --- Input Area ---
default_input = """Example:
Profile: Female, 45, 70kg, 165cm, Goal: Maintain weight, feel more energetic.
Today's Log:
- Food: Coffee(B), Salad w/ grilled chicken(L), Apple(Snack), Planning pasta for dinner.
- Activity: Walked dog for 20 minutes, felt tired during work.
- Other: Slept about 6 hours last night."""

user_input_text = st.text_area(
    "Your Profile, Goals, and Today's Log:",
    height=250,
    placeholder="Enter details like age, sex, weight, height, goals, food eaten, activity done, sleep, mood etc.",
    value=default_input # Provide a default example
)

# --- Submit Button ---
if st.button("💬 Get Health Advice"):
    if user_input_text and user_input_text != default_input and len(user_input_text) > 20: # Basic check
        # Use columns for better layout during processing
        col1, col2 = st.columns([1, 5])
        with col1:
            st.info("🧠 Thinking...")
        with col2:
            status_text = st.empty()
            progress_bar = st.progress(0)

        try:
            status_text.text("Sending information to AI agents...")
            progress_bar.progress(25)
            start_time = time.time()

            # Prepare JSON payload
            payload = {"user_input": user_input_text}

            # Send POST request with JSON data
            response = requests.post(BACKEND_URL, json=payload, timeout=180) # 3 min timeout

            end_time = time.time()
            status_text.text(f"AI agents responded in {end_time - start_time:.2f} seconds.")
            progress_bar.progress(75)

            response.raise_for_status() # Raise HTTPError for bad responses (4xx or 5xx)

            # --- Handle Response ---
            result_data = response.json()
            recommendation = result_data.get("recommendation", "No recommendation received.")
            alerts = result_data.get("alerts", [])

            st.success("✅ Advice Generated!")
            progress_bar.progress(100)
            status_text.text("Finished.")

            # Display Alerts First (if any)
            if alerts:
                 st.error("🚨 Important Alerts:")
                 for alert in alerts:
                      st.warning(alert) # Use warning style for alerts

            # Display Recommendation
            st.subheader("Personalized Suggestions:")
            st.markdown(recommendation) # Use markdown to render formatting


        except requests.exceptions.Timeout:
             st.error("❌ Timeout Error: The request to the backend timed out.")
             status_text.text("Error: Request timed out.")
             progress_bar.progress(100)
        except requests.exceptions.ConnectionError:
             st.error(f"❌ Connection Error: Could not connect to the backend at {BACKEND_URL.replace('/get_health_advice','')}." )
             st.info("Please ensure the backend server is running.")
             status_text.text("Error: Connection failed.")
             progress_bar.progress(100)
        except requests.exceptions.RequestException as e:
            st.error("❌ Request Error: An error occurred communicating with the backend.")
            error_msg = f"Details: {e}"
            try: # Try to get specific error from backend JSON response
                 error_detail = e.response.json()
                 error_msg += f" | Backend msg: {error_detail.get('error', 'N/A')}"
            except: pass
            st.error(error_msg)
            status_text.text(f"Error: {e}")
            progress_bar.progress(100)
        except Exception as e:
            st.error(f"An unexpected error occurred in the frontend: {e}")
            traceback.print_exc()
            status_text.text("Frontend Error.")
            progress_bar.progress(100)
    else:
         st.warning("Please enter your details in the text area above.")


st.markdown("---")
st.caption("Health Advisor MVP | Powered by AutoGen & Azure OpenAI")