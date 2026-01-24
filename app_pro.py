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
    st.sidebar.header("📐 物理空間與座標")
    coord_input = st.sidebar.text_input("座標 (Lat, Lng):", placeholder="33.6507, -117.8381")
    
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
    st.sidebar.markdown(f"空間質感建議：<span style='color:{q_color}; font-weight:bold;'>{quality_status}</span>", unsafe_allow_html=True)
    st.sidebar.caption(f"壓力補償係數: {pressure_coeff} (Ref: ADA Standard)")

    # --- 3. API 核心定義 ---
    G_KEY = st.secrets.get("GOOGLE_KEY")
    GEMINI_KEY = st.secrets.get("GEMINI_KEY")
    C_KEY = st.secrets.get("CENSUS_KEY")

    def get_census_data(lat, lng):
        try:
            geo_url = f"https://geo.fcc.gov/api/census/area?lat={lat}&lon={lng}&format=json"
            fips = requests.get(geo_url).json()['results'][0]['block_fips']
            vars = "B19013_001E,B01001_001E,B03002_006E,B03002_004E,B03002_012E,B01001_007E,B01001_011E"
            url = f"https://api.census.gov/data/2022/acs/acs5?get={vars}&for=tract:{fips[5:11]}&in=state:{fips[:2]}%20county:{fips[2:5]}&key={C_KEY}"
            d = requests.get(url).json()[1]
            pop = int(d[1]) if int(d[1]) > 0 else 1
            return int(d[0])/12, pop, {"東亞裔": int(d[2])/pop, "西裔": int(d[3])/pop, "南亞裔": int(d[4])/pop}, {"18-24": int(d[5])/pop, "25-34": int(d[6])/pop}
        except: return 5000, 1000, {}, {}

    def get_density(lat, lng):
        try:
            url = f"https://maps.googleapis.com/maps/api/place/nearbysearch/json?location={lat},{lng}&radius=1000&keyword=boba|tea&key={G_KEY}"
            return len(requests.get(url).json().get('results', []))
        except: return 5

    # --- 4. 戰略看板與加權概述 ---
    st.title("📚 Sharetea 2026 戰略指標體系")
    st.markdown("<div class='formula-card'>", unsafe_allow_html=True)
    st.latex(r"SFS = \frac{(Income \times TargetIndex) \times 7 \times PressureCoeff}{Density^{0.7} + 1}")
    st.markdown("</div>", unsafe_allow_html=True)

    with st.expander("📊 SFS 戰略加權核算與算法概述", expanded=True):
        sc1, sc2, sc3 = st.columns(3)
        with sc1:
            st.markdown("""
            **👥 目標族群加權 (CENSUS)**
            * **東亞裔 (華/韓/日裔)**：加權 **3.0x**
            * **社交主力 (25-34 歲)**：加權 **2.5x**
            """)
        with sc2:
            st.markdown("""
            **📐 物理環境補償 (ADA)**
            * **清晰級 (>35 sqft)**：加權 **1.2x**
            * **雜訊級 (<15 sqft)**：減權 **0.5x**
            """)
        with sc3:
            st.markdown("""
            **🛰️ 競爭壓制係數 (GOOGLE)**
            * **競業密度半徑**：1.0km
            * **壓制模型**：$Density^{0.7}$
            """)

    col_def1, col_def2, col_def3 = st.columns(3)
    with col_def1:
        st.markdown("<div class='definition-box'><b>SFS 戰略總分</b><br>整合 CENSUS 消費力、目標客群密度與競爭壓力。</div>", unsafe_allow_html=True)
    with col_def2:
        st.markdown("<div class='definition-box'><b>空間體感質量 (ADA)</b><br>基於人均面積判定，直接決定品牌體驗的物理上限。</div>", unsafe_allow_html=True)
    with col_def3:
        st.markdown("<div class='definition-box'><b>位置分級基準</b><br>M: 15k+ / C: 8.5k+ / X: < 8.5k。</div>", unsafe_allow_html=True)

    # --- 5. 執行分析 ---
    if st.sidebar.button("Execute Strategic Analysis"):
        if not coord_input: st.error("❌ 請提供座標")
        elif not GEMINI_KEY: st.error("❌ 找不到 GEMINI_KEY")
        else:
            try:
                lat, lng = [float(x.strip()) for x in coord_input.split(',')]
                with st.spinner("🚀 跨 API 數據採集與 2026 DNA 診斷中..."):
                    income, pop, eth, age = get_census_data(lat, lng)
                    density = get_density(lat, lng)
                    target_index = (eth.get("東亞裔", 0) * 3.0) + (age.get("25-34", 0) * 2.5)
                    final_sfs = ((income * (target_index if target_index > 0 else 1.1)) * 7 * pressure_coeff) / (math.pow(density + 1, 0.7))
                    
                    if cust_area < 250:
                        level, limit_msg = "高效普及 (eXpress-X)", f"⚠️ 空間狹窄 ({cust_area}sqft)：判定為 X 型態。"
                    else:
                        level = "品牌指標 (Model-M)" if final_sfs >= 15000 else "社區標準 (Community-C)" if final_sfs >= 8500 else "高效普及 (eXpress-X)"
                        limit_msg = f"✅ 空間條件適宜 ({quality_status})。"

                    m1, m2, m3, m4 = st.columns(4)
                    m1.metric("SFS 戰略總分", f"{final_sfs:.0f}")
                    m2.metric("位置分級 (Level)", level)
                    m3.metric("月均收入 (CENSUS)", f"${income:,.0f}")
                    m4.metric("周邊競業 (Google)", f"{density} 家")
                    st.warning(limit_msg)

                    st.divider()
                    strategic_packet = {
                        "SFS總分": round(final_sfs), "位置分級": level, "體感質量": quality_status,
                        "月收入": f"${income:,.0f}", "族裔結構": eth, "年齡組成": age,
                        "物理面積": f"{cust_area} sqft", "壓力係數(ADA)": pressure_coeff, "競爭密度": f"{density} 家/km"
                    }

                    col_map, col_ai = st.columns([1, 1])
                    with col_map:
                        map_url = f"https://maps.googleapis.com/maps/api/staticmap?center={lat},{lng}&zoom=17&size=800x640&scale=2&markers=color:red%7C{lat},{lng}&key={G_KEY}"
                        map_bytes = BytesIO(requests.get(map_url).content)
                        st.image(map_bytes, use_container_width=True, caption="📍 Retina 戰略掃描")
                    
                    with col_ai:
                        st.subheader("🤖 Gemini 3 Flash 全維度戰略判讀")
                        genai.configure(api_key=GEMINI_KEY)
                        model = genai.GenerativeModel('gemini-3-flash-preview')

                        brand_dna = """
                        【2026 Sharetea Express 品牌風格包】：
                        1. 視覺核心：現代極簡、採用暖米白、磨砂玻璃、半透明紅色壓克力。
                        2. 設計哲學：視覺降噪 (Visual De-noising)。若環境雜訊高，優先全屏蔽設計。
                        3. 社交定位：質感信號、融合藝術跨界，強調感官敘事而非速食感。
                        """

                        if "Model (M)" in level:
                            dynamic_task = f"任務 (M-品牌模式)：如何在 SFS:{round(final_sfs)} 的地標地段利用屏蔽設計排除雜訊？"
                        elif "Community (C)" in level:
                            dynamic_task = f"任務 (C-社交模式)：質感為 {quality_status}。如何結合聯名活動吸引鄰里客群？"
                        else:
                            dynamic_task = f"任務 (X-能效模式)：空間僅 {cust_area}sqft，如何建立視覺辨識度與轉換率？"

                        prompt = f"你現在是 Sharetea 2026 戰略專家。風格包：{brand_dna}\n數據包：{strategic_packet}\n{dynamic_task}\n建議維度：營運、行銷、設計。"
                        ai_res = model.generate_content([prompt, Image.open(map_bytes)])
                        st.markdown(ai_res.text)

            except Exception as e: 
                st.error(f"分析異常: {e}")

    st.caption("Produced by Marketing Designer. v10.1.1 | 數據加權與 2026 DNA 驅動。")
