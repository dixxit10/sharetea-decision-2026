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
        password = st.text_input("請輸入密碼", type="password")
        if st.button("開啟引擎"):
            if password == "sharetea2026":
                st.session_state["password_correct"] = True
                st.rerun()
            else: st.error("😕 密碼錯誤")
        return False
    return True

if check_password():
    # --- 1. UI & 定義區 ---
    st.set_page_config(page_title="Sharetea 2026 全維度評估", layout="wide")
    st.title("📚 名詞定義與戰略架構")
    
    # 使用 LaTeX 呈現對齊後的 SFS 公式
    st.markdown("<div style='background-color: #1C2128; padding: 20px; border-radius: 8px; border: 1px solid #30363D;'>", unsafe_allow_html=True)
    st.latex(r"SFS = \frac{(Spending \times TargetIndex) \times 7 \times EnvFactor \times PressureCoeff}{Density^{0.7} + 1}")
    st.markdown("</div>", unsafe_allow_html=True)
    
    # 名詞定義塊
    def_cols = st.columns(3)
    definitions = [
        ("SFS 戰略總分", "地段獲利潛力核心指標。"),
        ("空間壓力係數", "人均 < 25 sqft 時下修分值。"),
        ("環境與地段基因", "AI 掃描地圖識別鄰里質感。"),
        ("月均消費力", "CENSUS API 實時收入中位數。"),
        ("分級基準", "M: 15k+ / C: 8.5k+ / X: <8.5k"),
        ("顧客活動區", "200-460 sqft 效能區間。")
    ]
    for i, (title, desc) in enumerate(definitions):
        with def_cols[i % 3]:
            st.markdown(f"<div style='background-color: #161B22; border-left: 3px solid #238636; padding: 10px; margin-bottom: 10px;'><b>{title}</b><br>{desc}</div>", unsafe_allow_html=True)

    # --- 2. 側邊欄輸入 ---
    st.sidebar.header("📍 戰略座標輸入")
    coord_input = st.sidebar.text_input("座標 (Lat, Lng):", placeholder="34.1353, -118.0353")
    loc_type = st.sidebar.selectbox("地點型態:", ["Plaza", "Shopping Mall", "Main Street", "Community"])
    cust_area = st.sidebar.slider("顧客活動空間 (sq. ft.):", 200, 460, 300)
    seat_choice = st.sidebar.radio("座位數:", ["0-5 席", "6-12 席", "13-20 席"])

    # 空間壓力係數預算
    est_seats = 5 if "0-5" in seat_choice else 12 if "6-12" in seat_choice else 20
    area_per_seat = cust_area / est_seats
    pressure_coeff = 1.2 if area_per_seat >= 30 else 1.0 if area_per_seat >= 25 else 0.75

    # --- 3. API 核心函數 ---
    G_KEY = st.secrets["GOOGLE_KEY"]
    GEM_KEY = st.secrets["GEMINI_KEY"]
    C_KEY = st.secrets["CENSUS_KEY"]

    def get_census_data(lat, lng):
        try:
            geo_url = f"https://geo.fcc.gov/api/census/area?lat={lat}&lon={lng}&format=json"
            fips = requests.get(geo_url).json()['results'][0]['block_fips']
            vars = "B19013_001E,B01001_001E,B03002_006E,B03002_004E,B03002_012E,B01001_007E,B01001_011E"
            census_url = f"https://api.census.gov/data/2022/acs/acs5?get={vars}&for=tract:{fips[5:11]}&in=state:{fips[:2]}%20county:{fips[2:5]}&key={C_KEY}"
            d = requests.get(census_url).json()[1]
            income = int(d[0])/12
            pop = int(d[1])
            eth = {"東亞裔": int(d[2])/pop, "西裔": int(d[3])/pop, "南亞裔": int(d[4])/pop}
            age = {"18-24": int(d[5])/pop, "25-34": int(d[6])/pop}
            return income, eth, age
        except: return 5000, {}, {}

    def get_density(lat, lng):
        try:
            url = f"https://maps.googleapis.com/maps/api/place/nearbysearch/json?location={lat},{lng}&radius=1000&keyword=boba|tea&key={G_KEY}"
            return len(requests.get(url).json().get('results', []))
        except: return 5

    # --- 4. 執行評估 ---
    if st.sidebar.button("Execute Strategic Analysis"):
        if not coord_input: st.error("請提供座標")
        else:
            lat, lng = [float(x.strip()) for x in coord_input.split(',')]
            with st.spinner("📡 正在同步所有維度數據..."):
                # 數據收集
                income, eth, age = get_census_data(lat, lng)
                density = get_density(lat, lng)
                
                # SFS 計算
                target_index = (eth.get("東亞裔", 0) * 3.0) + (age.get("25-34", 0) * 2.5)
                final_sfs = ((income * (target_index if target_index > 0 else 1.1)) * 7 * 1.15 * pressure_coeff) / (math.pow(density + 1, 0.7))
                level = "Model (M)" if final_sfs >= 15000 else "Community (C)" if final_sfs >= 8500 else "eXpress (X)"

                # --- 渲染數據面板 ---
                col_map, col_metric = st.columns([2, 1])
                with col_map:
                    map_url = f"https://maps.googleapis.com/maps/api/staticmap?center={lat},{lng}&zoom=17&size=800x450&scale=2&markers=color:red%7C{lat},{lng}&key={G_KEY}"
                    map_bytes = BytesIO(requests.get(map_url).content)
                    st.image(map_bytes, use_container_width=True, caption="📍 實時地圖掃描")
                
                with col_metric:
                    st.metric("SFS 戰略總分", f"{final_sfs:.0f}")
                    st.metric("位置分級", level)
                    st.metric("周邊競爭數", f"{density} 家")
                    st.metric("月消費力", f"${income:,.0f}")

                st.divider()
                
                # 準備 AI 判讀包
                strategic_packet = {
                    "SFS分數": round(final_sfs),
                    "位置分級": level,
                    "族裔結構": eth,
                    "年齡結構": age,
                    "月均收入": f"${income:,.0f}",
                    "人均活動空間": f"{area_per_seat:.1f} sqft",
                    "空間壓力係數": pressure_coeff,
                    "周邊競爭數": density,
                    "地點型態": loc_type
                }

                # --- 🤖 Gemini 3 全維度解析 ---
                st.subheader("🤖 Gemini 3 Flash 全方位戰略判讀")
                genai.configure(api_key=GEM_KEY)
                model = genai.GenerativeModel('gemini-3-flash-preview')
                
                prompt = f"""
                你現在是 Sharetea 2026 品牌戰略顧問。請針對以下實時數據包與地圖截圖，進行『對齊解析』。
                
                【戰略數據包內容】：
                {strategic_packet}
                
                核心任務：
                1. 識別地圖截圖中的『視覺雜訊』(如加油站、車行、快餐店) 是否與 SFS 分級衝突。
                2. 判斷該區消費者的到店目的 (目的型社交、路過取餐、還是質感生活)。
                3. 給予三維度執行建議：
                   - 【營運】：人力配置、動線優化。
                   - 【行銷】：推廣策略、族群觸達。
                   - 【設計】：空間風格、視覺屏蔽需求。
                """
                
                ai_response = model.generate_content([prompt, Image.open(map_bytes)])
                st.markdown(ai_response.text)

    st.caption("Produced by Marketing Designer. v9.9.0 | 數據與 AI 對齊模式已開啟。")
