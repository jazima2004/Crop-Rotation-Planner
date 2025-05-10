import streamlit as st
import pandas as pd
import requests
import os
from datetime import datetime
import matplotlib.pyplot as plt
from dotenv import load_dotenv
load_dotenv()


# Setup
API_KEY = os.getenv("OPENWEATHER_API_KEY")
WEATHER_URL = "http://api.openweathermap.org/data/2.5/weather"
HISTORY_CSV = "crop_history.csv"
FEEDBACK_CSV = "feedback.csv"

if not os.path.exists(HISTORY_CSV):
    pd.DataFrame(columns=["date", "crop", "location", "soil_type"]).to_csv(HISTORY_CSV, index=False)
if not os.path.exists(FEEDBACK_CSV):
    pd.DataFrame(columns=["crop", "suggestion", "rating"]).to_csv(FEEDBACK_CSV, index=False)

ROTATION_RULES = {
    "Wheat": {
        "humid": {"Sandy": ["Legumes", "Millets"], "Clayey": ["Legumes", "Maize"], "Loamy": ["Legumes", "Maize", "Barley"]},
        "dry": {"Sandy": ["Millets", "Sorghum"], "Clayey": ["Legumes"], "Loamy": ["Millets", "Legumes"]},
        "avoid": ["Wheat", "Barley"]
    },
    "Rice": {
        "humid": {"Sandy": ["Legumes"], "Clayey": ["Legumes", "Vegetables"], "Loamy": ["Legumes", "Wheat"]},
        "dry": {"Sandy": ["Millets"], "Clayey": ["Legumes"], "Loamy": ["Legumes"]},
        "avoid": ["Rice"]
    },
    "Maize": {
        "humid": {"Sandy": ["Legumes"], "Clayey": ["Legumes", "Wheat"], "Loamy": ["Legumes", "Vegetables"]},
        "dry": {"Sandy": ["Millets"], "Clayey": ["Sorghum"], "Loamy": ["Millets"]},
        "avoid": ["Maize"]
    },
    "Legumes": {
        "humid": {"Sandy": ["Wheat", "Maize"], "Clayey": ["Rice", "Wheat"], "Loamy": ["Wheat", "Maize"]},
        "dry": {"Sandy": ["Millets"], "Clayey": ["Sorghum"], "Loamy": ["Wheat"]},
        "avoid": ["Legumes"]
    },
    "Millets": {
        "humid": {"Sandy": ["Legumes"], "Clayey": ["Legumes"], "Loamy": ["Legumes", "Wheat"]},
        "dry": {"Sandy": ["Legumes", "Sorghum"], "Clayey": ["Legumes"], "Loamy": ["Legumes"]},
        "avoid": ["Millets"]
    }
}

def get_climate(city="Delhi"):
    try:
        response = requests.get(WEATHER_URL, params={"q": city, "appid": API_KEY, "units": "metric"})
        response.raise_for_status()
        humidity = response.json()["main"]["humidity"]
        return "humid" if humidity > 50 else "dry"
    except:
        return "humid"  # fallback

def add_crop(crop, location, soil_type):
    date = datetime.now().strftime("%Y-%m-%d")
    new_crop = pd.DataFrame([{"date": date, "crop": crop, "location": location, "soil_type": soil_type}])
    new_crop.to_csv(HISTORY_CSV, mode="a", header=False, index=False)

def add_feedback(crop, suggestion, rating):
    new_feedback = pd.DataFrame([{"crop": crop, "suggestion": suggestion, "rating": rating}])
    new_feedback.to_csv(FEEDBACK_CSV, mode="a", header=False, index=False)

def suggest_rotation(crop, location, soil_type):
    df = pd.read_csv(HISTORY_CSV)
    feedback_df = pd.read_csv(FEEDBACK_CSV)
    past_crops = df[df["location"] == location]["crop"].tolist()
    climate = get_climate(location)

    if crop not in ROTATION_RULES:
        return "Crop not supported. Try Wheat, Rice, Maize, Legumes, or Millets."

    options = ROTATION_RULES[crop][climate].get(soil_type, ROTATION_RULES[crop][climate]["Loamy"])
    avoid = ROTATION_RULES[crop]["avoid"]
    feedback_scores = feedback_df[feedback_df["crop"] == crop].groupby("suggestion")["rating"].mean().to_dict()
    valid_options = [opt for opt in options if opt not in past_crops[-2:] and opt not in avoid]
    if feedback_scores:
        valid_options = sorted(valid_options, key=lambda x: feedback_scores.get(x, 0), reverse=True)
    if not valid_options:
        return "No suitable rotation options. Consider resetting history or trying another crop."
    return valid_options

def plot_suggestions(options):
    st.bar_chart(pd.DataFrame({"Crops": options, "Score": [1] * len(options)}).set_index("Crops"))

def plot_history(df):
    if df.empty:
        st.warning("No crop history available.")
    else:
        st.dataframe(df)
        st.line_chart(df["crop"].value_counts())

# UI
st.title("🌾 Crop Rotation Planner")

st.header("1️⃣ Add Current Crop")
crop = st.selectbox("Current Crop", ["Wheat", "Rice", "Maize", "Legumes", "Millets"])
location = st.text_input("Location", "Delhi")
soil = st.selectbox("Soil Type", ["Sandy", "Clayey", "Loamy"])
if st.button("Add Crop"):
    add_crop(crop, location, soil)
    st.success(f"Added {crop} for {location} ({soil} soil)")

st.header("2️⃣ Get Rotation Suggestions")
if st.button("Suggest Rotation"):
    result = suggest_rotation(crop, location, soil)
    if isinstance(result, str):
        st.warning(result)
    else:
        st.success(f"Suggested crops after {crop}: {', '.join(result)}")
        plot_suggestions(result)

        feedback = st.radio("Was the suggestion useful?", ["Yes", "No"])
        if st.button("Submit Feedback"):
            rating = 1 if feedback == "Yes" else 0
            add_feedback(crop, result[0], rating)
            st.info(f"Feedback recorded: {result[0]} rated as {feedback}")

st.header("3️⃣ View Crop History")
if st.button("Show History"):
    df = pd.read_csv(HISTORY_CSV)
    plot_history(df)

st.header("4️⃣ 🌤️ Real-time Climate Info")
city = st.text_input("Enter your city for live climate data", value="Delhi")
if st.button("Check Climate"):
    try:
        response = requests.get(WEATHER_URL, params={"q": city, "appid": API_KEY, "units": "metric"})
        data = response.json()
        humidity = data["main"]["humidity"]
        temperature = data["main"]["temp"]
        climate = "humid" if humidity > 50 else "dry"

        st.success(f"✅ City: {city}")
        st.write(f"🌡️ Temperature: {temperature}°C")
        st.write(f"💧 Humidity: {humidity}%")
        st.write(f"🌱 Climate Category: **{climate.upper()}** (used for crop suggestion)")
    except:
        st.error("Failed to fetch weather data. Check city name or API key.")
