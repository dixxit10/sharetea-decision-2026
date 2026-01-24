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
        </style>
        """, unsafe_allow_html=True)

    # --- 2. 側邊欄：物理空間與座標 ---
    st.sidebar.header("📐 物理空間與座標")
    coord_input = st.sidebar.text_input("座標 (Lat, Lng):", placeholder="33.6507, -117.8381")
    
    cust_area = st.sidebar.slider("顧客活動空間 (sq. ft.):", 100, 600, 300)
    seat_choice = st.sidebar.radio("預計座位數:", ["0-5 席", "6-12 席", "13-20 席", "21 席以上"])
    
    # 計算人均空間
    est_seats = 5 if "0-5" in seat_choice else 12 if "6-12" in seat_choice else 20 if "13-20" in seat_choice else 30
    area_per_seat = cust_area / est_seats
    
    # 空間壓力係數與【體感質量判定】
    if area_per_seat >= 35:
        pressure_coeff = 1.2
        quality_status = "✨ 極致清晰"
        q_color = "green"
    elif area_per_seat >= 25:
        pressure_coeff = 1.0
        quality_status = "✅ 標準質感"
        q_color = "blue"
    elif area_per_seat >= 15:
        pressure_coeff = 0.75
        quality_status = "⚠️ 體驗過載"
        q_color = "orange"
    else:
        pressure_coeff = 0.5
        quality_status = "🚨 嚴重雜訊"
        q_color = "red"
    
    st.sidebar.markdown("---")
    st.sidebar.subheader("📐 物理診斷報告")
    st.sidebar.write(f"人均空間: **{area_per_seat:.1f} sq. ft.**")
    st.sidebar.markdown(f"物理空間建議：<span style='color:{q_color}; font-weight:bold;'>{quality_status}</span>", unsafe_allow_html=True)
    st.sidebar.caption(f"壓力補償係數: {pressure_coeff}")

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

    # --- 4. 戰略看板 ---
    st.title("📚 Sharetea 2026 戰略指標體系")
    st.latex(r"SFS = \frac{(Income \times TargetIndex) \times 7 \times PressureCoeff}{Density^{0.7} + 1}")
    
    col_def1, col_def2, col_def3 = st.columns(3)
    with col_def1:
        st.markdown("<div class='definition-box'><b>SFS 戰略總分</b><br>量化地段獲利天花板指標。整合消費力、族群權重與空間壓力補償。</div>", unsafe_allow_html=True)
    with col_def2:
        st.markdown("<div class='definition-box'><b>空間體感質量</b><br>基於人均面積判定：過載、標準、清晰。直接決定品牌體驗的物理上限。</div>", unsafe_allow_html=True)
    with col_def3:
        st.markdown("<div class='definition-box'><b>位置分級基準</b><br>M: 15k+ / C: 8.5k+ / X: < 8.5k。SFS 達標但空間過載者將強制標註建議轉向 X 型態。</div>", unsafe_allow_html=True)

    # --- 5. 執行分析 ---
    if st.sidebar.button("Execute Strategic Analysis"):
        if not coord_input: 
            st.error("❌ 請提供座標")
        elif not GEMINI_KEY:
            st.error("❌ 找不到 GEMINI_KEY，請檢查 Secrets。")
        else:
            try:
                lat, lng = [float(x.strip()) for x in coord_input.split(',')]
                with st.spinner("🚀 數據同步與空間基因診斷中..."):
                    income, pop, eth, age = get_census_data(lat, lng)
                    density = get_density(lat, lng)
                    
                    target_index = (eth.get("東亞裔", 0) * 3.0) + (age.get("25-34", 0) * 2.5)
                    final_sfs = ((income * (target_index if target_index > 0 else 1.1)) * 7 * pressure_coeff) / (math.pow(density + 1, 0.7))
                    
                    # 最終分級判定 (結合 SFS 與物理限制)
                    if cust_area < 250:
                        level = "高效普及 (eXpress-X)"
                        limit_msg = f"⚠️ 空間狹窄 ({cust_area}sqft)：物理條件限制品牌體驗，建議以此區域之 X 店型營運。"
                    else:
                        level = "品牌指標 (Model-M)" if final_sfs >= 15000 else "社區標準 (Community-C)" if final_sfs >= 8500 else "高效普及 (eXpress-X)"
                        limit_msg = f"✅ 空間條件適宜：店型定位與 SFS 指數對齊 ({quality_status})。"

                    m1, m2, m3, m4 = st.columns(4)
                    m1.metric("SFS 戰略總分", f"{final_sfs:.0f}")
                    m2.metric("位置分級", level)
                    m3.metric("空間補償係數", f"{pressure_coeff}")
                    m4.metric("周邊競業數", f"{density} 家")
                    st.warning(limit_msg)

                    st.divider()
                    
                    strategic_packet = {
                        "SFS總分": round(final_sfs),
                        "位置分級": level,
                        "體感質量": quality_status,
                        "月收入(中位)": f"${income:,.0f}",
                        "族裔結構": eth,
                        "年齡組成": age,
                        "物理面積": f"{cust_area} sqft",
                        "人均面積": f"{area_per_seat:.1f} sqft",
                        "壓力係數": pressure_coeff,
                        "競爭密度": f"{density} 家/km"
                    }

                    col_map, col_ai = st.columns([1, 1])
                    with col_map:
                        map_url = f"https://maps.googleapis.com/maps/api/staticmap?center={lat},{lng}&zoom=17&size=800x640&scale=2&markers=color:red%7C{lat},{lng}&key={G_KEY}"
                        map_response = requests.get(map_url)
                        map_bytes = BytesIO(map_response.content)
                        st.image(map_bytes, use_container_width=True, caption="📍 戰略座標 Retina 掃描")
                    
                    with col_ai:
                        st.subheader("🤖 Gemini 3 Flash 全維度解析")
                        genai.configure(api_key=GEMINI_KEY)
                        model = genai.GenerativeModel('gemini-3-flash-preview')

                        # 動態任務分派
                        if "Model (M)" in level:
                            dynamic_task = f"""
                            任務 (Model-M 指標店模式)：
                            1. 【空間基因】：目前物理質量為 {quality_status}。評估如何利用這份空間感撐起品牌溢價？
                            2. 【設計策略】：如何處理地圖中周邊的雜訊，在 SFS:{round(final_sfs)} 的高價值地段創造純淨的品牌綠洲？
                            3. 【營運建議】：針對高收入族群設計精緻化服務流程。
                            """
                        elif "Community (C)" in level:
                            dynamic_task = f"""
                            任務 (Community-C 社區店模式)：
                            1. 【社交診斷】：體感質量為 {quality_status}。評估空間是否足以支持長期停留與社交回購？
                            2. 【行銷策略】：針對族群比例 {eth}，如何利用聯名活動創造打卡動力？
                            3. 【設計建議】：如何平衡座位舒適度與視覺張力。
                            """
                        else:
                            dynamic_task = f"""
                            任務 (eXpress-X 機能店模式)：
                            1. 【效能極大化】：空間判定為 {quality_status}。如何利用極簡模組掩蓋擁擠感並提升轉換率？
                            2. 【營運策略】：針對高峰轉換率，設計外送/自取雙動線。
                            3. 【視覺策略】：在繁忙街道中提升識別度，降低環境噪音干擾。
                            """

                        prompt = f"""
                        你現在是 Sharetea 2026 戰略專家。請根據以下「數據包」與「地圖截圖」進行診斷：
                        【數據包】：{strategic_packet}
                        {dynamic_task}
                        請針對【營運】、【行銷】、【設計】三個維度，給予簡易且精準的執行建議。
                        """
                        ai_res = model.generate_content([prompt, Image.open(map_bytes)])
                        st.markdown(ai_res.text)

            except Exception as e: 
                st.error(f"分析異常: {e}")

    st.caption("Produced by Marketing Designer. v10.0.1 | 空間質量與戰略分級對齊模式。")
