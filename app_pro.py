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
            else: st.error("😕 密碼錯誤")
        return False
    return True

if check_password():
    # --- 1. UI 配置 ---
    st.set_page_config(page_title="Sharetea Express 2026 戰略診斷", layout="wide")
    st.markdown("""
        <style>
        .stApp { background-color: #0E1117; color: #E6EDF3; }
        .definition-box { background-color: #1C2128; border-left: 3px solid #238636; padding: 15px; margin-bottom: 10px; border-radius: 4px; font-size: 0.85em; }
        </style>
        """, unsafe_allow_html=True)

    # --- 2. 側邊欄：空間與物理限制 (100-600 sqft) ---
    st.sidebar.header("📐 物理空間與座標")
    coord_input = st.sidebar.text_input("座標 (Lat, Lng):", placeholder="33.6507, -117.8381")
    
    # 擴展後的空間範圍
    cust_area = st.sidebar.slider("顧客活動空間 (sq. ft.):", 100, 600, 300)
    seat_choice = st.sidebar.radio("預計座位數:", ["0-5 席", "6-12 席", "13-20 席", "21 席以上"])
    
    # 物理空間硬性診斷邏輯
    est_seats = 5 if "0-5" in seat_choice else 12 if "6-12" in seat_choice else 20 if "13-20" in seat_choice else 30
    area_per_seat = cust_area / est_seats
    
    # 空間壓力係數 (Pressure Coeff)
    # 1.2: 極致舒適, 1.0: 標準, 0.75: 擁擠, 0.5: 極度壓迫(物理降級因子)
    pressure_coeff = 1.2 if area_per_seat >= 35 else 1.0 if area_per_seat >= 25 else 0.75 if area_per_seat >= 15 else 0.5
    
    st.sidebar.markdown("---")
    st.sidebar.subheader("📐 物理診斷報告")
    st.sidebar.write(f"人均空間: **{area_per_seat:.1f} sq. ft.**")
    
    # 物理硬限制：若空間太小，即便 SFS 高也會強制標註為 X 店型潛力
    physical_limit = "eXpress (X) 優先" if cust_area < 250 else "Community (C) 潛力" if cust_area < 450 else "Model (M) 潛力"
    st.sidebar.info(f"物理空間建議：{physical_limit}")

    # --- 3. API 核心函數 ---
    G_KEY = st.secrets["GOOGLE_KEY"]
    GEM_KEY = st.secrets["GEMINI_KEY"]
    C_KEY = st.secrets["CENSUS_KEY"]

    def get_census_data(lat, lng):
        try:
            geo_url = f"https://geo.fcc.gov/api/census/area?lat={lat}&lon={lng}&format=json"
            fips = requests.get(geo_url).json()['results'][0]['block_fips']
            vars = "B19013_001E,B01001_001E,B03002_006E,B03002_004E,B03002_012E,B01001_007E,B01001_011E"
            url = f"https://api.census.gov/data/2022/acs/acs5?get={vars}&for=tract:{fips[5:11]}&in=state:{fips[:2]}%20county:{fips[2:5]}&key={C_KEY}"
            d = requests.get(url).json()[1]
            return int(d[0])/12, int(d[1]), {"東亞裔": int(d[2])/int(d[1]), "西裔": int(d[3])/int(d[1]), "南亞裔": int(d[4])/int(d[1])}, {"18-24": int(d[5])/int(d[1]), "25-34": int(d[6])/int(d[1])}
        except: return 5000, 1000, {}, {}

    def get_density(lat, lng):
        try:
            url = f"https://maps.googleapis.com/maps/api/place/nearbysearch/json?location={lat},{lng}&radius=1000&keyword=boba|tea&key={G_KEY}"
            return len(requests.get(url).json().get('results', []))
        except: return 5

    # --- 4. 名詞定義區 ---
    st.title("📚 Sharetea 2026 戰略指標體系")
    st.latex(r"SFS = \frac{(Income \times TargetIndex) \times 7 \times PressureCoeff}{Density^{0.7} + 1}")
    
    col_def1, col_def2, col_def3 = st.columns(3)
    with col_def1:
        st.markdown("<div class='definition-box'><b>SFS 戰略總分</b><br>地段獲利天花板指標，受消費力與空間係數雙重影響。</div>", unsafe_allow_html=True)
    with col_def2:
        st.markdown("<div class='definition-box'><b>空間壓力係數</b><br>人均面積低於 15sqft 會產生極大視覺噪音，強制降級。</div>", unsafe_allow_html=True)
    with col_def3:
        st.markdown("<div class='definition-box'><b>月均消費力</b><br>Tract 等級實時收入中位數，決定溢價空間。</div>", unsafe_allow_html=True)

    # --- 5. 執行分析 ---
    if st.sidebar.button("Execute Strategic Analysis"):
        if not coord_input: st.error("請提供座標")
        else:
            lat, lng = [float(x.strip()) for x in coord_input.split(',')]
            with st.spinner("🚀 正在對齊物理空間與地段數據..."):
                income, pop, eth, age = get_census_data(lat, lng)
                density = get_density(lat, lng)
                
                # SFS 運算：納入物理空間壓力 (pressure_coeff)
                target_index = (eth.get("東亞裔", 0) * 3.0) + (age.get("25-34", 0) * 2.5)
                final_sfs = ((income * (target_index if target_index > 0 else 1.1)) * 7 * pressure_coeff) / (math.pow(density + 1, 0.7))
                
                # 自動對齊邏輯：若物理空間太小 (<250)，即便 SFS 高也判定為 X 店型
                if cust_area < 250:
                    level = "高效普及 (eXpress-X)"
                else:
                    level = "品牌指標 (Model-M)" if final_sfs >= 15000 else "社區標準 (Community-C)" if final_sfs >= 8500 else "高效普及 (eXpress-X)"

                # --- 數據面板呈現 ---
                m1, m2, m3, m4 = st.columns(4)
                m1.metric("SFS 戰略總分", f"{final_sfs:.0f}")
                m2.metric("位置分級", level)
                m3.metric("空間壓力係數", f"{pressure_coeff}")
                m4.metric("周邊競業數", f"{density} 家")

                st.divider()
                
                # 數據彙整包
                strategic_packet = {
                    "SFS總分": round(final_sfs),
                    "最終分級": level,
                    "月均收入": f"${income:,.0f}",
                    "族裔結構": eth,
                    "年齡組成": age,
                    "顧客活動空間": f"{cust_area} sqft",
                    "預計座位數": est_seats,
                    "人均空間": f"{area_per_seat:.1f} sqft",
                    "壓力係數": pressure_coeff,
                    "周邊競爭密度": density
                }

                # 地圖與 AI 解析
                col_map, col_ai = st.columns([1, 1])
                with col_map:
                    map_url = f"https://maps.googleapis.com/maps/api/staticmap?center={lat},{lng}&zoom=17&size=800x640&scale=2&markers=color:red%7C{lat},{lng}&key={G_KEY}"
                    map_bytes = BytesIO(requests.get(map_url).content)
                    st.image(map_bytes, use_container_width=True, caption="📍 Retina 環境掃描")
                
                with col_ai:
                    st.subheader("🤖 Gemini 3 Flash 全維度戰略判讀")
                    genai.configure(api_key=GEMINI_KEY)
                    model = genai.GenerativeModel('gemini-3-flash-preview')
                    
                    prompt = f"""
                    你現在是 Sharetea 2026 戰略專家。請根據以下對齊數據包與地圖進行診斷：
                    
                    【數據包】：{strategic_packet}
                    
                    任務：
                    1. 評估物理空間({cust_area}sqft)與地段潛力(SFS:{round(final_sfs)})是否匹配。
                    2. 若空間狹小但地段強，應如何設計以『掩蓋壓力』？
                    3. 提供簡易建議：
                       - 【營運】：如何處理高峰轉換率？
                       - 【行銷】：如何利用當地族群優勢？
                       - 【設計】：如何處理視覺噪音與屏蔽？
                    """
                    ai_res = model.generate_content([prompt, Image.open(map_bytes)])
                    st.markdown(ai_res.text)

    st.caption("Produced by Marketing Designer. v9.9.2 | 物理空間決定論已上線。")
