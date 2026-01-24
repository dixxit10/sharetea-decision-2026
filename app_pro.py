import streamlit as st
import pandas as pd
import math
import requests
import google.generativeai as genai
from io import BytesIO

# --- 0. 密碼驗證邏輯 (Password Gate) ---
def check_password():
    """若輸入正確密碼則回傳 True"""
    def password_entered():
        if st.session_state["password"] == "sharetea2026":
            st.session_state["password_correct"] = True
            del st.session_state["password"] 
        else:
            st.session_state["password_correct"] = False

    if "password_correct" not in st.session_state:
        st.title("🔐 Sharetea 戰略系統門禁")
        st.text_input("請輸入密碼以開啟戰略引擎", type="password", on_change=password_entered, key="password")
        return False
    elif not st.session_state["password_correct"]:
        st.title("🔐 Sharetea 戰略系統門禁")
        st.text_input("請輸入密碼以開啟戰略引擎", type="password", on_change=password_entered, key="password")
        st.error("😕 密碼錯誤，請重新輸入。")
        return False
    else:
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
    st.title("📚 名詞定義 v8.6")
    st.markdown("<p style='color: #8B949E; font-size: 1.2em; margin-top: -15px;'>Reducing Noise. Increasing Clarity.</p>", unsafe_allow_html=True)

    st.markdown("### Strategic Framework Definitions")

    st.markdown("<div class='formula-display'>", unsafe_allow_html=True)
    st.latex(r"SFS = \frac{(Spending Power \times Target Index) \times 7 \times Env Factor \times Scale Mult \times Pressure Coeff \times \mathbf{Context Factor}}{Density^{0.7} + 1}")
    st.markdown("</div>", unsafe_allow_html=True)

    def_col1, def_col2, def_col3 = st.columns(3)
    with def_col1:
        st.markdown("<div class='definition-box'><b>SFS 戰略總分</b><br>量化地段潛力的核心指標，結合消費力、目標客群適配度、環境質感與競爭稀釋係數。</div>", unsafe_allow_html=True)
        st.markdown("<div class='definition-box'><b>月均基礎消費力</b><br>根據CENSUS普查區月收入中位數。決定產品定價天花板與精品化空間。</div>", unsafe_allow_html=True)
    with def_col2:
        st.markdown("<div class='definition-box'><b>空間壓力係數 (Pressure Coeff)</b><br>依照ADA建議指數當人均面積低於 25 sq. ft. 時，判定為壓迫感雜訊並調降分值。</div>", unsafe_allow_html=True)
        st.markdown("<div class='definition-box'><b>位置分級基準</b><br>熱區指標 (P): 15000+<br>社區標準 (C): 8500+<br>高效普及 (X): < 8500</div>", unsafe_allow_html=True)
    with def_col3:
        st.markdown("<div class='definition-box'><b>環境質感因子 (Context Factor)</b><br>判斷鄰里質感。精品商圈加乘 (1.15x)；快餐雜訊區降權 (0.8x)，確保品牌力場一致。</div>", unsafe_allow_html=True)
        st.markdown("<div class='definition-box'><b>顧客活動區 (200-460 sqft)</b><br>精確定義之美學介入範圍，排除吧台與工作區。</div>", unsafe_allow_html=True)

    st.divider()

    # --- 3. 數據輸入 ---
    st.sidebar.header("查詢資料輸入(僅限美國區域)")
    coord_input = st.sidebar.text_input("📍座標輸入 (緯度, 經度):", placeholder="34.1425, -118.0483")
    loc_type = st.sidebar.selectbox("地點型態:", ["Shopping Mall", "Food Court", "Community", "Plaza", "Main Street"])

    st.sidebar.markdown("---")
    cust_area = st.sidebar.slider("顧客活動空間 (sq. ft.):", 200, 460, 300)
    seat_choice = st.sidebar.radio("座位數:", ["0-5 席", "6-12 席", "13-20 席"])

    # 場域質感評估 [修正模糊感的關鍵]
    context_choice = st.sidebar.selectbox(
        "🌆 場域質感評等 (鄰里基因):", 
        ["精品/生活方式 (Lifestyle)", "標準商圈 (Standard)", "快餐/機能雜訊 (Noisy)"]
    )
    context_map = {"精品/生活方式 (Lifestyle)": 1.15, "標準商圈 (Standard)": 1.0, "快餐/機能雜訊 (Noisy)": 0.8}
    context_factor = context_map[context_choice]

    # 空間壓力偵測
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

    # --- 輔助函數 ---
    def get_census_spending_power(lat, lng, api_key):
        try:
            geo_url = f"https://geo.fcc.gov/api/census/area?lat={lat}&lon={lng}&format=json"
            geo_res = requests.get(geo_url).json()
            fips = geo_res['results'][0]['block_fips']
            state, county, tract = fips[:2], fips[2:5], fips[5:11]
            census_url = f"https://api.census.gov/data/2022/acs/acs5?get=B19013_001E&for=tract:{tract}&in=state:{state}%20county:{county}&key={api_key}"
            data = requests.get(census_url).json()
            return int(data[1][0]) / 12
        except:
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
            prompt = f"以 Marketing Designer 顧問角度分析。數據：{context}。請特別針對『場域質感』與『店內空間壓力』的對比提供轉型執行建議。"
            return model.generate_content(prompt).text
        except Exception as e: return f"AI 診斷暫時不可用: {str(e)}"

    # --- 5. 核心執行 ---
    if st.sidebar.button("Execute Strategic Analysis"):
        if not coord_input:
            st.error("請提供座標資料。")
        else:
            try:
                parts = coord_input.split(',')
                lat, lng = float(parts[0].strip()), float(parts[1].strip())
                
                with st.spinner("正在執行全方位戰略核算..."):
                    spending_power = get_census_spending_power(lat, lng, CENSUS_KEY)
                    
                    if spending_power is None:
                        st.error("❌ 無法獲取美國政府普查數據。請確認座標是否在美國境內。")
                        st.stop()
                    
                    density = 12
                    eth_dict = {"華裔/東亞裔": 0.35, "墨西哥裔/西裔": 0.30, "社交核心": 0.35}
                    target_index = (0.35 * 2.5) + (0.35 * 2.0)
                    
                    # 整合 Context Factor 的最終演算公式
                    final_sfs = ((spending_power * target_index) * 7 * 1.1 * seat_mult * pressure_coeff * context_factor) / (math.pow(density, 0.7) + 1)
                    
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
                        st.metric("場域評等", context_choice)
                        st.metric("空間質量", quality_label)
                        st.metric("月消費力 (Census)", f"${spending_power:,.0f}")

                    st.divider()
                    st.subheader("🤖 Gemini 戰略診斷報告")
                    ctx = f"SFS:{final_sfs:.0f}, Tier:{level}, Context:{context_choice}, Quality:{quality_label}"
                    st.markdown(get_ai_diagnostic(ctx, GEMINI_KEY))

            except Exception as e:
                st.error(f"分析異常: {e}")

    st.caption("Produced by Marketing Designer. v8.6.0 | Reducing Noise. Increasing Clarity.")
