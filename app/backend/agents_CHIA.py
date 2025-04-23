import os
import json
import random
import asyncio
from openai import OpenAI
from autogen.agentchat import register_function
from autogen_agentchat.agents import AssistantAgent
from autogen_agentchat.conditions import TextMentionTermination
from autogen_agentchat.messages import StructuredMessage, TextMessage
from autogen_agentchat.teams import MagenticOneGroupChat
from autogen_agentchat.ui import Console
from autogen_core import CancellationToken
from autogen_core.memory import ListMemory, MemoryContent, MemoryMimeType
from autogen_core.models import SystemMessage, UserMessage
from autogen_core.tools import FunctionTool
from autogen_ext.models.openai import AzureOpenAIChatCompletionClient, OpenAIChatCompletionClient
from pydantic import BaseModel


with open("profile.json", "r") as file:
    profiles = json.load(file)
    random_index = random.randint(0, len(profiles) - 1)
    random_profile = profiles[random_index]

client = OpenAIChatCompletionClient(
    model="gpt-4o", 
    api_key=os.environ["GITHUB_TOKEN"], 
    base_url="https://models.inference.ai.azure.com"
)

sys_messages = """
    You are a professional nutritional manager.  
    1. Recommend a nutritionally balanced meal tailored to the user's age, gender, height, weight, activity level, disease history, dietary record and sleep condition.
    2. Provide three meal options formatted as a JSON menu, clearly listing the food items, calorie count for each item, and the total calorie count for the meal options. Exclude additional descriptors such as "choice" or "option" in the meal names. Ensure the structure is clear and accurate.  
    3. Base the menu recommendations on the time specified by the user. If no time is provided, default to the current time. Ensure the recommendations align with appropriate food choices for that time of day. If it is not a suitable time for eating, notify the user and offer guidance.  
    4. For users with chronic diseases, cancer, or other medical conditions, ensure the menu accounts for their specific dietary needs by recommending foods that support their condition and avoiding any that may exacerbate it.  
    5. Provide additional dietary advice, such as portion control, nutrition_considerations that enhance nutrient absorption.
    6. If the user requests to change the menu, avoid recommending any options that were previously provided and stored in memory.
    7. If possible, identify nearby restaurants serving meals similar to the recommended menus based on the user’s location and provide the name and details of the closest restaurant.  
    8. Always return True to new_menu.

    The following JSON data is user's profile:
    {profile}
""".format(profile=json.dumps(random_profile))

response = None

class FoodItem(BaseModel):
    food: str
    calories: int
class MealOption(BaseModel):
    menu_name: str
    item: list[FoodItem]
    total_calories: int
class NutritionConsiderations(BaseModel):
    calorie_target: int
    sodium_limit: str
    fiber_goal: str
    protein_focus: str
    note: str
class MealRecommender(BaseModel):
    meal_time: str
    meal_options: list[MealOption]
    nutrition_considerations: NutritionConsiderations
    dietary_advice: str
    new_menu: bool


async def get_dietary_data(query: str) -> str:
    """Get User dietary data."""
    return "Average daily intake of 1300 calories in the past week."
async def get_sleep_data(query: str) -> str:
    """Get User sleep data."""
    return "Average 7 hours of sleep per day in the past week."


async def save_recommendation_to_memory(meal_options):
    """Save recommendation to memory."""
    for meal_option in meal_options:
        await user_memory.add(MemoryContent(content=meal_option, mime_type=MemoryMimeType.TEXT))

dietary_tool = FunctionTool(
    get_dietary_data,
    description="Get dietary condition.",
    strict=True
)
sleep_tool = FunctionTool(
    get_sleep_data,
    description="Get sleep condition.",
    strict=True
)

user_memory = ListMemory()
meal_recommender_agent = AssistantAgent(
    name="MealRecommender",
    description="A helpful assistant that can manage diet.",
    system_message=sys_messages,
    output_content_type = MealRecommender,
    tools=[dietary_tool, sleep_tool],
    memory=[user_memory],
    model_client=client  
)



async def run_agents():
    print("Welcome to the Meal Recommender Chat!")
    print("Type your message below. Type 'exit' to quit.\n")

    global response
    while True:
        # 收集使用者輸入
        user_input = input("You: ")
        if user_input.lower() == "exit":
            print("Exiting chat. Goodbye!")
            break
        response = await meal_recommender_agent.on_messages(
            [TextMessage(content="Please recommend a meal plan.", source="user")],
            cancellation_token=CancellationToken(),
        )
        print(response.chat_message.content)

        meal_options = (json.loads((response.chat_message.content).json())).get("meal_options")
        for meal_option in meal_options:
            await user_memory.add(MemoryContent(content=meal_option, mime_type=MemoryMimeType.TEXT))
        print("Recommendation saved to memory.")
        print(user_memory.content)

        # await Console(
        #     meal_recommender_agent.on_messages_stream(
        #         [TextMessage(content="Please recommend a meal plan.", source="user")],
        #         cancellation_token=CancellationToken(),
        #     ),
        #     output_stats=True,
        # )

asyncio.run(run_agents())