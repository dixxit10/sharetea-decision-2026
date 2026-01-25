import streamlit as st
import pandas as pd
import math
import requests
import google.generativeai as genai
from io import BytesIO
from PIL import Image

# --- 0. 系統配置與 CSS (戰略黑主題) ---
st.set_page_config(page_title="Sharetea Express 2026 戰略診斷", layout="wide")

st.markdown("""
    <style>
    /* 全域背景 */
    .stApp { background-color: #0E0E0E; color: #E0E0E0; }
    
    /* 定義框樣式 */
    .definition-box { 
        background-color: #1A1A1A; 
        border-left: 3px solid #00FF41; 
        padding: 15px; 
        margin-bottom: 10px; 
        border-radius: 4px; 
        font-size: 0.9em; 
    }
    
    /* 數據指標卡片 */
    div[data-testid="metric-container"] { 
        background-color: #1C1C1C; 
        border: 1px solid #333; 
        padding: 15px; 
        border-radius: 8px; 
        color: #fff; 
    }
    label { color: #fff !important; }
    
    /* 載入動畫顏色 */
    .stSpinner > div { border-top-color: #00FF41 !important; }
    </style>
""", unsafe_allow_html=True)

# --- 1. 安全驗證邏輯 ---
def check_password():
    try:
        pwd = st.secrets["general"]["APP_PASSWORD"]
    except:
        pwd = "sharetea2026" 

    def password_entered():
        if st.session_state["password"] == pwd:
            st.session_state["password_correct"] = True
            del st.session_state["password"]
        else:
            st.session_state["password_correct"] = False

    if "password_correct" not in st.session_state:
        st.markdown("### 🔐 Sharetea 系統門禁")
        st.text_input("Security Access Code", type="password", on_change=password_entered, key="password")
        st.button("開啟戰略引擎", on_click=password_entered)
        return False
    elif not st.session_state["password_correct"]:
        st.markdown("### 🔐 Sharetea 系統門禁")
        st.text_input("Security Access Code", type="password", on_change=password_entered, key="password")
        st.button("開啟戰略引擎", on_click=password_entered)
        st.error("😕 密碼錯誤")
        return False
    else:
        return True

if check_password():
    # --- 2. 讀取 API Keys ---
    try:
        G_KEY = st.secrets["api_keys"]["GOOGLE_KEY"]
        GEMINI_KEY = st.secrets["api_keys"]["GEMINI_KEY"]
        C_KEY = st.secrets["api_keys"]["CENSUS_KEY"]
    except KeyError:
        st.error("⚠️ Secrets 設定不完整，請檢查 Streamlit 後台設定。")
        st.stop()

    # --- 3. 側邊欄：輸入區 ---
    st.sidebar.header("📐 物理空間與座標")
    
    location_input = st.sidebar.text_input(
        "目標位置 (地址 或 Lat,Lng):", 
        value="18558 Gale Ave, City of Industry, CA",
        help="輸入完整地址自動解析，或輸入 '緯度,經度'"
    )
    
    st.sidebar.markdown("---")
    st.sidebar.markdown("#### 空間參數")
    cust_area = st.sidebar.slider("顧客活動空間 (sq. ft.):", 100, 600, 300)
    seat_choice = st.sidebar.radio("預計座位數:", ["0-5 席", "6-12 席", "13-20 席", "21 席以上"], index=1)
    
    # 計算人均空間
    est_seats = 5 if "0-5" in seat_choice else 12 if "6-12" in seat_choice else 20 if "13-20" in seat_choice else 30
    area_per_seat = cust_area / est_seats if est_seats > 0 else 0
    
    # 空間壓力係數判定
    if area_per_seat >= 35:
        pressure_coeff = 1.2
        quality_status = "✨ 極致清晰 (Visual Clarity)"
        q_color = "#00FF41"
    elif area_per_seat >= 25:
        pressure_coeff = 1.0
        quality_status = "✅ 標準質感 (Standard)"
        q_color = "#3399FF"
    elif area_per_seat >= 15:
        pressure_coeff = 0.75
        quality_status = "⚠️ 體驗過載 (Overload)"
        q_color = "#FFAA00"
    else:
        pressure_coeff = 0.5
        quality_status = "🚨 嚴重雜訊 (Noise)"
        q_color = "#FF3333"
    
    st.sidebar.markdown(f"人均空間: **{area_per_seat:.1f} sq. ft.**")
    st.sidebar.markdown(f"判定: <span style='color:{q_color}; font-weight:bold;'>{quality_status}</span>", unsafe_allow_html=True)
    st.sidebar.caption(f"壓力補償係數: {pressure_coeff}x")

    # --- 4. 核心工具函式 (強化版) ---
    
    def resolve_location(input_str):
        """解析地址或座標，加入異常處理"""
        try:
            # 1. 嘗試解析為座標
            if "," in input_str and any(c.isdigit() for c in input_str):
                try:
                    parts = input_str.split(',')
                    # 確保只有兩個部分是數字
                    if len(parts) >= 2:
                        lat = float(parts[0].strip())
                        lng = float(parts[1].strip())
                        return lat, lng, f"座標: {lat}, {lng}"
                except ValueError:
                    pass # 如果轉換失敗，就當作地址處理

            # 2. 解析為地址
            url = f"https://maps.googleapis.com/maps/api/geocode/json?address={input_str}&key={G_KEY}"
            resp = requests.get(url, timeout=10).json()
            if resp['status'] == 'OK':
                loc = resp['results'][0]['geometry']['location']
                fmt_addr = resp['results'][0]['formatted_address']
                return loc['lat'], loc['lng'], fmt_addr
            else:
                return None, None, None
        except Exception as e:
            return None, None, None

    def get_census_data(lat, lng):
        """獲取人口數據，加入非美國地區的 Fallback 機制"""
        try:
            # FCC API (座標 -> FIPS)
            geo_url = f"https://geo.fcc.gov/api/census/area?lat={lat}&lon={lng}&format=json"
            fips_resp = requests.get(geo_url, timeout=5).json()
            
            #
