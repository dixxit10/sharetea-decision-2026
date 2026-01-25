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
        .formula-card { background-color: #0D1117; padding: 25px; border-radius: 8px; border: 1px solid #30363D; text-align: center; margin-bottom: 25px; }
        .logic-card { background-color: #161B22; padding: 20px; border-radius: 8px; border-top: 2px solid #238636; margin-bottom: 20px; }
        </style>
        """, unsafe_allow_html=True)

    # --- 2. 側邊欄：物理空間與座標 ---
    st.sidebar.header("📐 物理空間與座標系統")
    coord_input = st.sidebar.text_input("座標 (Lat, Lng):", placeholder="34.1425, -118.0483")
    
    cust_area = st.sidebar.slider("顧客活動空間 (sq. ft.):", 100, 600, 300)
    seat_choice = st.sidebar.radio("預計座位數:", ["0-5 席", "6-12 席", "13-20 席", "21 席以上"])
    
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
    st.sidebar.markdown(f"空間質量：<span style='color:{q_color}; font-weight:bold;'>{quality_status}</span>", unsafe_allow_html=True)

    # --- 3. API 核心定義 ---
    G_KEY = st.secrets.get("GOOGLE_KEY")
    GEMINI_KEY = st.secrets.get("GEMINI_KEY")
    C_KEY = st.secrets.get("CENSUS_KEY")

    def get_census_full_profile(lat, lng):
        try:
            geo_url = f"https://geo.fcc.gov/api/census/area?lat={lat}&lon={lng}&format=json"
            fips = requests.get(geo_url).json()['results'][0]['block_fips']
            vars = "B19013_001E,B01001_001E,B03002_006E,B03002_012E,B03002_004E,B03002_003E,B01001_007E,B01001_008E,B01001_009E,B01001_010E,B01001_011E,B01001_012E"
            url = f"https://api.census.gov/data/2022/acs/acs5?get={vars}&for=tract:{fips[5:11]}&in=state:{fips[:2]}%20county:{fips[2:5]}&key={C_KEY}"
            d = requests.get(url).json()[1]
            pop = int(d[1]) if int(d[1]) > 0 else 1
            income = int(d[0])/12 if int(d[0]) > 0 else 5000
            eth = {"華/台裔": int(d[2])/pop, "西裔": int(d[3])/pop, "白人": int(d[5])/pop, "其餘": (pop-int(d[2])-int(d[3])-int(d[5]))/pop}
            age_18_24 = (int(d[6])+int(d[7])+int(d[8])+int(d[9]))/pop
            age_25_34 = (int(d[10])+int(d[11]))/pop
            age = {"18-24": age_18_24, "25-34": age_25_34, "35+": 1 - age_18_24 - age_25_34}
            return income, eth, age
        except: return 5000, {}, {}

    def get_expanded_density(lat, lng):
        """擴大競業定義：包含餐飲(Restaurant)與甜點(Bakery/Dessert)"""
        try:
            url = f"https://maps.googleapis.com/maps/api/place/nearbysearch/json?location={lat},{lng}&radius=1000&keyword=tea|boba|coffee|dessert|bakery|restaurant&key={G_KEY}"
            res = requests.get(url).json()
            return len(res.get('results', []))
        except: return 15

    # --- 4. 名詞解釋與邏輯計算區 (完全展開) ---
    st.title("📚 Sharetea 2026 戰略指標與加權邏輯")
    st.markdown("<div class='formula-card'>", unsafe_allow_html=True)
    st.latex(r"SFS = \frac{(\text{Monthly Income} \times \text{Target Index}) \times 7 \times \text{Pressure Coeff}}{\text{Density}^{0.7} + 1}")
    st.markdown("</div>", unsafe_allow_html=True)

    # 展開邏輯說明
    l_col1, l_col2 = st.columns(2)
    with l_col1:
        st.markdown("""
        <div class='logic-card'>
        <h3>👥 Target Index (族裔與年齡加權)</h3>
        由 CENSUS API 實時計算該普查區的人口構成：<br><br>
        <b>1. 族裔加權 (Race Weight):</b><br>
        • 華/台裔、西裔、白人：<b>2.5x</b><br>
        • 其餘族裔：<b>2.0x</b><br><br>
        <b>2. 年齡加權 (Age Weight):</b><br>
        • 25-34 歲 (社交主力)：<b>2.5x</b><br>
        • 18-24 歲、35 歲以上：<b>2.0x</b><br><br>
        <i>*計算方式：TargetIndex = RaceWeight × AgeWeight</i>
        </div>
        """, unsafe_allow_html=True)
    with l_col2:
        st.markdown("""
        <div class='logic-card'>
        <h3>🛰️ Density & Space (競爭與物理)</h3>
        整合 Google Place API 與 ADA 空間標準：<br><br>
        <b>1. 廣義競爭密度 (Density):</b><br>
        • 涵蓋：珍奶、咖啡、甜點、麵包店、各類餐飲。<br>
        • 算法：採用 Density^0.7 進行非線性壓制。<br><br>
        <b>2. 空間壓力補償 (Pressure Coeff):</b><br>
        • 極致清晰 (>35 sqft)：<b>1.2x</b><br>
        • 標準質感 (25-34 sqft)：<b>1.0x</b><br>
        • 體驗過載 (15-24 sqft)：<b>0.75x</b><br>
        • 嚴重雜訊 (<15 sqft)：<b>0.5x</b>
        </div>
        """, unsafe_allow_html=True)

    # --- 5. 執行分析 ---
    if st.sidebar.button("Execute Strategic Analysis"):
        if not coord_input: st.error("❌ 請提供座標")
        else:
            try:
                lat, lng = [float(x.strip()) for x in coord_input.split(',')]
                with st.spinner("🚀 執行廣義競業分析與維度對齊..."):
                    income, eth, age = get_census_full_profile(lat, lng)
                    density = get_expanded_density(lat, lng)
                    
                    # 執行邏輯計算
                    r_w = (eth.get("華/台裔",0)*2.5) + (eth.get("西裔",0)*2.5) + (eth.get("白人",0)*2.5) + (eth.get("其餘",0)*2.0)
                    a_w = (age.get("25-34",0)*2.5) + (age.get("18-24",0)*2.0) + (age.get("35+",0)*2.0)
                    target_index = r_w * a_w
                    final_sfs = (income * target_index * 7 * pressure_coeff) / (math.pow(density + 1, 0.7))
                    
                    level = "Model (M)" if final_sfs >= 15000 else "Community (C)" if final_sfs >= 8500 else "eXpress (X)"
                    if cust_area < 250: level = "高效普及 (eXpress-X) [物理受限]"

                    # 核心數據卡片
                    m1, m2, m3, m4 = st.columns(4)
                    m1.metric("SFS 戰略總分", f"{final_sfs:.0f}")
                    m2.metric("位置分級", level.split(' ')[0])
                    m3.metric("月消費力", f"${income:,.0f}")
                    m4.metric("廣義競業數", f"{density} 家")
                    st.info(f"📍 座標分析結果已生成。TargetIndex: {target_index:.2f} | 壓力係數: {pressure_coeff}")

                    st.divider()
                    
                    # 封裝數據包
                    strategic_packet = {
                        "SFS": round(final_sfs), "分級": level, "收入": f"${income:,.0f}",
                        "族裔": eth, "年齡": age, "空間": f"{cust_area} sqft", "人均面積": f"{area_per_seat:.1f} sqft",
                        "競爭密度": f"{density} (含餐飲/甜點)", "加權指數": round(target_index, 2)
                    }

                    col_map, col_ai = st.columns([1, 1])
                    with col_map:
                        map_url = f"https://maps.googleapis.com/maps/api/staticmap?center={lat},{lng}&zoom=17&size=800x640&scale=2&markers=color:red%7C{lat},{lng}&key={G_KEY}"
                        map_bytes = BytesIO(requests.get(map_url).content)
                        st.image(map_bytes, use_container_width=True, caption="📍 Google Retina 實時照片")
                    
                    with col_ai:
                        st.subheader("🤖 Gemini 3 Flash-Preview 全維度解析")
                        genai.configure(api_key=GEMINI_KEY)
                        model = genai.GenerativeModel('gemini-3-flash-preview')
                        
                        brand_dna = "【2026 DNA】：現代極簡、視覺降噪、高質感屏蔽設計、Miffy 跨界藝術。"
                        prompt = f"""
                        你現在是 Sharetea 2026 戰略顧問。請參考品牌DNA：{brand_dna}
                        
                        請針對以下『對齊數據包』與『地圖照片』進行判讀：
                        數據包內容：{strategic_packet}
                        
                        任務：
                        1. 考量該地段高達 {density} 家的廣義競業(含甜點餐飲)，分析品牌如何突圍？
                        2. 根據族裔結構與空間物理限制，針對【營運、行銷、設計】給予2026定位建議。
                        """
                        ai_res = model.generate_content([prompt, Image.open(map_bytes)])
                        st.markdown(ai_res.text)

            except Exception as e: st.error(f"分析報錯: {e}")

    st.caption("Produced by Marketing Designer. v10.3.0 | 廣義競爭與權重展開模式。")
