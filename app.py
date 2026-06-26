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

# ========== TRANSLATIONS ==========
LANGUAGES = {
    "en": {"name": "English", "code": "en", "gtts": "en"},
    "fr": {"name": "Français", "code": "fr", "gtts": "fr"},
    "es": {"name": "Español", "code": "es", "gtts": "es"},
    "zh": {"name": "中文", "code": "zh", "gtts": "zh"}
}

T = {
    "en": {
        "app_title": "GlobalInternet.py Weather Station",
        "app_sub": "Real‑time weather monitoring for all 10 departments of Haiti",
        "live_badge": "● LIVE 24/7",
        "sidebar_contact": "Contact",
        "sidebar_email": "Email",
        "sidebar_phone": "Phone",
        "sidebar_website": "Website",
        "sidebar_voice": "AI Voice",
        "voice_button": "🔊 Read Weather Summary",
        "voice_playing": "✅ Weather summary played.",
        "voice_fail": "❌ Voice generation failed. Please ensure gTTS is installed.",
        "voice_waiting": "No weather data available. Please refresh.",
        "sidebar_status": "Data Status",
        "status_live": "Live",
        "status_cached": "Cached",
        "status_error": "Error",
        "last_update": "Last updated: {time}",
        "sidebar_about": "About",
        "about_text": """
        This weather station fetches real‑time data from **Open‑Meteo**,
        a free weather API that requires no API key.
        
        **Data includes:**
        - Temperature & Feels‑like
        - Humidity & Precipitation
        - Wind speed & Pressure
        - UV Index & Weather conditions
        
        Updates every **15 minutes** automatically.
        """,
        "refresh_button": "🔄 Refresh Now",
        "footer_text": "© 2026 GlobalInternet.py Online Software Company",
        "footer_built": "Built by **Gesner Deslandes** | (509) 4738-5663 | deslandes78@gmail.com",
        "footer_powered": "🌤️ Data powered by Open-Meteo | Free weather API | No API key required | Updated every 15 minutes",
        "summary_avg_temp": "Average Temperature",
        "summary_departments": "Departments",
        "summary_online": "online",
        "summary_last_update": "Last Update",
        "weather_title": "Current Weather by Department",
        "weather_details": "View Detailed Weather Table",
        "download_csv": "📥 Download Weather Data (CSV)",
        "feels_like": "Feels like {temp}°C",
        "precip": "Precipitation",
        "humidity": "Humidity",
        "wind": "Wind",
        "pressure": "Pressure",
        "uv": "UV Index",
        "data_unavailable": "Data unavailable",
        "error_connection": "Connection error",
        "weather_clear": "Clear sky",
        "weather_mainly_clear": "Mainly clear",
        "weather_partly_cloudy": "Partly cloudy",
        "weather_overcast": "Overcast",
        "weather_fog": "Fog",
        "weather_rime_fog": "Depositing rime fog",
        "weather_light_drizzle": "Light drizzle",
        "weather_moderate_drizzle": "Moderate drizzle",
        "weather_dense_drizzle": "Dense drizzle",
        "weather_slight_rain": "Slight rain",
        "weather_moderate_rain": "Moderate rain",
        "weather_heavy_rain": "Heavy rain",
        "weather_slight_snow": "Slight snow",
        "weather_moderate_snow": "Moderate snow",
        "weather_heavy_snow": "Heavy snow",
        "weather_slight_showers": "Slight rain showers",
        "weather_moderate_showers": "Moderate rain showers",
        "weather_violent_showers": "Violent rain showers",
        "weather_thunderstorm": "Thunderstorm",
        "weather_thunderstorm_hail": "Thunderstorm with hail",
        "weather_thunderstorm_heavy_hail": "Thunderstorm with heavy hail",
        "voice_script": """
Welcome to GlobalInternet.py Weather Station. This software detects and broadcasts real-time weather data from the nearest meteorological stations using the Open-Meteo API, providing you with accurate and up-to-date information for all 10 departments of Haiti.

This report was generated on {date} at {time} Haiti Standard Time.

{details}

{heat_advice}

{rain_info}

This weather forecast was brought to you by Gesner Deslandes, Engineer-in-Chief at GlobalInternet.py.

We are a Haitian software company committed to providing free, accurate, and life-saving information to our community. If you find this service useful, please support our work through Prisme Transfer or Moncash anywhere around the globe.

Contact us:
Phone / WhatsApp: (509) 4738-5663
Email: deslandes78@gmail.com

Your donation helps us continue bringing you more information and better services. Thank you for your support.
""",
        "voice_detail": "In {city}, {department}, it is currently {temp} degrees Celsius with {desc}. ",
        "heat_advice": """
The heat is already very intense across Haiti, especially in Port-au-Prince and the Ouest department. 
Here is what you can do to protect yourself and your family:
Stay hydrated – drink plenty of water throughout the day.
Avoid going outside between 11 AM and 4 PM when the sun is at its strongest.
Wear light-colored, loose-fitting clothing.
Use fans or air conditioning if available.
Never leave children or pets in parked vehicles.
Check on elderly neighbors and those with health conditions.
If you must be outdoors, wear a hat and use sunscreen.
Keep your home cool by closing curtains during the hottest hours.
Take cool showers to lower your body temperature.
Eat light meals and avoid heavy, hot foods.

Remember, heat exhaustion and heatstroke are serious. Listen to your body and rest in the shade when needed.
""",
        "rain_info": "Based on current data, rain is expected in the following departments: {rain_departments}. If you are in these areas, please carry an umbrella and stay safe.",
        "no_rain": "No rain is expected in any department at this time."
    },
    "fr": {
        "app_title": "Station Météo GlobalInternet.py",
        "app_sub": "Surveillance météo en temps réel pour les 10 départements d'Haïti",
        "live_badge": "● EN DIRECT 24/7",
        "sidebar_contact": "Contact",
        "sidebar_email": "Email",
        "sidebar_phone": "Téléphone",
        "sidebar_website": "Site web",
        "sidebar_voice": "Voix IA",
        "voice_button": "🔊 Lire le résumé météo",
        "voice_playing": "✅ Résumé météo diffusé.",
        "voice_fail": "❌ La génération vocale a échoué. Veuillez installer gTTS.",
        "voice_waiting": "Aucune donnée météo disponible. Veuillez actualiser.",
        "sidebar_status": "État des données",
        "status_live": "En direct",
        "status_cached": "Mis en cache",
        "status_error": "Erreur",
        "last_update": "Dernière mise à jour : {time}",
        "sidebar_about": "À propos",
        "about_text": """
        Cette station météo récupère des données en temps réel depuis **Open‑Meteo**,
        une API météo gratuite ne nécessitant pas de clé API.
        
        **Données incluses :**
        - Température et ressenti
        - Humidité et précipitations
        - Vitesse du vent et pression
        - Indice UV et conditions météo
        
        Mise à jour automatique toutes les **15 minutes**.
        """,
        "refresh_button": "🔄 Actualiser maintenant",
        "footer_text": "© 2026 GlobalInternet.py Online Software Company",
        "footer_built": "Construit par **Gesner Deslandes** | (509) 4738-5663 | deslandes78@gmail.com",
        "footer_powered": "🌤️ Données fournies par Open-Meteo | API météo gratuite | Aucune clé API requise | Mise à jour toutes les 15 minutes",
        "summary_avg_temp": "Température moyenne",
        "summary_departments": "Départements",
        "summary_online": "en ligne",
        "summary_last_update": "Dernière mise à jour",
        "weather_title": "Météo actuelle par département",
        "weather_details": "Voir le tableau détaillé de la météo",
        "download_csv": "📥 Télécharger les données météo (CSV)",
        "feels_like": "Ressenti {temp}°C",
        "precip": "Précipitations",
        "humidity": "Humidité",
        "wind": "Vent",
        "pressure": "Pression",
        "uv": "Indice UV",
        "data_unavailable": "Données indisponibles",
        "error_connection": "Erreur de connexion",
        "weather_clear": "Ciel dégagé",
        "weather_mainly_clear": "Principalement dégagé",
        "weather_partly_cloudy": "Partiellement nuageux",
        "weather_overcast": "Couvert",
        "weather_fog": "Brouillard",
        "weather_rime_fog": "Brouillard givrant",
        "weather_light_drizzle": "Bruine légère",
        "weather_moderate_drizzle": "Bruine modérée",
        "weather_dense_drizzle": "Bruine dense",
        "weather_slight_rain": "Pluie légère",
        "weather_moderate_rain": "Pluie modérée",
        "weather_heavy_rain": "Pluie forte",
        "weather_slight_snow": "Neige légère",
        "weather_moderate_snow": "Neige modérée",
        "weather_heavy_snow": "Neige forte",
        "weather_slight_showers": "Averses légères",
        "weather_moderate_showers": "Averses modérées",
        "weather_violent_showers": "Averses violentes",
        "weather_thunderstorm": "Orage",
        "weather_thunderstorm_hail": "Orage avec grêle",
        "weather_thunderstorm_heavy_hail": "Orage avec grêle forte",
        "voice_script": """
Bienvenue à la station météo GlobalInternet.py. Ce logiciel détecte et diffuse des données météo en temps réel provenant des stations météorologiques les plus proches via l'API Open-Meteo, vous fournissant des informations précises et à jour pour les 10 départements d'Haïti.

Ce rapport a été généré le {date} à {time} heure d'Haïti.

{details}

{heat_advice}

{rain_info}

Cette prévision météo vous a été présentée par Gesner Deslandes, ingénieur en chef chez GlobalInternet.py.

Nous sommes une entreprise de logiciels haïtienne engagée à fournir des informations gratuites, précises et vitales à notre communauté. Si vous trouvez ce service utile, veuillez soutenir notre travail via Prisme Transfer ou Moncash partout dans le monde.

Contactez-nous :
Téléphone / WhatsApp : (509) 4738-5663
Email : deslandes78@gmail.com

Votre don nous aide à continuer de vous apporter plus d'informations et de meilleurs services. Merci pour votre soutien.
""",
        "voice_detail": "À {city}, dans le département de {department}, il fait actuellement {temp} degrés Celsius avec {desc}. ",
        "heat_advice": """
La chaleur est déjà très intense dans toute la région, surtout à Port-au-Prince et dans le département de l'Ouest.
Voici ce que vous pouvez faire pour vous protéger, vous et votre famille :
Buvez beaucoup d'eau tout au long de la journée.
Évitez de sortir entre 11 heures et 16 heures, lorsque le soleil est le plus fort.
Portez des vêtements de couleur claire et amples.
Utilisez des ventilateurs ou la climatisation si disponible.
Ne laissez jamais les enfants ou les animaux dans des voitures en stationnement.
Prenez soin des voisins âgés et des personnes souffrant de problèmes de santé.
Si vous devez être à l'extérieur, portez un chapeau et utilisez de la crème solaire.
Gardez votre maison fraîche en fermant les rideaux pendant les heures les plus chaudes.
Prenez des douches fraîches pour abaisser votre température corporelle.
Mangez des repas légers et évitez les aliments lourds et chauds.

N'oubliez pas que l'épuisement par la chaleur et le coup de chaleur sont graves. Écoutez votre corps et reposez-vous à l'ombre si nécessaire.
""",
        "rain_info": "D'après les données actuelles, des pluies sont attendues dans les départements suivants : {rain_departments}. Si vous vous trouvez dans ces zones, munissez-vous d'un parapluie et restez en sécurité.",
        "no_rain": "Aucune pluie n'est attendue dans aucun département pour le moment."
    },
    "es": {
        "app_title": "Estación Meteorológica GlobalInternet.py",
        "app_sub": "Monitoreo meteorológico en tiempo real para los 10 departamentos de Haití",
        "live_badge": "● EN VIVO 24/7",
        "sidebar_contact": "Contacto",
        "sidebar_email": "Correo electrónico",
        "sidebar_phone": "Teléfono",
        "sidebar_website": "Sitio web",
        "sidebar_voice": "Voz IA",
        "voice_button": "🔊 Leer resumen del clima",
        "voice_playing": "✅ Resumen del clima reproducido.",
        "voice_fail": "❌ Falló la generación de voz. Asegúrate de instalar gTTS.",
        "voice_waiting": "No hay datos climáticos disponibles. Actualice.",
        "sidebar_status": "Estado de los datos",
        "status_live": "En vivo",
        "status_cached": "En caché",
        "status_error": "Error",
        "last_update": "Última actualización: {time}",
        "sidebar_about": "Acerca de",
        "about_text": """
        Esta estación meteorológica obtiene datos en tiempo real de **Open‑Meteo**,
        una API climática gratuita que no requiere clave API.
        
        **Datos incluidos:**
        - Temperatura y sensación térmica
        - Humedad y precipitación
        - Velocidad del viento y presión
        - Índice UV y condiciones climáticas
        
        Se actualiza automáticamente cada **15 minutos**.
        """,
        "refresh_button": "🔄 Actualizar ahora",
        "footer_text": "© 2026 GlobalInternet.py Online Software Company",
        "footer_built": "Construido por **Gesner Deslandes** | (509) 4738-5663 | deslandes78@gmail.com",
        "footer_powered": "🌤️ Datos proporcionados por Open-Meteo | API climática gratuita | No se requiere clave API | Actualizado cada 15 minutos",
        "summary_avg_temp": "Temperatura promedio",
        "summary_departments": "Departamentos",
        "summary_online": "en línea",
        "summary_last_update": "Última actualización",
        "weather_title": "Clima actual por departamento",
        "weather_details": "Ver tabla detallada del clima",
        "download_csv": "📥 Descargar datos climáticos (CSV)",
        "feels_like": "Sensación de {temp}°C",
        "precip": "Precipitación",
        "humidity": "Humedad",
        "wind": "Viento",
        "pressure": "Presión",
        "uv": "Índice UV",
        "data_unavailable": "Datos no disponibles",
        "error_connection": "Error de conexión",
        "weather_clear": "Cielo despejado",
        "weather_mainly_clear": "Mayormente despejado",
        "weather_partly_cloudy": "Parcialmente nublado",
        "weather_overcast": "Nublado",
        "weather_fog": "Niebla",
        "weather_rime_fog": "Niebla escarchada",
        "weather_light_drizzle": "Llovizna ligera",
        "weather_moderate_drizzle": "Llovizna moderada",
        "weather_dense_drizzle": "Llovizna densa",
        "weather_slight_rain": "Lluvia ligera",
        "weather_moderate_rain": "Lluvia moderada",
        "weather_heavy_rain": "Lluvia fuerte",
        "weather_slight_snow": "Nieve ligera",
        "weather_moderate_snow": "Nieve moderada",
        "weather_heavy_snow": "Nieve fuerte",
        "weather_slight_showers": "Chubascos ligeros",
        "weather_moderate_showers": "Chubascos moderados",
        "weather_violent_showers": "Chubascos violentos",
        "weather_thunderstorm": "Tormenta eléctrica",
        "weather_thunderstorm_hail": "Tormenta con granizo",
        "weather_thunderstorm_heavy_hail": "Tormenta con granizo fuerte",
        "voice_script": """
Bienvenido a la estación meteorológica de GlobalInternet.py. Este software detecta y transmite datos meteorológicos en tiempo real desde las estaciones meteorológicas más cercanas a través de la API Open-Meteo, proporcionándole información precisa y actualizada para los 10 departamentos de Haití.

Este informe fue generado el {date} a las {time} hora de Haití.

{details}

{heat_advice}

{rain_info}

Este pronóstico del tiempo fue presentado por Gesner Deslandes, ingeniero jefe de GlobalInternet.py.

Somos una empresa de software haitiana comprometida con proporcionar información gratuita, precisa y vital a nuestra comunidad. Si encuentra útil este servicio, apoye nuestro trabajo a través de Prisme Transfer o Moncash en cualquier parte del mundo.

Contáctenos:
Teléfono / WhatsApp: (509) 4738-5663
Correo electrónico: deslandes78@gmail.com

Su donación nos ayuda a seguir brindándole más información y mejores servicios. Gracias por su apoyo.
""",
        "voice_detail": "En {city}, departamento de {department}, actualmente hay {temp} grados Celsius con {desc}. ",
        "heat_advice": """
El calor ya es muy intenso en toda la región, especialmente en Puerto Príncipe y el departamento Oeste.
Esto es lo que puede hacer para protegerse a usted y a su familia:
Manténgase hidratado – beba mucha agua durante todo el día.
Evite salir entre las 11 a.m. y las 4 p.m., cuando el sol es más fuerte.
Use ropa de colores claros y holgada.
Use ventiladores o aire acondicionado si está disponible.
Nunca deje niños o mascotas en vehículos estacionados.
Cuide a los vecinos mayores y a las personas con problemas de salud.
Si debe estar al aire libre, use sombrero y protector solar.
Mantenga su hogar fresco cerrando las cortinas durante las horas más calurosas.
Tome duchas frías para bajar su temperatura corporal.
Coma comidas ligeras y evite alimentos pesados y calientes.

Recuerde que el agotamiento por calor y el golpe de calor son graves. Escuche a su cuerpo y descanse a la sombra cuando sea necesario.
""",
        "rain_info": "Según los datos actuales, se esperan lluvias en los siguientes departamentos: {rain_departments}. Si se encuentra en estas áreas, lleve un paraguas y manténgase seguro.",
        "no_rain": "No se esperan lluvias en ningún departamento en este momento."
    },
    "zh": {
        "app_title": "GlobalInternet.py 气象站",
        "app_sub": "海地 10 个省实时天气监测",
        "live_badge": "● 24/7 实时运行",
        "sidebar_contact": "联系方式",
        "sidebar_email": "电子邮件",
        "sidebar_phone": "电话",
        "sidebar_website": "网站",
        "sidebar_voice": "AI 语音",
        "voice_button": "🔊 朗读天气摘要",
        "voice_playing": "✅ 天气摘要已播放。",
        "voice_fail": "❌ 语音生成失败。请确保已安装 gTTS。",
        "voice_waiting": "暂无天气数据。请刷新。",
        "sidebar_status": "数据状态",
        "status_live": "实时",
        "status_cached": "缓存",
        "status_error": "错误",
        "last_update": "最后更新：{time}",
        "sidebar_about": "关于",
        "about_text": """
        此气象站从 **Open‑Meteo** 获取实时数据，
        这是一个免费的天气 API，无需 API 密钥。
        
        **包含数据：**
        - 温度及体感温度
        - 湿度和降水
        - 风速和气压
        - 紫外线指数和天气状况
        
        每 **15 分钟**自动更新。
        """,
        "refresh_button": "🔄 立即刷新",
        "footer_text": "© 2026 GlobalInternet.py 在线软件公司",
        "footer_built": "由 **Gesner Deslandes** 构建 | (509) 4738-5663 | deslandes78@gmail.com",
        "footer_powered": "🌤️ 数据由 Open-Meteo 提供 | 免费天气 API | 无需 API 密钥 | 每 15 分钟更新一次",
        "summary_avg_temp": "平均温度",
        "summary_departments": "省份",
        "summary_online": "在线",
        "summary_last_update": "最后更新",
        "weather_title": "各省当前天气",
        "weather_details": "查看详细天气表格",
        "download_csv": "📥 下载天气数据 (CSV)",
        "feels_like": "体感 {temp}°C",
        "precip": "降水量",
        "humidity": "湿度",
        "wind": "风速",
        "pressure": "气压",
        "uv": "紫外线指数",
        "data_unavailable": "数据不可用",
        "error_connection": "连接错误",
        "weather_clear": "晴天",
        "weather_mainly_clear": "晴间多云",
        "weather_partly_cloudy": "局部多云",
        "weather_overcast": "阴天",
        "weather_fog": "雾",
        "weather_rime_fog": "雾凇",
        "weather_light_drizzle": "小雨",
        "weather_moderate_drizzle": "中雨",
        "weather_dense_drizzle": "大雨",
        "weather_slight_rain": "小雨",
        "weather_moderate_rain": "中雨",
        "weather_heavy_rain": "大雨",
        "weather_slight_snow": "小雪",
        "weather_moderate_snow": "中雪",
        "weather_heavy_snow": "大雪",
        "weather_slight_showers": "小阵雨",
        "weather_moderate_showers": "中阵雨",
        "weather_violent_showers": "强阵雨",
        "weather_thunderstorm": "雷暴",
        "weather_thunderstorm_hail": "雷暴伴冰雹",
        "weather_thunderstorm_heavy_hail": "雷暴伴大冰雹",
        "voice_script": """
欢迎使用 GlobalInternet.py 气象站。该软件通过 Open-Meteo API 从最近的气象站检测并广播实时天气数据，为您提供海地所有 10 个省的准确和最新信息。

本报告于 {date} {time} 海地时间生成。

{details}

{heat_advice}

{rain_info}

本次天气预报由 GlobalInternet.py 首席工程师 Gesner Deslandes 为您提供。

我们是一家海地软件公司，致力于为我们的社区提供免费、准确和重要的信息。如果您觉得此服务有用，请通过 Prisme Transfer 或 Moncash 在全球任何地方支持我们的工作。

联系我们：
电话 / WhatsApp：(509) 4738-5663
电子邮件：deslandes78@gmail.com

您的捐赠帮助我们继续为您带来更多信息和更好的服务。感谢您的支持。
""",
        "voice_detail": "在 {city}，{department}省，当前温度为 {temp} 摄氏度，{desc}。",
        "heat_advice": """
海地各地已经非常炎热，尤其是在太子港和西部省。
以下是保护您和家人的建议：
多喝水，全天保持水分充足。
避免在上午 11 点到下午 4 点之间外出，此时阳光最强。
穿浅色、宽松的衣服。
如果有风扇或空调，请使用它们。
切勿将儿童或宠物留在停放的车辆中。
关照老年邻居和有健康问题的人。
如果必须外出，请戴帽子并使用防晒霜。
在一天中最热的时候拉上窗帘，保持室内凉爽。
洗冷水澡以降低体温。
吃清淡的食物，避免油腻和热食。

请记住，热衰竭和中暑是严重的健康问题。注意身体信号，必要时在阴凉处休息。
""",
        "rain_info": "根据当前数据，以下省份预计有雨：{rain_departments}。如果您在这些地区，请携带雨伞并注意安全。",
        "no_rain": "目前任何省份都没有降雨预报。"
    }
}

# ========== TRANSLATION FUNCTION ==========
def t(key):
    """Return translated string for current language"""
    lang = st.session_state.get("lang", "en")
    return T[lang].get(key, T["en"].get(key, key))

# ========== WEATHER DESCRIPTION TRANSLATION ==========
def get_weather_description_translated(code):
    """Return translated weather description based on current language"""
    lang = st.session_state.get("lang", "en")
    desc_key_map = {
        0: "weather_clear",
        1: "weather_mainly_clear",
        2: "weather_partly_cloudy",
        3: "weather_overcast",
        45: "weather_fog",
        48: "weather_rime_fog",
        51: "weather_light_drizzle",
        53: "weather_moderate_drizzle",
        55: "weather_dense_drizzle",
        61: "weather_slight_rain",
        63: "weather_moderate_rain",
        65: "weather_heavy_rain",
        71: "weather_slight_snow",
        73: "weather_moderate_snow",
        75: "weather_heavy_snow",
        80: "weather_slight_showers",
        81: "weather_moderate_showers",
        82: "weather_violent_showers",
        95: "weather_thunderstorm",
        96: "weather_thunderstorm_hail",
        99: "weather_thunderstorm_heavy_hail"
    }
    key = desc_key_map.get(code, "weather_clear")
    return t(key)

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

# ========== WEATHER DATA FETCH ==========
@st.cache_data(ttl=900)
def fetch_weather_data():
    results = []
    haiti_tz = pytz.timezone('America/Port-au-Prince')
    now = datetime.now(haiti_tz)
    
    for dept in HAITI_DEPARTMENTS:
        url = "https://api.open-meteo.com/v1/forecast"
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
        time.sleep(0.2)
    
    return results, now.strftime("%Y-%m-%d %I:%M:%S %p")

# ========== GENERATE VOICE SCRIPT ==========
def generate_weather_voice_script(weather_data):
    """Generate a full voice script with heat advice, rain predictions, and donation call"""
    if not weather_data:
        return t("voice_waiting")
    
    # Get current date and time in Haiti timezone
    haiti_tz = pytz.timezone('America/Port-au-Prince')
    now = datetime.now(haiti_tz)
    date_str = now.strftime("%B %d, %Y")
    time_str = now.strftime("%I:%M:%S %p")
    
    # Build details
    detail_template = t("voice_detail")
    details = ""
    for dept in weather_data:
        if dept.get("status") == "success":
            temp = dept.get("temperature", "N/A")
            code = dept.get("weather_code", 0)
            desc = get_weather_description_translated(code)
            city = dept.get("city", "")
            department = dept.get("department", "")
            details += detail_template.format(city=city, department=department, temp=temp, desc=desc)
    
    # Heat advice (always included)
    heat_advice = t("heat_advice")
    
    # Rain prediction - check which departments have precipitation > 0 or rain codes
    rain_departments = []
    rain_codes = [51, 53, 55, 61, 63, 65, 80, 81, 82, 95, 96, 99]
    for dept in weather_data:
        if dept.get("status") == "success":
            precip = dept.get("precipitation", 0)
            code = dept.get("weather_code", 0)
            if precip > 0 or code in rain_codes:
                rain_departments.append(dept.get("department", ""))
    
    if rain_departments:
        rain_info = t("rain_info").format(rain_departments=", ".join(rain_departments))
    else:
        rain_info = t("no_rain")
    
    # Build full script
    script_template = t("voice_script")
    script = script_template.format(
        date=date_str,
        time=time_str,
        details=details,
        heat_advice=heat_advice,
        rain_info=rain_info
    )
    return script

# ========== CUSTOM CSS ==========
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
    .live-clock {
        text-align: center;
        padding: 12px;
        background: rgba(0, 212, 255, 0.05);
        border: 1px solid #00d4ff;
        border-radius: 12px;
        margin: 10px 0;
        font-family: monospace;
        font-size: 1.2rem;
    }
    .live-clock .date {
        color: #8899bb;
        font-size: 0.9rem;
    }
    .live-clock .time {
        color: #00d4ff;
        font-size: 2rem;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)

# ========== SESSION STATE ==========
if "lang" not in st.session_state:
    st.session_state.lang = "en"
if 'weather_data' not in st.session_state:
    st.session_state.weather_data = None
if 'last_update' not in st.session_state:
    st.session_state.last_update = None
if 'api_status' not in st.session_state:
    st.session_state.api_status = "Initializing"

# ========== LIVE CLOCK HTML ==========
def get_live_clock_html():
    return """
    <div class="live-clock">
        <div class="date" id="liveDate">Loading...</div>
        <div class="time" id="liveTime">--:--:--</div>
        <div style="color:#667799; font-size:0.7rem;">Haiti Standard Time</div>
    </div>
    <script>
        function updateClock() {
            var now = new Date();
            var options = { timeZone: 'America/Port-au-Prince', year: 'numeric', month: 'long', day: 'numeric' };
            var dateStr = now.toLocaleDateString('en-US', options);
            var timeStr = now.toLocaleTimeString('en-US', { timeZone: 'America/Port-au-Prince', hour12: true, hour: '2-digit', minute: '2-digit', second: '2-digit' });
            document.getElementById('liveDate').textContent = dateStr;
            document.getElementById('liveTime').textContent = timeStr;
        }
        updateClock();
        setInterval(updateClock, 1000);
    </script>
    """

# ========== HEADER ==========
st.markdown(f"""
<div class="main-header">
    <h1>🌤️ {t('app_title')}</h1>
    <p>{t('app_sub')}</p>
    <span class="live-badge">{t('live_badge')}</span>
</div>
""", unsafe_allow_html=True)

# ========== SIDEBAR ==========
with st.sidebar:
    # Language selection
    lang_options = {"en": "English", "fr": "Français", "es": "Español", "zh": "中文"}
    selected_lang = st.selectbox(
        "🌐 Language",
        options=list(lang_options.keys()),
        format_func=lambda x: lang_options[x],
        index=list(lang_options.keys()).index(st.session_state.lang)
    )
    if selected_lang != st.session_state.lang:
        st.session_state.lang = selected_lang
        st.rerun()
    
    st.markdown("---")
    
    # Live Clock in Sidebar
    st.components.v1.html(get_live_clock_html(), height=130)
    
    st.markdown("---")
    
    # Profile Image and Name
    st.markdown("""
    <div style="text-align: center; margin-bottom: 20px;">
        <img src="https://raw.githubusercontent.com/Deslandes1/Weather-Station-of-Globalinternet.py-June-2026/main/Gesner%20Deslandes.png" 
             class="profile-img">
        <h3 class="profile-name">Gesner Deslandes</h3>
        <p class="profile-title">Engineer-in-Chief</p>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    st.markdown(f"### 📞 {t('sidebar_contact')}")
    st.markdown(f"""
    <div class="sidebar-contact">
        <strong>{t('sidebar_email')}:</strong> deslandes78@gmail.com<br>
        <strong>{t('sidebar_phone')}:</strong> (509) 4738-5663<br>
        <strong>{t('sidebar_website')}:</strong> <a href="https://globalinternetsitepyabh7v6tnmskxxnuplrdcgk.streamlit.app" style="color:#00d4ff;" target="_blank">globalinternet-py.com</a>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    st.markdown(f"### 🎤 {t('sidebar_voice')}")
    if st.button(t('voice_button'), use_container_width=True):
        if st.session_state.weather_data:
            script = generate_weather_voice_script(st.session_state.weather_data)
            with st.spinner("🎤 Generating voice..."):
                lang_code = LANGUAGES[st.session_state.lang]["gtts"]
                audio_bytes = generate_audio(script, lang_code)
                if audio_bytes:
                    st.audio(audio_bytes, format="audio/mp3")
                    st.success(t('voice_playing'))
                else:
                    st.error(t('voice_fail'))
        else:
            st.warning(t('voice_waiting'))
    
    st.markdown("---")
    
    st.markdown(f"### 🔄 {t('sidebar_status')}")
    status = st.session_state.api_status
    if "Live" in status:
        badge_class = "status-live"
        status_text = t('status_live')
    elif "Cached" in status:
        badge_class = "status-cached"
        status_text = t('status_cached')
    else:
        badge_class = "status-error"
        status_text = t('status_error')
    st.markdown(f'<span class="status-badge {badge_class}">{status_text}</span>', unsafe_allow_html=True)
    if st.session_state.last_update:
        st.caption(t('last_update').format(time=st.session_state.last_update))
    
    st.markdown("---")
    
    st.markdown(f"### 📊 {t('sidebar_about')}")
    st.markdown(t('about_text'))
    
    st.markdown("---")
    
    if st.button(t('refresh_button'), use_container_width=True):
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

# ========== LIVE CLOCK IN MAIN AREA ==========
st.components.v1.html(get_live_clock_html(), height=130)

# ========== SUMMARY SECTION ==========
if weather_data:
    success_count = sum(1 for d in weather_data if d.get("status") == "success")
    
    col_summary1, col_summary2, col_summary3 = st.columns(3)
    with col_summary1:
        st.markdown(f"""
        <div class="summary-box">
            <strong>🌡️ {t('summary_avg_temp')}</strong><br>
            <span style="font-size:2rem; color:#00d4ff;">
                {sum(d.get("temperature", 0) for d in weather_data if d.get("status") == "success") / max(1, success_count):.1f}°C
            </span>
        </div>
        """, unsafe_allow_html=True)
    with col_summary2:
        st.markdown(f"""
        <div class="summary-box">
            <strong>📊 {t('summary_departments')}</strong><br>
            <span style="font-size:2rem; color:#00d4ff;">
                {success_count}/{len(HAITI_DEPARTMENTS)}
            </span>
            <span style="color:#8899bb;">{t('summary_online')}</span>
        </div>
        """, unsafe_allow_html=True)
    with col_summary3:
        st.markdown(f"""
        <div class="summary-box">
            <strong>🕒 {t('summary_last_update')}</strong><br>
            <span style="font-size:1.2rem; color:#ffffff;">
                {st.session_state.last_update}
            </span>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("---")

# ========== WEATHER CARDS ==========
st.markdown(f"### 📍 {t('weather_title')}")

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
                    desc = get_weather_description_translated(code)
                    city = dept.get("city", "")
                    dept_name = dept.get("department", "")
                    
                    # Highlight Port-au-Prince with special styling
                    is_pap = "Port-au-Prince" in city
                    border_style = "border-color: #ff6b35; border-width: 2px;" if is_pap else ""
                    
                    st.markdown(f"""
                    <div class="weather-card" style="{border_style}">
                        <div class="city">{city} { '🔥' if is_pap else '' }</div>
                        <div class="dept">{dept_name}</div>
                        <div class="weather-icon">{icon}</div>
                        <div class="temp">{temp}°C</div>
                        <div style="color:#8899bb; font-size:0.9rem;">{desc}</div>
                        <div style="color:#aabbdd; font-size:0.9rem;">{t('feels_like').format(temp=feels)}</div>
                        <div class="details">
                            <span>💧 {t('humidity')}: {humidity}%</span>
                            <span>🌧️ {t('precip')}: {precip} mm</span>
                            <span>💨 {t('wind')}: {wind} km/h</span>
                            <span>📊 {t('pressure')}: {pressure} hPa</span>
                            <span>☀️ {t('uv')}: {uv}</span>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    st.markdown(f"""
                    <div class="weather-card" style="border-color:#e74c3c;">
                        <div class="city">{dept.get('city', 'Unknown')}</div>
                        <div class="dept">{dept.get('department', 'Unknown')}</div>
                        <div style="font-size:3rem; margin:10px 0;">⚠️</div>
                        <div style="color:#e74c3c;">{t('data_unavailable')}</div>
                        <div style="color:#8899bb; font-size:0.8rem;">{t('error_connection')}</div>
                    </div>
                    """, unsafe_allow_html=True)

# ========== DETAILED TABLE ==========
with st.expander(f"📊 {t('weather_details')}", expanded=False):
    if weather_data:
        table_data = []
        for d in weather_data:
            if d.get("status") == "success":
                table_data.append({
                    t('summary_departments'): d.get("department", ""),
                    "City": d.get("city", ""),
                    "Temperature (°C)": d.get("temperature", "N/A"),
                    "Feels Like (°C)": d.get("feels_like", "N/A"),
                    t('humidity') + " (%)": d.get("humidity", "N/A"),
                    t('precip') + " (mm)": d.get("precipitation", 0),
                    t('wind') + " (km/h)": d.get("wind_speed", "N/A"),
                    t('pressure') + " (hPa)": d.get("pressure", "N/A"),
                    t('uv'): d.get("uv_index", "N/A"),
                    "Conditions": get_weather_description_translated(d.get("weather_code", 0))
                })
        if table_data:
            df = pd.DataFrame(table_data)
            st.dataframe(df, use_container_width=True, height=400)
            
            csv = df.to_csv(index=False)
            st.download_button(
                label=t('download_csv'),
                data=csv,
                file_name=f"haiti_weather_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv",
                use_container_width=True
            )

# ========== AUTO-REFRESH ==========
if 'next_refresh' not in st.session_state:
    st.session_state.next_refresh = time.time() + 900

if time.time() > st.session_state.next_refresh:
    st.session_state.next_refresh = time.time() + 900
    st.cache_data.clear()
    st.rerun()

# ========== FOOTER ==========
st.markdown(f"""
<div class="footer">
    <p>{t('footer_text')}</p>
    <p>{t('footer_built')}</p>
    <p style="font-size:0.8rem; color:#445566;">
        {t('footer_powered')}
    </p>
</div>
""", unsafe_allow_html=True)
