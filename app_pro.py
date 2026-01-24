import streamlit as st
import pandas as pd
import math
import requests
import google.generativeai as genai
from io import BytesIO

# --- 0. 密碼驗證邏輯 (sharetea2026) ---
def check_password():
    if "password_correct" not in st.session_state:
        st.title("🔐 Sharetea 戰略系統門禁")
        password = st.text_input("請輸入密碼以開啟戰略引擎", type="password", key="password_gate")
        if st.button("開啟引擎"):
            if password == "sharetea2026":
                st.session_state["password_correct"] = True
                st.rerun()
            else:
                st.error("😕 密碼錯誤，請重新輸入。")
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
    st.title("📚 名詞定義 v8.6")
    st.markdown("<p style='color: #8B949E; font-size: 1.2em; margin-top: -15px;'>Reducing Noise. Increasing Clarity.</p>", unsafe_allow_html=True)

    st.markdown("### Strategic Framework Definitions")
    st.markdown("<div class='formula-display'>", unsafe_allow_html=True)
    st.latex(r"SFS = \frac{(Spending Power \times Target Index) \times 7 \times Env Factor \times Scale Mult \times Pressure Coeff \times \mathbf{Context Factor}}{Density^{0.7} + 1}")
    st.markdown("</div>", unsafe_allow_html=True)

    def_col1, def_col2, def_col3 = st.columns(3)
    with def_col1:
        st.markdown("<div class='definition-box'><b>SFS 戰略總分</b><br>量化地段潛力的核心指標，結合消費力、族群、環境基因與競爭稀釋係數。</div>", unsafe_allow_html=True)
        st.markdown("<div class='definition-box'><b>月均基礎消費力</b><br>根據 CENSUS 普查區月收入中位數。決定產品定價天花板與精品化空間。</div>", unsafe_allow_html=True)
    with def_col2:
        st.markdown("<div class='definition-box'><b>空間壓力係數 (Pressure Coeff)</b><br>依照 ADA 建議，當人均面積低於 25 sq. ft. 時，判定為壓迫感雜訊並調降分值。</div>", unsafe_allow_html=True)
        st.markdown("<div class='definition-box'><b>位置分級基準</b><br>熱區指標 (P): 15000+<br>社區標準 (C): 8500+<br>高效普及 (X): < 8500</div>", unsafe_allow_html=True)
    with def_col3:
        st.markdown("<div class='definition-box'><b>環境與地段基因 (Context Factor)</b><br>透過 Places API 掃描鄰里組成。精品商圈加乘 (1.15x)；快餐雜訊區降權 (0.8x)。</div>", unsafe_allow_html=True)
        st.markdown("<div class='definition-box'><b>顧客活動區 (200-460 sqft)</b><br>精確定義之美學介入範圍，排除吧台與工作區。</div>", unsafe_allow_html=True)

    st.divider()

    # --- 3. 數據輸入 ---
    st.sidebar.header("查詢資料輸入(僅限美國區域)")
    coord_input = st.sidebar.text_input("📍座標輸入 (緯度, 經度):", placeholder="34.1425, -118.0483")
    loc_type = st.sidebar.selectbox("地點型態:", ["Shopping Mall", "Food Court", "Community", "Plaza", "Main Street"])

    st.sidebar.markdown("---")
    cust_area = st.sidebar.slider("顧客活動空間 (sq. ft.):", 200, 460, 300)
    seat_choice = st.sidebar.radio("座位數:", ["0-5 席", "6-12 席", "13-20 席"])

    # 空間壓力邏輯
    est_seats = 5 if "0-5" in seat_choice else 12 if "6-12" in seat_choice else 20
    area_per_seat = cust_area / est_seats
    pressure_coeff = 1.2 if area_per_seat >= 30 else 1.0 if area_per_seat >= 25 else 0.75
    quality_label = "✨ 極致清晰" if pressure_coeff == 1.2 else "✅ 標準質感" if pressure_coeff == 1.0 else "⚠️ 體驗過載"

    G_KEY = st.secrets.get("GOOGLE_KEY")
    GEMINI_KEY = st.secrets.get("GEMINI_KEY")
    CENSUS_KEY = st.secrets.get("CENSUS_KEY")

    # --- 輔助函數：地段基因偵測 (Places API) ---
    def get_nearby_context(lat, lng, key):
        try:
            url = f"https://maps.googleapis.com/maps/api/place/nearbysearch/json?location={lat},{lng}&radius=500&type=restaurant&key={key}"
            res = requests.get(url).json()
            results = res.get('results', [])
            
            # 統計鄰居類型
            lifestyle_keywords = ['cafe', 'spa', 'beauty_salon', 'gallery', 'yoga', 'boutique']
            noise_keywords = ['fast_food', 'car_repair', 'gas_station']
            
            lifestyle_count = 0
            noise_count = 0
            
            for p in results:
                types = p.get('types', [])
                if any(k in str(types) for k in lifestyle_keywords): lifestyle_count += 1
                if any(k in str(types) for k in noise_keywords): noise_count += 1
            
            # 判定係數
            if lifestyle_count > noise_count + 2: return 1.15, "💎 精品地段基因", lifestyle_count, noise_count
            if noise_count > lifestyle_count + 1: return 0.8, "⚠️ 雜訊地段基因", lifestyle_count, noise_count
            return 1.0, "⚖️ 標準地段基因", lifestyle_count, noise_count
        except:
            return 1.0, "❓ 無法偵測基因", 0, 0

    def get_census_spending_power(lat, lng, api_key):
        try:
            geo_url = f"https://geo.fcc.gov/api/census/area?lat={lat}&lon={lng}&format=json"
            geo_res = requests.get(geo_url).json()
            fips = geo_res['results'][0]['block_fips']
            state, county, tract = fips[:2], fips[2:5], fips[5:11]
            census_url = f"https://api.census.gov/data/2022/acs/acs5?get=B19013_001E&for=tract:{tract}&in=state:{state}%20county:{county}&key={api_key}"
            data = requests.get(census_url).json()
            return int(data[1][0]) / 12
        except: return None

    def get_map_image_secure(lat, lng, key):
        url = f"https://maps.googleapis.com/maps/api/staticmap?center={lat},{lng}&zoom=17&size=800x450&scale=2&key={key}"
        res = requests.get(url)
        return BytesIO(res.content) if res.status_code == 200 else None

    # --- 5. 核心執行 ---
    if st.sidebar.button("Execute Strategic Analysis"):
        if not coord_input: st.error("請提供座標資料。")
        else:
            try:
                parts = coord_input.split(',')
                lat, lng = float(parts[0].strip()), float(parts[1].strip())
                
                with st.spinner("正在執行鄰里基因掃描與數據核算..."):
                    # 1. 聯動消費力
                    spending_power = get_census_spending_power(lat, lng, CENSUS_KEY)
                    if spending_power is None:
                        st.error("❌ 無法獲取美國政府數據，請確認座標位置。")
                        st.stop()
                    
                    # 2. 聯動地段基因 (Place API)
                    context_factor, context_label, l_count, n_count = get_nearby_context(lat, lng, G_KEY)
                    
                    # 3. 演算 SFS
                    density = 12
                    target_index = (0.35 * 2.5) + (0.35 * 2.0)
                    seat_mult = 1.0 if "0-5" in seat_choice else 1.2 if "6-12" in seat_choice else 1.5
                    
                    final_sfs = ((spending_power * target_index) * 7 * 1.1 * seat_mult * pressure_coeff * context_factor) / (math.pow(density, 0.7) + 1)
                    level = "熱區指標 (P)" if final_sfs >= 15000 else "社區標準 (C)" if final_sfs >= 8500 else "高效普及 (X)"
                    gap_pct = max(0, (15000 - final_sfs) / 15000)

                    # --- 畫面呈現 ---
                    m1, m2 = st.columns([2, 1])
                    with m1:
                        st.subheader("Strategic Geographic Snapshot")
                        map_bytes = get_map_image_secure(lat, lng, G_KEY)
                        if map_bytes: st.image(map_bytes, use_container_width=True)
                    with m2:
                        st.subheader("Key Strategic Metrics")
                        st.metric("SFS 分數", f"{final_sfs:.0f}")
                        st.metric("位置型態", level)
                        st.metric("地段基因", context_label)
                        st.metric("空間質量", quality_label)
                        st.metric("月消費力", f"${spending_power:,.0f}")

                    st.divider()
                    
                    # 鄰里基因細分 (增加清晰度)
                    st.subheader("🧬 鄰里基因組成分析 (500m 範圍)")
                    c1, c2, c3 = st.columns(3)
                    c1.write(f"精品/生活方式店鋪: **{l_count}**")
                    c2.write(f"快餐/機能雜訊店鋪: **{n_count}**")
                    c3.write(f"環境加乘係數: **{context_factor}x**")
                    
                    st.divider()
                    st.subheader("🤖 Gemini 戰略診斷報告")
                    genai.configure(api_key=GEMINI_KEY.strip())
                    model = genai.GenerativeModel('gemini-1.5-flash')
                    ctx = f"SFS:{final_sfs:.0f}, Tier:{level}, Context:{context_label}, Quality:{quality_label}"
                    st.markdown(model.generate_content(f"以行銷、設計顧問角度分析數據：{ctx}。請針對『地段基因』與『空間呼吸感』提供具體轉型建議。").text)

            except Exception as e: st.error(f"分析異常: {e}")

    st.caption("Produced by Marketing Designer. v8.6.0 | Reducing Noise. Increasing Clarity.")
