from openai import OpenAI
from dotenv import load_dotenv
import os
import re
from weather_api import get_weather_data

load_dotenv()

weather_agent = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
weather_system = """

You run in a loop of Thought, action ,pause and observation one by one.
At the end of the loop you output an Answer
Use Thought to describe your thoughts about the question you have been asked.
Use Action to run one of the actions available to you - then return PAUSE.
Observation will be the result of running those actions.If you dont have any actions then perform that action by yourself in observation section.
Always go through the step of thought,observation and action even if you dont have tool write action:I dont have tool for this thing so i will do it myself

your available actions are :


get_weather_data:
# e.g. get_weather_data: 52.52, 13.41
# Fetches weather data for the specified latitude and longitude.
# Returns a dictionary containing current temperature, wind speed,
# and hourly weather details (temperature, humidity, wind speed).

# Example session:

# Question: What is the weather in patna in bihar?
# Thought: I need to find the longitude and latitude of patna.The longitude and latiude of patna is  25.5941° N latitude and 85.1356° E longitude.
# Action: get_weather_data: 25.5941,85.1356
# PAUSE 


# You will be called again with this:

# RESULT FROM ACTION: 
{'latitude': 28.625, 'longitude': 77.25, 'temperature': 21.4, 'wind_speed': 10.1}


#Based on the RESULT FROM ACTION do observation

OBSERVATION: Now i have blah blah (just saying, you mention it) set info now i will move ahead for anwer or starting nextchain of though,action and observation until i get the answer

# If you have the answer, output it as the Answer.

# Answer: Here are some of the relevant data about weather in patna
Current Weather:
Temperature: 2.5°C
Wind Speed: 10.7 km/h
Additional Information:
Timezone: GMT
Location Elevation: 38.0 meters above sea level

Reminder:

You will always fetch weather using the tools i have given you.
never answer anything by doing yourself.. the tools are itself capable
of giving you the answer. so wait for json to come otherwise never give answers

if you dont have tool to do something use your own brain like suppose

because you just have one tool 

For example
suppose the user asks the combined weather of italy and brazil
Thought: To find the weather of italy and brazil i need to fetch the temperature of both 
one at a time 

Actions:get_weather_data: 25.5941,85.1356 (of italy)

#you will be called again by user with this 



RESULT FROM ACTION:
{'latitude': 28.625, 'longitude': 77.25, 'temperature': 21.6, 'wind_speed': 10.9}

OBSERVATION: Now i have blah blah (just saying, you mention it) set info now i will move ahead for anwer or starting nextchain of though,action and observation until i get the answer


Thought- Now i have the temperature of italy.. lets go for brazil
Actions:get_weather_data: 25.5941,85.1356
Observation: 
{'latitude': 28.625, 'longitude': 77.25, 'temperature': 21.6, 'wind_speed': 10.9}

RESULT FROM ACTION:
{'latitude': 30.625, 'longitude': 77.25, 'temperature': 28, 'wind_speed': 10.9}




Thought:Now i have the temperature of both...now i need to combine it
Action:I dont have any calculator tool to do it . so i will do it myself in the next part that is observation #NOGIVENTOOLREQUIRED



Observation:- italy has 23 degree temperature and brazil had 25...so the sum would be 28+21.6=49.6
Answer:I finally have the answer the cobined temperature of italy and brazil is 48 degree celsiuis
# Now it's your turn:



"""
history = []
history.append({"role": "system", "content": weather_system})


# print(completion.choices[0].message.content)

class Agent:
    def __init__(self, agent, messages):
        # self.system=system
        self.agent = agent
        self.messages = messages

    def __call__(self, usermessage: str = ""):
        self.messages.append({"role": "user", "content": usermessage})

        completion = weather_agent.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=self.messages
        )

        result = completion.choices[0].message.content
        self.messages.append({"role": "assistant", "content": result})
        return result


def extract_relevant_data(weather_json):
    """
    Extracts longitude, latitude, temperature, and wind speed from the JSON response.
    Args:
        weather_json (dict): The JSON response from the weather API.
    Returns:
        dict: A dictionary with extracted values.
    """
    relevant_data = {
        "latitude": weather_json.get("latitude"),
        "longitude": weather_json.get("longitude"),
        "temperature": weather_json["current"]["temperature_2m"],
        "wind_speed": weather_json["current"]["wind_speed_10m"]
    }
    return relevant_data


def iterate(max_iteration=10, userinput: str = ""):
    agent = Agent(weather_agent, history)
    tools = ["get_weather_data"]
    upcoming_prompt = userinput

    i = 0
    while i < max_iteration:
        i += 1
        result = agent(upcoming_prompt)
        print(result)

        if "PAUSE" in result and "Action" in result:

            match = re.search(r"Action:\s*([a-zA-Z_]+):\s*([\d.\-\s,]+)", result)  
            if match:
                function_name = match.group(1)
                arguments = match.group(2).strip().split(",") 
                arguments = [arg.strip() for arg in arguments]  

                try:
                    arguments = [float(arg) for arg in arguments if arg]  
                except ValueError as e:
                    print(f"Error converting arguments to float: {e}")
                    continue

                if function_name in globals():  
                    func = globals()[function_name]

                    weather_json = func(*arguments)
                    relevant_data = extract_relevant_data(weather_json) 
                    print(f"hey this is the info {relevant_data}")
                    upcoming_prompt = f"RESULT FROM ACTION: {relevant_data}"
                    continue

        if "Answer" in result:
            break

print("-----------Ask to me anything about the Weather ----------")

usermessage = input("User:")

iterate(10, usermessage)
