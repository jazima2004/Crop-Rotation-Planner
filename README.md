# Crop-Rotation-Planner
applinlk: https://crop-rotation-planner-xmm6qk6o9vsocqdbgddpq8.streamlit.app/

Here’s the summary with subheadings for better clarity:

---

### **Farmer's Crop Rotation Planner**

###**About**
This web application assists farmers in planning sustainable crop rotations by leveraging real-time weather data and predefined crop rotation rules. It helps optimize crop productivity while promoting soil health by suggesting suitable crops based on current conditions.

---

### **Key Features**

1. **Crop Rotation Suggestions**

   * Provides crop rotation options based on **climate**, **soil type**, and **season**.
   * Suggests crops that avoid potential pests and diseases by analyzing past crop history.

2. **Real-time Climate Data**

   * Integrates with the **OpenWeatherMap API** to fetch **temperature** and **humidity** data.
   * Uses this data to determine whether the climate is **humid** or **dry**, which impacts crop rotation suggestions.

3. **Location Map**

   * Displays farm location on an interactive map using **Folium**.
   * Visualizes weather conditions and suggested crops for the selected location.

4. **Feedback System**

   * Allows farmers to **rate crop suggestions** (useful or not) and provide feedback.
   * Feedback is stored to improve future crop rotation suggestions.

5. **Export Rotation Plan**

   * Provides an option to **download the crop rotation plan** in **CSV format** for offline use.
   * The plan includes details like current crop, suggested rotations, and date.

6. **Crop History Tracking**

   * Keeps a record of past crop planting decisions, soil types, and seasons.
   * Helps in making data-driven decisions for future planting cycles.

---

### **Technologies Used**

* **Streamlit**: For building the interactive web interface.
* **Folium**: For creating interactive maps to visualize locations.
* **Pandas**: For data handling and storing crop history.
* **OpenWeatherMap API**: To fetch real-time climate data for location-based suggestions.
* **Python**: For backend processing and logic implementation.

---

### **Benefits for Farmers**

* **Informed Decision-Making**: Uses historical and real-time data to make optimal crop rotation suggestions.
* **Sustainability**: Helps in maintaining soil health by recommending appropriate crops.
* **Convenience**: Offers an easy-to-use interface for managing crop data and receiving suggestions.
* **Improved Productivity**: Maximizes yields by recommending the most suitable crops based on climate and soil conditions.

---










