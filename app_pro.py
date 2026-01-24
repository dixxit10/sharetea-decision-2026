import streamlit as st
import requests
import pandas as pd
import math

# --- 1. UI 介面配置 ---
st.set_page_config(page_title="Sharetea Express 決策引擎 v3.5", layout="wide")

# --- 2. CSS 樣式 (深色除噪美學) ---
st.markdown("""
    <style>
    .stApp { background-color: #0E1117; color: #FFFFFF; }
    [data-testid="stSidebar"] { background-color: #161B22; border-right: 1px solid #30363D; }
    h1, h2, h3, h4, p { color: #FFFFFF !important; font-family: 'Inter', sans-serif; }
    .stMetric [data-testid="stMetricValue"] { color: #00D166 !important; }
    .stButton>button {
        background-color: #238636; color: white; border-radius: 8px;
        border: none; width: 100%; transition: 0.3s; height: 3.5em; font-weight: bold;
    }
    .stButton>button:hover { background-color: #2ea043; border: 1px solid #FFFFFF; }
    </style>
    """, unsafe_allow_html=True)

# --- 3. 名詞定義 (Strategic Definitions) ---
st.title("🧋 Sharetea Express 決策引擎 v3.5")
st.markdown("<h5 style='color: #8B949E !important;'>2026 戰略：Reducing Noise. Increasing Clarity.</h5>", unsafe_allow_html=True)

with st.expander("📚 診斷名詞定義與演算邏輯"):
    st.markdown("""
    * **SFS (Strategic Fit Score)**：27 組演算法蒸餾出的選址適配總分，反映 **9.5 級獲利** 潛力。
    * **位置分級**：對標「熱區指標 (A+)」、「社區標準 (B)」、「高效普及 (C)」三層戰略。
    * **消費力 (Spending Power)**：以家庭年收入/12 為基礎，評估該區支撐高單價產品的經濟實力。
    * **精英級密度 ($Density^{0.7}$)**：非線性衰減模型，將競爭壓力轉化為市場流量驗證紅利。
    """)

st.divider()

# --- 4. 訪問權限 ---
if "auth" not in st.session_state:
    st.session_state["auth"] = False

if not st.session_state["auth"]:
    pwd = st.text_input("輸入 2026 戰略通訊碼:", type="password")
    if st.button("驗證進入"):
        if pwd == st.secrets["APP_PASSWORD"]: 
            st.session_state["auth"] = True
            st.rerun()
        else:
            st.error("❌ 密碼錯誤。")
    st.stop()

# --- 5. 側邊欄：數據輸入 ---
st.sidebar.header("📍 選址環境參數")
coord_input = st.sidebar.text_input("座標 (Lat, Lng):", placeholder="33.8581, -118.0804")

zoning_map = {"商業/商場": 1.0, "混合分區": 0.7, "純住宅區 (法律禁止)": 0.0}
zoning_factor = zoning_map[st.sidebar.selectbox("🏗️ 地段分區:", options=list(zoning_map.keys()))]

visibility = st.sidebar.slider("👁️ 能見度評分 (1-10):", 1, 10, 7)

seat_map = {"5人以下 (Small)": 1.0, "6-20人 (Standard)": 1.2, "21-30人 (Flagship)": 1.5}
seat_multiplier = seat_map[st.sidebar.radio("🪑 預計座位規模:", options=list(seat_map.keys()), index=1)]

CENSUS_KEY = st.secrets["CENSUS_KEY"]
GOOGLE_KEY = st.secrets["GOOGLE_KEY"]

# --- 6. 執行診斷引擎 ---
if st.sidebar.button("啟動精英戰略診斷"):
    if zoning_factor == 0:
        st.error("🛑 法律排除：純住宅區無法經營。")
    elif not coord_input:
        st.warning("請先提供座標。")
    else:
        try:
            parts = coord_input.split(',')
            lat, lng = float(parts[0].strip()), float(parts[1].strip())
            
            with st.spinner("正在解析 27 組演算數據..."):
                # (1) Google API
                p_url = f"https://maps.googleapis.com/maps/api/place/nearbysearch/json?location={lat},{lng}&radius=3218&keyword=bubble+tea|boba&key={GOOGLE_KEY}"
                density = len(requests.get(p_url).json().get('results', []))

                # (2) Census API
                c_geo_url = f"https://geocoding.geo.census.gov/geocoder/geographies/coordinates?x={lng}&y={lat}&benchmark=Public_AR_Current&vintage=Current_Current&format=json"
                tract = requests.get(c_geo_url).json()['result']['geographies']['Census Tracts'][0]
                
                # 族裔與年齡細分欄位
                fields = "B01003_001E,B19013_001E,B03002_003E,B03001_004E,B01001_011E,B01001_012E,B01001_035E,B01001_036E,B02015_002E,B02015_005E,B02015_009E,B02015_012E,B01001_010E,B01001_034E"
                census_url = f"https://api.census.gov/data/2022/acs/acs5?get={fields}&for=tract:{tract['TRACT']}&in=state:{tract['STATE']}%20county:{tract['COUNTY']}&key={CENSUS_KEY}"
                c = requests.get(census_url).json()[1]

                # 數據解析
                pop = int(c[0]) if c[0] else 1
                spending_power = (int(c[1]) if c[1] else 85000) / 12
                
                # 6 大族裔佔比
                chinese_r = int(c[8]) / pop # 華裔/台灣裔
                mexican_r = int(c[3]) / pop # 墨西哥裔/西裔
                se_asian_r = int(c[9]) / pop # 東南亞裔 (Filipino/Viet)
                e_asian_r = int(c[10]) / pop # 東亞裔 (Korean)
                s_asian_r = int(c[11]) / pop # 南亞裔 (Indian)
                white_r = int(c[2]) / pop    # 白人

                # 年齡細分
                gen_z_r = (int(c[12]) + int(c[13])) / pop # 18-24 視覺驅動
                social_pro_r = (int(c[4]) + int(c[5]) + int(c[6]) + int(c[7])) / pop # 25-34 社交主力

            # --- SFS 精英演算 ---
            target_index = (chinese_r * 2.0) + (mexican_r * 1.5) + (social_pro_r * 2.5)
            market_potential = (spending_power * 0.5) + (spending_power * target_index * 0.5)
            final_sfs = (market_potential * visibility * zoning_factor * seat_multiplier) / (math.pow(density, 0.7) + 1)

            # --- 戰略差距分析 (10% 門檻) ---
            T_A, T_B, T_C = 15000, 8500, 4500
            if final_sfs >= T_A: grade, color = "Grade A+ (熱區指標)", "gold"
            elif final_sfs >= T_B: grade, color = "Grade B (社區標準)", "orange"
            elif final_sfs >= T_C: grade, color = "Grade C (高效普及)", "blue"
            else: grade, color = "Grade F (戰略排除)", "red"

            gap_info = "📍 戰略穩定：明確維持該戰略位置。"
            if grade.startswith("Grade B"):
                gap = (T_A - final_sfs) / T_A
                if gap <= 0.1: gap_info = f"📈 **潛力躍升**：距離 A+ 旗艦標竿僅差 {gap:.1%}。"
            elif grade.startswith("Grade C"):
                gap = (T_B - final_sfs) / T_B
                if gap <= 0.1: gap_info = f"📈 **潛力躍升**：距離 B 社區標準僅差 {gap:.1%}。"

            # 消費行為與預判
            if spending_power > 7500 and social_pro_r > 0.22:
                behavior = "社交美學導向 (Social/Aesthetic)"
                behavior_detail = "具備極高 Miffy 聯名與高品質包裝的溢價承受力。"
            elif spending_power < 5000 or density > 15:
                behavior = "低價/隨機導向 (Price Sensitive)"
                behavior_detail = "受路過便利性或促銷驅動，品牌忠誠度較易流失。"
            else:
                behavior = "品質生活導向 (Quality Daily)"
                behavior_detail = "追求社區便利與品質穩定。對標：星巴克。"

            # --- 報告呈現 ---
            st.subheader("📊 Sharetea 2026 選址診斷摘要")
            m1, m2, m3, m4 = st.columns(4)
            m1.metric("SFS 戰略總分", f"{final_sfs:.0f}")
            m2.metric("當前位置分級", grade)
            m3.metric("月均基礎消費力", f"${spending_power:,.0f}")
            m4.metric("周邊競業數", f"{density} 家")

            st.divider()
            l_col, r_col = st.columns(2)
            with l_col:
                st.markdown(f"### 🎯 戰略差距分析\n{gap_info}")
                st.markdown(f"### 🛍️ 消費行為與預判\n* **核心行為**：{behavior}\n* **細部預判**：{behavior_detail}")
                st.markdown(f"### 🏆 綜合建議\n該地段對標 **{grade.split(' ')[2]}**。建議優化「低糖/少冰」與高品質原葉茶配方，維持品牌標竿地位。")

            with r_col:
                st.markdown("### 👥 人口組成與年齡細分")
                eth_df = pd.DataFrame({
                    "族群類別": ["華裔/台灣裔", "墨西哥裔/西裔", "東南亞裔", "東亞裔 (韓)", "南亞裔", "白人"],
                    "比例佔比": [f"{chinese_r:.1%}", f"{mexican_r:.1%}", f"{se_asian_r:.1%}", f"{e_asian_r:.1%}", f"{s_asian_r:.1%}", f"{white_r:.1%}"]
                })
                st.table(eth_df)
                
                age_df = pd.DataFrame({
                    "客群分段": ["18-24 歲 (視覺驅動)", "25-34 歲 (社交主力)", "35 歲以上"],
                    "比例佔比": [f"{gen_z_r:.1%}", f"{social_pro_r:.1%}", f"{(1-gen_z_r-social_pro_r):.1%}"]
                })
                st.table(age_df)

        except Exception as e:
            st.error(f"❌ 診斷雜訊 (請核對座標): {e}")

st.caption("Produced by Marketing Designer. 2026 Strategy Roadmap.")
