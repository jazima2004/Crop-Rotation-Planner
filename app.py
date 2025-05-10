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
HISTORY_CSV = "crop_history.csv"
FEEDBACK_CSV = "feedback.csv"

if not os.path.exists(HISTORY_CSV):
    pd.DataFrame(columns=["date", "crop", "location", "soil_type", "season"]).to_csv(HISTORY_CSV, index=False)
if not os.path.exists(FEEDBACK_CSV):
    pd.DataFrame(columns=["crop", "suggestion", "rating", "notes"]).to_csv(FEEDBACK_CSV, index=False)

# Farming-themed CSS with white text and fixed scrolling
st.markdown(
    """
    <style>
    .stApp {
        background-image: linear-gradient(rgba(0, 0, 0, 0.3), rgba(0, 0, 0, 0.3)), 
                         url("https://raw.githubusercontent.com/jazima2004/Crop-Rotation-Planner/main/agri1.jpg");
        background-size: cover;
        background-position: center;
        background-repeat: no-repeat;
        background-color: #4CAF50 !important; /* Fallback color */
        overflow-y: auto !important; /* Ensure scrolling is enabled */
        min-height: 100vh; /* Ensure it takes at least full viewport height */
    }
    /* Fallback: Set all text in stApp to white, except specific elements */
    .stApp * {
        color: #FFFFFF !important;
    }
    /* Override for sidebar to keep its text readable (not white) */
    .stSidebar, .stSidebar * {
        color: #000000 !important; /* Black text for sidebar */
    }
    /* Override for buttons to keep their text white (already set by button style) */
    .stButton>button {
        background-color: #4CAF50;
        color: white !important;
        border-radius: 5px;
        border: none;
        padding: 10px;
        width: 100%;
        margin-bottom: 5px;
        font-weight: bold;
    }
    .stButton>button:hover {
        background-color: #45a049;
    }
    .stSidebar {
        background-color: rgba(255, 255, 255, 0.9);
        border-right: 2px solid #4CAF50;
    }
    /* Titles and headers */
    h1, h2, .stMarkdown h1, .stMarkdown h2, .stMarkdown h1 *, .stMarkdown h2 * {
        color: #FFFFFF !important;
        text-shadow: 1px 1px 2px rgba(0,0,0,0.2);
    }
    /* Subtext and general text (e.g., st.write) */
    .stMarkdown p, .stMarkdown div, .stMarkdown p *, .stMarkdown div * {
        color: #FFFFFF !important;
    }
    /* Input labels */
    .stSelectbox label, .stTextInput label, .stTextArea label, .stRadio label,
    .stSelectbox label *, .stTextInput label *, .stTextArea label *, .stRadio label * {
        color: #FFFFFF !important;
    }
    /* Messages (success, info, warning, error) */
    .stSuccess, .stInfo, .stWarning, .stError,
    .stSuccess *, .stInfo *, .stWarning *, .stError * {
        color: #FFFFFF !important;
        background-color: rgba(0, 0, 0, 0.7) !important;
        border-radius: 5px;
        padding: 10px;
    }
    /* Ensure form submit button text remains white */
    .stFormSubmitButton button {
        color: #FFFFFF !important;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# Rotation rules with seasons
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

@st.cache_data
def get_climate(city="Delhi"):
    try:
        response = requests.get(WEATHER_URL, params={"q": city, "appid": API_KEY, "units": "metric"})
        response.raise_for_status()
        data = response.json()
        humidity = data["main"]["humidity"]
        lat = data["coord"]["lat"]
        lon = data["coord"]["lon"]
        return "humid" if humidity > 50 else "dry", lat, lon, humidity, data["main"]["temp"]
    except:
        return "humid", 28.6139, 77.2090, None, None  # Fallback to Delhi coordinates

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
    climate, _, _, _, _ = get_climate(location)

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

# Initialize session state
if "inputs" not in st.session_state:
    st.session_state.inputs = {
        "crop": "Wheat",
        "location": "Delhi",
        "soil": "Sandy",
        "season": "Monsoon"
    }
if "map_data" not in st.session_state:
    st.session_state.map_data = {"city": "Delhi", "climate": "humid", "lat": 28.6139, "lon": 77.2090, "suggestions": None}
if "suggestions" not in st.session_state:
    st.session_state.suggestions = None
if "page" not in st.session_state:
    st.session_state.page = "Add Crop"

# Sidebar buttons
st.sidebar.title("🌾 Crop Rotation Planner")
if st.sidebar.button("Add Crop"):
    st.session_state.page = "Add Crop"
if st.sidebar.button("Get Rotation Suggestions"):
    st.session_state.page = "Get Rotation Suggestions"
if st.sidebar.button("Submit Feedback"):
    st.session_state.page = "Submit Feedback"
if st.sidebar.button("Export Rotation Plan"):
    st.session_state.page = "Export Rotation Plan"
if st.sidebar.button("View Crop History"):
    st.session_state.page = "View Crop History"
if st.sidebar.button("Reset Crop History"):
    st.session_state.page = "Reset Crop History"
if st.sidebar.button("Real-time Climate Info"):
    st.session_state.page = "Real-time Climate Info"
if st.sidebar.button("Location Map"):
    st.session_state.page = "Location Map"

# Main content based on selected page
st.title("Farmer's Crop Rotation Planner")
st.write("Plan sustainable crop rotations with real-time climate data!")

# Shared inputs
def render_inputs():
    with st.form("crop_form"):
        st.session_state.inputs["crop"] = st.selectbox("Current Crop", ["Wheat", "Rice", "Maize", "Legumes", "Millets"], key="crop")
        st.session_state.inputs["location"] = st.text_input("Location", st.session_state.inputs["location"], key="location")
        st.session_state.inputs["soil"] = st.selectbox("Soil Type", ["Sandy", "Clayey", "Loamy"], key="soil")
        st.session_state.inputs["season"] = st.selectbox("Season", ["Monsoon", "Winter", "Summer"], key="season")
        return st.form_submit_button("Submit")

# Page content
if st.session_state.page == "Add Crop":
    st.header("Add Current Crop")
    if render_inputs():
        add_crop(
            st.session_state.inputs["crop"],
            st.session_state.inputs["location"],
            st.session_state.inputs["soil"],
            st.session_state.inputs["season"]
        )
        st.success(f"Added {st.session_state.inputs['crop']} for {st.session_state.inputs['location']} ({st.session_state.inputs['soil']} soil, {st.session_state.inputs['season']})")

elif st.session_state.page == "Get Rotation Suggestions":
    st.header("Get Rotation Suggestions")
    render_inputs()
    if st.button("Suggest Rotation"):
        st.session_state.suggestions = suggest_rotation(
            st.session_state.inputs["crop"],
            st.session_state.inputs["location"],
            st.session_state.inputs["soil"],
            st.session_state.inputs["season"]
        )
        climate, lat, lon, _, _ = get_climate(st.session_state.inputs["location"])
        st.session_state.map_data = {
            "city": st.session_state.inputs["location"],
            "climate": climate,
            "lat": lat,
            "lon": lon,
            "suggestions": st.session_state.suggestions
        }
    if st.session_state.suggestions:
        if isinstance(st.session_state.suggestions, str):
            st.warning(st.session_state.suggestions)
        else:
            st.success(f"Suggested crops after {st.session_state.inputs['crop']}: {', '.join(st.session_state.suggestions)}")
            plot_suggestions(st.session_state.suggestions)
            if st.session_state.map_data["lat"] and st.session_state.map_data["lon"]:
                map_obj = create_map(
                    st.session_state.map_data["city"],
                    st.session_state.map_data["climate"],
                    st.session_state.map_data["lat"],
                    st.session_state.map_data["lon"],
                    st.session_state.map_data["suggestions"]
                )
                if map_obj:
                    st_folium(map_obj, width=700, height=400, key="map", returned_objects=[])

elif st.session_state.page == "Submit Feedback":
    st.header("Submit Feedback")
    if st.session_state.suggestions and isinstance(st.session_state.suggestions, list):
        feedback = st.radio("Was the suggestion useful?", ["Yes", "No"])
        feedback_notes = st.text_area("Feedback Notes", placeholder="e.g., Legumes worked well")
        if st.button("Submit Feedback"):
            rating = 1 if feedback == "Yes" else 0
            add_feedback(st.session_state.inputs["crop"], st.session_state.suggestions[0], rating, feedback_notes)
            st.info(f"Feedback recorded: {st.session_state.suggestions[0]} rated as {feedback}")
    else:
        st.warning("No suggestions available. Please get rotation suggestions first.")

elif st.session_state.page == "Export Rotation Plan":
    st.header("Export Rotation Plan")
    if st.button("Export Plan"):
        if st.session_state.suggestions and isinstance(st.session_state.suggestions, list):
            plan = pd.DataFrame({
                "Current Crop": [st.session_state.inputs["crop"]],
                "Suggested Rotations": [", ".join(st.session_state.suggestions)],
                "Date": [datetime.now().strftime("%Y-%m-%d")]
            })
            plan.to_csv("rotation_plan.csv", index=False)
            with open("rotation_plan.csv", "rb") as file:
                st.download_button("Download Plan", file, "rotation_plan.csv")
            st.success("Rotation plan exported!")
        else:
            st.warning("No suggestions to export. Please get rotation suggestions first.")

elif st.session_state.page == "View Crop History":
    st.header("View Crop History")
    df = pd.read_csv(HISTORY_CSV)
    climate, lat, lon, _, _ = get_climate(st.session_state.inputs["location"])
    st.session_state.map_data = {
        "city": st.session_state.inputs["location"],
        "climate": climate,
        "lat": lat,
        "lon": lon,
        "suggestions": None
    }
    plot_history(df)
    if st.session_state.map_data["lat"] and st.session_state.map_data["lon"]:
        map_obj = create_map(
            st.session_state.map_data["city"],
            st.session_state.map_data["climate"],
            st.session_state.map_data["lat"],
            st.session_state.map_data["lon"],
            st.session_state.map_data["suggestions"]
        )
        if map_obj:
            st_folium(map_obj, width=700, height=400, key="map", returned_objects=[])

elif st.session_state.page == "Reset Crop History":
    st.header("Reset Crop History")
    if st.button("Reset History"):
        pd.DataFrame(columns=["date", "crop", "location", "soil_type", "season"]).to_csv(HISTORY_CSV, index=False)
        st.success("Crop history reset.")

elif st.session_state.page == "Real-time Climate Info":
    st.header("Real-time Climate Info")
    city = st.text_input("Enter your city for live climate data", value=st.session_state.inputs["location"])
    if st.button("Check Climate"):
        climate, lat, lon, humidity, temp = get_climate(city)
        st.session_state.map_data = {
            "city": city,
            "climate": climate,
            "lat": lat,
            "lon": lon,
            "suggestions": None
        }
        if humidity is not None:
            st.success(f"✅ City: {city}")
            st.write(f"🌡️ Temperature: {temp}°C")
            st.write(f"💧 Humidity: {humidity}%")
            st.write(f"🌱 Climate Category: **{climate.upper()}** (used for crop suggestion)")
        else:
            st.error("Failed to fetch weather data. Using default location (Delhi).")
    if st.session_state.map_data["lat"] and st.session_state.map_data["lon"]:
        map_obj = create_map(
            st.session_state.map_data["city"],
            st.session_state.map_data["climate"],
            st.session_state.map_data["lat"],
            st.session_state.map_data["lon"],
            st.session_state.map_data["suggestions"]
        )
        if map_obj:
            st_folium(map_obj, width=700, height=400, key="map", returned_objects=[])

elif st.session_state.page == "Location Map":
    st.header("Location Map")
    if st.session_state.map_data["lat"] and st.session_state.map_data["lon"]:
        map_obj = create_map(
            st.session_state.map_data["city"],
            st.session_state.map_data["climate"],
            st.session_state.map_data["lat"],
            st.session_state.map_data["lon"],
            st.session_state.map_data["suggestions"]
        )
        if map_obj:
            st_folium(map_obj, width=700, height=400, key="map", returned_objects=[])
    else:
        st.warning("No location data available. Please check climate or get suggestions first.")
