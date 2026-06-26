import streamlit as st
import requests
import pandas as pd
import time
from datetime import datetime, timedelta
import pytz
import json
import tempfile
import os
import re

# ========== VOICE GENERATION (gTTS) ==========
try:
    from gtts import gTTS
    VOICE_AVAILABLE = True
except ImportError:
    VOICE_AVAILABLE = False

def generate_audio(text, lang_code="en"):
    """Generate audio from text using gTTS"""
    if not VOICE_AVAILABLE or not text.strip():
        return None
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as tmp:
            tmp_path = tmp.name
        tts = gTTS(text=text, lang=lang_code, slow=False)
        tts.save(tmp_path)
        with open(tmp_path, "rb") as f:
            audio_bytes = f.read()
        os.unlink(tmp_path)
        return audio_bytes
    except Exception as e:
        return None

# ========== PAGE CONFIG ==========
st.set_page_config(
    page_title="GlobalInternet.py | Weather Station Haiti",
    layout="wide",
    page_icon="🌤️"
)

# ========== CUSTOM CSS – DARK THEME WITH BRIGHT WEATHER CARDS ==========
st.markdown("""
<style>
    .stApp {
        background: #0a0a0f;
        background-image: 
            radial-gradient(circle at 20% 30%, rgba(60, 80, 120, 0.15) 0%, transparent 25%),
            radial-gradient(circle at 70% 60%, rgba(60, 80, 120, 0.10) 0%, transparent 35%),
            radial-gradient(circle at 40% 80%, rgba(80, 100, 150, 0.12) 0%, transparent 30%),
            radial-gradient(circle at 85% 20%, rgba(40, 60, 100, 0.08) 0%, transparent 40%);
        color: #ffffff;
    }
    [data-testid="stSidebar"] {
        background: #0d0d12;
        background-image: 
            radial-gradient(circle at 30% 40%, rgba(70, 90, 130, 0.12) 0%, transparent 30%),
            radial-gradient(circle at 70% 70%, rgba(50, 70, 100, 0.08) 0%, transparent 35%);
        border-right: 1px solid #2a2a3a;
    }
    [data-testid="stSidebar"] .stMarkdown,
    [data-testid="stSidebar"] label,
    [data-testid="stSidebar"] .stCaption {
        color: #ffffff !important;
    }
    h1, h2, h3, h4, h5, h6, p, li, .stMarkdown, .stCaption, label {
        color: #ffffff !important;
    }
    .weather-card {
        background: rgba(20, 30, 50, 0.7);
        border: 1px solid #2a3a5a;
        border-radius: 16px;
        padding: 20px;
        margin: 10px 0;
        text-align: center;
        backdrop-filter: blur(5px);
        transition: transform 0.3s, box-shadow 0.3s;
        height: 100%;
    }
    .weather-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 8px 30px rgba(50, 150, 255, 0.15);
        border-color: #4a8aff;
    }
    .weather-card .temp {
        font-size: 3rem;
        font-weight: bold;
        color: #00d4ff;
        margin: 5px 0;
    }
    .weather-card .city {
        font-size: 1.2rem;
        font-weight: 600;
        color: #ffffff;
        margin-bottom: 5px;
    }
    .weather-card .dept {
        font-size: 0.85rem;
        color: #8899bb;
        margin-bottom: 8px;
    }
    .weather-card .weather-icon {
        font-size: 3.5rem;
        margin: 5px 0;
    }
    .weather-card .details {
        display: flex;
        justify-content: center;
        gap: 15px;
        flex-wrap: wrap;
        font-size: 0.85rem;
        color: #aabbdd;
        margin-top: 8px;
    }
    .weather-card .details span {
        background: rgba(255,255,255,0.05);
        padding: 3px 10px;
        border-radius: 12px;
        border: 1px solid #2a3a5a;
    }
    .main-header {
        text-align: center;
        padding: 20px 0;
        border-bottom: 2px solid #2a3a5a;
        margin-bottom: 30px;
    }
    .main-header h1 {
        color: #00d4ff;
        font-size: 2.8rem;
        margin: 0;
        text-shadow: 0 0 30px rgba(0, 212, 255, 0.2);
    }
    .main-header p {
        color: #8899bb;
        font-size: 1.1rem;
    }
    .main-header .live-badge {
        display: inline-block;
        background: #00ff64;
        color: #0a0a0f;
        padding: 4px 16px;
        border-radius: 20px;
        font-size: 0.8rem;
        font-weight: bold;
        animation: pulse 2s infinite;
        margin-top: 5px;
    }
    @keyframes pulse {
        0% { opacity: 1; }
        50% { opacity: 0.5; }
        100% { opacity: 1; }
    }
    .footer {
        text-align: center;
        padding: 20px 0;
        border-top: 1px solid #2a3a5a;
        margin-top: 30px;
        color: #667799;
        font-size: 0.9rem;
    }
    .stButton>button {
        background: linear-gradient(135deg, #00d4ff, #0088ff) !important;
        color: #0a0a0f !important;
        border: none !important;
        border-radius: 8px !important;
        font-weight: 600 !important;
        padding: 10px 20px !important;
        width: 100% !important;
    }
    .stButton>button:hover {
        transform: scale(1.02);
        box-shadow: 0 0 30px rgba(0, 212, 255, 0.3);
    }
    .status-badge {
        padding: 4px 12px;
        border-radius: 12px;
        font-size: 0.8rem;
        font-weight: bold;
        display: inline-block;
        margin-bottom: 4px;
    }
    .status-live {
        background: #2ecc71;
        color: #0a0a0f;
    }
    .status-cached {
        background: #f39c12;
        color: #0a0a0f;
    }
    .status-error {
        background: #e74c3c;
        color: #ffffff;
    }
    .sidebar-contact {
        background: rgba(20,30,50,0.8);
        border: 1px solid #2a3a5a;
        border-radius: 8px;
        padding: 12px;
        margin: 10px 0;
        font-size: 0.85rem;
    }
    .sidebar-contact strong {
        color: #00d4ff;
    }
    .summary-box {
        background: rgba(0, 212, 255, 0.05);
        border: 1px solid #00d4ff;
        border-radius: 12px;
        padding: 15px 20px;
        margin: 10px 0;
        color: #ffffff;
    }
    .summary-box strong {
        color: #00d4ff;
    }
    .alert-box {
        background: rgba(255, 193, 7, 0.1);
        border-left: 4px solid #ffc107;
        padding: 10px 15px;
        border-radius: 4px;
        margin: 10px 0;
        color: #ffffff;
    }
    /* Profile image styling */
    .profile-img {
        width: 120px;
        height: 120px;
        border-radius: 50%;
        object-fit: cover;
        border: 2px solid #00d4ff;
        display: block;
        margin: 0 auto 8px auto;
    }
    .profile-name {
        color: #ffffff;
        text-align: center;
        margin-top: 8px;
        margin-bottom: 0;
        font-size: 1.2rem;
    }
    .profile-title {
        color: #8899bb;
        text-align: center;
        font-size: 0.9rem;
        margin-top: 0;
    }
</style>
""", unsafe_allow_html=True)

# ========== HAITI DEPARTMENTS ==========
HAITI_DEPARTMENTS = [
    {"name": "Artibonite", "city": "Gonaïves", "lat": 19.45, "lon": -72.68},
    {"name": "Centre", "city": "Hinche", "lat": 19.15, "lon": -72.00},
    {"name": "Grand'Anse", "city": "Jérémie", "lat": 18.65, "lon": -74.12},
    {"name": "Nippes", "city": "Miragoâne", "lat": 18.45, "lon": -73.10},
    {"name": "Nord", "city": "Cap-Haïtien", "lat": 19.76, "lon": -72.20},
    {"name": "Nord-Est", "city": "Fort-Liberté", "lat": 19.67, "lon": -71.84},
    {"name": "Nord-Ouest", "city": "Port-de-Paix", "lat": 19.95, "lon": -72.83},
    {"name": "Ouest", "city": "Port-au-Prince", "lat": 18.54, "lon": -72.34},
    {"name": "Sud-Est", "city": "Jacmel", "lat": 18.23, "lon": -72.54},
    {"name": "Sud", "city": "Les Cayes", "lat": 18.20, "lon": -73.75},
]

# ========== WEATHER ICON MAPPING ==========
def get_weather_icon(weather_code):
    """Map Open-Meteo weather code to emoji"""
    icons = {
        0: "☀️", 1: "🌤️", 2: "⛅", 3: "☁️",
        45: "🌫️", 48: "🌫️",
        51: "🌧️", 53: "🌧️", 55: "🌧️",
        61: "🌧️", 63: "🌧️", 65: "🌧️",
        71: "❄️", 73: "❄️", 75: "❄️",
        80: "🌦️", 81: "🌦️", 82: "🌦️",
        95: "⛈️", 96: "⛈️", 99: "⛈️"
    }
    return icons.get(weather_code, "🌤️")

def get_weather_description(weather_code):
    """Get weather description from code"""
    desc = {
        0: "Clear sky", 1: "Mainly clear", 2: "Partly cloudy", 3: "Overcast",
        45: "Fog", 48: "Depositing rime fog",
        51: "Light drizzle", 53: "Moderate drizzle", 55: "Dense drizzle",
        61: "Slight rain", 63: "Moderate rain", 65: "Heavy rain",
        71: "Slight snow", 73: "Moderate snow", 75: "Heavy snow",
        80: "Slight rain showers", 81: "Moderate rain showers", 82: "Violent rain showers",
        95: "Thunderstorm", 96: "Thunderstorm with hail", 99: "Thunderstorm with heavy hail"
    }
    return desc.get(weather_code, "Unknown")

# ========== WEATHER DATA FETCH ==========
@st.cache_data(ttl=900)  # Cache for 15 minutes
def fetch_weather_data():
    """Fetch weather data for all 10 departments from Open-Meteo"""
    results = []
    haiti_tz = pytz.timezone('America/Port-au-Prince')
    now = datetime.now(haiti_tz)
    
    for dept in HAITI_DEPARTMENTS:
        url = f"https://api.open-meteo.com/v1/forecast"
        params = {
            "latitude": dept["lat"],
            "longitude": dept["lon"],
            "current": ["temperature_2m", "relative_humidity_2m", "apparent_temperature", 
                        "precipitation", "weather_code", "wind_speed_10m", 
                        "pressure_msl", "uv_index"],
            "timezone": "America/Port-au-Prince",
            "forecast_days": 1
        }
        try:
            response = requests.get(url, params=params, timeout=10)
            if response.status_code == 200:
                data = response.json()
                current = data.get("current", {})
                results.append({
                    "department": dept["name"],
                    "city": dept["city"],
                    "lat": dept["lat"],
                    "lon": dept["lon"],
                    "temperature": current.get("temperature_2m", "N/A"),
                    "feels_like": current.get("apparent_temperature", "N/A"),
                    "humidity": current.get("relative_humidity_2m", "N/A"),
                    "precipitation": current.get("precipitation", 0),
                    "wind_speed": current.get("wind_speed_10m", "N/A"),
                    "pressure": current.get("pressure_msl", "N/A"),
                    "uv_index": current.get("uv_index", "N/A"),
                    "weather_code": current.get("weather_code", 0),
                    "timestamp": now.strftime("%Y-%m-%d %I:%M:%S %p"),
                    "status": "success"
                })
            else:
                results.append({
                    "department": dept["name"],
                    "city": dept["city"],
                    "lat": dept["lat"],
                    "lon": dept["lon"],
                    "status": "error",
                    "error": f"HTTP {response.status_code}"
                })
        except Exception as e:
            results.append({
                "department": dept["name"],
                "city": dept["city"],
                "lat": dept["lat"],
                "lon": dept["lon"],
                "status": "error",
                "error": str(e)
            })
        time.sleep(0.2)  # Rate limit protection
    
    return results, now.strftime("%Y-%m-%d %I:%M:%S %p")

# ========== GENERATE VOICE SCRIPT ==========
def generate_weather_voice_script(weather_data):
    """Generate a voice script summarizing the weather"""
    if not weather_data:
        return "No weather data available at this time."
    
    script = "Welcome to GlobalInternet.py Weather Station. Here is the current weather across Haiti's 10 departments. "
    
    for dept in weather_data:
        if dept.get("status") == "success":
            temp = dept.get("temperature", "N/A")
            desc = get_weather_description(dept.get("weather_code", 0))
            city = dept.get("city", "")
            script += f"In {city}, it is currently {temp} degrees Celsius with {desc}. "
    
    script += "Thank you for using GlobalInternet.py Weather Station."
    return script

# ========== SESSION STATE ==========
if 'weather_data' not in st.session_state:
    st.session_state.weather_data = None
if 'last_update' not in st.session_state:
    st.session_state.last_update = None
if 'api_status' not in st.session_state:
    st.session_state.api_status = "Initializing"

# ========== HEADER ==========
st.markdown("""
<div class="main-header">
    <h1>🌤️ GlobalInternet.py Weather Station</h1>
    <p>Real‑time weather monitoring for all 10 departments of Haiti</p>
    <span class="live-badge">● LIVE 24/7</span>
</div>
""", unsafe_allow_html=True)

# ========== SIDEBAR ==========
with st.sidebar:
    # --- Profile Image and Name ---
    st.markdown("""
    <div style="text-align: center; margin-bottom: 20px;">
        <img src="https://raw.githubusercontent.com/Deslandes1/Weather-Station-of-Globalinternet.py-June-2026/main/Gesner%20Deslandes.png" 
             class="profile-img">
        <h3 class="profile-name">Gesner Deslandes</h3>
        <p class="profile-title">Engineer-in-Chief</p>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    st.markdown("### 📞 Contact")
    st.markdown("""
    <div class="sidebar-contact">
        <strong>Email:</strong> deslandes78@gmail.com<br>
        <strong>Phone:</strong> (509) 4738-5663<br>
        <strong>Website:</strong> <a href="https://globalinternetsitepyabh7v6tnmskxxnuplrdcgk.streamlit.app" style="color:#00d4ff;" target="_blank">globalinternet-py.com</a>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    st.markdown("### 🎤 AI Voice")
    if st.button("🔊 Read Weather Summary", use_container_width=True):
        if st.session_state.weather_data:
            script = generate_weather_voice_script(st.session_state.weather_data)
            with st.spinner("🎤 Generating voice..."):
                audio_bytes = generate_audio(script, "en")
                if audio_bytes:
                    st.audio(audio_bytes, format="audio/mp3")
                    st.success("✅ Weather summary played.")
                else:
                    st.error("❌ Voice generation failed. Please ensure gTTS is installed.")
        else:
            st.warning("No weather data available. Please refresh.")
    
    st.markdown("---")
    
    st.markdown("### 🔄 Data Status")
    status = st.session_state.api_status
    if "Live" in status:
        badge_class = "status-live"
        status_text = "Live"
    elif "Cached" in status:
        badge_class = "status-cached"
        status_text = "Cached"
    else:
        badge_class = "status-error"
        status_text = "Error"
    st.markdown(f'<span class="status-badge {badge_class}">{status_text}</span>', unsafe_allow_html=True)
    if st.session_state.last_update:
        st.caption(f"Last updated: {st.session_state.last_update}")
    
    st.markdown("---")
    
    st.markdown("### 📊 About")
    st.markdown("""
    This weather station fetches real‑time data from **Open‑Meteo**,
    a free weather API that requires no API key.
    
    **Data includes:**
    - Temperature & Feels‑like
    - Humidity & Precipitation
    - Wind speed & Pressure
    - UV Index & Weather conditions
    
    Updates every **15 minutes** automatically.
    """)
    
    st.markdown("---")
    
    if st.button("🔄 Refresh Now", use_container_width=True):
        st.cache_data.clear()
        st.rerun()
    
    st.markdown("---")
    st.markdown("### 🌐 GlobalInternet.py")
    st.markdown("Built by **Gesner Deslandes**, Engineer‑in‑Chief")
    st.markdown("*Connecting the global market with local expertise.*")

# ========== MAIN CONTENT ==========

# Fetch weather data
if st.session_state.weather_data is None:
    with st.spinner("🌤️ Fetching weather data for all 10 departments..."):
        data, timestamp = fetch_weather_data()
        st.session_state.weather_data = data
        st.session_state.last_update = timestamp
        st.session_state.api_status = "Live"
        st.rerun()

weather_data = st.session_state.weather_data

# ========== SUMMARY SECTION ==========
if weather_data:
    # Count successful fetches
    success_count = sum(1 for d in weather_data if d.get("status") == "success")
    error_count = len(weather_data) - success_count
    
    col_summary1, col_summary2, col_summary3 = st.columns(3)
    with col_summary1:
        st.markdown(f"""
        <div class="summary-box">
            <strong>🌡️ Average Temperature</strong><br>
            <span style="font-size:2rem; color:#00d4ff;">
                {sum(d.get("temperature", 0) for d in weather_data if d.get("status") == "success") / max(1, success_count):.1f}°C
            </span>
        </div>
        """, unsafe_allow_html=True)
    with col_summary2:
        st.markdown(f"""
        <div class="summary-box">
            <strong>📊 Departments</strong><br>
            <span style="font-size:2rem; color:#00d4ff;">
                {success_count}/{len(HAITI_DEPARTMENTS)}
            </span>
            <span style="color:#8899bb;">online</span>
        </div>
        """, unsafe_allow_html=True)
    with col_summary3:
        st.markdown(f"""
        <div class="summary-box">
            <strong>🕒 Last Update</strong><br>
            <span style="font-size:1.2rem; color:#ffffff;">
                {st.session_state.last_update}
            </span>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("---")

# ========== WEATHER CARDS – 2 COLUMNS ==========
st.markdown("### 📍 Current Weather by Department")

# Split into rows of 2
for i in range(0, len(weather_data), 2):
    cols = st.columns(2)
    for j, col in enumerate(cols):
        idx = i + j
        if idx < len(weather_data):
            dept = weather_data[idx]
            with col:
                if dept.get("status") == "success":
                    temp = dept.get("temperature", "N/A")
                    feels = dept.get("feels_like", "N/A")
                    humidity = dept.get("humidity", "N/A")
                    precip = dept.get("precipitation", 0)
                    wind = dept.get("wind_speed", "N/A")
                    pressure = dept.get("pressure", "N/A")
                    uv = dept.get("uv_index", "N/A")
                    code = dept.get("weather_code", 0)
                    icon = get_weather_icon(code)
                    desc = get_weather_description(code)
                    city = dept.get("city", "")
                    dept_name = dept.get("department", "")
                    
                    st.markdown(f"""
                    <div class="weather-card">
                        <div class="city">{city}</div>
                        <div class="dept">{dept_name}</div>
                        <div class="weather-icon">{icon}</div>
                        <div class="temp">{temp}°C</div>
                        <div style="color:#8899bb; font-size:0.9rem;">{desc}</div>
                        <div style="color:#aabbdd; font-size:0.9rem;">Feels like {feels}°C</div>
                        <div class="details">
                            <span>💧 {humidity}%</span>
                            <span>🌧️ {precip} mm</span>
                            <span>💨 {wind} km/h</span>
                            <span>📊 {pressure} hPa</span>
                            <span>☀️ UV {uv}</span>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    st.markdown(f"""
                    <div class="weather-card" style="border-color:#e74c3c;">
                        <div class="city">{dept.get('city', 'Unknown')}</div>
                        <div class="dept">{dept.get('department', 'Unknown')}</div>
                        <div style="font-size:3rem; margin:10px 0;">⚠️</div>
                        <div style="color:#e74c3c;">Data unavailable</div>
                        <div style="color:#8899bb; font-size:0.8rem;">{dept.get('error', 'Connection error')}</div>
                    </div>
                    """, unsafe_allow_html=True)

# ========== DETAILED TABLE ==========
with st.expander("📊 View Detailed Weather Table", expanded=False):
    if weather_data:
        table_data = []
        for d in weather_data:
            if d.get("status") == "success":
                table_data.append({
                    "Department": d.get("department", ""),
                    "City": d.get("city", ""),
                    "Temperature (°C)": d.get("temperature", "N/A"),
                    "Feels Like (°C)": d.get("feels_like", "N/A"),
                    "Humidity (%)": d.get("humidity", "N/A"),
                    "Precipitation (mm)": d.get("precipitation", 0),
                    "Wind (km/h)": d.get("wind_speed", "N/A"),
                    "Pressure (hPa)": d.get("pressure", "N/A"),
                    "UV Index": d.get("uv_index", "N/A"),
                    "Conditions": get_weather_description(d.get("weather_code", 0))
                })
        if table_data:
            df = pd.DataFrame(table_data)
            st.dataframe(df, use_container_width=True, height=400)
            
            # Download CSV
            csv = df.to_csv(index=False)
            st.download_button(
                label="📥 Download Weather Data (CSV)",
                data=csv,
                file_name=f"haiti_weather_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv",
                use_container_width=True
            )

# ========== AUTO-REFRESH ==========
# Auto-refresh every 15 minutes (900 seconds)
if 'next_refresh' not in st.session_state:
    st.session_state.next_refresh = time.time() + 900

if time.time() > st.session_state.next_refresh:
    st.session_state.next_refresh = time.time() + 900
    st.cache_data.clear()
    st.rerun()

# ========== FOOTER ==========
st.markdown(f"""
<div class="footer">
    <p>© 2026 GlobalInternet.py Online Software Company</p>
    <p>Built by <strong>Gesner Deslandes</strong> | (509) 4738-5663 | deslandes78@gmail.com</p>
    <p style="font-size:0.8rem; color:#445566;">
        🌤️ Data powered by <a href="https://open-meteo.com" style="color:#00d4ff;" target="_blank">Open-Meteo</a>
        | Free weather API | No API key required
        | Updated every 15 minutes
    </p>
</div>
""", unsafe_allow_html=True)
