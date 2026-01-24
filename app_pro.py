import streamlit as st
import requests
import pandas as pd
import math

# --- 1. UI 介面配置 ---
st.set_page_config(page_title="Sharetea Express 決策引擎 v3", layout="wide")

# --- 2. CSS 樣式 (深色除噪版) ---
st.markdown("""
    <style>
    .stApp { background-color: #0E1117; color: #FFFFFF; }
    [data-testid="stSidebar"] { background-color: #161B22; border-right: 1px solid #30363D; }
    h1, h2, h3, h4, p { color: #FFFFFF !important; font-family: 'Inter', sans-serif; }
    .stMetric [data-testid="stMetricValue"] { color: #00D166 !important; }
    .stButton>button {
        background-color: #238636; color: white; border-radius: 8px;
        border: none; width: 100%; transition: 0.3s; height: 3.5em;
    }
    .stButton>button:hover { background-color: #2ea043; border: 1px solid #FFFFFF; }
    </style>
    """, unsafe_allow_html=True)

st.title("🧋 Sharetea Express 決策引擎 v3")
st.markdown("<h5 style='color: #8B949E !important;'>2026 精英演算：座位數 x 區域 x 行為 (5 支柱核心版)</h5>", unsafe_allow_html=True)
st.divider()

# --- 3. 訪問權限 ---
if "auth" not in st.session_state:
    st.session_state["auth"] = False

if not st.session_state["auth"]:
    pwd = st.text_input("請輸入 2026 戰略通訊碼:", type="password")
    if st.button("驗證進入"):
        if pwd == st.secrets["APP_PASSWORD"]: 
            st.session_state["auth"] = True
            st.rerun()
        else:
            st.error("❌ 密碼錯誤。")
    st.stop()

# --- 4. 側邊欄：戰略參數輸入 ---
st.sidebar.header("📍 選址環境參數")
coord_input = st.sidebar.text_input("貼上座標 (Lat, Lng):", placeholder="33.8581, -118.0804")

zoning_map = {"商業/商場": 1.0, "混合分區": 0.7, "純住宅區 (法律禁止)": 0.0}
selected_zoning = st.sidebar.selectbox("🏗️ 地段分區:", options=list(zoning_map.keys()))
zoning_factor = zoning_map[selected_zoning]

visibility = st.sidebar.slider("👁️ 能見度/人流評分 (1-10):", 1, 10, 7)

# 座位規模加權 (5 支柱演算法之一)
seat_map = {"5人以下 (Small)": 1.0, "6-20人 (Standard)": 1.2, "21-30人 (Flagship)": 1.5}
selected_seat = st.sidebar.radio("🪑 預計座位規模:", options=list(seat_map.keys()), index=1)
seat_multiplier = seat_map[selected_seat]

CENSUS_KEY = st.secrets["CENSUS_KEY"]
GOOGLE_KEY = st.secrets["GOOGLE_KEY"]

# --- 5. 執行診斷引擎 ---
if st.sidebar.button("啟動戰略診斷"):
    if zoning_factor == 0:
        st.error("🛑 法律排除：純住宅區無法開法經營，已終止診斷。")
    elif not coord_input:
        st.warning("請輸入座標。")
    else:
        try:
            parts = coord_input.split(',')
            lat, lng = float(parts[0].strip()), float(parts[1].strip())
            
            with st.spinner("正在解析 27 組演算數據..."):
                # (1) Google API - 競業密度
                place_url = f"https://maps.googleapis.com/maps/api/place/nearbysearch/json?location={lat},{lng}&radius=3218&keyword=bubble+tea|boba&key={GOOGLE_KEY}"
                density = len(requests.get(place_url).json().get('results', []))

                # (2) Census API - 人口與年齡細分
                c_geo_url = f"https://geocoding.geo.census.gov/geocoder/geographies/coordinates?x={lng}&y={lat}&benchmark=Public_AR_Current&vintage=Current_Current&format=json"
                tract = requests.get(c_geo_url).json()['result']['geographies']['Census Tracts'][0]
                
                fields = "B01003_001E,B19013_001E,B03002_003E,B03001_003E,B01001_010E,B01001_011E,B01001_012E,B01001_034E,B01001_035E,B01001_036E,B03002_006E"
                census_url = f"https://api.census.gov/data/2022/acs/acs5?get={fields}&for=tract:{tract['TRACT']}&in=state:{tract['STATE']}%20county:{tract['COUNTY']}&key={CENSUS_KEY}"
                c_res = requests.get(census_url).json()[1]

                # 數據解析
                pop = int(c_res[0]) if c_res[0] else 1
                spending_power = (int(c_res[1]) if c_res[1] else 88000) / 12
                asian_r, hispanic_r = int(c_res[10])/pop, int(c_res[3])/pop
                
                # 年齡細分組成
                gen_z_r = (int(c_res[4]) + int(c_res[7])) / pop # 18-24 歲
                social_pro_r = (int(c_res[5]) + int(c_res[6]) + int(c_res[8]) + int(c_res[9])) / pop # 25-34 歲社交主力

            # --- SFS 精英演算邏輯 (解決通膨與雜訊) ---
            target_index = (asian_r * 1.5) + (hispanic_r * 1.5) + (social_pro_r * 2.5)
            market_potential = (spending_power * 0.5) + (spending_power * target_index * 0.5)
            final_sfs = (market_potential * visibility * zoning_factor * seat_multiplier) / (math.pow(density, 0.7) + 1)

            # --- 戰略位置分級與門檻分析 (10% 差距邏輯) ---
            T_A, T_B, T_C = 15000, 8500, 4500
            
            if final_sfs >= T_A: 
                grade, color, gap_text = "Grade A+ (熱區指標)", "gold", "📍 戰略確診：明確維持該戰略位置。"
            elif final_sfs >= T_B:
                grade, color = "Grade B (社區標準)", "orange"
                gap_to_a = (T_A - final_sfs) / T_A
                gap_text = f"📈 **潛力躍升**：距離 A+ 僅差 {gap_to_a:.1%}。" if gap_to_a <= 0.1 else "📍 戰略穩定：明確維持該戰略位置。"
            elif final_sfs >= T_C:
                grade, color = "Grade C (高效普及)", "blue"
                gap_to_b = (T_B - final_sfs) / T_B
                gap_text = f"📈 **潛力躍升**：距離 B 僅差 {gap_to_b:.1%}。" if gap_to_b <= 0.1 else "📍 戰略穩定：明確維持該戰略位置。"
            else:
                grade, color, gap_text = "Grade F (排除)", "red", "🛑 戰略排除。"

            # 消費行為與風格預判
            behavior = "社交美學導向" if social_pro_r > 0.22 else "品質穩定導向"
            style = "偏好鮮果系列與視覺衝擊" if hispanic_r > asian_r else "偏好純茶系列與低糖機能配方"

            # --- 輸出精英診斷報告 ---
            st.subheader("📊 2026 選址診斷摘要")
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("SFS 戰略總分", f"{final_sfs:.0f}")
            c2.metric("當前位置分級", grade)
            c3.metric("月均基礎消費力", f"${spending_power:,.0f}")
            c4.metric("周邊競業數", f"{density} 家")

            st.divider()
            
            l_col, r_col = st.columns(2)
            with l_col:
                st.markdown(f"### 🎯 戰略差距分析\n{gap_text}")
                st.markdown(f"### 🛍️ 消費行為與預判\n* **核心行為**：{behavior}\n* **消費風格**：{style}")
            
            with r_col:
                st.markdown("### 👥 人口與年齡組成細分")
                age_table = pd.DataFrame({
                    "客群類別": ["18-24 歲 (視覺驅動)", "25-34 歲 (社交主力)", "35 歲以上 (品質導向)"],
                    "比例佔比": [f"{gen_z_r:.1%}", f"{social_pro_r:.1%}", f"{(1-gen_z_r-social_pro_r):.1%}"]
                })
                st.table(age_table)

        except Exception as e:
            st.error(f"❌ 診斷中斷: {e}")

st.caption("Produced by Marketing Designer. 2026 Strategy Roadmap.")
