import streamlit as st
from datetime import datetime
import random
from PIL import Image
try:
    from streamlit_geolocation import streamlit_geolocation
except ImportError:
    streamlit_geolocation = None
from services.weather import get_weather
from services.plant_health import analyze_plant
from engine.conflict_engine import resolve_conflict
from services.database import (
    initialize_database,
    save_decision,
    get_all_decisions,
    clear_all_decisions
)
from services.auth import (
    initialize_users,
    create_user,
    login_user
)
# -------------------- SENSOR CALIBRATION --------------------

SENSOR_PROFILES = {
    "SM-001": {
        "sensor": "Soil Moisture",
        "accuracy": 92,
        "reference": 30,
        "offset": 3,
    }
}


def calibrate_soil_moisture(raw_value, module_id="SM-001"):
    profile = SENSOR_PROFILES.get(module_id)

    if not profile:
        return raw_value, 0, 0

    corrected_value = raw_value + profile["offset"]

    corrected_value = max(0, min(100, corrected_value))

    return corrected_value, profile["accuracy"], profile["offset"]
def smooth_sensor_readings(readings):
    if not readings:
        return 0

    return round(sum(readings) / len(readings), 2)

# =========================================================
# PAGE CONFIG
# =========================================================

st.set_page_config(
    page_title="AgriResolve AI",
    page_icon="🌾",
    layout="wide"
)
st.markdown("""
<style>

.main {
    background-color: #f7f9f7;
}

.block-container {
    padding-top: 1.5rem;
    padding-bottom: 2rem;
    max-width: 1400px;
}

h1, h2, h3 {
    color: #173b2a;
    font-weight: 700;
}

.agri-card {
    background: white;
    padding: 20px;
    border-radius: 16px;
    border: 1px solid #e6ebe7;
    box-shadow: 0 3px 12px rgba(0,0,0,0.05);
    margin-bottom: 18px;
}

.metric-card {
    background: white;
    padding: 18px;
    border-radius: 14px;
    border: 1px solid #e5ebe6;
    box-shadow: 0 2px 8px rgba(0,0,0,0.04);
}

.stButton > button {
    border-radius: 10px;
    border: 1px solid #d9e2dc;
    font-weight: 600;
    min-height: 42px;
}

.stButton > button:hover {
    border-color: #2e7d32;
    transform: translateY(-1px);
}

section[data-testid="stSidebar"] {
    background-color: #ffffff;
    border-right: 1px solid #e5ebe6;
}

</style>
""", unsafe_allow_html=True)

# =========================================================
# INITIALIZE DATABASES
# =========================================================

initialize_database()
initialize_users()


# =========================================================
# SESSION STATE
# =========================================================

DEFAULTS = {
    "authenticated": False,
    "user": None,

    "soil_moisture": 45,
    "soil_temperature": 28,
    "soil_humidity": 60,
    "soil_ph": 6.5,

    "nitrogen": 50,
    "phosphorus": 40,
    "potassium": 45,

    "pest_risk": "Low",
    "plant_analysis": None,

    "weather_data": None,
    "rain_probability": 30,

    "latitude": 11.0168,
    "longitude": 76.9558,

    "selected_crop": "Rice",
    "crop_stage": "Vegetative",
    "subscription":"Free",
    "access_role": "Farmer",
    "language": "English",
    "weather_mode": "Live Weather",
    
    "iot_running": False,
}


for key, value in DEFAULTS.items():
    if key not in st.session_state:
        st.session_state[key] = value


# =========================================================
# TRANSLATION SYSTEM
# =========================================================

TRANSLATIONS = {

    "English": {

        # General
        "app_title": "AgriResolve AI",
        "app_subtitle": "AI Farm Decision Intelligence Platform",
        "app_description":
            "Turning conflicting agricultural data into one clear and explainable farm action.",

        # Authentication
        "login": "🔐 Login",
        "signup": "🆕 Sign Up",
        "welcome_back": "Welcome Back",
        "create_account": "Create Account",
        "email": "📧 Email",
        "password": "🔑 Password",
        "confirm_password": "🔑 Confirm Password",
        "full_name": "👤 Full Name",
        "role": "👥 Role",
        "farmer": "Farmer",
        "fpo_role": "FPO / Field Officer",
        "agritech_role": "Agritech Organization",
        "login_button": "🔐 Login",
        "create_account_button": "🆕 Create Account",
        "enter_credentials": "Please enter your email and password.",
        "invalid_login": "Invalid email or password.",
        "fill_required": "Please fill all required fields.",
        "password_length": "Password must contain at least 6 characters.",
        "password_mismatch": "Passwords do not match.",
        "account_created":
            "Account created successfully. Open Login and sign in.",

        # Sidebar
        "language": "🌐 Language",
        "weather_mode": "Weather Mode",
        "live_weather": "Live Weather",
        "demo": "Demo",
        "testing": "Testing",
        "navigation": "Navigation",
        "logout": "🚪 Logout",
        "role_label": "👥 Role: ",

        # Navigation
        "dashboard": "🏠 Farm Dashboard",
        "soil": "🌱 Soil Sensor",
        "weather": "🌦️ Weather",
        "pest": "🐛 Pest & Disease",
        "decision": "🤖 AI Decision",
        "history": "🕘 Decision History",
        "fpo": "📊 FPO Insights",
        "pricing": "💳 Plans & Pricing",
        

        # Dashboard
        "farm_dashboard": "🌾 Farm Dashboard",
        "farm_location": "### 📍 Farm Location",
        "select_crop": "🌱 Select Crop",
        "growth_stage": "🌿 Growth Stage",
        "soil_moisture": "💧 Soil Moisture",
        "rain_probability": "🌧️ Rain Probability",
        "pest_risk": "🐛 Pest Risk",
        "temperature": "🌡️ Temperature",
        "latest_ai": "### 🤖 Latest AI Decision",
        "recommended_action": "🎯 Recommended Action",
        "priority": "Priority",
        "confidence": "Confidence",
        "conflict": "Conflict",
        "no_decision":
            "No AI decision yet. Open AI Decision to generate one.",
        "irrigation_conflict":
            "⚠️ Possible irrigation conflict: low soil moisture and high rainfall probability.",
        "water_condition":
            "⚠️ Water-management condition: high soil moisture and low rainfall probability.",
        "high_pest":
            "🐛 High pest risk detected. Crop inspection should be prioritized.",
        "no_major_conflict":
            "✅ No major immediate conflict detected from current signals.",

        # Location
        "latitude": "Latitude",
        "longitude": "Longitude",
        "update_location": "📍 Update Farm Location",
        "location_detected": "Location detected: ",
        "location_updated": "Farm location updated.",

        # Soil
        "soil_sensor": "🌱 Soil Sensor Simulator",
        "soil_info":
            "Currently simulated. This can later receive ESP32/IoT sensor readings.",
        "soil_temperature": "🌡️ Soil Temperature (°C)",
        "soil_humidity": "💦 Soil Humidity (%)",
        "soil_ph": "🧪 Soil pH",
        "nitrogen": "Nitrogen (N)",
        "phosphorus": "Phosphorus (P)",
        "potassium": "Potassium (K)",
        "soil_updated": "✅ Soil values updated.",

        # Weather
        "weather_intelligence": "🌦️ Weather Intelligence",
        "humidity": "💧 Humidity",
        "wind": "💨 Wind",
        "forecast": "### 📅 7-Day Forecast",
        "today": "Today",
        "tomorrow": "Tomorrow",
        "rain": "Rain",

        # Pest
        "pest_analysis": "🐛 Pest & Disease Analysis",
        "upload_image": "📷 Upload Plant Image",
        "uploaded_image": "Uploaded Crop Image",
        "analyze_image": "🔎 Analyze Crop Image",
        "analyzing": "Analyzing crop image...",
        "analysis_completed": "Plant image analysis completed.",
        "diagnosis_unavailable": "Image diagnosis is currently unavailable for ",
        "decision_continue":
            "The decision engine will continue using weather, soil, crop stage and pest-risk signals.",
        "analysis_failed": "Plant analysis failed.",

        # Decision
        "ai_decision": "🤖 AI Farm Decision",
        "crop": "🌱 Crop",
        "testing_scenario": "🧪 Testing Scenario",
        "current_farm": "Current Farm Data",
        "low_soil_high_rain": "Low Soil + High Rain",
        "low_soil_low_rain": "Low Soil + Low Rain",
        "high_soil_high_rain": "High Soil + High Rain",
        "high_pest_risk": "High Pest Risk",
        "generate_decision": "🤖 Generate AI Decision",
        "decision_conflict": "⚠️ Conflict: ",
        "no_conflict": "✅ No major conflict detected.",
        "why_decision": "### 🧠 Why this decision?",
        "evidence": "### 📊 Evidence",
        "conflict_detected": "Conflict detected.",

        # History
        "decision_history": "🕘 Decision History",
        "no_history": "📭 No decisions recorded yet.",
        "total_decisions": "Total Decisions",
        "conflicts": "Conflicts",
        "high_priority": "High Priority",
        "avg_confidence": "Avg Confidence",
        "clear_history": "🗑️ Clear Decision History",
        "history_cleared": "Decision history cleared.",

        # FPO
        "fpo_intelligence": "📊 FPO Farm Intelligence",
        "recent_priority": "### 🚨 Recent Priority Decisions",
        "crop_summary": "### 🌾 Crop-wise Summary",
        "no_priority": "No high or medium priority records.",
        "no_farm_data": "No farm decision data is available yet.",

        # Pricing
        "plans_pricing": "💳 Plans & Pricing",
        "pricing_description":
            "Choose a plan based on the level of agricultural decision intelligence you need.",
        "prototype_pricing":
            "💡 These are proposed prototype pricing plans for the AgriResolve AI business model.",
        "simple_scalable": "### 🌾 Simple and scalable pricing",

        "individual_farmers": "🌱 FOR INDIVIDUAL FARMERS",
        "farmer_free": "Farmer Free",
        "free_description": "Basic tools for understanding farm conditions.",
        "start_free": "🚀 Start Free",

        "recommended_farmers": "⭐ RECOMMENDED FOR FARMERS",
        "farmer_premium": "Farmer Premium",
        "premium_description":
            "Advanced decision support for individual farm management.",
        "upgrade_premium": "⭐ Upgrade to Premium",

        "organizations": "🏢 FOR ORGANIZATIONS",
        "fpo_organization": "FPO / Organization",
        "organization_description":
            "Multi-farm intelligence for FPOs, field officers and agritech teams.",
        "contact_fpo": "🏢 Contact for FPO",

        "per_month": "/month",
        "everything_free": "Everything in Free",
        "ai_conflict": "AI conflict detection",
        "explainable": "Explainable recommendations",
        "pest_disease": "Pest & disease analysis",
        "decision_history_feature": "Decision history",
        "advanced_insights": "Advanced farm insights",
        "farm_dashboard_feature": "Farm dashboard",
        "weather_information": "Weather information",
        "soil_simulator": "Soil simulator",
        "basic_crop": "Basic crop monitoring",
        "advanced_ai": "Advanced AI insights",
        "organization_analytics": "Organization analytics",
        "multi_farm": "Multi-farm monitoring",
        "fpo_dashboard": "FPO intelligence dashboard",
        "priority_identification": "Priority case identification",
        "crop_analytics": "Crop-wise analytics",
        "organization_insights": "Organization-level insights",

        "payment_later":
            "Premium payment integration can be connected later using a payment gateway.",
        "fpo_manual":
            "For the hackathon prototype, FPO onboarding can be handled manually. A dedicated contact and payment workflow can be integrated later.",

        "feature_comparison": "### 📊 Feature Comparison",
        "business_model": "### 💡 AgriResolve AI Business Model",
        "b2c_title": "B2C — Farmers",
        "b2c_text":
            "• Free basic access\n• Premium decision intelligence\n• Affordable monthly subscription\n• Optional future mobile application",
        "b2b_title": "B2B — Organizations",
        "b2b_text":
            "• FPO subscriptions\n• Field officer dashboards\n• Agritech integrations\n• Future API / enterprise plans",
        "business_success":
            "🌾 AgriResolve AI is designed to support farmers while also helping organizations manage agricultural decisions across many farms.",

        # Footer
        "footer":
            "🌾 AgriResolve AI — Explainable Agricultural Decision Intelligence Platform",

        # Weather error
        "weather_unavailable": "Live weather unavailable: ",

        # Misc
        "simulation": "Simulation",
        "basic": "Basic",
        "advanced": "Advanced",
        "limited": "Limited",
        "multi_farm_value": "Multi-farm",
        "yes": "Yes",
        "no": "No",
        "not_available": "N/A",
        "no_explanation": "No explanation available."
    },


    "Tamil": {

        "app_title": "AgriResolve AI",
        "app_subtitle": "AI விவசாய முடிவு நுண்ணறிவு தளம்",
        "app_description":
            "முரண்படும் விவசாயத் தரவுகளை ஒருங்கிணைத்து தெளிவான மற்றும் விளக்கக்கூடிய விவசாய நடவடிக்கையை வழங்குகிறது.",

        "login": "🔐 உள்நுழைவு",
        "signup": "🆕 பதிவு செய்யவும்",
        "welcome_back": "மீண்டும் வரவேற்கிறோம்",
        "create_account": "கணக்கை உருவாக்கவும்",
        "email": "📧 மின்னஞ்சல்",
        "password": "🔑 கடவுச்சொல்",
        "confirm_password": "🔑 கடவுச்சொல்லை உறுதிப்படுத்தவும்",
        "full_name": "👤 முழுப் பெயர்",
        "role": "👥 பங்கு",
        "farmer": "விவசாயி",
        "fpo_role": "FPO / கள அலுவலர்",
        "agritech_role": "Agritech நிறுவனம்",
        "login_button": "🔐 உள்நுழைக",
        "create_account_button": "🆕 கணக்கை உருவாக்கு",
        "enter_credentials": "உங்கள் மின்னஞ்சல் மற்றும் கடவுச்சொல்லை உள்ளிடவும்.",
        "invalid_login": "தவறான மின்னஞ்சல் அல்லது கடவுச்சொல்.",
        "fill_required": "தேவையான அனைத்து புலங்களையும் நிரப்பவும்.",
        "password_length": "கடவுச்சொல்லில் குறைந்தது 6 எழுத்துகள் இருக்க வேண்டும்.",
        "password_mismatch": "கடவுச்சொற்கள் பொருந்தவில்லை.",
        "account_created":
            "கணக்கு வெற்றிகரமாக உருவாக்கப்பட்டது. Login-ஐ திறந்து உள்நுழையவும்.",

        "language": "🌐 மொழி",
        "weather_mode": "வானிலை முறை",
        "live_weather": "நேரடி வானிலை",
        "demo": "டெமோ",
        "testing": "சோதனை",
        "navigation": "வழிசெலுத்தல்",
        "logout": "🚪 வெளியேறு",
        "role_label": "👥 பங்கு: ",

        "dashboard": "🏠 பண்ணை டாஷ்போர்டு",
        "soil": "🌱 மண் சென்சார்",
        "weather": "🌦️ வானிலை",
        "pest": "🐛 பூச்சி மற்றும் நோய்",
        "decision": "🤖 AI முடிவு",
        "history": "🕘 முடிவு வரலாறு",
        "fpo": "📊 FPO தகவல்கள்",
        "pricing": "💳 திட்டங்கள் மற்றும் விலை",

        "farm_dashboard": "🌾 பண்ணை டாஷ்போர்டு",
        "farm_location": "### 📍 பண்ணை இருப்பிடம்",
        "select_crop": "🌱 பயிரைத் தேர்ந்தெடுக்கவும்",
        "growth_stage": "🌿 வளர்ச்சி நிலை",
        "soil_moisture": "💧 மண் ஈரப்பதம்",
        "rain_probability": "🌧️ மழை வாய்ப்பு",
        "pest_risk": "🐛 பூச்சி அபாயம்",
        "temperature": "🌡️ வெப்பநிலை",
        "latest_ai": "### 🤖 சமீபத்திய AI முடிவு",
        "recommended_action": "🎯 பரிந்துரைக்கப்படும் நடவடிக்கை",
        "priority": "முன்னுரிமை",
        "confidence": "நம்பகத்தன்மை",
        "conflict": "முரண்பாடு",
        "no_decision":
            "AI முடிவு இன்னும் இல்லை. ஒன்றை உருவாக்க AI முடிவைத் திறக்கவும்.",
        "irrigation_conflict":
            "⚠️ சாத்தியமான பாசன முரண்பாடு: குறைந்த மண் ஈரப்பதம் மற்றும் அதிக மழை வாய்ப்பு.",
        "water_condition":
            "⚠️ நீர் மேலாண்மை நிலை: அதிக மண் ஈரப்பதம் மற்றும் குறைந்த மழை வாய்ப்பு.",
        "high_pest":
            "🐛 அதிக பூச்சி அபாயம் கண்டறியப்பட்டது. பயிர் பரிசோதனைக்கு முன்னுரிமை அளிக்கவும்.",
        "no_major_conflict":
            "✅ தற்போதைய தரவுகளின் அடிப்படையில் பெரிய உடனடி முரண்பாடு இல்லை.",

        "latitude": "அட்சரேகை",
        "longitude": "தீர்க்கரேகை",
        "update_location": "📍 பண்ணை இருப்பிடத்தைப் புதுப்பிக்கவும்",
        "location_detected": "இருப்பிடம் கண்டறியப்பட்டது: ",
        "location_updated": "பண்ணை இருப்பிடம் புதுப்பிக்கப்பட்டது.",

        "soil_sensor": "🌱 மண் சென்சார் சிமுலேட்டர்",
        "soil_info":
            "தற்போது இது சிமுலேஷன் ஆகும். பின்னர் ESP32/IoT சென்சார் தரவுகளைப் பெறலாம்.",
        "soil_temperature": "🌡️ மண் வெப்பநிலை (°C)",
        "soil_humidity": "💦 மண் ஈரப்பதம் (%)",
        "soil_ph": "🧪 மண் pH",
        "nitrogen": "நைட்ரஜன் (N)",
        "phosphorus": "பாஸ்பரஸ் (P)",
        "potassium": "பொட்டாசியம் (K)",
        "soil_updated": "✅ மண் மதிப்புகள் புதுப்பிக்கப்பட்டன.",

        "weather_intelligence": "🌦️ வானிலை நுண்ணறிவு",
        "humidity": "💧 ஈரப்பதம்",
        "wind": "💨 காற்று",
        "forecast": "### 📅 7 நாள் வானிலை முன்னறிவிப்பு",
        "today": "இன்று",
        "tomorrow": "நாளை",
        "rain": "மழை",

        "pest_analysis": "🐛 பூச்சி மற்றும் நோய் பகுப்பாய்வு",
        "upload_image": "📷 பயிர் படத்தைப் பதிவேற்றவும்",
        "uploaded_image": "பதிவேற்றப்பட்ட பயிர் படம்",
        "analyze_image": "🔎 பயிர் படத்தைப் பகுப்பாய்வு செய்க",
        "analyzing": "பயிர் படத்தைப் பகுப்பாய்வு செய்கிறது...",
        "analysis_completed": "பயிர் படப் பகுப்பாய்வு முடிந்தது.",
        "diagnosis_unavailable": "இந்த பயிருக்கான பட நோய் கண்டறிதல் தற்போது கிடைக்கவில்லை: ",
        "decision_continue":
            "வானிலை, மண், பயிர் வளர்ச்சி நிலை மற்றும் பூச்சி அபாயத் தரவுகளைப் பயன்படுத்தி முடிவு தொடரும்.",
        "analysis_failed": "பயிர் பகுப்பாய்வு தோல்வியடைந்தது.",

        "ai_decision": "🤖 AI விவசாய முடிவு",
        "crop": "🌱 பயிர்",
        "testing_scenario": "🧪 சோதனை நிலை",
        "current_farm": "தற்போதைய பண்ணை தரவு",
        "low_soil_high_rain": "குறைந்த மண் + அதிக மழை",
        "low_soil_low_rain": "குறைந்த மண் + குறைந்த மழை",
        "high_soil_high_rain": "அதிக மண் + அதிக மழை",
        "high_pest_risk": "அதிக பூச்சி அபாயம்",
        "generate_decision": "🤖 AI முடிவை உருவாக்கவும்",
        "decision_conflict": "⚠️ முரண்பாடு: ",
        "no_conflict": "✅ பெரிய முரண்பாடு கண்டறியப்படவில்லை.",
        "why_decision": "### 🧠 இந்த முடிவு ஏன்?",
        "evidence": "### 📊 ஆதாரங்கள்",
        "conflict_detected": "முரண்பாடு கண்டறியப்பட்டது.",

        "decision_history": "🕘 முடிவு வரலாறு",
        "no_history": "📭 எந்த முடிவுகளும் இதுவரை பதிவு செய்யப்படவில்லை.",
        "total_decisions": "மொத்த முடிவுகள்",
        "conflicts": "முரண்பாடுகள்",
        "high_priority": "அதிக முன்னுரிமை",
        "avg_confidence": "சராசரி நம்பகத்தன்மை",
        "clear_history": "🗑️ முடிவு வரலாற்றை அழிக்கவும்",
        "history_cleared": "முடிவு வரலாறு அழிக்கப்பட்டது.",

        "fpo_intelligence": "📊 FPO பண்ணை நுண்ணறிவு",
        "recent_priority": "### 🚨 சமீபத்திய முன்னுரிமை முடிவுகள்",
        "crop_summary": "### 🌾 பயிர் வாரியான சுருக்கம்",
        "no_priority": "அதிக அல்லது நடுத்தர முன்னுரிமை பதிவுகள் இல்லை.",
        "no_farm_data": "பண்ணை முடிவு தரவு இன்னும் கிடைக்கவில்லை.",

        "plans_pricing": "💳 திட்டங்கள் மற்றும் விலை",
        "pricing_description":
            "உங்களுக்கு தேவையான விவசாய முடிவு நுண்ணறிவின் அடிப்படையில் ஒரு திட்டத்தைத் தேர்ந்தெடுக்கவும்.",
        "prototype_pricing":
            "💡 இவை AgriResolve AI வணிக மாதிரிக்கான முன்மொழியப்பட்ட prototype விலைகள்.",
        "simple_scalable": "### 🌾 எளிய மற்றும் விரிவாக்கக்கூடிய விலைத் திட்டங்கள்",

        "individual_farmers": "🌱 தனிப்பட்ட விவசாயிகளுக்காக",
        "farmer_free": "விவசாயி இலவச திட்டம்",
        "free_description": "பண்ணை நிலைமைகளைப் புரிந்துகொள்ள அடிப்படை கருவிகள்.",
        "start_free": "🚀 இலவசமாக தொடங்கவும்",

        "recommended_farmers": "⭐ விவசாயிகளுக்குப் பரிந்துரைக்கப்படுகிறது",
        "farmer_premium": "விவசாயி Premium",
        "premium_description":
            "தனிப்பட்ட பண்ணை மேலாண்மைக்கான மேம்பட்ட முடிவு ஆதரவு.",
        "upgrade_premium": "⭐ Premium-க்கு மேம்படுத்தவும்",

        "organizations": "🏢 நிறுவனங்களுக்காக",
        "fpo_organization": "FPO / நிறுவனம்",
        "organization_description":
            "FPO, கள அலுவலர்கள் மற்றும் Agritech குழுக்களுக்கான பல பண்ணை நுண்ணறிவு.",
        "contact_fpo": "🏢 FPO தொடர்பு",

        "per_month": "/மாதம்",
        "everything_free": "Free திட்டத்தில் உள்ள அனைத்தும்",
        "ai_conflict": "AI முரண்பாடு கண்டறிதல்",
        "explainable": "விளக்கக்கூடிய பரிந்துரைகள்",
        "pest_disease": "பூச்சி மற்றும் நோய் பகுப்பாய்வு",
        "decision_history_feature": "முடிவு வரலாறு",
        "advanced_insights": "மேம்பட்ட பண்ணை நுண்ணறிவு",
        "farm_dashboard_feature": "பண்ணை டாஷ்போர்டு",
        "weather_information": "வானிலை தகவல்",
        "soil_simulator": "மண் சிமுலேட்டர்",
        "basic_crop": "அடிப்படை பயிர் கண்காணிப்பு",
        "advanced_ai": "மேம்பட்ட AI நுண்ணறிவு",
        "organization_analytics": "நிறுவன பகுப்பாய்வு",
        "multi_farm": "பல பண்ணை கண்காணிப்பு",
        "fpo_dashboard": "FPO நுண்ணறிவு டாஷ்போர்டு",
        "priority_identification": "முன்னுரிமை வழக்குகளை கண்டறிதல்",
        "crop_analytics": "பயிர் வாரியான பகுப்பாய்வு",
        "organization_insights": "நிறுவன அளவிலான நுண்ணறிவு",

        "payment_later":
            "Premium payment integration-ஐ பின்னர் payment gateway மூலம் இணைக்கலாம்.",
        "fpo_manual":
            "Hackathon prototype-க்கு FPO onboarding-ஐ கைமுறையாக செய்யலாம். பின்னர் தனிப்பட்ட தொடர்பு மற்றும் payment workflow இணைக்கலாம்.",

        "feature_comparison": "### 📊 அம்ச ஒப்பீடு",
        "business_model": "### 💡 AgriResolve AI வணிக மாதிரி",
        "b2c_title": "B2C — விவசாயிகள்",
        "b2c_text":
            "• இலவச அடிப்படை அணுகல்\n• Premium முடிவு நுண்ணறிவு\n• குறைந்த மாத சந்தா\n• எதிர்கால மொபைல் பயன்பாடு",
        "b2b_title": "B2B — நிறுவனங்கள்",
        "b2b_text":
            "• FPO சந்தாக்கள்\n• கள அலுவலர் டாஷ்போர்டுகள்\n• Agritech ஒருங்கிணைப்புகள்\n• எதிர்கால API / Enterprise திட்டங்கள்",
        "business_success":
            "🌾 AgriResolve AI விவசாயிகளுக்கு ஆதரவளிப்பதுடன் பல பண்ணைகளின் விவசாய முடிவுகளை நிறுவனங்கள் நிர்வகிக்கவும் உதவுகிறது.",

        "footer":
            "🌾 AgriResolve AI — விளக்கக்கூடிய விவசாய முடிவு நுண்ணறிவு தளம்",

        "weather_unavailable": "நேரடி வானிலை கிடைக்கவில்லை: ",
        "simulation": "சிமுலேஷன்",
        "basic": "அடிப்படை",
        "advanced": "மேம்பட்ட",
        "limited": "வரையறுக்கப்பட்டது",
        "multi_farm_value": "பல பண்ணை",
        "yes": "ஆம்",
        "no": "இல்லை",
        "not_available": "கிடைக்கவில்லை",
        "no_explanation": "விளக்கம் கிடைக்கவில்லை."
    },


    "Telugu": {

        "app_title": "AgriResolve AI",
        "app_subtitle": "AI వ్యవసాయ నిర్ణయ మేధస్సు వేదిక",
        "app_description":
            "విరుద్ధమైన వ్యవసాయ డేటాను ఒక స్పష్టమైన మరియు వివరించగల వ్యవసాయ చర్యగా మార్చడం.",

        "login": "🔐 లాగిన్",
        "signup": "🆕 సైన్ అప్",
        "welcome_back": "మళ్లీ స్వాగతం",
        "create_account": "ఖాతాను సృష్టించండి",
        "email": "📧 ఇమెయిల్",
        "password": "🔑 పాస్‌వర్డ్",
        "confirm_password": "🔑 పాస్‌వర్డ్ నిర్ధారించండి",
        "full_name": "👤 పూర్తి పేరు",
        "role": "👥 పాత్ర",
        "farmer": "రైతు",
        "fpo_role": "FPO / ఫీల్డ్ ఆఫీసర్",
        "agritech_role": "Agritech సంస్థ",
        "login_button": "🔐 లాగిన్",
        "create_account_button": "🆕 ఖాతా సృష్టించండి",
        "enter_credentials": "మీ ఇమెయిల్ మరియు పాస్‌వర్డ్ నమోదు చేయండి.",
        "invalid_login": "తప్పు ఇమెయిల్ లేదా పాస్‌వర్డ్.",
        "fill_required": "అవసరమైన అన్ని వివరాలను నమోదు చేయండి.",
        "password_length": "పాస్‌వర్డ్‌లో కనీసం 6 అక్షరాలు ఉండాలి.",
        "password_mismatch": "పాస్‌వర్డ్‌లు సరిపోలలేదు.",
        "account_created":
            "ఖాతా విజయవంతంగా సృష్టించబడింది. Login తెరిచి సైన్ ఇన్ చేయండి.",

        "language": "🌐 భాష",
        "weather_mode": "వాతావరణ మోడ్",
        "live_weather": "లైవ్ వాతావరణం",
        "demo": "డెమో",
        "testing": "టెస్టింగ్",
        "navigation": "నావిగేషన్",
        "logout": "🚪 లాగ్ అవుట్",
        "role_label": "👥 పాత్ర: ",

        "dashboard": "🏠 వ్యవసాయ డాష్‌బోర్డ్",
        "soil": "🌱 మట్టి సెన్సార్",
        "weather": "🌦️ వాతావరణం",
        "pest": "🐛 తెగుళ్లు మరియు వ్యాధులు",
        "decision": "🤖 AI నిర్ణయం",
        "history": "🕘 నిర్ణయ చరిత్ర",
        "fpo": "📊 FPO సమాచారం",
        "pricing": "💳 ప్లాన్స్ మరియు ధరలు",

        "farm_dashboard": "🌾 వ్యవసాయ డాష్‌బోర్డ్",
        "farm_location": "### 📍 వ్యవసాయ స్థానం",
        "select_crop": "🌱 పంటను ఎంచుకోండి",
        "growth_stage": "🌿 పెరుగుదల దశ",
        "soil_moisture": "💧 మట్టి తేమ",
        "rain_probability": "🌧️ వర్షం అవకాశం",
        "pest_risk": "🐛 తెగులు ప్రమాదం",
        "temperature": "🌡️ ఉష్ణోగ్రత",
        "latest_ai": "### 🤖 తాజా AI నిర్ణయం",
        "recommended_action": "🎯 సిఫార్సు చేయబడిన చర్య",
        "priority": "ప్రాధాన్యత",
        "confidence": "నమ్మక స్థాయి",
        "conflict": "విరుద్ధత",
        "no_decision":
            "ఇంకా AI నిర్ణయం లేదు. నిర్ణయం రూపొందించడానికి AI Decision తెరవండి.",
        "irrigation_conflict":
            "⚠️ నీటిపారుదల విరుద్ధత: తక్కువ మట్టి తేమ మరియు అధిక వర్షం అవకాశం.",
        "water_condition":
            "⚠️ నీటి నిర్వహణ పరిస్థితి: అధిక మట్టి తేమ మరియు తక్కువ వర్షం అవకాశం.",
        "high_pest":
            "🐛 అధిక తెగులు ప్రమాదం గుర్తించబడింది. పంటను పరిశీలించండి.",
        "no_major_conflict":
            "✅ ప్రస్తుత సంకేతాల ఆధారంగా పెద్ద తక్షణ విరుద్ధత లేదు.",

        "latitude": "అక్షాంశం",
        "longitude": "రేఖాంశం",
        "update_location": "📍 వ్యవసాయ స్థానాన్ని నవీకరించండి",
        "location_detected": "స్థానం గుర్తించబడింది: ",
        "location_updated": "వ్యవసాయ స్థానం నవీకరించబడింది.",

        "soil_sensor": "🌱 మట్టి సెన్సార్ సిమ్యులేటర్",
        "soil_info":
            "ప్రస్తుతం ఇది సిమ్యులేషన్. తరువాత ESP32/IoT సెన్సార్ డేటాను పొందవచ్చు.",
        "soil_temperature": "🌡️ మట్టి ఉష్ణోగ్రత (°C)",
        "soil_humidity": "💦 మట్టి తేమ (%)",
        "soil_ph": "🧪 మట్టి pH",
        "nitrogen": "నైట్రోజన్ (N)",
        "phosphorus": "ఫాస్ఫరస్ (P)",
        "potassium": "పొటాషియం (K)",
        "soil_updated": "✅ మట్టి విలువలు నవీకరించబడ్డాయి.",

        "weather_intelligence": "🌦️ వాతావరణ మేధస్సు",
        "humidity": "💧 తేమ",
        "wind": "💨 గాలి",
        "forecast": "### 📅 7 రోజుల వాతావరణ అంచనా",
        "today": "ఈ రోజు",
        "tomorrow": "రేపు",
        "rain": "వర్షం",

        "pest_analysis": "🐛 తెగులు మరియు వ్యాధి విశ్లేషణ",
        "upload_image": "📷 పంట చిత్రాన్ని అప్‌లోడ్ చేయండి",
        "uploaded_image": "అప్‌లోడ్ చేసిన పంట చిత్రం",
        "analyze_image": "🔎 పంట చిత్రాన్ని విశ్లేషించండి",
        "analyzing": "పంట చిత్రాన్ని విశ్లేషిస్తోంది...",
        "analysis_completed": "పంట చిత్రం విశ్లేషణ పూర్తయింది.",
        "diagnosis_unavailable": "ఈ పంటకు చిత్ర ఆధారిత నిర్ధారణ ప్రస్తుతం అందుబాటులో లేదు: ",
        "decision_continue":
            "వాతావరణం, మట్టి, పంట దశ మరియు తెగులు ప్రమాద సంకేతాలను ఉపయోగించి నిర్ణయం కొనసాగుతుంది.",
        "analysis_failed": "పంట విశ్లేషణ విఫలమైంది.",

        "ai_decision": "🤖 AI వ్యవసాయ నిర్ణయం",
        "crop": "🌱 పంట",
        "testing_scenario": "🧪 పరీక్షా పరిస్థితి",
        "current_farm": "ప్రస్తుత వ్యవసాయ డేటా",
        "low_soil_high_rain": "తక్కువ మట్టి + అధిక వర్షం",
        "low_soil_low_rain": "తక్కువ మట్టి + తక్కువ వర్షం",
        "high_soil_high_rain": "అధిక మట్టి + అధిక వర్షం",
        "high_pest_risk": "అధిక తెగులు ప్రమాదం",
        "generate_decision": "🤖 AI నిర్ణయాన్ని రూపొందించండి",
        "decision_conflict": "⚠️ విరుద్ధత: ",
        "no_conflict": "✅ పెద్ద విరుద్ధత గుర్తించబడలేదు.",
        "why_decision": "### 🧠 ఈ నిర్ణయం ఎందుకు?",
        "evidence": "### 📊 ఆధారాలు",
        "conflict_detected": "విరుద్ధత గుర్తించబడింది.",

        "decision_history": "🕘 నిర్ణయ చరిత్ర",
        "no_history": "📭 ఇంకా నిర్ణయాలు నమోదు కాలేదు.",
        "total_decisions": "మొత్తం నిర్ణయాలు",
        "conflicts": "విరుద్ధతలు",
        "high_priority": "అధిక ప్రాధాన్యత",
        "avg_confidence": "సగటు నమ్మక స్థాయి",
        "clear_history": "🗑️ నిర్ణయ చరిత్రను తొలగించండి",
        "history_cleared": "నిర్ణయ చరిత్ర తొలగించబడింది.",

        "fpo_intelligence": "📊 FPO వ్యవసాయ మేధస్సు",
        "recent_priority": "### 🚨 ఇటీవలి ప్రాధాన్యత నిర్ణయాలు",
        "crop_summary": "### 🌾 పంట వారీ సారాంశం",
        "no_priority": "అధిక లేదా మధ్యస్థ ప్రాధాన్యత రికార్డులు లేవు.",
        "no_farm_data": "వ్యవసాయ నిర్ణయ డేటా ఇంకా అందుబాటులో లేదు.",

        "plans_pricing": "💳 ప్లాన్స్ మరియు ధరలు",
        "pricing_description":
            "మీకు అవసరమైన వ్యవసాయ నిర్ణయ మేధస్సు స్థాయి ఆధారంగా ప్లాన్ ఎంచుకోండి.",
        "prototype_pricing":
            "💡 ఇవి AgriResolve AI వ్యాపార నమూనా కోసం ప్రతిపాదిత prototype ధరలు.",
        "simple_scalable": "### 🌾 సరళమైన మరియు విస్తరించగల ధరలు",

        "individual_farmers": "🌱 వ్యక్తిగత రైతుల కోసం",
        "farmer_free": "Farmer Free",
        "free_description": "వ్యవసాయ పరిస్థితులను అర్థం చేసుకోవడానికి ప్రాథమిక సాధనాలు.",
        "start_free": "🚀 ఉచితంగా ప్రారంభించండి",

        "recommended_farmers": "⭐ రైతులకు సిఫార్సు",
        "farmer_premium": "Farmer Premium",
        "premium_description":
            "వ్యక్తిగత వ్యవసాయ నిర్వహణ కోసం అధునాతన నిర్ణయ సహాయం.",
        "upgrade_premium": "⭐ Premiumకి అప్‌గ్రేడ్ చేయండి",

        "organizations": "🏢 సంస్థల కోసం",
        "fpo_organization": "FPO / సంస్థ",
        "organization_description":
            "FPOలు, ఫీల్డ్ ఆఫీసర్లు మరియు Agritech బృందాల కోసం బహుళ వ్యవసాయ మేధస్సు.",
        "contact_fpo": "🏢 FPOని సంప్రదించండి",

        "per_month": "/నెల",
        "everything_free": "Freeలో ఉన్న అన్ని ఫీచర్లు",
        "ai_conflict": "AI విరుద్ధత గుర్తింపు",
        "explainable": "వివరణాత్మక సిఫార్సులు",
        "pest_disease": "తెగులు మరియు వ్యాధి విశ్లేషణ",
        "decision_history_feature": "నిర్ణయ చరిత్ర",
        "advanced_insights": "అధునాతన వ్యవసాయ మేధస్సు",
        "farm_dashboard_feature": "వ్యవసాయ డాష్‌బోర్డ్",
        "weather_information": "వాతావరణ సమాచారం",
        "soil_simulator": "మట్టి సిమ్యులేటర్",
        "basic_crop": "ప్రాథమిక పంట పర్యవేక్షణ",
        "advanced_ai": "అధునాతన AI మేధస్సు",
        "organization_analytics": "సంస్థ విశ్లేషణ",
        "multi_farm": "బహుళ వ్యవసాయ పర్యవేక్షణ",
        "fpo_dashboard": "FPO మేధస్సు డాష్‌బోర్డ్",
        "priority_identification": "ప్రాధాన్యత కేసుల గుర్తింపు",
        "crop_analytics": "పంట వారీ విశ్లేషణ",
        "organization_insights": "సంస్థ స్థాయి మేధస్సు",

        "payment_later":
            "Premium payment integrationను తరువాత payment gatewayతో అనుసంధానించవచ్చు.",
        "fpo_manual":
            "Hackathon prototype కోసం FPO onboardingను మాన్యువల్‌గా చేయవచ్చు. తరువాత ప్రత్యేక contact మరియు payment workflowను జోడించవచ్చు.",

        "feature_comparison": "### 📊 ఫీచర్ పోలిక",
        "business_model": "### 💡 AgriResolve AI వ్యాపార నమూనా",
        "b2c_title": "B2C — రైతులు",
        "b2c_text":
            "• ఉచిత ప్రాథమిక యాక్సెస్\n• Premium నిర్ణయ మేధస్సు\n• సరసమైన నెలవారీ సబ్‌స్క్రిప్షన్\n• భవిష్యత్ మొబైల్ అప్లికేషన్",
        "b2b_title": "B2B — సంస్థలు",
        "b2b_text":
            "• FPO సబ్‌స్క్రిప్షన్లు\n• ఫీల్డ్ ఆఫీసర్ డాష్‌బోర్డులు\n• Agritech ఇంటిగ్రేషన్లు\n• భవిష్యత్ API / Enterprise ప్లాన్స్",
        "business_success":
            "🌾 AgriResolve AI రైతులకు సహాయం చేయడంతో పాటు అనేక వ్యవసాయ క్షేత్రాల నిర్ణయాలను సంస్థలు నిర్వహించడంలో సహాయపడుతుంది.",

        "footer":
            "🌾 AgriResolve AI — వివరించగల వ్యవసాయ నిర్ణయ మేధస్సు వేదిక",

        "weather_unavailable": "లైవ్ వాతావరణం అందుబాటులో లేదు: ",
        "simulation": "సిమ్యులేషన్",
        "basic": "ప్రాథమిక",
        "advanced": "అధునాతన",
        "limited": "పరిమితం",
        "multi_farm_value": "బహుళ వ్యవసాయం",
        "yes": "అవును",
        "no": "కాదు",
        "not_available": "అందుబాటులో లేదు",
        "no_explanation": "వివరణ అందుబాటులో లేదు."
    },


    "Hindi": {

        "app_title": "AgriResolve AI",
        "app_subtitle": "AI कृषि निर्णय बुद्धिमत्ता प्लेटफॉर्म",
        "app_description":
            "विरोधाभासी कृषि डेटा को एक स्पष्ट और समझने योग्य कृषि कार्रवाई में बदलना।",

        "login": "🔐 लॉगिन",
        "signup": "🆕 साइन अप",
        "welcome_back": "वापसी पर स्वागत है",
        "create_account": "खाता बनाएं",
        "email": "📧 ईमेल",
        "password": "🔑 पासवर्ड",
        "confirm_password": "🔑 पासवर्ड की पुष्टि करें",
        "full_name": "👤 पूरा नाम",
        "role": "👥 भूमिका",
        "farmer": "किसान",
        "fpo_role": "FPO / फील्ड अधिकारी",
        "agritech_role": "Agritech संगठन",
        "login_button": "🔐 लॉगिन",
        "create_account_button": "🆕 खाता बनाएं",
        "enter_credentials": "कृपया अपना ईमेल और पासवर्ड दर्ज करें।",
        "invalid_login": "गलत ईमेल या पासवर्ड।",
        "fill_required": "कृपया सभी आवश्यक जानकारी भरें।",
        "password_length": "पासवर्ड में कम से कम 6 अक्षर होने चाहिए।",
        "password_mismatch": "पासवर्ड मेल नहीं खाते।",
        "account_created":
            "खाता सफलतापूर्वक बनाया गया। Login खोलकर साइन इन करें।",

        "language": "🌐 भाषा",
        "weather_mode": "मौसम मोड",
        "live_weather": "लाइव मौसम",
        "demo": "डेमो",
        "testing": "टेस्टिंग",
        "navigation": "नेविगेशन",
        "logout": "🚪 लॉग आउट",
        "role_label": "👥 भूमिका: ",

        "dashboard": "🏠 फार्म डैशबोर्ड",
        "soil": "🌱 मिट्टी सेंसर",
        "weather": "🌦️ मौसम",
        "pest": "🐛 कीट और रोग",
        "decision": "🤖 AI निर्णय",
        "history": "🕘 निर्णय इतिहास",
        "fpo": "📊 FPO जानकारी",
        "pricing": "💳 योजनाएं और मूल्य",

        "farm_dashboard": "🌾 फार्म डैशबोर्ड",
        "farm_location": "### 📍 फार्म का स्थान",
        "select_crop": "🌱 फसल चुनें",
        "growth_stage": "🌿 विकास अवस्था",
        "soil_moisture": "💧 मिट्टी की नमी",
        "rain_probability": "🌧️ वर्षा की संभावना",
        "pest_risk": "🐛 कीट जोखिम",
        "temperature": "🌡️ तापमान",
        "latest_ai": "### 🤖 नवीनतम AI निर्णय",
        "recommended_action": "🎯 अनुशंसित कार्रवाई",
        "priority": "प्राथमिकता",
        "confidence": "विश्वसनीयता",
        "conflict": "संघर्ष",
        "no_decision":
            "अभी कोई AI निर्णय नहीं है। निर्णय बनाने के लिए AI Decision खोलें।",
        "irrigation_conflict":
            "⚠️ संभावित सिंचाई संघर्ष: कम मिट्टी की नमी और अधिक वर्षा की संभावना।",
        "water_condition":
            "⚠️ जल प्रबंधन स्थिति: अधिक मिट्टी की नमी और कम वर्षा की संभावना।",
        "high_pest":
            "🐛 उच्च कीट जोखिम पाया गया। फसल निरीक्षण को प्राथमिकता दें।",
        "no_major_conflict":
            "✅ वर्तमान संकेतों के आधार पर कोई बड़ा तत्काल संघर्ष नहीं मिला।",

        "latitude": "अक्षांश",
        "longitude": "देशांतर",
        "update_location": "📍 फार्म का स्थान अपडेट करें",
        "location_detected": "स्थान पाया गया: ",
        "location_updated": "फार्म का स्थान अपडेट किया गया।",

        "soil_sensor": "🌱 मिट्टी सेंसर सिम्युलेटर",
        "soil_info":
            "अभी यह सिमुलेशन है। बाद में ESP32/IoT सेंसर रीडिंग प्राप्त की जा सकती है।",
        "soil_temperature": "🌡️ मिट्टी का तापमान (°C)",
        "soil_humidity": "💦 मिट्टी की नमी (%)",
        "soil_ph": "🧪 मिट्टी pH",
        "nitrogen": "नाइट्रोजन (N)",
        "phosphorus": "फॉस्फोरस (P)",
        "potassium": "पोटैशियम (K)",
        "soil_updated": "✅ मिट्टी के मान अपडेट किए गए।",

        "weather_intelligence": "🌦️ मौसम बुद्धिमत्ता",
        "humidity": "💧 नमी",
        "wind": "💨 हवा",
        "forecast": "### 📅 7-दिन का मौसम पूर्वानुमान",
        "today": "आज",
        "tomorrow": "कल",
        "rain": "वर्षा",

        "pest_analysis": "🐛 कीट और रोग विश्लेषण",
        "upload_image": "📷 पौधे की तस्वीर अपलोड करें",
        "uploaded_image": "अपलोड की गई फसल तस्वीर",
        "analyze_image": "🔎 फसल तस्वीर का विश्लेषण करें",
        "analyzing": "फसल तस्वीर का विश्लेषण हो रहा है...",
        "analysis_completed": "फसल तस्वीर का विश्लेषण पूरा हुआ।",
        "diagnosis_unavailable": "इस फसल के लिए तस्वीर आधारित निदान अभी उपलब्ध नहीं है: ",
        "decision_continue":
            "निर्णय इंजन मौसम, मिट्टी, फसल अवस्था और कीट जोखिम संकेतों का उपयोग जारी रखेगा।",
        "analysis_failed": "फसल विश्लेषण विफल हुआ।",

        "ai_decision": "🤖 AI कृषि निर्णय",
        "crop": "🌱 फसल",
        "testing_scenario": "🧪 परीक्षण स्थिति",
        "current_farm": "वर्तमान फार्म डेटा",
        "low_soil_high_rain": "कम मिट्टी + अधिक वर्षा",
        "low_soil_low_rain": "कम मिट्टी + कम वर्षा",
        "high_soil_high_rain": "अधिक मिट्टी + अधिक वर्षा",
        "high_pest_risk": "उच्च कीट जोखिम",
        "generate_decision": "🤖 AI निर्णय बनाएं",
        "decision_conflict": "⚠️ संघर्ष: ",
        "no_conflict": "✅ कोई बड़ा संघर्ष नहीं मिला।",
        "why_decision": "### 🧠 यह निर्णय क्यों?",
        "evidence": "### 📊 प्रमाण",
        "conflict_detected": "संघर्ष पाया गया।",

        "decision_history": "🕘 निर्णय इतिहास",
        "no_history": "📭 अभी कोई निर्णय दर्ज नहीं है।",
        "total_decisions": "कुल निर्णय",
        "conflicts": "संघर्ष",
        "high_priority": "उच्च प्राथमिकता",
        "avg_confidence": "औसत विश्वसनीयता",
        "clear_history": "🗑️ निर्णय इतिहास साफ करें",
        "history_cleared": "निर्णय इतिहास साफ कर दिया गया।",

        "fpo_intelligence": "📊 FPO कृषि बुद्धिमत्ता",
        "recent_priority": "### 🚨 हाल के प्राथमिकता निर्णय",
        "crop_summary": "### 🌾 फसल-वार सारांश",
        "no_priority": "कोई उच्च या मध्यम प्राथमिकता रिकॉर्ड नहीं है।",
        "no_farm_data": "अभी कोई कृषि निर्णय डेटा उपलब्ध नहीं है।",

        "plans_pricing": "💳 योजनाएं और मूल्य",
        "pricing_description":
            "अपनी कृषि निर्णय बुद्धिमत्ता की आवश्यकता के अनुसार योजना चुनें।",
        "prototype_pricing":
            "💡 ये AgriResolve AI बिजनेस मॉडल के लिए प्रस्तावित prototype कीमतें हैं।",
        "simple_scalable": "### 🌾 सरल और विस्तार योग्य मूल्य",

        "individual_farmers": "🌱 व्यक्तिगत किसानों के लिए",
        "farmer_free": "Farmer Free",
        "free_description": "कृषि परिस्थितियों को समझने के लिए बुनियादी उपकरण।",
        "start_free": "🚀 मुफ्त शुरू करें",

        "recommended_farmers": "⭐ किसानों के लिए अनुशंसित",
        "farmer_premium": "Farmer Premium",
        "premium_description":
            "व्यक्तिगत कृषि प्रबंधन के लिए उन्नत निर्णय सहायता।",
        "upgrade_premium": "⭐ Premium में अपग्रेड करें",

        "organizations": "🏢 संगठनों के लिए",
        "fpo_organization": "FPO / संगठन",
        "organization_description":
            "FPO, फील्ड अधिकारियों और Agritech टीमों के लिए बहु-फार्म बुद्धिमत्ता।",
        "contact_fpo": "🏢 FPO से संपर्क करें",

        "per_month": "/माह",
        "everything_free": "Free की सभी सुविधाएं",
        "ai_conflict": "AI संघर्ष पहचान",
        "explainable": "समझाने योग्य अनुशंसाएं",
        "pest_disease": "कीट और रोग विश्लेषण",
        "decision_history_feature": "निर्णय इतिहास",
        "advanced_insights": "उन्नत कृषि बुद्धिमत्ता",
        "farm_dashboard_feature": "फार्म डैशबोर्ड",
        "weather_information": "मौसम जानकारी",
        "soil_simulator": "मिट्टी सिम्युलेटर",
        "basic_crop": "बुनियादी फसल निगरानी",
        "advanced_ai": "उन्नत AI बुद्धिमत्ता",
        "organization_analytics": "संगठन विश्लेषण",
        "multi_farm": "बहु-फार्म निगरानी",
        "fpo_dashboard": "FPO बुद्धिमत्ता डैशबोर्ड",
        "priority_identification": "प्राथमिकता मामलों की पहचान",
        "crop_analytics": "फसल-वार विश्लेषण",
        "organization_insights": "संगठन स्तर की बुद्धिमत्ता",

        "payment_later":
            "Premium payment integration को बाद में payment gateway के माध्यम से जोड़ा जा सकता है।",
        "fpo_manual":
            "Hackathon prototype के लिए FPO onboarding मैन्युअल रूप से किया जा सकता है। बाद में contact और payment workflow जोड़ा जा सकता है।",

        "feature_comparison": "### 📊 फीचर तुलना",
        "business_model": "### 💡 AgriResolve AI बिजनेस मॉडल",
        "b2c_title": "B2C — किसान",
        "b2c_text":
            "• मुफ्त बुनियादी पहुंच\n• Premium निर्णय बुद्धिमत्ता\n• किफायती मासिक सदस्यता\n• भविष्य का मोबाइल एप्लिकेशन",
        "b2b_title": "B2B — संगठन",
        "b2b_text":
            "• FPO सदस्यता\n• फील्ड अधिकारी डैशबोर्ड\n• Agritech एकीकरण\n• भविष्य के API / Enterprise प्लान",
        "business_success":
            "🌾 AgriResolve AI किसानों का समर्थन करने के साथ संगठनों को कई फार्मों के कृषि निर्णयों को प्रबंधित करने में मदद करता है।",

        "footer":
            "🌾 AgriResolve AI — समझाने योग्य कृषि निर्णय बुद्धिमत्ता प्लेटफॉर्म",

        "weather_unavailable": "लाइव मौसम उपलब्ध नहीं है: ",
        "simulation": "सिमुलेशन",
        "basic": "बुनियादी",
        "advanced": "उन्नत",
        "limited": "सीमित",
        "multi_farm_value": "बहु-फार्म",
        "yes": "हाँ",
        "no": "नहीं",
        "not_available": "उपलब्ध नहीं",
        "no_explanation": "कोई विवरण उपलब्ध नहीं है।"
    },


    "Kannada": {

        "app_title": "AgriResolve AI",
        "app_subtitle": "AI ಕೃಷಿ ನಿರ್ಧಾರ ಬುದ್ಧಿಮತ್ತೆ ವೇದಿಕೆ",
        "app_description":
            "ವಿರೋಧಾಭಾಸ ಹೊಂದಿರುವ ಕೃಷಿ ಮಾಹಿತಿಯನ್ನು ಒಂದು ಸ್ಪಷ್ಟ ಮತ್ತು ವಿವರಿಸಬಹುದಾದ ಕೃಷಿ ಕ್ರಮವಾಗಿ ಪರಿವರ್ತಿಸುವುದು.",

        "login": "🔐 ಲಾಗಿನ್",
        "signup": "🆕 ಸೈನ್ ಅಪ್",
        "welcome_back": "ಮತ್ತೆ ಸ್ವಾಗತ",
        "create_account": "ಖಾತೆ ರಚಿಸಿ",
        "email": "📧 ಇಮೇಲ್",
        "password": "🔑 ಪಾಸ್‌ವರ್ಡ್",
        "confirm_password": "🔑 ಪಾಸ್‌ವರ್ಡ್ ದೃಢೀಕರಿಸಿ",
        "full_name": "👤 ಪೂರ್ಣ ಹೆಸರು",
        "role": "👥 ಪಾತ್ರ",
        "farmer": "ರೈತ",
        "fpo_role": "FPO / ಕ್ಷೇತ್ರ ಅಧಿಕಾರಿ",
        "agritech_role": "Agritech ಸಂಸ್ಥೆ",
        "login_button": "🔐 ಲಾಗಿನ್",
        "create_account_button": "🆕 ಖಾತೆ ರಚಿಸಿ",
        "enter_credentials": "ನಿಮ್ಮ ಇಮೇಲ್ ಮತ್ತು ಪಾಸ್‌ವರ್ಡ್ ನಮೂದಿಸಿ.",
        "invalid_login": "ತಪ್ಪಾದ ಇಮೇಲ್ ಅಥವಾ ಪಾಸ್‌ವರ್ಡ್.",
        "fill_required": "ಅಗತ್ಯವಿರುವ ಎಲ್ಲಾ ವಿವರಗಳನ್ನು ಭರ್ತಿ ಮಾಡಿ.",
        "password_length": "ಪಾಸ್‌ವರ್ಡ್ ಕನಿಷ್ಠ 6 ಅಕ್ಷರಗಳನ್ನು ಹೊಂದಿರಬೇಕು.",
        "password_mismatch": "ಪಾಸ್‌ವರ್ಡ್‌ಗಳು ಹೊಂದಿಕೆಯಾಗುತ್ತಿಲ್ಲ.",
        "account_created":
            "ಖಾತೆ ಯಶಸ್ವಿಯಾಗಿ ರಚಿಸಲಾಗಿದೆ. Login ತೆರೆಯಿರಿ ಮತ್ತು ಸೈನ್ ಇನ್ ಮಾಡಿ.",

        "language": "🌐 ಭಾಷೆ",
        "weather_mode": "ಹವಾಮಾನ ಮೋಡ್",
        "live_weather": "ಲೈವ್ ಹವಾಮಾನ",
        "demo": "ಡೆಮೊ",
        "testing": "ಪರೀಕ್ಷೆ",
        "navigation": "ನ್ಯಾವಿಗೇಶನ್",
        "logout": "🚪 ಲಾಗ್ ಔಟ್",
        "role_label": "👥 ಪಾತ್ರ: ",

        "dashboard": "🏠 ಫಾರ್ಮ್ ಡ್ಯಾಶ್‌ಬೋರ್ಡ್",
        "soil": "🌱 ಮಣ್ಣು ಸೆನ್ಸರ್",
        "weather": "🌦️ ಹವಾಮಾನ",
        "pest": "🐛 ಕೀಟ ಮತ್ತು ರೋಗ",
        "decision": "🤖 AI ನಿರ್ಧಾರ",
        "history": "🕘 ನಿರ್ಧಾರ ಇತಿಹಾಸ",
        "fpo": "📊 FPO ಮಾಹಿತಿ",
        "pricing": "💳 ಯೋಜನೆಗಳು ಮತ್ತು ಬೆಲೆ",

        "farm_dashboard": "🌾 ಫಾರ್ಮ್ ಡ್ಯಾಶ್‌ಬೋರ್ಡ್",
        "farm_location": "### 📍 ಫಾರ್ಮ್ ಸ್ಥಳ",
        "select_crop": "🌱 ಬೆಳೆ ಆಯ್ಕೆಮಾಡಿ",
        "growth_stage": "🌿 ಬೆಳವಣಿಗೆಯ ಹಂತ",
        "soil_moisture": "💧 ಮಣ್ಣಿನ ತೇವಾಂಶ",
        "rain_probability": "🌧️ ಮಳೆಯ ಸಾಧ್ಯತೆ",
        "pest_risk": "🐛 ಕೀಟ ಅಪಾಯ",
        "temperature": "🌡️ ತಾಪಮಾನ",
        "latest_ai": "### 🤖 ಇತ್ತೀಚಿನ AI ನಿರ್ಧಾರ",
        "recommended_action": "🎯 ಶಿಫಾರಸು ಮಾಡಿದ ಕ್ರಮ",
        "priority": "ಆದ್ಯತೆ",
        "confidence": "ವಿಶ್ವಾಸ ಮಟ್ಟ",
        "conflict": "ವಿರೋಧಾಭಾಸ",
        "no_decision":
            "ಇನ್ನೂ AI ನಿರ್ಧಾರವಿಲ್ಲ. ನಿರ್ಧಾರ ರಚಿಸಲು AI Decision ತೆರೆಯಿರಿ.",
        "irrigation_conflict":
            "⚠️ ನೀರಾವರಿ ವಿರೋಧಾಭಾಸ: ಕಡಿಮೆ ಮಣ್ಣಿನ ತೇವಾಂಶ ಮತ್ತು ಹೆಚ್ಚಿನ ಮಳೆಯ ಸಾಧ್ಯತೆ.",
        "water_condition":
            "⚠️ ನೀರಿನ ನಿರ್ವಹಣಾ ಪರಿಸ್ಥಿತಿ: ಹೆಚ್ಚಿನ ಮಣ್ಣಿನ ತೇವಾಂಶ ಮತ್ತು ಕಡಿಮೆ ಮಳೆಯ ಸಾಧ್ಯತೆ.",
        "high_pest":
            "🐛 ಹೆಚ್ಚಿನ ಕೀಟ ಅಪಾಯ ಕಂಡುಬಂದಿದೆ. ಬೆಳೆ ಪರಿಶೀಲನೆಗೆ ಆದ್ಯತೆ ನೀಡಿ.",
        "no_major_conflict":
            "✅ ಪ್ರಸ್ತುತ ಸೂಚನೆಗಳ ಆಧಾರದ ಮೇಲೆ ಯಾವುದೇ ದೊಡ್ಡ ತಕ್ಷಣದ ವಿರೋಧಾಭಾಸ ಕಂಡುಬಂದಿಲ್ಲ.",

        "latitude": "ಅಕ್ಷಾಂಶ",
        "longitude": "ರೇಖಾಂಶ",
        "update_location": "📍 ಫಾರ್ಮ್ ಸ್ಥಳವನ್ನು ನವೀಕರಿಸಿ",
        "location_detected": "ಸ್ಥಳ ಕಂಡುಬಂದಿದೆ: ",
        "location_updated": "ಫಾರ್ಮ್ ಸ್ಥಳ ನವೀಕರಿಸಲಾಗಿದೆ.",

        "soil_sensor": "🌱 ಮಣ್ಣು ಸೆನ್ಸರ್ ಸಿಮ್ಯುಲೇಟರ್",
        "soil_info":
            "ಪ್ರಸ್ತುತ ಇದು ಸಿಮ್ಯುಲೇಶನ್ ಆಗಿದೆ. ನಂತರ ESP32/IoT ಸೆನ್ಸರ್ ಡೇಟಾವನ್ನು ಪಡೆಯಬಹುದು.",
        "soil_temperature": "🌡️ ಮಣ್ಣಿನ ತಾಪಮಾನ (°C)",
        "soil_humidity": "💦 ಮಣ್ಣಿನ ತೇವಾಂಶ (%)",
        "soil_ph": "🧪 ಮಣ್ಣು pH",
        "nitrogen": "ನೈಟ್ರೋಜನ್ (N)",
        "phosphorus": "ಫಾಸ್ಫರಸ್ (P)",
        "potassium": "ಪೊಟ್ಯಾಸಿಯಮ್ (K)",
        "soil_updated": "✅ ಮಣ್ಣಿನ ಮೌಲ್ಯಗಳನ್ನು ನವೀಕರಿಸಲಾಗಿದೆ.",

        "weather_intelligence": "🌦️ ಹವಾಮಾನ ಬುದ್ಧಿಮತ್ತೆ",
        "humidity": "💧 ತೇವಾಂಶ",
        "wind": "💨 ಗಾಳಿ",
        "forecast": "### 📅 7 ದಿನಗಳ ಹವಾಮಾನ ಮುನ್ಸೂಚನೆ",
        "today": "ಇಂದು",
        "tomorrow": "ನಾಳೆ",
        "rain": "ಮಳೆ",

        "pest_analysis": "🐛 ಕೀಟ ಮತ್ತು ರೋಗ ವಿಶ್ಲೇಷಣೆ",
        "upload_image": "📷 ಸಸ್ಯದ ಚಿತ್ರವನ್ನು ಅಪ್‌ಲೋಡ್ ಮಾಡಿ",
        "uploaded_image": "ಅಪ್‌ಲೋಡ್ ಮಾಡಿದ ಬೆಳೆ ಚಿತ್ರ",
        "analyze_image": "🔎 ಬೆಳೆ ಚಿತ್ರವನ್ನು ವಿಶ್ಲೇಷಿಸಿ",
        "analyzing": "ಬೆಳೆ ಚಿತ್ರವನ್ನು ವಿಶ್ಲೇಷಿಸಲಾಗುತ್ತಿದೆ...",
        "analysis_completed": "ಬೆಳೆ ಚಿತ್ರ ವಿಶ್ಲೇಷಣೆ ಪೂರ್ಣಗೊಂಡಿದೆ.",
        "diagnosis_unavailable": "ಈ ಬೆಳೆಗೆ ಚಿತ್ರ ಆಧಾರಿತ ರೋಗನಿರ್ಣಯವು ಪ್ರಸ್ತುತ ಲಭ್ಯವಿಲ್ಲ: ",
        "decision_continue":
            "ಹವಾಮಾನ, ಮಣ್ಣು, ಬೆಳೆ ಹಂತ ಮತ್ತು ಕೀಟ ಅಪಾಯದ ಮಾಹಿತಿಯನ್ನು ಬಳಸಿಕೊಂಡು ನಿರ್ಧಾರ ಮುಂದುವರಿಯುತ್ತದೆ.",
        "analysis_failed": "ಬೆಳೆ ವಿಶ್ಲೇಷಣೆ ವಿಫಲವಾಗಿದೆ.",

        "ai_decision": "🤖 AI ಕೃಷಿ ನಿರ್ಧಾರ",
        "crop": "🌱 ಬೆಳೆ",
        "testing_scenario": "🧪 ಪರೀಕ್ಷಾ ಪರಿಸ್ಥಿತಿ",
        "current_farm": "ಪ್ರಸ್ತುತ ಫಾರ್ಮ್ ಡೇಟಾ",
        "low_soil_high_rain": "ಕಡಿಮೆ ಮಣ್ಣು + ಹೆಚ್ಚಿನ ಮಳೆ",
        "low_soil_low_rain": "ಕಡಿಮೆ ಮಣ್ಣು + ಕಡಿಮೆ ಮಳೆ",
        "high_soil_high_rain": "ಹೆಚ್ಚಿನ ಮಣ್ಣು + ಹೆಚ್ಚಿನ ಮಳೆ",
        "high_pest_risk": "ಹೆಚ್ಚಿನ ಕೀಟ ಅಪಾಯ",
        "generate_decision": "🤖 AI ನಿರ್ಧಾರವನ್ನು ರಚಿಸಿ",
        "decision_conflict": "⚠️ ವಿರೋಧಾಭಾಸ: ",
        "no_conflict": "✅ ಯಾವುದೇ ದೊಡ್ಡ ವಿರೋಧಾಭಾಸ ಕಂಡುಬಂದಿಲ್ಲ.",
        "why_decision": "### 🧠 ಈ ನಿರ್ಧಾರ ಏಕೆ?",
        "evidence": "### 📊 ಸಾಕ್ಷ್ಯಗಳು",
        "conflict_detected": "ವಿರೋಧಾಭಾಸ ಕಂಡುಬಂದಿದೆ.",

        "decision_history": "🕘 ನಿರ್ಧಾರ ಇತಿಹಾಸ",
        "no_history": "📭 ಇನ್ನೂ ಯಾವುದೇ ನಿರ್ಧಾರ ದಾಖಲಾಗಿಲ್ಲ.",
        "total_decisions": "ಒಟ್ಟು ನಿರ್ಧಾರಗಳು",
        "conflicts": "ವಿರೋಧಾಭಾಸಗಳು",
        "high_priority": "ಹೆಚ್ಚಿನ ಆದ್ಯತೆ",
        "avg_confidence": "ಸರಾಸರಿ ವಿಶ್ವಾಸ",
        "clear_history": "🗑️ ನಿರ್ಧಾರ ಇತಿಹಾಸವನ್ನು ತೆರವುಗೊಳಿಸಿ",
        "history_cleared": "ನಿರ್ಧಾರ ಇತಿಹಾಸವನ್ನು ತೆರವುಗೊಳಿಸಲಾಗಿದೆ.",

        "fpo_intelligence": "📊 FPO ಫಾರ್ಮ್ ಬುದ್ಧಿಮತ್ತೆ",
        "recent_priority": "### 🚨 ಇತ್ತೀಚಿನ ಆದ್ಯತೆಯ ನಿರ್ಧಾರಗಳು",
        "crop_summary": "### 🌾 ಬೆಳೆವಾರು ಸಾರಾಂಶ",
        "no_priority": "ಹೆಚ್ಚಿನ ಅಥವಾ ಮಧ್ಯಮ ಆದ್ಯತೆಯ ದಾಖಲೆಗಳಿಲ್ಲ.",
        "no_farm_data": "ಇನ್ನೂ ಯಾವುದೇ ಕೃಷಿ ನಿರ್ಧಾರ ಡೇಟಾ ಲಭ್ಯವಿಲ್ಲ.",

        "plans_pricing": "💳 ಯೋಜನೆಗಳು ಮತ್ತು ಬೆಲೆ",
        "pricing_description":
            "ನಿಮಗೆ ಅಗತ್ಯವಿರುವ ಕೃಷಿ ನಿರ್ಧಾರ ಬುದ್ಧಿಮತ್ತೆಯ ಮಟ್ಟದ ಆಧಾರದ ಮೇಲೆ ಯೋಜನೆಯನ್ನು ಆಯ್ಕೆಮಾಡಿ.",
        "prototype_pricing":
            "💡 ಇವು AgriResolve AI ವ್ಯವಹಾರ ಮಾದರಿಗಾಗಿ ಪ್ರಸ್ತಾಪಿಸಲಾದ prototype ಬೆಲೆಗಳು.",
        "simple_scalable": "### 🌾 ಸರಳ ಮತ್ತು ವಿಸ್ತರಿಸಬಹುದಾದ ಬೆಲೆ",

        "individual_farmers": "🌱 ವೈಯಕ್ತಿಕ ರೈತರಿಗಾಗಿ",
        "farmer_free": "Farmer Free",
        "free_description": "ಕೃಷಿ ಪರಿಸ್ಥಿತಿಗಳನ್ನು ಅರ್ಥಮಾಡಿಕೊಳ್ಳಲು ಮೂಲಭೂತ ಸಾಧನಗಳು.",
        "start_free": "🚀 ಉಚಿತವಾಗಿ ಪ್ರಾರಂಭಿಸಿ",

        "recommended_farmers": "⭐ ರೈತರಿಗೆ ಶಿಫಾರಸು",
        "farmer_premium": "Farmer Premium",
        "premium_description":
            "ವೈಯಕ್ತಿಕ ಕೃಷಿ ನಿರ್ವಹಣೆಗಾಗಿ ಸುಧಾರಿತ ನಿರ್ಧಾರ ಸಹಾಯ.",
        "upgrade_premium": "⭐ Premium ಗೆ ಅಪ್‌ಗ್ರೇಡ್ ಮಾಡಿ",

        "organizations": "🏢 ಸಂಸ್ಥೆಗಳಿಗಾಗಿ",
        "fpo_organization": "FPO / ಸಂಸ್ಥೆ",
        "organization_description":
            "FPOಗಳು, ಕ್ಷೇತ್ರ ಅಧಿಕಾರಿಗಳು ಮತ್ತು Agritech ತಂಡಗಳಿಗಾಗಿ ಬಹು-ಫಾರ್ಮ್ ಬುದ್ಧಿಮತ್ತೆ.",
        "contact_fpo": "🏢 FPO ಸಂಪರ್ಕಿಸಿ",

        "per_month": "/ತಿಂಗಳು",
        "everything_free": "Freeನಲ್ಲಿರುವ ಎಲ್ಲಾ ವೈಶಿಷ್ಟ್ಯಗಳು",
        "ai_conflict": "AI ವಿರೋಧಾಭಾಸ ಪತ್ತೆ",
        "explainable": "ವಿವರಿಸಬಹುದಾದ ಶಿಫಾರಸುಗಳು",
        "pest_disease": "ಕೀಟ ಮತ್ತು ರೋಗ ವಿಶ್ಲೇಷಣೆ",
        "decision_history_feature": "ನಿರ್ಧಾರ ಇತಿಹಾಸ",
        "advanced_insights": "ಸುಧಾರಿತ ಕೃಷಿ ಬುದ್ಧಿಮತ್ತೆ",
        "farm_dashboard_feature": "ಫಾರ್ಮ್ ಡ್ಯಾಶ್‌ಬೋರ್ಡ್",
        "weather_information": "ಹವಾಮಾನ ಮಾಹಿತಿ",
        "soil_simulator": "ಮಣ್ಣು ಸಿಮ್ಯುಲೇಟರ್",
        "basic_crop": "ಮೂಲಭೂತ ಬೆಳೆ ಮೇಲ್ವಿಚಾರಣೆ",
        "advanced_ai": "ಸುಧಾರಿತ AI ಬುದ್ಧಿಮತ್ತೆ",
        "organization_analytics": "ಸಂಸ್ಥೆ ವಿಶ್ಲೇಷಣೆ",
        "multi_farm": "ಬಹು-ಫಾರ್ಮ್ ಮೇಲ್ವಿಚಾರಣೆ",
        "fpo_dashboard": "FPO ಬುದ್ಧಿಮತ್ತೆ ಡ್ಯಾಶ್‌ಬೋರ್ಡ್",
        "priority_identification": "ಆದ್ಯತೆಯ ಪ್ರಕರಣಗಳ ಗುರುತಿಸುವಿಕೆ",
        "crop_analytics": "ಬೆಳೆವಾರು ವಿಶ್ಲೇಷಣೆ",
        "organization_insights": "ಸಂಸ್ಥೆಯ ಮಟ್ಟದ ಬುದ್ಧಿಮತ್ತೆ",

        "payment_later":
            "Premium payment integration ಅನ್ನು ನಂತರ payment gateway ಮೂಲಕ ಸಂಪರ್ಕಿಸಬಹುದು.",
        "fpo_manual":
            "Hackathon prototypeಗಾಗಿ FPO onboarding ಅನ್ನು ಕೈಯಾರೆ ಮಾಡಬಹುದು. ನಂತರ contact ಮತ್ತು payment workflow ಸೇರಿಸಬಹುದು.",

        "feature_comparison": "### 📊 ವೈಶಿಷ್ಟ್ಯ ಹೋಲಿಕೆ",
        "business_model": "### 💡 AgriResolve AI ವ್ಯವಹಾರ ಮಾದರಿ",
        "b2c_title": "B2C — ರೈತರು",
        "b2c_text":
            "• ಉಚಿತ ಮೂಲಭೂತ ಪ್ರವೇಶ\n• Premium ನಿರ್ಧಾರ ಬುದ್ಧಿಮತ್ತೆ\n• ಕೈಗೆಟುಕುವ ಮಾಸಿಕ subscription\n• ಭವಿಷ್ಯದ ಮೊಬೈಲ್ ಅಪ್ಲಿಕೇಶನ್",
        "b2b_title": "B2B — ಸಂಸ್ಥೆಗಳು",
        "b2b_text":
            "• FPO subscriptions\n• ಕ್ಷೇತ್ರ ಅಧಿಕಾರಿ ಡ್ಯಾಶ್‌ಬೋರ್ಡ್‌ಗಳು\n• Agritech integrations\n• ಭವಿಷ್ಯದ API / Enterprise ಯೋಜನೆಗಳು",
        "business_success":
            "🌾 AgriResolve AI ರೈತರಿಗೆ ಬೆಂಬಲ ನೀಡುವುದರ ಜೊತೆಗೆ ಅನೇಕ ಫಾರ್ಮ್‌ಗಳ ಕೃಷಿ ನಿರ್ಧಾರಗಳನ್ನು ನಿರ್ವಹಿಸಲು ಸಂಸ್ಥೆಗಳಿಗೆ ಸಹಾಯ ಮಾಡುತ್ತದೆ.",

        "footer":
            "🌾 AgriResolve AI — ವಿವರಿಸಬಹುದಾದ ಕೃಷಿ ನಿರ್ಧಾರ ಬುದ್ಧಿಮತ್ತೆ ವೇದಿಕೆ",

        "weather_unavailable": "ಲೈವ್ ಹವಾಮಾನ ಲಭ್ಯವಿಲ್ಲ: ",
        "simulation": "ಸಿಮ್ಯುಲೇಶನ್",
        "basic": "ಮೂಲಭೂತ",
        "advanced": "ಸುಧಾರಿತ",
        "limited": "ಸೀಮಿತ",
        "multi_farm_value": "ಬಹು-ಫಾರ್ಮ್",
        "yes": "ಹೌದು",
        "no": "ಇಲ್ಲ",
        "not_available": "ಲಭ್ಯವಿಲ್ಲ",
        "no_explanation": "ವಿವರಣೆ ಲಭ್ಯವಿಲ್ಲ."
    }
}


def T(key):
    language = st.session_state.get(
        "language",
        "English"
    )

    return TRANSLATIONS.get(
        language,
        TRANSLATIONS["English"]
    ).get(
        key,
        TRANSLATIONS["English"].get(
            key,
            key
        )
    )


# =========================================================
# LOGIN / SIGN UP
# =========================================================

if not st.session_state.authenticated:

    st.markdown("# 🌾 AgriResolve AI")

    st.markdown(
        "### " + T("app_subtitle")
    )

    st.write(
        T("app_description")
    )

    login_tab, signup_tab = st.tabs(
        [
            T("login"),
            T("signup")
        ]
    )

    # =====================================================
    # LOGIN
    # =====================================================

    with login_tab:

        st.subheader(
            T("welcome_back")
        )

        email = st.text_input(
            T("email"),
            key="login_email"
        )

        password = st.text_input(
            T("password"),
            type="password",
            key="login_password"
        )

        if st.button(
            T("login_button"),
            type="primary",
            use_container_width=True,
            key="login_btn"
        ):

            if not email.strip() or not password:

                st.warning(
                    T("enter_credentials")
                )

            else:

                user = login_user(
                    email,
                    password
                )

                if user:

                    st.session_state.authenticated = True
                    st.session_state.user = user

                    st.rerun()

                else:

                    st.error(
                        T("invalid_login")
                    )

    # =====================================================
    # SIGN UP
    # =====================================================

    with signup_tab:

        st.subheader(
            T("create_account")
        )

        name = st.text_input(
            T("full_name"),
            key="signup_name"
        )

        email2 = st.text_input(
            T("email"),
            key="signup_email"
        )

        password2 = st.text_input(
            T("password"),
            type="password",
            key="signup_password"
        )

        confirm = st.text_input(
            T("confirm_password"),
            type="password",
            key="signup_confirm"
        )

        role = st.selectbox(
            T("role"),
            [
                T("farmer"),
                T("fpo_role"),
                T("agritech_role")
            ],
            key="signup_role"
        )

        role_map = {
            T("farmer"): "Farmer",
            T("fpo_role"): "FPO / Field Officer",
            T("agritech_role"): "Agritech Organization"
        }

        if st.button(
            T("create_account_button"),
            type="primary",
            use_container_width=True,
            key="signup_btn"
        ):

            if (
                not name.strip()
                or not email2.strip()
                or not password2
            ):

                st.warning(
                    T("fill_required")
                )

            elif len(password2) < 6:

                st.warning(
                    T("password_length")
                )

            elif password2 != confirm:

                st.error(
                    T("password_mismatch")
                )

            else:

                ok, message = create_user(
                    name,
                    email2,
                    password2,
                    role_map[role]
                )

                if ok:

                    st.success(
                        T("account_created")
                    )

                else:

                    st.error(message)

    st.stop()


# =========================================================
# CUSTOM CSS
# =========================================================

st.markdown(
    """
    <style>

    .hero {
        padding: 24px;
        border-radius: 18px;
        background: #edf7ed;
        border: 1px solid #d6ead6;
        margin-bottom: 18px;
    }

    .hero h1 {
        color: #1b5e20;
    }

    .card {
        padding: 18px;
        border-radius: 16px;
        background: white;
        border: 1px solid #dcebdd;
        margin-bottom: 12px;
    }

    .decision {
        padding: 20px;
        border-radius: 16px;
        background: #edf7ed;
        border-left: 6px solid #2e7d32;
        margin: 12px 0;
    }

    .pricing-card {
        padding: 28px;
        border-radius: 20px;
        border: 1px solid #dcebdd;
        background: white;
        min-height: 430px;
        box-shadow: 0 4px 14px rgba(0, 0, 0, 0.06);
    }

    .pricing-card h2 {
        color: #1b5e20;
    }

    .price {
        font-size: 32px;
        font-weight: 700;
        color: #2e7d32;
        margin: 12px 0;
    }

    .pricing-highlight {
        padding: 8px 14px;
        border-radius: 20px;
        background: #e8f5e9;
        color: #1b5e20;
        font-weight: 600;
        display: inline-block;
        margin-bottom: 10px;
    }

    .feature {
        margin: 10px 0;
    }

    </style>
    """,
    unsafe_allow_html=True
)


# =========================================================
# USER
# =========================================================

user = st.session_state.user


# =========================================================
# SIDEBAR
# =========================================================

st.sidebar.title(
    "🌾 AgriResolve AI"
)

st.sidebar.success(
    "👤 " + str(user["name"])
)

st.sidebar.caption(
    "📧 " + str(user["email"])
)

st.sidebar.caption(
    T("role_label") + str(
        user["role"]
    )
)


# =========================================================
# LOGOUT
# =========================================================

if st.sidebar.button(
    T("logout"),
    use_container_width=True,
    key="logout"
):

    st.session_state.authenticated = False
    st.session_state.user = None

    st.rerun()


st.sidebar.markdown("---")


# =========================================================
# LANGUAGE
# =========================================================

language_options = [
    "English",
    "Tamil",
    "Telugu",
    "Hindi",
    "Kannada"
]
if "language" not in st.session_state:
    st.session_state.language = "English"

language = st.sidebar.selectbox(
    T("language"),
    language_options,
    index=language_options.index(
        st.session_state.language
    ),
    key="language"
)


# =========================================================
# WEATHER MODE
# =========================================================

weather_mode_options = [
    "Live Weather",
    "Demo",
    "Testing"
]

weather_mode = st.sidebar.radio(
    T("weather_mode"),
    weather_mode_options,
    format_func=lambda x: {
        "Live Weather": T("live_weather"),
        "Demo": T("demo"),
        "Testing": T("testing")
    }[x],
    key="weather_mode"
)


# =========================================================
# NAVIGATION TRANSLATIONS
# =========================================================

NAV = {

    "English": [
        T("dashboard"),
        T("soil"),
        T("weather"),
        T("pest"),
        T("decision"),
        T("history"),
        T("fpo"),
        T("pricing")
    ],

    "Tamil": [
        T("dashboard"),
        T("soil"),
        T("weather"),
        T("pest"),
        T("decision"),
        T("history"),
        T("fpo"),
        T("pricing")
    ],

    "Telugu": [
        T("dashboard"),
        T("soil"),
        T("weather"),
        T("pest"),
        T("decision"),
        T("history"),
        T("fpo"),
        T("pricing")
    ],

    "Hindi": [
        T("dashboard"),
        T("soil"),
        T("weather"),
        T("pest"),
        T("decision"),
        T("history"),
        T("fpo"),
        T("pricing")
    ],

    "Kannada": [
        T("dashboard"),
        T("soil"),
        T("weather"),
        T("pest"),
        T("decision"),
        T("history"),
        T("fpo"),
        T("pricing")
    ]

}


nav = NAV[language]


# =========================================================
# NAVIGATION
# =========================================================

if "navigation_target" in st.session_state:

    target_page = st.session_state["navigation_target"]

    if target_page in nav:
        st.session_state["navigation"] = target_page

    del st.session_state["navigation_target"]


page = st.sidebar.radio(
    T("navigation"),
    nav,
    key="navigation"
)

page_index = nav.index(page)

current_page = [
    "dashboard",
    "soil",
    "weather",
    "pest",
    "decision",
    "history",
    "fpo",
    "pricing",
][page_index]

# =========================================================
# HEADER
# =========================================================

st.markdown(
    """
    <div class="hero">

        <h1>🌾 AgriResolve AI</h1>

        <p>
            <b>"""
    + T("app_subtitle")
    + """</b>
        </p>

        <p>
            """
    + T("app_description")
    + """
        </p>

    </div>
    """,
    unsafe_allow_html=True
)


# =========================================================
# CROPS
# =========================================================

CROPS = [

    "Rice",
    "Wheat",
    "Maize",
    "Sorghum",
    "Millet",
    "Barley",
    "Tomato",
    "Potato",
    "Brinjal",
    "Chilli",
    "Onion",
    "Cabbage",
    "Cauliflower",
    "Carrot",
    "Okra",
    "Groundnut",
    "Soybean",
    "Green Gram",
    "Black Gram",
    "Chickpea",
    "Cotton",
    "Sugarcane",
    "Banana",
    "Coconut",
    "Mango",
    "Grapes",
    "Other"

]


STAGES = [

    "Seedling",
    "Vegetative",
    "Flowering",
    "Fruiting",
    "Maturity"

]


# =========================================================
# DISPLAY TRANSLATIONS FOR CROPS
# =========================================================

CROP_TRANSLATIONS = {

    "English": {
        "Rice": "Rice",
        "Wheat": "Wheat",
        "Maize": "Maize",
        "Sorghum": "Sorghum",
        "Millet": "Millet",
        "Barley": "Barley",
        "Tomato": "Tomato",
        "Potato": "Potato",
        "Brinjal": "Brinjal",
        "Chilli": "Chilli",
        "Onion": "Onion",
        "Cabbage": "Cabbage",
        "Cauliflower": "Cauliflower",
        "Carrot": "Carrot",
        "Okra": "Okra",
        "Groundnut": "Groundnut",
        "Soybean": "Soybean",
        "Green Gram": "Green Gram",
        "Black Gram": "Black Gram",
        "Chickpea": "Chickpea",
        "Cotton": "Cotton",
        "Sugarcane": "Sugarcane",
        "Banana": "Banana",
        "Coconut": "Coconut",
        "Mango": "Mango",
        "Grapes": "Grapes",
        "Other": "Other"
    },

    "Tamil": {
        "Rice": "நெல்",
        "Wheat": "கோதுமை",
        "Maize": "மக்காச்சோளம்",
        "Sorghum": "சோளம்",
        "Millet": "சிறுதானியம்",
        "Barley": "பார்லி",
        "Tomato": "தக்காளி",
        "Potato": "உருளைக்கிழங்கு",
        "Brinjal": "கத்தரிக்காய்",
        "Chilli": "மிளகாய்",
        "Onion": "வெங்காயம்",
        "Cabbage": "முட்டைக்கோஸ்",
        "Cauliflower": "காலிஃபிளவர்",
        "Carrot": "கேரட்",
        "Okra": "வெண்டைக்காய்",
        "Groundnut": "நிலக்கடலை",
        "Soybean": "சோயாபீன்",
        "Green Gram": "பச்சைப்பயறு",
        "Black Gram": "உளுந்து",
        "Chickpea": "கொண்டைக்கடலை",
        "Cotton": "பருத்தி",
        "Sugarcane": "கரும்பு",
        "Banana": "வாழை",
        "Coconut": "தேங்காய்",
        "Mango": "மாம்பழம்",
        "Grapes": "திராட்சை",
        "Other": "மற்றவை"
    },

    "Telugu": {
        "Rice": "వరి",
        "Wheat": "గోధుమ",
        "Maize": "మొక్కజొన్న",
        "Sorghum": "జొన్న",
        "Millet": "సజ్జలు",
        "Barley": "బార్లీ",
        "Tomato": "టమాటా",
        "Potato": "బంగాళాదుంప",
        "Brinjal": "వంకాయ",
        "Chilli": "మిరపకాయ",
        "Onion": "ఉల్లిపాయ",
        "Cabbage": "క్యాబేజీ",
        "Cauliflower": "కాలీఫ్లవర్",
        "Carrot": "క్యారెట్",
        "Okra": "బెండకాయ",
        "Groundnut": "వేరుశెనగ",
        "Soybean": "సోయాబీన్",
        "Green Gram": "పెసరపప్పు",
        "Black Gram": "మినపప్పు",
        "Chickpea": "శనగ",
        "Cotton": "పత్తి",
        "Sugarcane": "చెరకు",
        "Banana": "అరటి",
        "Coconut": "కొబ్బరి",
        "Mango": "మామిడి",
        "Grapes": "ద్రాక్ష",
        "Other": "ఇతర"
    },

    "Hindi": {
        "Rice": "धान",
        "Wheat": "गेहूं",
        "Maize": "मक्का",
        "Sorghum": "ज्वार",
        "Millet": "बाजरा",
        "Barley": "जौ",
        "Tomato": "टमाटर",
        "Potato": "आलू",
        "Brinjal": "बैंगन",
        "Chilli": "मिर्च",
        "Onion": "प्याज",
        "Cabbage": "पत्तागोभी",
        "Cauliflower": "फूलगोभी",
        "Carrot": "गाजर",
        "Okra": "भिंडी",
        "Groundnut": "मूंगफली",
        "Soybean": "सोयाबीन",
        "Green Gram": "मूंग",
        "Black Gram": "उड़द",
        "Chickpea": "चना",
        "Cotton": "कपास",
        "Sugarcane": "गन्ना",
        "Banana": "केला",
        "Coconut": "नारियल",
        "Mango": "आम",
        "Grapes": "अंगूर",
        "Other": "अन्य"
    },

    "Kannada": {
        "Rice": "ಭತ್ತ",
        "Wheat": "ಗೋಧಿ",
        "Maize": "ಮೆಕ್ಕೆಜೋಳ",
        "Sorghum": "ಜೋಳ",
        "Millet": "ಸಿರಿಧಾನ್ಯ",
        "Barley": "ಬಾರ್ಲಿ",
        "Tomato": "ಟೊಮ್ಯಾಟೊ",
        "Potato": "ಆಲೂಗಡ್ಡೆ",
        "Brinjal": "ಬದನೆಕಾಯಿ",
        "Chilli": "ಮೆಣಸಿನಕಾಯಿ",
        "Onion": "ಈರುಳ್ಳಿ",
        "Cabbage": "ಎಲೆಕೋಸು",
        "Cauliflower": "ಹೂಕೋಸು",
        "Carrot": "ಕ್ಯಾರೆಟ್",
        "Okra": "ಬೆಂಡೆಕಾಯಿ",
        "Groundnut": "ಕಡಲೆಕಾಯಿ",
        "Soybean": "ಸೋಯಾಬೀನ್",
        "Green Gram": "ಹೆಸರುಕಾಳು",
        "Black Gram": "ಉದ್ದಿನಕಾಳು",
        "Chickpea": "ಕಡಲೆ",
        "Cotton": "ಹತ್ತಿ",
        "Sugarcane": "ಕಬ್ಬು",
        "Banana": "ಬಾಳೆಹಣ್ಣು",
        "Coconut": "ತೆಂಗಿನಕಾಯಿ",
        "Mango": "ಮಾವು",
        "Grapes": "ದ್ರಾಕ್ಷಿ",
        "Other": "ಇತರೆ"
    }

}


STAGE_TRANSLATIONS = {

    "English": {
        "Seedling": "Seedling",
        "Vegetative": "Vegetative",
        "Flowering": "Flowering",
        "Fruiting": "Fruiting",
        "Maturity": "Maturity"
    },

    "Tamil": {
        "Seedling": "நாற்று நிலை",
        "Vegetative": "வளர்ச்சி நிலை",
        "Flowering": "பூக்கும் நிலை",
        "Fruiting": "காய் / பழம் உருவாகும் நிலை",
        "Maturity": "முதிர்ச்சி நிலை"
    },

    "Telugu": {
        "Seedling": "మొలక దశ",
        "Vegetative": "వృద్ధి దశ",
        "Flowering": "పుష్పించే దశ",
        "Fruiting": "కాయలు/పండ్ల దశ",
        "Maturity": "పక్వ దశ"
    },

    "Hindi": {
        "Seedling": "अंकुर अवस्था",
        "Vegetative": "वानस्पतिक अवस्था",
        "Flowering": "फूल अवस्था",
        "Fruiting": "फल अवस्था",
        "Maturity": "परिपक्वता अवस्था"
    },

    "Kannada": {
        "Seedling": "ಸಸಿ ಹಂತ",
        "Vegetative": "ಬೆಳವಣಿಗೆ ಹಂತ",
        "Flowering": "ಹೂ ಬಿಡುವ ಹಂತ",
        "Fruiting": "ಹಣ್ಣು ಬಿಡುವ ಹಂತ",
        "Maturity": "ಪಕ್ವ ಹಂತ"
    }

}


def crop_label(crop):
    return CROP_TRANSLATIONS.get(
        language,
        CROP_TRANSLATIONS["English"]
    ).get(
        crop,
        crop
    )


def stage_label(stage):
    return STAGE_TRANSLATIONS.get(
        language,
        STAGE_TRANSLATIONS["English"]
    ).get(
        stage,
        stage
    )


# =========================================================
# DEMO WEATHER
# =========================================================

def demo_weather():

    return {

        "current": {
            "temperature_2m": 29,
            "relative_humidity_2m": 72,
            "precipitation": 0,
            "rain": 0,
            "wind_speed_10m": 12
        },

        "daily": {

            "time": [
                "Today",
                "Tomorrow",
                "Day 3",
                "Day 4",
                "Day 5",
                "Day 6",
                "Day 7"
            ],

            "precipitation_probability_max": [
                75,
                65,
                55,
                40,
                30,
                25,
                20
            ],

            "precipitation_sum": [
                4.2,
                3.1,
                2,
                1,
                0.5,
                0,
                0
            ],

            "temperature_2m_max": [
                31,
                30,
                30,
                31,
                32,
                32,
                33
            ],

            "temperature_2m_min": [
                24,
                24,
                23,
                24,
                24,
                25,
                25
            ]

        }

    }


# =========================================================
# TESTING WEATHER
# =========================================================

def testing_weather():

    return {

        "current": {
            "temperature_2m": 31,
            "relative_humidity_2m": 60,
            "precipitation": 0,
            "rain": 0,
            "wind_speed_10m": 10
        },

        "daily": {

            "time": [
                "Today",
                "Tomorrow",
                "Day 3",
                "Day 4",
                "Day 5",
                "Day 6",
                "Day 7"
            ],

            "precipitation_probability_max": [
                20,
                25,
                30,
                20,
                15,
                10,
                10
            ],

            "precipitation_sum": [
                0,
                0.5,
                1,
                0.2,
                0,
                0,
                0
            ],

            "temperature_2m_max": [
                32,
                33,
                33,
                34,
                34,
                35,
                35
            ],

            "temperature_2m_min": [
                24,
                24,
                25,
                25,
                25,
                26,
                26
            ]

        }

    }


# =========================================================
# LOAD WEATHER
# =========================================================

def load_weather():

    if weather_mode == "Demo":
        return demo_weather()

    if weather_mode == "Testing":
        return testing_weather()

    try:

        data = get_weather(
            st.session_state.latitude,
            st.session_state.longitude
        )

        st.session_state.weather_data = data

        return data

    except Exception as exc:

        st.warning(
            T("weather_unavailable")
            + str(exc)
        )

        return None


# =========================================================
# RAIN PROBABILITY
# =========================================================

def get_rain_probability():

    data = load_weather()

    if data:

        values = data.get(
            "daily",
            {}
        ).get(
            "precipitation_probability_max",
            [0]
        )

        rain = (
            values[0]
            if values
            else 0
        )

        st.session_state.rain_probability = rain

        return rain

    return st.session_state.rain_probability


# =========================================================
# SAVE DECISION
# =========================================================

def save_decision_record(
    crop,
    stage,
    soil,
    rain,
    pest,
    decision
):

    record = {

        "Date & Time":
            datetime.now().strftime(
                "%Y-%m-%d %H:%M:%S"
            ),

        "Crop":
            crop,

        "Growth Stage":
            stage,

        "Latitude":
            round(
                float(
                    st.session_state.latitude
                ),
                4
            ),

        "Longitude":
            round(
                float(
                    st.session_state.longitude
                ),
                4
            ),

        "Soil Moisture (%)":
            soil,

        "Rain Probability (%)":
            rain,

        "Pest Risk":
            pest,

        "Conflict":
            (
                "Yes"
                if decision.get(
                    "conflict_detected"
                )
                else "No"
            ),

        "Conflict Type":
            decision.get(
                "conflict_type",
                "No major conflict"
            ),

        "Recommended Action":
            decision.get(
                "recommendation",
                "N/A"
            ),

        "Priority":
            decision.get(
                "priority",
                "N/A"
            ),

        "Confidence (%)":
            decision.get(
                "confidence",
                0
            )

    }

    save_decision(record)


# =========================================================
# LOCATION
# =========================================================

def show_location():

    st.markdown(
        T("farm_location")
    )

    location = streamlit_geolocation()

    if location:

        latitude = location.get("latitude")
        longitude = location.get("longitude")

        if (
            latitude is not None
            and longitude is not None
        ):

            st.session_state.latitude = float(latitude)
            st.session_state.longitude = float(longitude)
            st.session_state.weather_data = None

            st.success(
                T("location_detected")
                + str(round(latitude, 4))
                + ", "
                + str(round(longitude, 4))
            )

    col1, col2 = st.columns(2)

    with col1:

        latitude = st.number_input(
            T("latitude"),
            min_value=-90.0,
            max_value=90.0,
            value=float(
                st.session_state.latitude
            ),
            step=0.0001,
            format="%.4f",
            key="manual_lat"
        )

    with col2:

        longitude = st.number_input(
            T("longitude"),
            min_value=-180.0,
            max_value=180.0,
            value=float(
                st.session_state.longitude
            ),
            step=0.0001,
            format="%.4f",
            key="manual_lon"
        )

    if st.button(
        T("update_location"),
        key="update_location"
    ):

        st.session_state.latitude = latitude
        st.session_state.longitude = longitude
        st.session_state.weather_data = None

        st.success(
            T("location_updated")
        )


# =========================================================
# FARM DASHBOARD
# =========================================================

if current_page == "dashboard":

    st.subheader(
        T("farm_dashboard")
    )

    show_location()

    col1, col2 = st.columns(2)

    display_crops = [
        crop_label(crop)
        for crop in CROPS
    ]

    with col1:

        selected_display_crop = st.selectbox(
            T("select_crop"),
            display_crops,
            index=CROPS.index(
                st.session_state.selected_crop
            ),
            key="dashboard_crop"
        )

        crop = CROPS[
            display_crops.index(
                selected_display_crop
            )
        ]

    display_stages = [
        stage_label(stage)
        for stage in STAGES
    ]

    with col2:

        selected_display_stage = st.selectbox(
            T("growth_stage"),
            display_stages,
            index=STAGES.index(
                st.session_state.crop_stage
            ),
            key="dashboard_stage"
        )

        stage = STAGES[
            display_stages.index(
                selected_display_stage
            )
        ]

    st.session_state.selected_crop = crop
    st.session_state.crop_stage = stage

    data = load_weather()

    current = (
        data.get(
            "current",
            {}
        )
        if data
        else {}
    )

    rain = st.session_state.rain_probability

    if data:

        probabilities = data.get(
            "daily",
            {}
        ).get(
            "precipitation_probability_max",
            [0]
        )

        rain = (
            probabilities[0]
            if probabilities
            else 0
        )

        st.session_state.rain_probability = rain

    soil = st.session_state.soil_moisture
    pest = st.session_state.pest_risk

    # -------------------- FARM STATUS CARDS --------------------

    st.markdown("### 📊 Farm Status")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            T("soil_moisture"),
            str(soil) + "%"
        )

    with col2:
        st.metric(
            T("rain_probability"),
            str(rain) + "%"
        )

    with col3:
        st.metric(
            T("pest_risk"),
            pest
        )

    with col4:
        st.metric(
            T("temperature"),
            str(
                current.get(
                    "temperature_2m",
                    "N/A"
                )
            ) + "°C"
        )


# -------------------- SOIL --------------------

elif current_page == "soil":

    st.subheader("🌱 Smart Soil Sensor & Calibration")

    st.info(
        "📡 Sensor readings are processed using multi-reading smoothing "
        "and calibration before AI decision-making."
    )

    # ---------------- SENSOR MODULE ----------------

    st.markdown("### 📡 Sensor Information")

    col1, col2 = st.columns(2)

    with col1:
        st.metric(
            "Sensor Module",
            "SM-001"
        )

    with col2:
        st.metric(
            "Sensor Accuracy",
            "92%"
        )
    # ---------------- RAW READINGS ----------------

    st.markdown("### 💧 Soil Moisture Readings")

    r1, r2, r3, r4, r5 = st.columns(5)

    with r1:
        reading1 = st.slider("Reading 1", 0, 100, 27, key="soil_r1")

    with r2:
        reading2 = st.slider("Reading 2", 0, 100, 28, key="soil_r2")

    with r3:
        reading3 = st.slider("Reading 3", 0, 100, 27, key="soil_r3")

    with r4:
        reading4 = st.slider("Reading 4", 0, 100, 29, key="soil_r4")

    with r5:
        reading5 = st.slider("Reading 5", 0, 100, 27, key="soil_r5")

    # ---------------- SMOOTHING ----------------

    readings = [
        reading1,
        reading2,
        reading3,
        reading4,
        reading5
    ]

    smoothed_moisture = smooth_sensor_readings(readings)

    # ---------------- CALIBRATION ----------------

    corrected_moisture, sensor_accuracy, correction = calibrate_soil_moisture(
        smoothed_moisture,
        "SM-001"
    )

    st.session_state.soil_moisture = corrected_moisture

    # ---------------- RESULTS ----------------

    st.markdown("### 🎯 Sensor Processing Result")

    c1, c2, c3, c4 = st.columns(4)

    with c1:
        st.metric(
            "📡 Raw Average",
            f"{smoothed_moisture}%"
        )

    with c2:
        st.metric(
            "🎯 Reference",
            "30%"
        )

    with c3:
        st.metric(
            "🔧 Correction",
            f"+{correction}%"
        )

    with c4:
        st.metric(
            "✅ Corrected Value",
            f"{corrected_moisture}%"
        )

    st.success(
        f"✅ Corrected soil moisture of {corrected_moisture}% "
        f"will be used by the AI decision system."
    )

    st.caption(
        f"Sensor Module: SM-001 • Calibration Accuracy: {sensor_accuracy}%"
    )

# ---------------- ESP32 STATUS ----------------
    
    st.subheader("🌱 Smart Soil IoT Monitor")

    if st.session_state.iot_running:
        st.success("🟢 ESP32 ONLINE • Virtual sensors transmitting live data")
    else:
        st.warning("🟡 ESP32 OFFLINE • Start the virtual sensor")

    st.markdown(
        """
        <div style="
            background: linear-gradient(135deg,#0b5d1e,#2e7d32);
            padding: 20px;
            border-radius: 18px;
            color: white;
            margin: 15px 0;
        ">
            <h2 style="margin:0;">📡 ESP32 Virtual Soil Sensor</h2>
            <p style="margin:8px 0 0;">
                Device ID: ESP32-AGRI-001 |
                Connection: Wi-Fi |
                Mode: Laptop Simulation
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # ---------------- START / STOP ----------------

    c1, c2 = st.columns(2)

    with c1:
        if st.button(
            "▶️ Start Live Sensor",
            use_container_width=True,
            key="start_virtual_sensor",
        ):
            st.session_state.iot_running = True
            st.rerun()

    with c2:
        if st.button(
            "⏹️ Stop Sensor",
            use_container_width=True,
            key="stop_virtual_sensor",
        ):
            st.session_state.iot_running = False
            st.rerun()

    # ---------------- AUTOMATIC SENSOR VALUES ----------------

    if st.session_state.iot_running:

        # Soil moisture
        st.session_state.soil_moisture = max(
            0,
            min(
                100,
                st.session_state.soil_moisture
                + random.uniform(-2.0, 2.0),
            ),
        )

        # Soil temperature
        st.session_state.soil_temperature = max(
            10,
            min(
                50,
                st.session_state.soil_temperature
                + random.uniform(-0.5, 0.5),
            ),
        )

        # Soil humidity
        st.session_state.soil_humidity = max(
            0,
            min(
                100,
                st.session_state.soil_humidity
                + random.uniform(-2.0, 2.0),
            ),
        )

        # Soil pH
        st.session_state.soil_ph = max(
            3.0,
            min(
                10.0,
                st.session_state.soil_ph
                + random.uniform(-0.08, 0.08),
            ),
        )

        # Nitrogen
        st.session_state.nitrogen = max(
            0,
            min(
                100,
                st.session_state.nitrogen
                + random.uniform(-3, 3),
            ),
        )

        # Phosphorus
        st.session_state.phosphorus = max(
            0,
            min(
                100,
                st.session_state.phosphorus
                + random.uniform(-3, 3),
            ),
        )

        # Potassium
        st.session_state.potassium = max(
            0,
            min(
                100,
                st.session_state.potassium
                + random.uniform(-3, 3),
            ),
        )

    # ---------------- LIVE READINGS ----------------

    st.markdown("### 📊 Live Sensor Readings")

    c1, c2, c3, c4 = st.columns(4)

    with c1:
        st.metric(
            "💧 Soil Moisture",
            f"{st.session_state.soil_moisture:.1f} %",
        )

    with c2:
        st.metric(
            "🌡️ Soil Temperature",
            f"{st.session_state.soil_temperature:.1f} °C",
        )

    with c3:
        st.metric(
            "💦 Soil Humidity",
            f"{st.session_state.soil_humidity:.1f} %",
        )

    with c4:
        st.metric(
            "🧪 Soil pH",
            f"{st.session_state.soil_ph:.2f}",
        )

    # ---------------- NPK ----------------

    st.markdown("### 🧬 Nutrient Sensor Data")

    n1, n2, n3 = st.columns(3)

    with n1:
        st.metric(
            "🌿 Nitrogen (N)",
            f"{st.session_state.nitrogen:.1f} ppm",
        )

    with n2:
        st.metric(
            "🌱 Phosphorus (P)",
            f"{st.session_state.phosphorus:.1f} ppm",
        )

    with n3:
        st.metric(
            "🌾 Potassium (K)",
            f"{st.session_state.potassium:.1f} ppm",
        )

    # ---------------- SENSOR CONDITION ----------------

    st.markdown("### 🔎 Sensor Analysis")

    moisture = st.session_state.soil_moisture

    if moisture < 30:
        st.error("🔴 Soil moisture is low — irrigation may be required.")
    elif moisture < 60:
        st.warning("🟡 Soil moisture is moderate — continue monitoring.")
    else:
        st.success("🟢 Soil moisture is adequate.")

    if st.session_state.iot_running:

        st.caption("🔄 Live virtual sensor data is updating...")

        # Automatically refresh approximately every 2 seconds
        import time
        time.sleep(2)
        st.rerun()
# =========================================================
# WEATHER
# =========================================================

elif current_page == "weather":

    st.subheader(
        T("weather_intelligence")
    )

    data = load_weather()

    if data:

        current = data.get(
            "current",
            {}
        )

        daily = data.get(
            "daily",
            {}
        )

        probabilities = daily.get(
            "precipitation_probability_max",
            [0]
        )

        rain = (
            probabilities[0]
            if probabilities
            else 0
        )

        st.session_state.rain_probability = rain

        col1, col2, col3, col4 = st.columns(4)

        with col1:

            st.metric(
                T("temperature"),
                str(
                    current.get(
                        "temperature_2m",
                        "N/A"
                    )
                )
                + " °C"
            )

        with col2:

            st.metric(
                T("humidity"),
                str(
                    current.get(
                        "relative_humidity_2m",
                        "N/A"
                    )
                )
                + "%"
            )

        with col3:

            st.metric(
                T("rain_probability"),
                str(rain)
                + "%"
            )

        with col4:

            st.metric(
                T("wind"),
                str(
                    current.get(
                        "wind_speed_10m",
                        "N/A"
                    )
                )
                + " km/h"
            )

        st.markdown(
            T("forecast")
        )

        dates = daily.get(
            "time",
            []
        )

        rainfall = daily.get(
            "precipitation_sum",
            []
        )

        highs = daily.get(
            "temperature_2m_max",
            []
        )

        lows = daily.get(
            "temperature_2m_min",
            []
        )

        for i, date in enumerate(dates):

            if (
                i >= len(probabilities)
                or i >= len(rainfall)
                or i >= len(highs)
                or i >= len(lows)
            ):

                break

            if i == 0:

                day = T("today")

            elif i == 1:

                day = T("tomorrow")

            else:

                day = date

            st.write(
                "**"
                + str(day)
                + "** — "
                + str(highs[i])
                + "°C / "
                + str(lows[i])
                + "°C | "
                + T("rain")
                + " "
                + str(probabilities[i])
                + "% | "
                + str(rainfall[i])
                + " mm"
            )


# =========================================================
# PEST & DISEASE
# =========================================================

elif current_page == "pest":

    st.subheader(
        T("pest_analysis")
    )

    display_crops = [
        crop_label(crop)
        for crop in CROPS
    ]

    selected_display_crop = st.selectbox(
        T("select_crop"),
        display_crops,
        key="pest_crop"
    )

    crop = CROPS[
        display_crops.index(
            selected_display_crop
        )
    ]

    uploaded = st.file_uploader(
        T("upload_image"),
        type=[
            "jpg",
            "jpeg",
            "png"
        ],
        key="plant_image"
    )

    if uploaded:

        image = Image.open(
            uploaded
        )

        st.image(
            image,
            caption=T("uploaded_image"),
            width=400
        )

        if st.button(
            T("analyze_image"),
            type="primary",
            key="analyze_button"
        ):

            with st.spinner(
                T("analyzing")
            ):

                result = analyze_plant(
                    uploaded.getvalue(),
                    crop.lower()
                )

            if result.get("success"):

                st.session_state.plant_analysis = result
                st.session_state.pest_risk = "Medium"

                st.success(
                    T("analysis_completed")
                )

                st.json(
                    result.get(
                        "data",
                        {}
                    )
                )

            elif result.get("unsupported_crop"):

                st.warning(
                    T("diagnosis_unavailable")
                    + crop_label(crop)
                )

                st.info(
                    T("decision_continue")
                )

            else:

                st.error(
                    result.get(
                        "error",
                        T("analysis_failed")
                    )
                )


# =========================================================
# AI DECISION
# =========================================================

elif current_page == "decision":

    st.subheader(
        T("ai_decision")
    )

    display_crops = [
        crop_label(crop)
        for crop in CROPS
    ]

    selected_display_crop = st.selectbox(
        T("crop"),
        display_crops,
        index=CROPS.index(
            st.session_state.selected_crop
        ),
        key="decision_crop"
    )

    crop = CROPS[
        display_crops.index(
            selected_display_crop
        )
    ]

    display_stages = [
        stage_label(stage)
        for stage in STAGES
    ]

    selected_display_stage = st.selectbox(
        T("growth_stage"),
        display_stages,
        index=STAGES.index(
            st.session_state.crop_stage
        ),
        key="decision_stage"
    )

    stage = STAGES[
        display_stages.index(
            selected_display_stage
        )
    ]

    rain = get_rain_probability()

    pest_options = [
        "Low",
        "Medium",
        "High"
    ]

    pest = st.selectbox(
        T("pest_risk"),
        pest_options,
        index=pest_options.index(
            st.session_state.pest_risk
        ),
        key="decision_pest"
    )

    st.session_state.selected_crop = crop
    st.session_state.crop_stage = stage
    st.session_state.pest_risk = pest

    col1, col2, col3 = st.columns(3)

    with col1:

        st.metric(
            T("soil_moisture"),
            str(
                st.session_state.soil_moisture
            )
            + "%"
        )

    with col2:

        st.metric(
            T("rain_probability"),
            str(rain)
            + "%"
        )

    with col3:

        st.metric(
            T("pest_risk"),
            pest
        )

    scenario_labels = [
        T("current_farm"),
        T("low_soil_high_rain"),
        T("low_soil_low_rain"),
        T("high_soil_high_rain"),
        T("high_pest_risk")
    ]

    scenario = st.selectbox(
        T("testing_scenario"),
        scenario_labels,
        key="scenario"
    )

    scenario_map = {
        T("current_farm"): "Current Farm Data",
        T("low_soil_high_rain"): "Low Soil + High Rain",
        T("low_soil_low_rain"): "Low Soil + Low Rain",
        T("high_soil_high_rain"): "High Soil + High Rain",
        T("high_pest_risk"): "High Pest Risk"
    }

    scenario_internal = scenario_map[scenario]

    soil = st.session_state.soil_moisture
    pest = st.session_state.pest_risk
    rain_value = rain
    pest_value = pest

    if scenario_internal == "Low Soil + High Rain":

        soil = 25
        rain_value = 80
        pest_value = "Low"

    elif scenario_internal == "Low Soil + Low Rain":

        soil = 20
        rain_value = 20
        pest_value = "Low"

    elif scenario_internal == "High Soil + High Rain":

        soil = 75
        rain_value = 80
        pest_value = "Low"

    elif scenario_internal == "High Pest Risk":

        pest_value = "High"

    if st.button(
        T("generate_decision"),
        type="primary",
        key="generate_decision"
    ):

        decision = resolve_conflict(
            soil,
            rain_value,
            pest_value,
            stage
        )

        save_decision_record(
            crop,
            stage,
            soil,
            rain_value,
            pest_value,
            decision
        )

        if decision.get(
            "conflict_detected"
        ):

            st.warning(
                T("decision_conflict")
                + str(
                    decision.get(
                        "conflict_type",
                        T("conflict_detected")
                    )
                )
            )

        else:

            st.success(
                T("no_conflict")
            )

        st.markdown(
            "<div class='decision'>"
            "<h3>"
            + T("recommended_action")
            + "</h3>"
            "<p>"
            + str(
                decision.get(
                    "recommendation",
                    T("not_available")
                )
            )
            + "</p>"
            "</div>",
            unsafe_allow_html=True
        )

        col1, col2 = st.columns(2)

        with col1:

            st.metric(
                T("priority"),
                decision.get(
                    "priority",
                    T("not_available")
                )
            )

        with col2:

            st.metric(
                T("confidence"),
                str(
                    decision.get(
                        "confidence",
                        0
                    )
                )
                + "%"
            )

        st.markdown(
            T("why_decision")
        )

        st.write(
            decision.get(
                "decision_reason",
                T("no_explanation")
            )
        )

        st.markdown(
            T("evidence")
        )

        for item in decision.get(
            "evidence",
            []
        ):

            st.write(
                "• "
                + str(item)
            )

        for warning in decision.get(
            "warnings",
            []
        ):

            st.warning(
                str(warning)
            )
# =========================================================
# DECISION HISTORY
# =========================================================

elif current_page == "history":

    st.subheader(
        T("decision_history")
    )

    history = get_all_decisions()

    if not history:

        st.info(
            T("no_history")
        )

    else:

        total = len(history)

        conflicts = sum(
            1
            for record in history
            if record.get(
                "Conflict"
            ) == "Yes"
        )

        high = sum(
            1
            for record in history
            if record.get(
                "Priority"
            ) == "High"
        )

        confidences = [
            float(
                record.get(
                    "Confidence (%)",
                    0
                )
            )
            for record in history
        ]

        average = (
            sum(confidences)
            / len(confidences)
            if confidences
            else 0
        )

        col1, col2, col3, col4 = st.columns(4)

        with col1:

            st.metric(
                T("total_decisions"),
                total
            )

        with col2:

            st.metric(
                T("conflicts"),
                conflicts
            )

        with col3:

            st.metric(
                T("high_priority"),
                high
            )

        with col4:

            st.metric(
                T("avg_confidence"),
                "%.1f%%" % average
            )

        history_display = []

        for record in history:

            translated_record = record.copy()

            translated_record[
                "Crop"
            ] = crop_label(
                record.get(
                    "Crop",
                    "Other"
                )
            )

            translated_record[
                "Growth Stage"
            ] = stage_label(
                record.get(
                    "Growth Stage",
                    "Vegetative"
                )
            )

            history_display.append(
                translated_record
            )

        st.dataframe(
            history_display,
            use_container_width=True,
            hide_index=True
        )

        if st.button(
            T("clear_history"),
            key="clear_history"
        ):

            clear_all_decisions()

            st.success(
                T("history_cleared")
            )

            st.rerun()


# =========================================================
# FPO INSIGHTS
# =========================================================


elif current_page == "fpo":

    if st.session_state.get("access_role") != "FPO":

        st.warning("🔒 FPO / Business access required.")

        st.info(
            "Please activate FPO / Business access from Plans & Pricing."
        )

    if st.button(
        "💳 Go to Plans & Pricing",
        use_container_width=True,
        key="go_to_pricing"
    ):
        st.session_state["navigation_target"] = "💳 Plans & Pricing"
        st.rerun()

        st.stop()

    st.subheader("📊 FPO Farm Intelligence")    

    st.subheader(
        T("fpo_intelligence")
    )

    records = get_all_decisions()

    total = len(records)

    conflicts = sum(
        1
        for record in records
        if record.get(
            "Conflict"
        ) == "Yes"
    )

    high = sum(
        1
        for record in records
        if record.get(
            "Priority"
        ) == "High"
    )

    confidences = [
        float(
            record.get(
                "Confidence (%)",
                0
            )
        )
        for record in records
    ]

    average = (
        sum(confidences)
        / len(confidences)
        if confidences
        else 0
    )

    col1, col2, col3, col4 = st.columns(4)

    with col1:

        st.metric(
            T("total_decisions"),
            total
        )

    with col2:

        st.metric(
            T("high_priority"),
            high
        )

    with col3:

        st.metric(
            T("conflicts"),
            conflicts
        )

    with col4:

        st.metric(
            T("avg_confidence"),
            "%.1f%%" % average
        )

    if records:

        st.markdown(
            T("recent_priority")
        )

        priority = [
            record
            for record in records
            if record.get(
                "Priority"
            )
            in [
                "High",
                "Medium"
            ]
        ]

        if priority:

            priority_display = []

            for record in priority[:10]:

                translated_record = record.copy()

                translated_record[
                    "Crop"
                ] = crop_label(
                    record.get(
                        "Crop",
                        "Other"
                    )
                )

                translated_record[
                    "Growth Stage"
                ] = stage_label(
                    record.get(
                        "Growth Stage",
                        "Vegetative"
                    )
                )

                priority_display.append(
                    translated_record
                )

            st.dataframe(
                priority_display,
                use_container_width=True,
                hide_index=True
            )

        else:

            st.success(
                T("no_priority")
            )

        st.markdown(
            T("crop_summary")
        )

        summary = {}

        for record in records:

            crop = record.get(
                "Crop",
                "Unknown"
            )

            if crop not in summary:

                summary[crop] = {

                    "Crop": crop_label(crop),
                    "Decisions": 0,
                    "Conflicts": 0,
                    "High Priority": 0

                }

            summary[crop]["Decisions"] += 1

            if record.get(
                "Conflict"
            ) == "Yes":

                summary[crop]["Conflicts"] += 1

            if record.get(
                "Priority"
            ) == "High":

                summary[crop]["High Priority"] += 1

        st.dataframe(
            list(
                summary.values()
            ),
            use_container_width=True,
            hide_index=True
        )

    else:

        st.info(
            T("no_farm_data")
        )


# =========================================================
# PLANS & PRICING
# =========================================================

elif current_page == "pricing":

    st.subheader(
        T("plans_pricing")
    )

    st.write(
        T("pricing_description")
    )

    st.info(
        T("prototype_pricing")
    )

    st.markdown(
        T("simple_scalable")
    )

    plan1, plan2, plan3 = st.columns(3)

    # =====================================================
    # FREE PLAN
    # =====================================================

    with plan1:

        st.markdown(
            """
            <div class="pricing-card">

                <div class="pricing-highlight">
                    """
            + T("individual_farmers")
            + """
                </div>

                <h2>"""
            + T("farmer_free")
            + """</h2>

                <div class="price">
                    ₹0
                    <small>"""
            + T("per_month")
            + """</small>
                </div>

                <p>"""
            + T("free_description")
            + """</p>

                <hr>

                <div class="feature">✅ """
            + T("farm_dashboard_feature")
            + """</div>

                <div class="feature">✅ """
            + T("weather_information")
            + """</div>

                <div class="feature">✅ """
            + T("soil_simulator")
            + """</div>

                <div class="feature">✅ """
            + T("basic_crop")
            + """</div>

                <div class="feature">❌ """
            + T("advanced_ai")
            + """</div>

                <div class="feature">❌ """
            + T("organization_analytics")
            + """</div>

            </div>
            """,
            unsafe_allow_html=True
        )

        st.button(
            T("start_free"),
            use_container_width=True,
            key="free_plan"
        )

    # =====================================================
    # PREMIUM PLAN
    # =====================================================

    with plan2:

        st.markdown(
            """
            <div class="pricing-card">

                <div class="pricing-highlight">
                    """
            + T("recommended_farmers")
            + """
                </div>

                <h2>"""
            + T("farmer_premium")
            + """</h2>

                <div class="price">
                    ₹99
                    <small>"""
            + T("per_month")
            + """</small>
                </div>

                <p>"""
            + T("premium_description")
            + """</p>

                <hr>

                <div class="feature">✅ """
            + T("everything_free")
            + """</div>

                <div class="feature">✅ """
            + T("ai_conflict")
            + """</div>

                <div class="feature">✅ """
            + T("explainable")
            + """</div>

                <div class="feature">✅ """
            + T("pest_disease")
            + """</div>

                <div class="feature">✅ """
            + T("decision_history_feature")
            + """</div>

                <div class="feature">✅ """
            + T("advanced_insights")
            + """</div>

            </div>
            """,
            unsafe_allow_html=True
        )

        if st.button(
            T("upgrade_premium"),
            use_container_width=True,
            key="premium_plan"
        ):
            st.session_state["payment_demo"] = True

        if st.session_state.get("payment_demo", False):

            st.markdown("### 💳 Demo Payment")

            st.info(
                "This is a prototype payment flow for demonstration. "
                "No real money will be charged."
            )

            st.write("**Premium Subscription**")
            st.write("Amount: **₹99 / month**")

            if st.button(
                "💳 Pay ₹99 (Demo)",
                use_container_width=True,
                key="demo_pay_99"
            ):
                st.session_state["subscription"] = "Premium"
                st.session_state["payment_demo"] = False

                st.success("✅ Payment Successful!")
                st.success("🎉 Premium Subscription Activated!")

    # =====================================================
    # FPO PLAN
    # =====================================================

    with plan3:

        
        if st.button(
            "🏢 Enter FPO / Business Access",
            use_container_width=True,
            key="fpo_plan"
        ):
            st.session_state["show_fpo_access"] = True

        if st.session_state.get("show_fpo_access", False):

            st.markdown("### 🔐 FPO / Business Access")

            st.info(
                "Demo access for FPO and agricultural organizations. "
                "No real payment is required."
            )

            fpo_code = st.text_input(
                "Enter FPO Access Code",
                type="password",
                key="fpo_access_code"
            )

            if st.button(
                "🚜 Access FPO Dashboard",
                use_container_width=True,
                key="fpo_dashboard_login"
            ):

                if fpo_code == "FPO2026":

                    st.session_state["access_role"] = "FPO"
                    st.session_state["subscription"] = "FPO"
                    st.session_state["show_fpo_access"] = False

                    st.success(
                        "✅ FPO / Business access activated!"
                    )

                else:

                    st.error(
                        "❌ Invalid FPO access code."
                    )

    st.markdown("---")

    st.markdown(
        T("feature_comparison")
    )

    comparison = [

        {
            "Feature": T("farm_dashboard_feature"),
            "Farmer Free": "✅",
            "Farmer Premium": "✅",
            "FPO / Organization": "✅"
        },

        {
            "Feature": T("weather_information"),
            "Farmer Free": "✅",
            "Farmer Premium": "✅",
            "FPO / Organization": "✅"
        },

        {
            "Feature": T("soil_simulator"),
            "Farmer Free": T("basic"),
            "Farmer Premium": T("advanced"),
            "FPO / Organization": T("multi_farm_value")
        },

        {
            "Feature": T("ai_conflict"),
            "Farmer Free": "—",
            "Farmer Premium": "✅",
            "FPO / Organization": "✅"
        },

        {
            "Feature": T("pest_disease"),
            "Farmer Free": T("basic"),
            "Farmer Premium": "✅",
            "FPO / Organization": "✅"
        },

        {
            "Feature": T("decision_history_feature"),
            "Farmer Free": T("limited"),
            "Farmer Premium": "✅",
            "FPO / Organization": "✅"
        },

        {
            "Feature": T("fpo_dashboard"),
            "Farmer Free": "—",
            "Farmer Premium": "—",
            "FPO / Organization": "✅"
        }

    ]

    st.dataframe(
        comparison,
        use_container_width=True,
        hide_index=True
    )

    st.markdown("---")

    st.markdown(
        T("business_model")
    )

    business_col1, business_col2 = st.columns(2)

    with business_col1:

        st.markdown(
            "**"
            + T("b2c_title")
            + "**\n\n"
            + T("b2c_text")
        )

    with business_col2:

        st.markdown(
            "**"
            + T("b2b_title")
            + "**\n\n"
            + T("b2b_text")
        )

    st.success(
        T("business_success")
    )


# =========================================================
# FOOTER
# =========================================================

st.markdown("---")

st.caption(
    T("footer")
)               
