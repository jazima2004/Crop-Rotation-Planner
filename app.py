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

# Farming-themed CSS with white text, black input/button/dropdown options, and fixed scrolling
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
    /* Override for buttons to have black text */
    .stButton>button {
        background-color: #66BB6A; /* Lighter green for contrast with black text */
        color: #000000 !important;
        border-radius: 5px;
        border: none;
        padding: 10px;
        width: 100%;
        margin-bottom: 5px;
        font-weight: bold;
    }
    .stButton>button:hover {
        background-color: #5DAE61; /* Slightly darker on hover */
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
    /* Text input text (already black) */
    .stTextInput input {
        color: #000000 !important;
        background-color: #FFFFFF !important;
        border: 1px solid #4CAF50 !important;
        border-radius: 5px;
        padding: 5px;
    }
    /* Dropdown (selectbox) text (selected option) */
    .stSelectbox select {
        color: #000000 !important;
        background-color: #FFFFFF !important;
        border: 1px solid #4CAF50 !important;
        border-radius: 5px;
        padding: 5px;
    }
    /* Dropdown options (more specific selector to ensure black text) */
    div.stSelectbox select option,
    [data-baseweb="select"] option {
        color: #000000 !important;
        background-color: #FFFFFF !important;
    }
    /* Add hover effect for dropdown options */
    div.stSelectbox select option:hover,
    [data-baseweb="select"] option:hover {
        background-color: #F0F0F0 !important; /* Light gray on hover */
    }
    /* Messages (success, info, warning, error) */
    .stSuccess, .stInfo, .stWarning, .stError,
    .stSuccess *, .stInfo *, .stWarning *, .stError * {
        color: #FFFFFF !important;
        background-color: rgba(0, 0, 0, 0.7) !important;
        border-radius: 5px;
        padding: 10px;
    }
    /* Form submit button text (already black) */
    .stFormSubmitButton button {
        color: #000000 !important;
        background-color: #66BB6A !important;
        border-radius: 5px;
        border: none;
        padding: 10px;
        font-weight: bold;
    }
    .stFormSubmitButton button:hover {
        background-color: #5DAE61 !important;
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
    fol
