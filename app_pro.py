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
    
    # 空間壓力係數與【體感質量判定】 (基於 ADA 舒適度基準調整)
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

    # --- 4. 戰略看板 (前端數據卡片) ---
    st.title("📚 Sharetea 2026 戰略指標體系")
    st.latex(r"SFS = \frac{(Income \times TargetIndex) \times 7 \times PressureCoeff}{Density^{0.7} + 1}")
    
    col_def1, col_def2, col_def3 = st.columns(3)
    with col_def1:
        st.markdown("<div class='definition-box'><b>SFS 戰略總分</b><br>整合 CENSUS 消費力、目標客群權重與 Google API 競爭壓力之獲利潛力分。</div>", unsafe_allow_html=True)
    with col_def2:
        st.markdown("<div class='definition-box'><b>空間壓力係數 (ADA)</b><br>基於 ADA 人均面積標準判定。低於 15sqft 視為嚴重雜訊，將大幅拉低品牌溢價。</div>", unsafe_allow_html=True)
    with col_def3:
        st.markdown("<div class='definition-box'><b>位置分級基準</b><br>M: 15k+ / C: 8.5k+ / X: < 8.5k。由硬數據驅動，結合 Gemini 3 視覺基因診斷。</div>", unsafe_allow_html=True)

    # --- 5. 執行分析 ---
    if st.sidebar.button("Execute Strategic Analysis"):
        if not coord_input: 
            st.error("❌ 請提供座標")
        elif not GEMINI_KEY:
            st.error("❌ 找不到 GEMINI_KEY，請檢查 Secrets。")
        else:
            try:
                lat, lng = [float(x.strip()) for x in coord_input.split(',')]
                with st.spinner("🚀 跨 API 數據採集與 2026 DNA 診斷中..."):
                    # 數據採集
                    income, pop, eth, age = get_census_data(lat, lng)
                    density = get_density(lat, lng)
                    
                    # SFS 戰略運算
                    target_index = (eth.get("東亞裔", 0) * 3.0) + (age.get("25-34", 0) * 2.5)
                    final_sfs = ((income * (target_index if target_index > 0 else 1.1)) * 7 * pressure_coeff) / (math.pow(density + 1, 0.7))
                    
                    # 對齊分級
                    if cust_area < 250:
                        level = "高效普及 (eXpress-X)"
                        limit_msg = f"⚠️ 物理限制：空間僅 {cust_area}sqft，由硬性空間門檻判定為 X 型態。"
                    else:
                        level = "品牌指標 (Model-M)" if final_sfs >= 15000 else "社區標準 (Community-C)" if final_sfs >= 8500 else "高效普及 (eXpress-X)"
                        limit_msg = f"✅ 物理適宜：空間符合預設店型規模 ({quality_status})。"

                    # --- 前端數據卡片展示 ---
                    m1, m2, m3, m4 = st.columns(4)
                    m1.metric("SFS 戰略總分", f"{final_sfs:.0f}")
                    m2.metric("位置分級 (Level)", level)
                    m3.metric("月均收入 (CENSUS)", f"${income:,.0f}")
                    m4.metric("周邊競業 (Google)", f"{density} 家")
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
                        "壓力係數(ADA)": pressure_coeff,
                        "競爭密度(Google)": f"{density} 家/km"
                    }

                    # --- 地圖與 Gemini 3 解析 ---
                    col_map, col_ai = st.columns([1, 1])
                    with col_map:
                        map_url = f"https://maps.googleapis.com/maps/api/staticmap?center={lat},{lng}&zoom=17&size=800x640&scale=2&markers=color:red%7C{lat},{lng}&key={G_KEY}"
                        map_bytes = BytesIO(requests.get(map_url).content)
                        st.image(map_bytes, use_container_width=True, caption="📍 戰略座標 Retina 掃描")
                    
                    with col_ai:
                        st.subheader("🤖 Gemini 3 Flash 全維度戰略判讀")
                        genai.configure(api_key=GEMINI_KEY)
                        model = genai.GenerativeModel('gemini-3-flash-preview')

                        # --- 核心新增：2026 品牌風格包 (Brand DNA) ---
                        brand_dna = """
                        【2026 Sharetea Express 品牌風格包】：
                        1. 視覺核心：現代極簡、大量採用暖米白、磨砂、半透明紅色壓克力。
                        2. 設計哲學：視覺溫和、清晰。若環境複雜，優先考慮全屏蔽設計，打造隔離干擾的「品牌安全感」。
                        3. 社交定位：生活質感信號，融合藝術跨界，強調觸感、聽覺、感官敘事而非傳統速食感。
                        4. 執行目標：即使是 eXpress 店型，也需維持模組化的精緻度與清晰的品牌視覺基準。
                        """

                        if "Model (M)" in level:
                            dynamic_task = f"任務 (M-品牌模式)：如何在 SFS:{round(final_sfs)} 的地標級地段，利用屏蔽設計排除地圖中的視覺雜訊，撐起極致品牌溢價？"
                        elif "Community (C)" in level:
                            dynamic_task = f"任務 (C-社交模式)：體感質量為 {quality_status}。如何結合聯名和網路活動吸引長期穩定的鄰里客群進行社交？"
                        else:
                            dynamic_task = f"任務 (X-能效模式)：空間僅 {cust_area}sqft，如何利用在雜亂街道中建立強大的視覺辨識度與出杯轉換率？"

                        prompt = f"""
                        你現在是 Sharetea 2026 戰略專家。請參考品牌風格包：
                        {brand_dna}
                        
                        根據以下數據包與地圖診斷：
                        【數據包】：{strategic_packet}
                        
                        {dynamic_task}
                        
                        請針對【營運】、【行銷】、【設計】三個維度，給予符合 2026 任務目標為準的簡易建議。
                        """
                        ai_res = model.generate_content([prompt, Image.open(map_bytes)])
                        st.markdown(ai_res.text)

            except Exception as e: 
                st.error(f"分析異常: {e}")

    st.caption("Produced by Marketing Designer. v10.0.1 | 數據對齊與 2026 品牌 DNA 驅動。")
