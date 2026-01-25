import streamlit as st
import pandas as pd
import math
import requests
import google.generativeai as genai
from io import BytesIO
from PIL import Image

# --- 0. 驗證邏輯 ---
def check_password():
    if "password_correct" not in st.session_state:
        st.title("🔐 Sharetea 系統門禁")
        password = st.text_input("請輸入密碼以開啟引擎", type="password")
        if st.button("開啟引擎"):
            if password == "sharetea2026":
                st.session_state["password_correct"] = True
                st.rerun()
            else: 
                st.error("😕 密碼錯誤")
        return False
    return True

if check_password():
    # --- 1. UI 配置 ---
    st.set_page_config(page_title="Sharetea Express 2026 戰略診斷", layout="wide")
    st.markdown("""
        <style>
        .stApp { background-color: #0E1117; color: #E6EDF3; }
        .definition-box { background-color: #1C2128; border-left: 3px solid #238636; padding: 15px; margin-bottom: 10px; border-radius: 4px; font-size: 0.85em; }
        div[data-testid="metric-container"] { background-color: #1C2128; border: 1px solid #30363D; padding: 15px; border-radius: 8px; }
        .formula-card { background-color: #0D1117; padding: 20px; border-radius: 8px; border: 1px solid #30363D; text-align: center; margin-bottom: 20px; }
        </style>
        """, unsafe_allow_html=True)

    # --- 2. 側邊欄：物理空間與座標 ---
    st.sidebar.header("📐 物理空間與座標系統")
    coord_input = st.sidebar.text_input("座標 (Lat, Lng):", placeholder="34.1425, -118.0483")
    
    cust_area = st.sidebar.slider("顧客活動空間 (sq. ft.):", 100, 600, 300)
    seat_choice = st.sidebar.radio("預計座位數:", ["0-5 席", "6-12 席", "13-20 席", "21 席以上"])
    
    # 計算人均空間與壓力係數 (ADA 基準)
    est_seats = 5 if "0-5" in seat_choice else 12 if "6-12" in seat_choice else 20 if "13-20" in seat_choice else 30
    area_per_seat = cust_area / est_seats
    
    if area_per_seat >= 35:
        pressure_coeff, quality_status, q_color = 1.2, "✨ 極致清晰", "green"
    elif area_per_seat >= 25:
        pressure_coeff, quality_status, q_color = 1.0, "✅ 標準質感", "blue"
    elif area_per_seat >= 15:
        pressure_coeff, quality_status, q_color = 0.75, "⚠️ 體驗過載", "orange"
    else:
        pressure_coeff, quality_status, q_color = 0.5, "🚨 嚴重雜訊", "red"
    
    st.sidebar.markdown("---")
    st.sidebar.subheader("📐 物理診斷報告")
    st.sidebar.write(f"人均空間: **{area_per_seat:.1f} sq. ft.**")
    st.sidebar.markdown(f"空間質量建議：<span style='color:{q_color}; font-weight:bold;'>{quality_status}</span>", unsafe_allow_html=True)

    # --- 3. API 核心與數據抓取 ---
    G_KEY = st.secrets.get("GOOGLE_KEY")
    GEMINI_KEY = st.secrets.get("GEMINI_KEY")
    C_KEY = st.secrets.get("CENSUS_KEY")

    def get_census_full_profile(lat, lng):
        try:
            geo_url = f"https://geo.fcc.gov/api/census/area?lat={lat}&lon={lng}&format=json"
            fips = requests.get(geo_url).json()['results'][0]['block_fips']
            vars = "B19013_001E,B01001_001E,B03002_006E,B03002_004E,B03002_003E,B01001_007E,B01001_008E,B01001_009E,B01001_010E,B01001_011E,B01001_012E"
            url = f"https://api.census.gov/data/2022/acs/acs5?get={vars}&for=tract:{fips[5:11]}&in=state:{fips[:2]}%20county:{fips[2:5]}&key={C_KEY}"
            d = requests.get(url).json()[1]
            pop = int(d[1]) if int(d[1]) > 0 else 1
            
            income = int(d[0])/12 if int(d[0]) > 0 else 5000
            eth = {
                "華/台裔 (核心)": int(d[2])/pop, "西裔 (核心)": int(d[3])/pop, 
                "白人 (核心)": int(d[4])/pop, "其餘族裔": (pop - int(d[2]) - int(d[3]) - int(d[4]))/pop
            }
            age_18_24 = (int(d[5])+int(d[6])+int(d[7])+int(d[8]))/pop
            age_25_34 = (int(d[9])+int(d[10]))/pop
            age = {"18-24 歲": age_18_24, "25-34 歲 (社交主力)": age_25_34, "35+ 歲": 1 - age_18_24 - age_25_34}
            return income, eth, age
        except: return 5000, {}, {}

    def get_density(lat, lng):
        try:
            url = f"https://maps.googleapis.com/maps/api/place/nearbysearch/json?location={lat},{lng}&radius=1000&keyword=boba|tea&key={G_KEY}"
            return len(requests.get(url).json().get('results', []))
        except: return 5

    # --- 4. 戰略看板與加權概述 ---
    st.title("📚 Sharetea 2026 戰略指標體系")
    st.markdown("<div class='formula-card'>", unsafe_allow_html=True)
    st.latex(r"SFS = \frac{(\text{Income} \times \text{TargetIndex}) \times 7 \times \text{PressureCoeff}}{\text{Density}^{0.7} + 1}")
    st.markdown("</div>", unsafe_allow_html=True)

    with st.expander("📊 SFS 戰略權重核算概述", expanded=True):
        sc1, sc2, sc3 = st.columns(3)
        with sc1:
            st.markdown("**👥 族裔加權 (Race Weight)**")
            st.caption("華/台裔、西裔、白人: 2.5x / 其餘: 2.0x")
        with sc2:
            st.markdown("**🎂 年齡加權 (Age Weight)**")
            st.caption("25-34歲 (主力): 2.5x / 其餘: 2.0x")
        with sc3:
            st.markdown("**🛰️ 競爭壓制 (Google Density)**")
            st.caption("1.0km 半徑 / 非線性衰減模型")

    # --- 5. 執行分析 ---
    if st.sidebar.button("Execute Strategic Analysis"):
        if not coord_input: st.error("❌ 請提供座標")
        else:
            try:
                lat, lng = [float(x.strip()) for x in coord_input.split(',')]
                with st.spinner("🚀 正在擷取維度數據並執行 DNA 對齊..."):
                    income, eth, age = get_census_full_profile(lat, lng)
                    density = get_density(lat, lng)
                    
                    # SFS 權重運算
                    race_weight = (eth.get("華/台裔 (核心)", 0) * 2.5) + (eth.get("西裔 (核心)", 0) * 2.5) + (eth.get("白人 (核心)", 0) * 2.5) + (eth.get("其餘族裔", 0) * 2.0)
                    age_weight = (age.get("25-34 歲 (社交主力)", 0) * 2.5) + (age.get("18-24 歲", 0) * 2.0) + (age.get("35+ 歲", 0) * 2.0)
                    target_index = race_weight * age_weight
                    final_sfs = (income * target_index * 7 * pressure_coeff) / (math.pow(density + 1, 0.7))
                    
                    # 分級與物理限制
                    level = "Model (M)" if final_sfs >= 15000 else "Community (C)" if final_sfs >= 8500 else "eXpress (X)"
                    if cust_area < 250: level = "高效普及 (eXpress-X) [物理受限]"

                    # 渲染數據卡片
                    m1, m2, m3, m4 = st.columns(4)
                    m1.metric("SFS 戰略總分", f"{final_sfs:.0f}")
                    m2.metric("位置分級", level.split(' ')[0])
                    m3.metric("月消費力", f"${income:,.0f}")
                    m4.metric("周邊競爭", f"{density} 家")

                    st.divider()
                    
                    # 彙整數據包
                    strategic_packet = {
                        "SFS總分": round(final_sfs), "位置分級": level, "月收入": f"${income:,.0f}",
                        "族裔結構": eth, "年齡結構": age, "空間面積": f"{cust_area} sqft",
                        "人均面積": f"{area_per_seat:.1f} sqft", "壓力係數": pressure_coeff,
                        "競爭數": density, "TargetIndex": round(target_index, 2)
                    }

                    col_map, col_ai = st.columns([1, 1])
                    with col_map:
                        map_url = f"https://maps.googleapis.com/maps/api/staticmap?center={lat},{lng}&zoom=17&size=800x640&scale=2&markers=color:red%7C{lat},{lng}&key={G_KEY}"
                        map_bytes = BytesIO(requests.get(map_url).content)
                        st.image(map_bytes, use_container_width=True, caption="📍 戰略座標 Retina 掃描")
                    
                    with col_ai:
                        st.subheader("🤖 Gemini 3 Flash 全維度解析")
                        genai.configure(api_key=GEMINI_KEY)
                        model = genai.GenerativeModel('gemini-3-flash-preview')
                        
                        brand_dna = "【2026 DNA】：現代極簡、視覺降噪、高質感屏蔽、Miffy 跨界藝術感。"
                        prompt = f"你現在是 Sharetea 2026 戰略顧問。請參考品牌 DNA：{brand_dna}\n針對以下數據包與地圖圖片進行深度判讀：\n{strategic_packet}\n請給予【營運、行銷、設計】的精準建議。"
                        
                        ai_res = model.generate_content([prompt, Image.open(map_bytes)])
                        st.markdown(ai_res.text)

            except Exception as e: st.error(f"分析報錯: {e}")

    st.caption("Produced by Marketing Designer. v10.2.5 | 數據維度全對齊模式。")
