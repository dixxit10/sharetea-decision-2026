import streamlit as st
import pandas as pd
import math
import requests
import google.generativeai as genai
from io import BytesIO

# --- 0. 密碼驗證邏輯 ---
def check_password():
    if "password_correct" not in st.session_state:
        st.title("🔐 Sharetea 戰略系統門禁")
        password = st.text_input("請輸入密碼以開啟戰略引擎", type="password", key="password_input")
        if st.button("登入"):
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
        .definition-box { 
            background-color: #1C2128; border-left: 3px solid #238636; 
            padding: 20px; margin-bottom: 20px; border-radius: 0 4px 4px 0; 
            font-size: 0.92em; line-height: 1.6; min-height: 160px;
            display: flex; flex-direction: column;
        }
        div[data-testid="metric-container"] { 
            background-color: #1C2128; border: 1px solid #30363D; padding: 25px; border-radius: 8px; 
        }
        .stButton>button { 
            background: #238636; color: white; border: none;
            border-radius: 4px; font-weight: 500; width: 100%; height: 3.5em; text-transform: uppercase; letter-spacing: 1px;
        }
        .formula-display { 
            background-color: #0D1117; border: 1px solid #30363D; padding: 25px; 
            border-radius: 4px; margin: 25px 0; text-align: center;
        }
        h1, h2, h3 { font-weight: 600; letter-spacing: -0.5px; }
        </style>
        """, unsafe_allow_html=True)

    # --- 2. 規則定義 ---
    st.title("📚 名詞定義 v8.5.1")
    st.markdown("<p style='color: #8B949E; font-size: 1.2em; margin-top: -15px;'>Reducing Noise. Increasing Clarity.</p>", unsafe_allow_html=True)

    st.markdown("### Strategic Framework Definitions")
    st.markdown("<div class='formula-display'>", unsafe_allow_html=True)
    st.latex(r"SFS = \frac{(Spending Power \times Target Index) \times 7 \times Env Factor \times Scale Mult \times Pressure Coeff}{Density^{0.7} + 1}")
    st.markdown("</div>", unsafe_allow_html=True)

    def_col1, def_col2, def_col3 = st.columns(3)
    with def_col1:
        st.markdown("<div class='definition-box'><b>SFS 戰略總分</b><br>量化地段潛力的核心指標，結合消費力、目標客群適配度與競爭稀釋係數。</div>", unsafe_allow_html=True)
        st.markdown("<div class='definition-box'><b>月均基礎消費力</b><br>根據CENSUS普查區月收入中位數。決定產品定價天花板與精品化空間。</div>", unsafe_allow_html=True)
    with def_col2:
        st.markdown("<div class='definition-box'><b>空間壓力係數 (Pressure Coeff)</b><br>依照ADA建議指數當人均面積低於 25 sq. ft. 時，判定為壓迫感雜訊並調降分值。</div>", unsafe_allow_html=True)
        st.markdown("<div class='definition-box'><b>位置分級基準</b><br>熱區指標 (P): 15000+<br>社區標準 (C): 8500+<br>高效普及 (X): < 8500</div>", unsafe_allow_html=True)
    with def_col3:
        st.markdown("<div class='definition-box'><b>戰略排除 (Exclusion)</b><br>若 SFS 未達該地段屬性之最低基準線，系統將封鎖詳細數據，確保精準開發。</div>", unsafe_allow_html=True)
        st.markdown("<div class='definition-box'><b>顧客活動區 (200-460 sqft)</b><br>精確定義之美學介入範圍，排除吧台與工作區。</div>", unsafe_allow_html=True)

    st.divider()

    # --- 3. 數據輸入 ---
    st.sidebar.header("查詢資料輸入(僅限美國區域)")
    coord_input = st.sidebar.text_input("📍座標輸入 (緯度, 經度):", placeholder="34.1425, -118.0483")
    loc_type = st.sidebar.selectbox("地點型態:", ["Shopping Mall", "Food Court", "Community", "Plaza", "Main Street"])

    st.sidebar.markdown("---")
    cust_area = st.sidebar.slider("顧客活動空間 (sq. ft.):", 200, 460, 300)
    seat_choice = st.sidebar.radio("座位數:", ["0-5 席", "6-12 席", "13-20 席"])

    est_seats = 5 if "0-5" in seat_choice else 12 if "6-12" in seat_choice else 20
    area_per_seat = cust_area / est_seats

    if area_per_seat >= 30: 
        pressure_coeff, seat_mult, quality_label = 1.2, 1.5, "✨ 極致清晰"
    elif 25 <= area_per_seat < 30:
        pressure_coeff, seat_mult, quality_label = 1.0, 1.2, "✅ 標準質感"
    else:
        pressure_coeff, seat_mult, quality_label = 0.75, 1.0, "⚠️ 體驗過載"

    st.sidebar.info(f"人均空間: {area_per_seat:.1f} sq. ft./seat\n當前狀態: {quality_label}")

    G_KEY = st.secrets.get("GOOGLE_KEY")
    GEMINI_KEY = st.secrets.get("GEMINI_KEY")
    CENSUS_KEY = st.secrets.get("CENSUS_KEY")

    # --- 修正後的 Census 函數 (含診斷資訊) ---
    def get_census_spending_power(lat, lng, api_key):
        try:
            # 1. FCC Geo API
            geo_url = f"https://geo.fcc.gov/api/census/area?lat={lat}&lon={lng}&format=json"
            geo_res = requests.get(geo_url).json()
            if not geo_res.get('results'): return "GEO_ERROR"
            
            fips = geo_res['results'][0]['block_fips']
            state, county, tract = fips[:2], fips[2:5], fips[5:11]
            
            # 2. Census API
            census_url = f"https://api.census.gov/data/2022/acs/acs5?get=B19013_001E&for=tract:{tract}&in=state:{state}%20county:{county}&key={api_key}"
            response = requests.get(census_url)
            if response.status_code != 200: return "API_KEY_ERROR"
            
            data = response.json()
            income = int(data[1][0])
            return income / 12 if income > 0 else "NO_DATA"
        except Exception:
            return None

    def get_map_image_secure(lat, lng, key):
        url = f"https://maps.googleapis.com/maps/api/staticmap?center={lat},{lng}&zoom=17&size=800x450&scale=2&key={key}"
        response = requests.get(url)
        return BytesIO(response.content) if response.status_code == 200 else None

    def get_ai_diagnostic(context, api_key):
        if not api_key: return "API Key Configuration Missing."
        try:
            genai.configure(api_key=api_key.strip())
            model = genai.GenerativeModel('gemini-1.5-flash')
            prompt = f"以 Marketing Designer 顧問角度，針對：{context} 提供：1.【評分地理成因】 2.【轉型執行建議】"
            return model.generate_content(prompt).text
        except Exception as e: return f"AI 診斷暫時不可用: {str(e)}"

    # --- 5. 核心執行 ---
    if st.sidebar.button("Execute Strategic Analysis"):
        if not coord_input:
            st.error("請提供座標資料。")
        else:
            try:
                # 確保座標順序正確 (緯度, 經度)
                parts = coord_input.split(',')
                lat, lng = float(parts[0].strip()), float(parts[1].strip())
                
                with st.spinner("正在聯動政府數據與地理稽核..."):
                    result = get_census_spending_power(lat, lng, CENSUS_KEY)
                    
                    if result == "GEO_ERROR":
                        st.error("📍 座標無法識別，請確認格式為『緯度, 經度』(美國經度應為負數)。")
                        st.stop()
                    elif result == "API_KEY_ERROR":
                        st.error("🏛️ Census API 金鑰無效或受限。")
                        st.stop()
                    elif result == "NO_DATA" or result is None:
                        st.error("❌ 該區域普查數據缺失。請確認是否為居住/商業混合區。")
                        st.stop()
                    
                    spending_power = result
                    density = 12
                    target_index = (0.35 * 2.5) + (0.35 * 2.0)
                    final_sfs = ((spending_power * target_index) * 7 * 1.1 * seat_mult * pressure_coeff) / (math.pow(density, 0.7) + 1)
                    
                    level = "熱區指標 (P)" if final_sfs >= 15000 else "社區標準 (C)" if final_sfs >= 8500 else "高效普及 (X)"
                    gap_pct = max(0, (15000 - final_sfs) / 15000)

                    # --- 畫面呈現 ---
                    m1, m2 = st.columns([2, 1])
                    with m1:
                        st.subheader("Strategic Geographic Snapshot")
                        map_bytes = get_map_image_secure(lat, lng, G_KEY)
                        if map_bytes: st.image(map_bytes, use_container_width=True, caption="📍 Retina Density Scan")
                    with m2:
                        st.subheader("Key Strategic Metrics")
                        st.metric("SFS 分數", f"{final_sfs:.0f}")
                        st.metric("位置型態", level)
                        st.metric("型態差距", f"{gap_pct:.1%}")
                        st.metric("空間質量", quality_label)
                        st.metric("月消費力 (Census)", f"${spending_power:,.0f}")
                        st.metric("周邊競業", f"{density}") # 修復多餘引號

                    st.divider()
                    st.subheader("🤖 Gemini 戰略診斷報告")
                    ctx = f"SFS:{final_sfs:.0f}, Tier:{level}, Area:{cust_area}sqft, Quality:{quality_label}"
                    st.markdown(get_ai_diagnostic(ctx, GEMINI_KEY))

            except Exception as e:
                st.error(f"分析異常: {e}")

    st.caption("Produced by Marketing Designer. v8.5.1 | Reducing Noise. Increasing Clarity.")
