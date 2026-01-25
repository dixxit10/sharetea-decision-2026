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
        .logic-card { background-color: #161B22; padding: 20px; border-radius: 8px; border-top: 2px solid #238636; margin-bottom: 20px; min-height: 300px; }
        .data-header { color: #238636; font-weight: bold; margin-bottom: 10px; border-bottom: 1px solid #30363D; }
        </style>
        """, unsafe_allow_html=True)

    # --- 2. 側邊欄：戰略座標與物理空間 ---
    st.sidebar.header("📍 戰略座標與物理空間")
    coord_input = st.sidebar.text_input("座標 (Lat, Lng):", placeholder="34.1425, -118.0483")
    loc_type = st.sidebar.selectbox("地段基因型態:", ["Plaza", "Shopping Mall", "Main Street", "Community"])
    
    st.sidebar.markdown("---")
    cust_area = st.sidebar.slider("顧客活動空間 (sq. ft.):", 100, 600, 300)
    seat_choice = st.sidebar.radio("預計座位數:", ["0-5 席", "6-12 席", "13-20 席", "21 席以上"])
    
    # 物理診斷計算
    est_seats = 5 if "0-5" in seat_choice else 12 if "6-12" in seat_choice else 20 if "13-20" in seat_choice else 30
    area_per_seat = cust_area / est_seats
    pressure_coeff = 1.2 if area_per_seat >= 35 else 1.0 if area_per_seat >= 25 else 0.75 if area_per_seat >= 15 else 0.5
    
    # --- 3. API 核心定義 ---
    G_KEY = st.secrets.get("GOOGLE_KEY")
    GEMINI_KEY = st.secrets.get("GEMINI_KEY")
    C_KEY = st.secrets.get("CENSUS_KEY")

    def get_census_full_profile(lat, lng):
        try:
            geo_url = f"https://geo.fcc.gov/api/census/area?lat={lat}&lon={lng}&format=json"
            fips = requests.get(geo_url).json()['results'][0]['block_fips']
            vars = "B19013_001E,B01001_001E,B03002_006E,B03002_012E,B03002_004E,B03002_003E,B01001_007E,B01001_011E"
            url = f"https://api.census.gov/data/2022/acs/acs5?get={vars}&for=tract:{fips[5:11]}&in=state:{fips[:2]}%20county:{fips[2:5]}&key={C_KEY}"
            d = requests.get(url).json()[1]
            pop = int(d[1]) if int(d[1]) > 0 else 1
            income = int(d[0])/12 if d[0] and int(d[0]) > 0 else 4500
            eth = {"華/台裔": int(d[2])/pop, "西裔": int(d[4])/pop, "白人": int(d[5])/pop, "其餘": (pop-int(d[2])-int(d[4])-int(d[5]))/pop}
            age = {"18-24": int(d[6])/pop, "25-34": int(d[7])/pop, "35+": 1-(int(d[6])+int(d[7]))/pop}
            return income, eth, age
        except: return 4500, {"華/台裔": 0.25, "西裔": 0.25, "白人": 0.25, "其餘": 0.25}, {"18-24": 0.3, "25-34": 0.3, "35+": 0.4}

    def get_expanded_density(lat, lng):
        try:
            url = f"https://maps.googleapis.com/maps/api/place/nearbysearch/json?location={lat},{lng}&radius=1000&keyword=tea|boba|coffee|dessert|bakery|restaurant&key={G_KEY}"
            return len(requests.get(url).json().get('results', []))
        except: return 10

    # --- 4. 前端展示：名詞解釋與加權邏輯 ---
    st.title("📚 Sharetea 2026 戰略體系與數據對齊")
    st.markdown("<div class='formula-card'>", unsafe_allow_html=True)
    st.latex(r"SFS = \frac{(\text{Monthly Income} \times \text{Target Index}) \times 7 \times \text{Pressure Coeff}}{\text{Density}^{0.7} + 1}")
    st.markdown("</div>", unsafe_allow_html=True)

    l_col1, l_col2 = st.columns(2)
    with l_col1:
        st.markdown(f"""
        <div class='logic-card'>
        <h3>👥 Target Index (客群加權)</h3>
        <b>1. 族裔權重:</b> 華/台、西、白人 <b>2.5x</b> / 其餘 <b>2.0x</b><br>
        <b>2. 年齡權重:</b> 25-34歲 <b>2.5x</b> / 其餘 <b>2.0x</b><br>
        <b>3. 地段基因：</b> <b>{loc_type}</b>
        </div>
        """, unsafe_allow_html=True)
    with l_col2:
        st.markdown("""
        <div class='logic-card'>
        <h3>🛰️ 競爭壓制與空間品質</h3>
        <b>1. 廣義競爭密度:</b> 涵蓋全品類餐飲，Density^0.7 壓制。<br>
        <b>2. 空間補償:</b> 清晰(>35sqft) <b>1.2x</b> / 雜訊(<15sqft) <b>0.5x</b>
        </div>
        """, unsafe_allow_html=True)

    # --- 5. 執行分析 ---
    if st.sidebar.button("Execute Strategic Analysis"):
        if not coord_input: st.error("❌ 請提供座標")
        else:
            try:
                lat, lng = [float(x.strip()) for x in coord_input.split(',')]
                with st.spinner("🚀 綜合數據對齊中..."):
                    income, eth, age = get_census_full_profile(lat, lng)
                    density = get_expanded_density(lat, lng)
                    
                    r_w = (eth.get("華/台裔",0)*2.5) + (eth.get("西裔",0)*2.5) + (eth.get("白人",0)*2.5) + (eth.get("其餘",0)*2.0)
                    a_w = (age.get("25-34",0)*2.5) + (age.get("18-24",0)*2.0) + (age.get("35+",0)*2.0)
                    target_index = r_w * a_w
                    final_sfs = (income * target_index * 7 * pressure_coeff) / (math.pow(density + 1, 0.7))
                    level = "Model (M)" if final_sfs >= 15000 else "Community (C)" if final_sfs >= 8500 else "eXpress (X)"
                    if cust_area < 250: level = "高效普及 (eXpress-X) [物理受限]"

                    # --- 診斷看板 ---
                    st.divider()
                    st.subheader("📋 綜合戰略診斷看板")
                    m1, m2, m3, m4 = st.columns(4)
                    m1.metric("SFS 戰略總分", f"{final_sfs:.0f}")
                    m2.metric("戰略分級", level.split(' ')[0])
                    m3.metric("月消費力", f"${income:,.0f}")
                    m4.metric("廣義競業", f"{density} 家")

                    # 數據明細 (百分比化)
                    st.markdown("<div class='data-header'>📊 實時數據明細 (已同步百分比)</div>", unsafe_allow_html=True)
                    d_col1, d_col2, d_col3 = st.columns(3)
                    with d_col1:
                        st.write("**族裔分布 (CENSUS)**")
                        eth_df = pd.DataFrame(eth.items(), columns=["族群", "比例"])
                        eth_df["比例"] = eth_df["比例"].map('{:.1%}'.format) # 修正為百分比
                        st.table(eth_df.set_index("族群"))
                    with d_col2:
                        st.write("**年齡結構 (CENSUS)**")
                        age_df = pd.DataFrame(age.items(), columns=["段落", "比例"])
                        age_df["比例"] = age_df["比例"].map('{:.1%}'.format) # 修正為百分比
                        st.table(age_df.set_index("段落"))
                    with d_col3:
                        st.write("**物理與指數指標**")
                        st.write(f"• 壓力係數: {pressure_coeff}")
                        st.write(f"• 人均面積: {area_per_seat:.1f} sqft")
                        st.write(f"• Target Index: {target_index:.2f}")

                    # 地圖照片
                    col_map, col_ai = st.columns([1, 1])
                    with col_map:
                        map_url = f"https://maps.googleapis.com/maps/api/staticmap?center={lat},{lng}&zoom=17&size=800x640&scale=2&markers=color:red%7C{lat},{lng}&key={G_KEY}"
                        map_content = requests.get(map_url).content
                        map_img = Image.open(BytesIO(map_content))
                        st.image(map_img, use_container_width=True, caption=f"📍 {loc_type} Retina 照片")
                    
                    # AI 解析 (加入 429 錯誤處理)
                    with col_ai:
                        st.subheader("🤖 Gemini 3 Flash 全維度判讀")
                        try:
                            genai.configure(api_key=GEMINI_KEY)
                            model = genai.GenerativeModel('gemini-3-flash-preview')
                            packet = {"SFS": round(final_sfs), "分級": level, "地段基因": loc_type, "競業": density, "收入": income, "人均空間": area_per_seat}
                            brand_dna = "2026 DNA: 現代極簡、視覺降噪、高質感屏蔽設計、Miffy藝術跨界。"
                            prompt = f"你是顧問。品牌DNA: {brand_dna}。根據數據 {packet} 與照片，給予建議。針對 {density} 家競爭者給予突圍策略。"
                            st.markdown(model.generate_content([prompt, map_img]).text)
                        except Exception as e:
                            if "429" in str(e):
                                st.warning("⚠️ **Gemini API 配額暫時用盡** (Error 429)。這是因為免費層級的頻率限制，請等待約 1 分鐘後再重試，或升級 API 方案。")
                            else:
                                st.error(f"AI 判讀發生其他錯誤: {e}")

            except Exception as e: st.error(f"系統報錯: {e}")

    st.caption("Produced by Marketing Designer. v10.3.9 | 百分比對齊與配額監控模式。")
