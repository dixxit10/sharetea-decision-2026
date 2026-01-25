import streamlit as st
import pandas as pd
import numpy as np

# -----------------------------------------------------------------------------
# 1. Page Configuration & CSS Styling (The "Strategic Black" Theme)
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="Sharetea Express 2026 SFS System",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS to enforce the "Strategic Black" look
st.markdown("""
    <style>
    /* Main Background */
    .stApp {
        background-color: #0E0E0E;
        color: #E0E0E0;
    }
    h1, h2, h3 { color: #FFFFFF !important; font-family: 'Helvetica Neue', sans-serif; font-weight: 700; }
    .strategic-green { color: #00FF41 !important; font-family: 'Courier New', monospace; font-weight: bold; }
    .strategic-red { color: #FF3333 !important; font-family: 'Courier New', monospace; font-weight: bold; }
    .stTextInput > div > div > input { background-color: #1C1C1C; color: #FFFFFF; border: 1px solid #333; }
    .stSelectbox > div > div > div { background-color: #1C1C1C; color: #FFFFFF; }
    .metric-box { background-color: #1A1A1A; border-left: 3px solid #00FF41; padding: 15px; margin-bottom: 10px; }
    .ai-analysis { font-family: 'Courier New', monospace; background-color: #111; padding: 15px; border: 1px solid #333; color: #CCCCCC; white-space: pre-wrap; }
    </style>
""", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# 2. Security & Authentication Function
# -----------------------------------------------------------------------------
def check_password():
    """Returns `True` if the user had the correct password."""

    def password_entered():
        """Checks whether a password entered by the user is correct."""
        if st.session_state["password"] == st.secrets["general"]["APP_PASSWORD"]:
            st.session_state["password_correct"] = True
            del st.session_state["password"]  # don't store password
        else:
            st.session_state["password_correct"] = False

    if "password_correct" not in st.session_state:
        # First run, show input for password.
        st.markdown("### 🔒 Sharetea Express 2026 Strategic System")
        st.text_input(
            "Security Access Code", type="password", on_change=password_entered, key="password"
        )
        return False
    elif not st.session_state["password_correct"]:
        # Password not correct, show input + error.
        st.markdown("### 🔒 Sharetea Express 2026 Strategic System")
        st.text_input(
            "Security Access Code", type="password", on_change=password_entered, key="password"
        )
        st.error("⛔ ACCESS DENIED: Invalid Security Code")
        return False
    else:
        # Password correct.
        return True

# -----------------------------------------------------------------------------
# 3. Main Application Logic (Protected)
# -----------------------------------------------------------------------------
if check_password():
    
    # --- Load API Keys Safely (Ready for future integration) ---
    # 這些變數現在可以在程式碼中安全使用，例如傳遞給 Google Maps API
    try:
        CENSUS_KEY = st.secrets["api_keys"]["CENSUS_KEY"]
        GOOGLE_KEY = st.secrets["api_keys"]["GOOGLE_KEY"]
        GEMINI_KEY = st.secrets["api_keys"]["GEMINI_KEY"]
    except FileNotFoundError:
        st.error("⚠️ secrets.toml not found. Please setup your keys.")
        st.stop()

    # --- Original SFS Logic Starts Here ---
    
    def calculate_target_index(race_dist, age_dist):
        race_score = ((race_dist['Asian'] + race_dist['Hispanic'] + race_dist['White']) * 2.5 + (race_dist['Other']) * 1.0) / 100
        age_score = ((age_dist['25-34'] * 2.5) + (age_dist['18-24'] * 2.3) + (age_dist['35-45'] * 2.0) + (age_dist['Other'] * 1.0)) / 100
        return (race_score + age_score) / 2

    def get_env_weight(env_type):
        mapping = {"Shopping Mall": 1.2, "Community": 1.0, "Plaza": 1.0, "Main Street": 0.8, "Food Court": 0.8, "Transit Hub": 0.8, "Office District": 0.8}
        return mapping.get(env_type, 1.0)

    def calculate_pressure_coeff(area, seats_cat):
        seat_map = {"0-6 席": 4, "7-12 席": 10, "13-20 席": 17, "20+ 席": 25}
        est_seats = seat_map.get(seats_cat, 10)
        if est_seats == 0: est_seats = 1
        sqft_per_person = area / est_seats
        if sqft_per_person >= 35: return 1.2, sqft_per_person, "視覺純淨 (Visual Clarity)"
        elif sqft_per_person < 15: return 0.5, sqft_per_person, "嚴重過載 (Overload)"
        else: return 1.0, sqft_per_person, "標準平衡 (Balanced)"

    def determine_store_model(sfs):
        if sfs >= 15000: return "Model (M)", "品牌綠洲店", "質感溢價、感官引導"
        elif sfs >= 8500: return "Community (C)", "社區標準店", "社交黏度、鄰里連結"
        else: return "eXpress (X)", "高效機能店", "能效轉換、快速取餐"

    # --- Sidebar ---
    st.sidebar.markdown("### ⬅️ Strategic Input")
    st.sidebar.markdown("---")
    loc_name = st.sidebar.text_input("店名 / 專案代號", "Sharetea DTLA-01")
    coords = st.sidebar.text_input("Google Maps 座標", "34.0407, -118.2468")
    env_type = st.sidebar.selectbox("地段基因 (Environment)", ["Shopping Mall", "Community", "Plaza", "Main Street", "Food Court", "Transit Hub", "Office District"])
    
    st.sidebar.markdown("#### 物理空間")
    area_sqft = st.sidebar.number_input("顧客活動空間 (sq. ft.)", 100, 600, 250)
    seats_cat = st.sidebar.radio("預計座位數", ["0-6 席", "7-12 席", "13-20 席", "20+ 席"], index=1)
    
    st.sidebar.markdown("#### 市場數據")
    monthly_income = st.sidebar.number_input("預估月營收 ($)", value=45000)
    density = st.sidebar.number_input("1km 競業密度", value=5)

    st.sidebar.markdown("---")
    st.sidebar.markdown("#### 族裔分布 (%)")
    race_asian = st.sidebar.slider("華/台/亞裔 %", 0, 100, 40)
    race_hisp = st.sidebar.slider("西裔 %", 0, 100, 20)
    race_white = st.sidebar.slider("白人 %", 0, 100, 20)
    race_other = max(0, 100 - (race_asian + race_hisp + race_white))
    st.sidebar.caption(f"其他族裔: {race_other}%")

    st.sidebar.markdown("#### 年齡分布 (%)")
    age_25_34 = st.sidebar.slider("25-34 歲 %", 0, 100, 35)
    age_18_24 = st.sidebar.slider("18-24 歲 %", 0, 100, 25)
    age_35_45 = st.sidebar.slider("35-45 歲 %", 0, 100, 20)
    age_other = max(0, 100 - (age_25_34 + age_18_24 + age_35_45))
    st.sidebar.caption(f"其他: {age_other}%")

    execute_btn = st.sidebar.button("執行戰略分析 Execute", type="primary")

    # --- Header ---
    with st.expander("📐 SFS 核心運算邏輯 (已驗證 Access Granted)", expanded=False):
        st.write("System Integrity Check: OK. Keys Loaded.")

    if execute_btn:
        # Calcs
        race_dist = {'Asian': race_asian, 'Hispanic': race_hisp, 'White': race_white, 'Other': race_other}
        age_dist = {'25-34': age_25_34, '18-24': age_18_24, '35-45': age_35_45, 'Other': age_other}
        target_index = calculate_target_index(race_dist, age_dist)
        env_weight = get_env_weight(env_type)
        pressure_coeff, sqft_pp, pressure_status = calculate_pressure_coeff(area_sqft, seats_cat)
        numerator = (monthly_income * target_index * env_weight) * 7 * pressure_coeff
        denominator = (density ** 0.7) + 1
        sfs_score = numerator / denominator
        model_code, model_name, model_task = determine_store_model(sfs_score)

        # Output
        st.title(f"📍 戰略決策報告: {loc_name}")
        st.markdown(f"**座標**: `{coords}` (API 連線準備就緒)")

        col1, col2, col3, col4 = st.columns(4)
        with col1: st.markdown(f"<div class='metric-box'><h3>SFS 總分</h3><span class='strategic-green' style='font-size: 32px'>{int(sfs_score):,}</span></div>", unsafe_allow_html=True)
        with col2: 
            color_class = "strategic-green" if "M" in model_code else "white"
            st.markdown(f"<div class='metric-box'><h3>店型判定</h3><span class='{color_class}' style='font-size: 24px'>{model_code}</span><br><small>{model_name}</small></div>", unsafe_allow_html=True)
        with col3: st.markdown(f"<div class='metric-box'><h3>Target Index</h3><span style='font-size: 24px'>{target_index:.2f}x</span></div>", unsafe_allow_html=True)
        with col4:
            p_color = "strategic-red" if pressure_coeff < 1.0 else "strategic-green"
            st.markdown(f"<div class='metric-box'><h3>Pressure Coeff</h3><span class='{p_color}' style='font-size: 24px'>{pressure_coeff}x</span><br><small>{pressure_status}</small></div>", unsafe_allow_html=True)

        st.markdown("### 2. 全透明數據明細")
        c1, c2 = st.columns(2)
        with c1: 
            st.markdown("**族裔結構**")
            st.dataframe(pd.DataFrame([race_dist]).T.rename(columns={0:'%'}), use_container_width=True)
        with c2: 
            st.markdown("**年齡結構**")
            st.dataframe(pd.DataFrame([age_dist]).T.rename(columns={0:'%'}), use_container_width=True)

        # Analysis Text Generation
        if "M" in model_code:
            design_strat = "全屏蔽式設計隔離外部視覺噪音。大量運用暖米白清水模。"
            ops_strat = "藝廊式引導：降低單位時間服務人次，增加停留質感。"
        elif "C" in model_code:
            design_strat = "保留部分通透性以吸引鄰里目光。"
            ops_strat = "混合模式：尖峰時刻快速取餐，離峰時刻社交中心。"
        else:
            design_strat = "磨砂金屬，強調功能性與識別速度。"
            ops_strat = "F1 維修站模式：導入全自助點餐機。"
            
        ai_content = f"""
[ SYSTEM GENERATED REPORT - 2026 STRATEGIC PROTOCOL ]
-----------------------------------------------------
TARGET MODEL   : {model_code} - {model_name}
MISSION        : {model_task}

[ 營運與行銷方針 ]
-----------------------------------------------------
> 動線策略: {ops_strat}
> 品牌 DNA: {design_strat}
> 獲客總結: Index {target_index:.2f}x. {"建議投入最高級別預算" if target_index > 2.0 else "建議折扣策略"}。
        """
        st.markdown(f"<div class='ai-analysis'>{ai_content}</div>", unsafe_allow_html=True)

else:
    # Stop execution if password is wrong
    st.stop()
