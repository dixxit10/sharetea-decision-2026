import streamlit as st
import pandas as pd
import math
import requests
import google.generativeai as genai
from io import BytesIO
from PIL import Image

# --- 0. 密碼驗證邏輯 ---
def check_password():
    if "password_correct" not in st.session_state:
        st.title("🔐 Sharetea 系統門禁")
        password = st.text_input("請輸入密碼以開啟引擎", type="password", key="password_gate")
        if st.button("開啟引擎"):
            if password == "sharetea2026":
                st.session_state["password_correct"] = True
                st.rerun()
            else:
                st.error("😕 密碼錯誤")
        return False
    return True

if check_password():
    # --- 1. UI & CSS 配置 ---
    st.set_page_config(page_title="Sharetea Express 2026 全方位評估", layout="wide")
    st.markdown("""
        <style>
        .stApp { background-color: #0E1117; color: #E6EDF3; font-family: 'Inter', sans-serif; }
        .definition-box { background-color: #1C2128; border-left: 3px solid #238636; padding: 20px; margin-bottom: 20px; border-radius: 0 4px 4px 0; }
        div[data-testid="metric-container"] { background-color: #1C2128; border: 1px solid #30363D; padding: 25px; border-radius: 8px; }
        .stButton>button { background: #238636; color: white; border: none; border-radius: 4px; font-weight: 500; width: 100%; height: 3.5em; }
        </style>
        """, unsafe_allow_html=True)

    # --- 2. 側邊欄輸入：【即時運算區】 ---
    st.sidebar.header("📍 戰略座標輸入")
    coord_input = st.sidebar.text_input("座標 (Lat, Lng):", placeholder="34.1353, -118.0353")
    loc_type = st.sidebar.selectbox("地點型態:", ["Plaza", "Shopping Mall", "Main Street", "Community"])
    
    st.sidebar.markdown("---")
    cust_area = st.sidebar.slider("顧客活動空間 (sq. ft.):", 200, 460, 300)
    seat_choice = st.sidebar.radio("座位數:", ["0-5 席", "6-12 席", "13-20 席"])

    # 🚀 【核心修正 1：恢復拉動即時顯示】
    # 此邏輯位於按鈕外，確保 UI 實時反應空間質量
    est_seats = 5 if "0-5" in seat_choice else 12 if "6-12" in seat_choice else 20
    area_per_seat = cust_area / est_seats
    pressure_coeff = 1.2 if area_per_seat >= 30 else 1.0 if area_per_seat >= 25 else 0.75
    quality_label = "✨ 極致清晰" if pressure_coeff == 1.2 else "✅ 標準質感" if pressure_coeff == 1.0 else "⚠️ 體驗過載"
    
    st.sidebar.subheader("📐 空間美學診斷")
    st.sidebar.info(f"當前質量判定：{quality_label}")
    st.sidebar.caption(f"人均空間：{area_per_seat:.1f} sq. ft. (壓力係數: {pressure_coeff})")

    # --- 3. 配置與數據對接函數 ---
    G_KEY = st.secrets.get("GOOGLE_KEY")
    GEMINI_KEY = st.secrets.get("GEMINI_KEY")
    CENSUS_KEY = st.secrets.get("CENSUS_KEY")

    def get_census_full_profile(lat, lng, api_key):
        try:
            geo_url = f"https://geo.fcc.gov/api/census/area?lat={lat}&lon={lng}&format=json"
            geo_res = requests.get(geo_url).json()
            fips = geo_res['results'][0]['block_fips']
            state, county, tract = fips[:2], fips[2:5], fips[5:11]
            
            vars = "B19013_001E,B01001_001E,B03002_006E,B03002_004E,B03002_003E,B03002_012E,B03002_005E," + \
                   "B01001_007E,B01001_008E,B01001_009E,B01001_010E,B01001_031E,B01001_032E,B01001_033E,B01001_034E," + \
                   "B01001_011E,B01001_012E,B01001_035E,B01001_036E"
            census_url = f"https://api.census.gov/data/2022/acs/acs5?get={vars}&for=tract:{tract}&in=state:{state}%20county:{county}&key={api_key}"
            res = requests.get(census_url).json()
            d = res[1]
            total_pop = int(d[1]) if int(d[1]) > 0 else 1
            income = int(d[0]) / 12 if int(d[0]) > 0 else 0
            
            eth = {"華裔/東亞裔": int(d[2])/total_pop, "墨西哥裔/西裔": int(d[3])/total_pop, "白人": int(d[4])/total_pop, "東南亞裔": int(d[5])/total_pop}
            age = {"18-24 歲": sum(int(x) for x in d[7:15])/total_pop, "25-34 歲 (社交主力)": sum(int(x) for x in d[15:19])/total_pop}
            return income, eth, age
        except: return None, None, None

    def get_vision_analysis(image_bytes, sfs_context, api_key):
        try:
            genai.configure(api_key=api_key)
            model = genai.GenerativeModel('gemini-1.5-flash')
            img = Image.open(image_bytes)
            prompt = f"依照營運、行銷、設計角度判讀此地圖。數據：{sfs_context}。分析 M/C/X 定位是否與視覺雜訊(加油站/汽修)衝突並給予建議。"
            response = model.generate_content([prompt, img])
            return response.text
        except: return "AI 診斷異常。"

    # --- 4. 戰略報告呈現 ---
    st.title("📚 名詞定義 v8.9.8")
    # ... (此處保留原本的名詞定義區塊文字，維持結構)

    if st.sidebar.button("Execute Strategic Analysis"):
        if not coord_input: st.error("請提供座標。")
        else:
            try:
                parts = coord_input.split(',')
                lat, lng = float(parts[0].strip()), float(parts[1].strip())
                
                with st.spinner("正在執行全數據對接..."):
                    income, dynamic_eth, dynamic_age = get_census_full_profile(lat, lng, CENSUS_KEY)
                    
                    # 🚀 【核心修正 2：確保人口普查結果正確渲染】
                    if income is None:
                        st.error("❌ 普查連線中斷。請檢查 CENSUS_KEY 或座標。")
                    else:
                        real_density = 12 # 示意數值，或接入 Places API
                        target_index = (dynamic_eth.get("華裔/東亞裔", 0) * 2.5) + (dynamic_age.get("25-34 歲 (社交主力)", 0) * 3.0)
                        final_sfs = ((income * (target_index if target_index > 0 else 1)) * 7 * 1.1 * pressure_coeff) / (math.pow(real_density + 1, 0.7))
                        level = "品牌指標 (Model-M)" if final_sfs >= 15000 else "社區標準 (Community-C)" if final_sfs >= 8500 else "高效普及 (eXpress-X)"

                        # --- 渲染結果 ---
                        m1, m2 = st.columns([2, 1])
                        with m1:
                            st.image(f"https://maps.googleapis.com/maps/api/staticmap?center={lat},{lng}&zoom=17&size=800x450&scale=2&key={G_KEY}", use_container_width=True)
                        with m2:
                            st.metric("SFS 戰略總分", f"{final_sfs:.0f}")
                            st.metric("位置分級", level)
                            st.metric("月消費力", f"${income:,.0f}")
                        
                        st.divider()
                        d1, d2 = st.columns(2)
                        with d1:
                            st.subheader("👥 實時族群與詳細年齡")
                            st.table(pd.DataFrame(dynamic_eth.items(), columns=["族裔", "比例"]).style.format({"比例":"{:.1%}"}))
                            st.table(pd.DataFrame(dynamic_age.items(), columns=["年齡段", "比例"]).style.format({"比例":"{:.1%}"}))
                        
                        with d2:
                            st.subheader("🧠 全維度戰略定位")
                            # M/C/X 複合判定邏輯
                            if income > 7500 and dynamic_age.get("25-34 歲 (社交主力)", 0) > 0.3:
                                store_type, advice = "Model (M)", "💎 重點：『視覺降噪』，建立品牌綠洲。"
                            elif income > 5000 and dynamic_age.get("18-24 歲", 0) > 0.25:
                                store_type, advice = "Community (C)", "📸 重點：強化視覺張力與 Miffy 聯名吸睛度。"
                            else:
                                store_type, advice = "eXpress (X)", "🛵 重點：高效動線與機能模組。"
                            
                            st.metric("建議店型定位", store_type)
                            st.warning(advice)
                            if store_type == "Model (M)":
                                st.error("⚠️ 環境警示：存在質感斷層，建議採用『全屏蔽式』設計以維持 Clarity。")

            except Exception as e: st.error(f"分析報錯: {e}")

    st.caption("Produced by Marketing Designer. v9.2.0 | Reducing Noise. Increasing Clarity.")
