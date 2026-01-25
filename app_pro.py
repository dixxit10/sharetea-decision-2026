import streamlit as st
import pandas as pd
import math
import requests
import google.generativeai as genai
from io import BytesIO
from PIL import Image

# --- 0. 系統配置與 CSS ---
st.set_page_config(page_title="Sharetea Express 2026 戰略診斷", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #0E0E0E; color: #E0E0E0; }
    .definition-box { 
        background-color: #1A1A1A; 
        border-left: 3px solid #00FF41; 
        padding: 15px; 
        margin-bottom: 10px; 
        border-radius: 4px; 
        font-size: 0.9em; 
    }
    div[data-testid="metric-container"] { 
        background-color: #1C1C1C; 
        border: 1px solid #333; 
        padding: 15px; 
        border-radius: 8px; 
        color: #fff; 
    }
    label { color: #fff !important; }
    .stSpinner > div { border-top-color: #00FF41 !important; }
    </style>
""", unsafe_allow_html=True)

# --- 1. 安全驗證邏輯 (改用 Form 表單，絕對防崩潰) ---
def check_password():
    # 如果已經登入成功，直接回傳 True
    if st.session_state.get("password_correct", False):
        return True

    # 安全讀取正確密碼
    try:
        correct_pwd = st.secrets["general"]["APP_PASSWORD"]
    except:
        correct_pwd = "sharetea2026"

    # 使用 Form 表單，這是最穩定的輸入方式
    with st.form("login_form"):
        st.markdown("### 🔐 Sharetea 系統門禁")
        # 這裡不使用 on_change，避免 KeyError
        input_pwd = st.text_input("Security Access Code", type="password")
        submit_button = st.form_submit_button("開啟戰略引擎")

    if submit_button:
        if input_pwd == correct_pwd:
            st.session_state["password_correct"] = True
            st.rerun() # 登入成功後立即刷新頁面
        else:
            st.error("😕 密碼錯誤")
            
    return False

# 程式進入點
if check_password():
    
    # --- 2. 讀取 API Keys (安全讀取器) ---
    def get_api_key(key_name):
        try:
            return st.secrets["api_keys"][key_name]
        except:
            return None

    G_KEY = get_api_key("GOOGLE_KEY")
    GEMINI_KEY = get_api_key("GEMINI_KEY")
    C_KEY = get_api_key("CENSUS_KEY")

    if not G_KEY:
        st.warning("⚠️ 警告：未偵測到 Google Maps API Key，地圖與定位功能將無法使用。")

    # --- 3. 側邊欄輸入 ---
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
    
    # 空間壓力
