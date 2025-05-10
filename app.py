import streamlit as st
import pandas as pd
import requests
import os
from datetime import datetime
import folium
from streamlit_folium import st_folium
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Setup
API_KEY = os.getenv("OPENWEATHER_API_KEY")
WEATHER_URL = "http://api.openweathermap.org/data/2.5/weather"
GEOCODING_URL = "http://api.openweathermap.org/geo/1.0/direct"
HISTORY_CSV = "crop_history.csv"
FEEDBACK_CSV = "feedback.csv"

if not os.path.exists(HISTORY_CSV):
    pd.DataFrame(columns=["date", "crop", "location", "soil_type", "season"]).to_csv(HISTORY_CSV, index=False)
if not os.path.exists(FEEDBACK_CSV):
    pd.DataFrame(columns=["crop", "suggestion", "rating", "notes"]).to_csv(FEEDBACK_CSV, index=False)

# Expanded rotation rules with seasons
ROTATION_RULES = {
    "Wheat": {
        "humid": {
            "Sandy": {"Monsoon": ["Legumes", "Millets"], "Winter": ["Legumes"], "Summer": []},
            "Clayey": {"Monsoon": ["Legumes", "Maize"], "Winter": ["Legumes"], "Summer": []},
            "Loamy": {"Monsoon": ["Legumes", "Maize", "Barley"], "Winter": ["Legumes", "Barley"], "Summer": []}
        },
        "dry": {
            "Sandy": {"Monsoon": ["Millets", "Sorghum"], "Winter": ["Millets"], "Summer": ["Sorghum"]},
            "Clayey": {"Monsoon": ["Legumes"], "Winter": [], "Summer": []},
            "Loamy": {"Monsoon": ["Millets", "Legumes"], "Winter": ["Millets"], "Summer": []}
        },
        "avoid": ["Wheat", "Barley"]
    },
    "Rice": {
        "humid": {
            "Sandy": {"Monsoon": ["Legumes"], "Winter": [], "Summer": []},
            "Clayey": {"Monsoon": ["Legumes", "Vegetables"], "Winter": ["Wheat"], "Summer": []},
            "Loamy": {"Monsoon": ["Legumes", "Wheat"], "Winter": ["Wheat"], "Summer": []}
        },
        "dry": {
            "Sandy": {"Monsoon": ["Millets"], "Winter": [], "Summer": []},
            "Clayey": {"Monsoon": ["Legumes"], "Winter": [], "Summer": []},
            "Loamy": {"Monsoon": ["Legumes"], "Winter": [], "Summer": []}
        },
        "avoid": ["Rice"]
    },
    "Maize": {
        "humid": {
            "Sandy": {"Monsoon": ["Legumes"], "Winter": [], "Summer": []},
            "Clayey": {"Monsoon": ["Legumes", "Wheat"], "Winter": ["Wheat"], "Summer": []},
            "Loamy": {"Monsoon": ["Legumes", "Vegetables"], "Winter": ["Wheat"], "Summer": []}
        },
        "dry": {
            "Sandy": {"Monsoon": ["Millets"], "Winter": [], "Summer": ["Sorghum"]},
            "Clayey": {"Monsoon": ["Sorghum"], "Winter": [], "Summer": []},
            "Loamy": {"Monsoon": ["Millets"], "Winter": [], "Summer": []}
        },
        "avoid": ["Maize"]
    },
    "Legumes": {
        "humid": {
            "Sandy": {"Monsoon": ["Wheat", "Maize"], "Winter": ["Wheat"], "Summer": []},
            "Clayey": {"Monsoon": ["Rice", "Wheat"], "Winter": ["Wheat"], "Summer": []},
            "Loamy": {"Monsoon": ["Wheat", "Maize"], "Winter": ["Wheat"], "Summer": []}
        },
        "dry": {
            "Sandy": {"Monsoon": ["Millets"], "Winter": ["Wheat"], "Summer": []},
            "Clayey": {"Monsoon": ["Sorghum"], "Winter": [], "Summer": []},
            "Loamy": {"Monsoon": ["Wheat"], "Winter": ["Wheat"], "Summer": []}
        },
        "avoid": ["Legumes"]
    },
    "Millets": {
        "humid": {
            "Sandy": {"Monsoon": ["Legumes"], "Winter": [], "Summer": []},
            "Clayey": {"Monsoon": ["Legumes"], "Winter": [], "Summer": []},
            "Loamy": {"Monsoon": ["Legumes", "Wheat"], "Winter": ["Wheat"], "Summer": []}
        },
        "dry": {
            "Sandy": {"Monsoon": ["Legumes", "Sorghum"], "Winter": [], "Summer": ["Sorghum"]},
            "Clayey": {"Monsoon": ["Legumes"], "Winter": [], "Summer": []},
            "Loamy": {"Monsoon": ["Legumes"], "Winter": [], "Summer": []}
        },
        "avoid": ["Millets"]
    }
}

def get_climate(city="Delhi"):
    try:
        response = requests.get(WEATHER_URL, params={"q": city, "appid": API_KEY, "units": "metric"})
        response.raise_for_status()
        data = response.json()
        humidity = data["main"]["humidity"]
        return "humid" if humidity > 50 else "dry", data["coord"]["lat"], data["coord"]["lon"], humidity
    except:
        return "humid", None, None, None  # Fallback

def add_crop(crop, location, soil_type, season):
    date = datetime.now().strftime("%Y-%m-%d")
    new_crop = pd.DataFrame([{"date": date, "crop": crop, "location": location, "soil_type": soil_type, "season": season}])
    new_crop.to_csv(HISTORY_CSV, mode="a", header=False, index=False)

def add_feedback(crop, suggestion, rating, notes):
    new_feedback = pd.DataFrame([{"crop": crop, "suggestion": suggestion, "rating": rating, "notes": notes}])
    new_feedback.to_csv(FEEDBACK_CSV, mode="a", header=False, index=False)

def suggest_rotation(crop, location, soil_type, season):
    df = pd.read_csv(HISTORY_CSV)
    feedback_df = pd.read_csv(FEEDBACK_CSV)
    past_crops = df[df["location"] == location]["crop"].tolist()
    climate, _, _, _ = get_climate(location)

    if crop not in ROTATION_RULES:
        return "Crop not supported. Try Wheat, Rice, Maize, Legumes, or Millets."

    options = ROTATION_RULES[crop][climate].get(soil_type, ROTATION_RULES[crop][climate]["Loamy"]).get(season, [])
    avoid = ROTATION_RULES[crop]["avoid"]
    feedback_scores = feedback_df[feedback_df["crop"] == crop].groupby("suggestion")["rating"].mean().to_dict()
    valid_options = [opt for opt in options if opt not in past_crops[-2:] and opt not in avoid]
    if feedback_scores:
        valid_options = sorted(valid_options, key=lambda x: feedback_scores.get(x, 0), reverse=True)
    if not valid_options:
        return "No suitable rotation options for this season. Try another crop or season."
    return valid_options

def create_map(city, climate, lat, lon, suggestions=None):
    if lat is None or lon is None:
        return None
    m = folium.Map(location=[lat, lon], zoom_start=8)
    color = "blue" if climate == "humid" else "orange"
    popup = f"{city}<br>Climate: {climate}<br>Suggestions: {', '.join(suggestions) if suggestions else 'N/A'}"
    folium.Marker([lat, lon], popup=popup, icon=folium.Icon(color=color)).add_to(m)
    return m

def plot_suggestions(options):
    st.bar_chart(pd.DataFrame({"Crops": options, "Score": [1] * len(options)}).set_index("Crops"))

def plot_history(df):
    if df.empty:
        st.warning("No crop history available.")
    else:
        st.dataframe(df)
        st.line_chart(df["crop"].value_counts())

# UI
st.title("🌾 Farmer's Crop Rotation Planner")
st.write("Plan sustainable crop rotations with real-time climate data!")

# Add crop
st.header("1️⃣ Add Current Crop")
with st.form("crop_form"):
    crop = st.selectbox("Current Crop", ["Wheat", "Rice", "Maize", "Legumes", "Millets"])
    location = st.text_input("Location", "Delhi")
    soil = st.selectbox("Soil Type", ["Sandy", "Clayey", "Loamy"])
    season = st.selectbox("Season", ["Monsoon", "Winter", "Summer"])
    submit = st.form_submit_button("Add Crop")
    if submit:
        add_crop(crop, location, soil, season)
        st.success(f"Added {crop} for {location} ({soil} soil, {season})")

# Get suggestions
st.header("2️⃣ Get Rotation Suggestions")
if st.button("Suggest Rotation"):
    result = suggest_rotation(crop, location, soil, season)
    climate, lat, lon, _ = get_climate(location)
    if isinstance(result, str):
        st.warning(result)
    else:
        st.success(f"Suggested crops after {crop}: {', '.join(result)}")
        plot_suggestions(result)
        map_obj = create_map(location, climate, lat, lon, result)
        if map_obj:
            st_folium(map_obj, width=700, height=400)

        feedback = st.radio("Was the suggestion useful?", ["Yes", "No"])
        feedback_notes = st.text_area("Feedback Notes", placeholder="e.g., Legumes worked well")
        if st.button("Submit Feedback"):
            rating = 1 if feedback == "Yes" else 0
            add_feedback(crop, result[0], rating, feedback_notes)
            st.info(f"Feedback recorded: {result[0]} rated as {feedback}")

# Export plan
st.header("3️⃣ Export Rotation Plan")
if st.button("Export Plan"):
    result = suggest_rotation(crop, location, soil, season)
    if isinstance(result, list):
        plan = pd.DataFrame({
            "Current Crop": [crop],
            "Suggested Rotations": [", ".join(result)],
            "Date": [datetime.now().strftime("%Y-%m-%d")]
        })
        plan.to_csv("rotation_plan.csv", index=False)
        with open("rotation_plan.csv", "rb") as file:
            st.download_button("Download Plan", file, "rotation_plan.csv")
        st.success("Rotation plan exported!")
    else:
        st.warning("No suggestions to export.")

# View history
st.header("4️⃣ View Crop History")
if st.button("Show History"):
    df = pd.read_csv(HISTORY_CSV)
    plot_history(df)
    map_obj = create_map(location, climate, lat, lon)
    if map_obj:
        st_folium(map_obj, width=700, height=400)

# Reset history
st.header("5️⃣ Reset Crop History")
if st.button("Reset History"):
    pd.DataFrame(columns=["date", "crop", "location", "soil_type", "season"]).to_csv(HISTORY_CSV, index=False)
    st.success("Crop history reset.")

# Real-time climate info
st.header("6️⃣ 🌤️ Real-time Climate Info")
city = st.text_input("Enter your city for live climate data", value="Delhi")
if st.button("Check Climate"):
    try:
        response = requests.get(WEATHER_URL, params={"q": city, "appid": API_KEY, "units": "metric"})
        response.raise_for_status()
        data = response.json()
        humidity = data["main"]["humidity"]
        temperature = data["main"]["temp"]
        climate = "humid" if humidity > 50 else "dry"
        lat, lon = data["coord"]["lat"], data["coord"]["lon"]

        st.success(f"✅ City: {city}")
        st.write(f"🌡️ Temperature: {temperature}°C")
        st.write(f"💧 Humidity: {humidity}%")
        st.write(f"🌱 Climate Category: **{climate.upper()}** (used for crop suggestion)")
        map_obj = create_map(city, climate, lat, lon)
        if map_obj:
            st_folium(map_obj, width=700, height=400)
    except:
        st.error("Failed to fetch weather data. Check city name or API key.")
