import streamlit as st
import requests
import pandas as pd
import math

# --- 1. UI 與 CSS ---
st.set_page_config(page_title="Sharetea Express 決策引擎 v3.7", layout="wide")
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

# --- 2. 名詞定義 ---
st.title("🧋 Sharetea Express 決策引擎 v3.7")
st.markdown("<h5 style='color: #8B949E !important;'>2026 戰略核心：減少雜訊，增加清晰度</h5>", unsafe_allow_html=True)

with st.expander("📚 查看診斷名詞定義"):
    st.markdown("""
    * **SFS (Strategic Fit Score)**：綜合 27 組演算法 (座位x區域x行為) 的戰略適配總分。
    * **熱區指標 (Hotspot Index)**：高美學溢價、高坪效與社交驅動的旗艦地段。
    * **社區標準 (Community Standard)**：平衡品質、便利與生活態度的核心選址。
    * **高效普及 (Efficiency Access)**：強調垂直供應鏈、價格導向與快速通路的擴張型選址。
    """)

st.divider()

# --- 3. 權限與側邊欄 ---
if "auth" not in st.session_state: st.session_state["auth"] = False
if not st.session_state["auth"]:
    pwd = st.text_input("輸入 2026 戰略通訊碼:", type="password")
    if st.button("驗證進入"):
        if pwd == st.secrets["APP_PASSWORD"]: st.session_state["auth"] = True; st.rerun()
        else: st.error("❌ 驗證失敗。")
    st.stop()

st.sidebar.header("📍 選址戰略數據輸入")
coord_input = st.sidebar.text_input("座標 (Lat, Lng):", placeholder="33.8581, -118.0804")
zoning_map = {"商業/商場": 1.0, "混合分區": 0.7, "純住宅區 (法律禁止)": 0.0}
zoning_factor = zoning_map[st.sidebar.selectbox("🏗️ 地段分區:", options=list(zoning_map.keys()))]
visibility = st.sidebar.slider("👁️ 能見度評分 (1-10):", 1, 10, 7)
seat_map = {"5人以下 (高效)": 1.0, "6-20人 (標準)": 1.2, "21-30人 (旗艦)": 1.5}
seat_multiplier = seat_map[st.sidebar.radio("🪑 預計空間規模:", options=list(seat_map.keys()), index=1)]

CENSUS_KEY = st.secrets["CENSUS_KEY"]
GOOGLE_KEY = st.secrets["GOOGLE_KEY"]

# --- 4. 診斷執行 ---
if st.sidebar.button("啟動選址戰略診斷"):
    if zoning_factor == 0: st.error("🛑 法律排除：純住宅區禁止經營。")
    elif not coord_input: st.warning("請提供座標數據。")
    else:
        try:
            parts = coord_input.split(','); lat, lng = float(parts[0].strip()), float(parts[1].strip())
            with st.spinner("正在進行精英演算..."):
                # Google & Census API 調用 (省略細節，確保代碼精簡)
                place_url = f"https://maps.googleapis.com/maps/api/place/nearbysearch/json?location={lat},{lng}&radius=3218&keyword=bubble+tea|boba&key={GOOGLE_KEY}"
                density = len(requests.get(place_url).json().get('results', []))
                
                c_geo_url = f"https://geocoding.geo.census.gov/geocoder/geographies/coordinates?x={lng}&y={lat}&benchmark=Public_AR_Current&vintage=Current_Current&format=json"
                tract = requests.get(c_geo_url).json()['result']['geographies']['Census Tracts'][0]
                
                # 族群與年齡欄位 (ACS5 2022)
                fields = "B01003_001E,B19013_001E,B03002_003E,B03001_004E,B01001_011E,B01001_012E,B01001_035E,B01001_036E,B02015_002E,B02015_009E,B02015_015E,B02015_005E"
                census_url = f"https://api.census.gov/data/2022/acs/acs5?get={fields}&for=tract:{tract['TRACT']}&in=state:{tract['STATE']}%20county:{tract['COUNTY']}&key={CENSUS_KEY}"
                c = requests.get(census_url).json()[1]

                pop = int(c[0]) if c[0] else 1; spending_power = (int(c[1]) if c[1] else 85000) / 12
                chinese_r, mexican_r, east_asian_r = int(c[8])/pop, int(c[3])/pop, int(c[9])/pop
                se_asian_r, south_asian_r, white_r = int(c[11])/pop, int(c[10])/pop, int(c[2])/pop
                social_r = (int(c[4]) + int(c[5]) + int(c[6]) + int(c[7])) / pop

            # --- 5. 戰略邏輯計算 ---
            target_index = (chinese_r * 2.0) + (mexican_r * 1.5) + (social_r * 2.5)
            market_potential = (spending_power * 0.5) + (spending_power * target_index * 0.5)
            final_sfs = (market_potential * visibility * zoning_factor * seat_multiplier) / (math.pow(density, 0.7) + 1)

            # 戰略位置判定
            T_HOT, T_STD, T_EFF = 15000, 8500, 4500
            if final_sfs >= T_HOT: level, color = "熱區指標 (Hotspot Index)", "gold"
            elif final_sfs >= T_STD: level, color = "社區標準 (Community Standard)", "orange"
            elif final_sfs >= T_EFF: level, color = "高效普及 (Efficiency Access)", "blue"
            else: level, color = "戰略排除 (Exclusion)", "red"

            # 10% 差距分析
            gap_info = "📍 戰略穩定：明確維持該戰略位置。"
            if level == "社區標準 (Community Standard)":
                gap = (T_HOT - final_sfs) / T_HOT
                if gap <= 0.15: gap_info = f"📈 **潛力躍升**：距離『熱區指標』僅差 {gap:.1%}。"
            elif level == "高效普及 (Efficiency Access)":
                gap = (T_STD - final_sfs) / T_STD
                if gap <= 0.15: gap_info = f"📈 **潛力躍升**：距離『社區標準』僅差 {gap:.1%}。"

            # 消費行為預判
            if spending_power < 6000 and density > 15:
                behavior = "價格導向型 (Price-Driven)"; bev_detail = "對價格極敏感，品牌忠誠度低。"
            elif density > 15:
                behavior = "快速消費型 (Fast Consumption)"; bev_detail = "追求路過便利，能見度優先於美學設計。"
            else:
                behavior = "品質生活導向"; bev_detail = "社區穩定消費，重視生活態度。"

            # --- 6. 最終診斷報告輸出 ---
            st.subheader("📊 Sharetea 2026 選址診斷摘要")
            m1, m2, m3, m4, m5 = st.columns(5)
            m1.metric("SFS 戰略總分", f"{final_sfs:.0f}")
            m2.metric("戰略位置", level)
            m3.metric("月消費動能", f"${spending_power:,.0f}")
            m4.metric("周邊競業", f"{density} 家")
            m5.metric("核心行為", behavior)

            st.divider()
            l_col, r_col = st.columns(2)
            with l_col:
                st.markdown(f"### 🎯 戰略差距分析\n{gap_info}")
                st.markdown(f"### 🛍️ 消費行為預判\n* **預判模式**：{behavior}\n* **行為細節**：{bev_detail}")
                st.info(f"🏆 **綜合建議**：\n對標『{level.split(' ')[0]}』。若處於高效普及位置，建議轉向『垂直供應鏈』以解套競爭壓力。")

            with r_col:
                st.markdown("### 👥 人口組成與年齡細分")
                eth_df = pd.DataFrame({
                    "族群": ["華裔/台灣裔", "墨西哥裔/西裔", "東南亞裔", "東亞裔", "南亞裔", "白人"],
                    "佔比": [f"{chinese_r:.1%}", f"{mexican_r:.1%}", f"{se_asian_r:.1%}", f"{east_asian_r:.1%}", f"{south_asian_r:.1%}", f"{white_r:.1%}"]
                })
                st.table(eth_df)
                st.caption(f"社交主力 (25-34): {social_r:.1%} | 消費力評級: {'標竿' if spending_power > 7500 else '普及'}")

        except Exception as e: st.error(f"❌ 診斷雜訊: {e}")

st.caption("Produced by Marketing Designer. v3.7.1 Build 2026.")

