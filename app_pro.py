import streamlit as st
import requests
import pandas as pd
import math

# --- 1. UI 介面配置 ---
st.set_page_config(page_title="Sharetea Express 決策引擎 v3.9", layout="wide")

# --- 2. CSS 樣式 (品牌深色除噪美學) ---
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

# --- 3. 戰略名詞定義 (展開設計) ---
st.title("🧋 Sharetea Express 決策引擎 v3.9")
st.markdown("<h5 style='color: #8B949E !important;'>2026 核心戰略：都會品牌店轉型實施路徑</h5>", unsafe_allow_html=True)

st.markdown("### 📚 戰略名詞定義 (Strategic Definitions)")
col_def1, col_def2 = st.columns(2)
with col_def1:
    st.markdown("""
    * **SFS (Strategic Fit Score)**：綜合 27 組演算 (座位數x區域x行為) 的戰略適配總分。
    * **熱區指標 (Hotspot Index)**：具備高昂美學溢價、高坪效與社交影響力的旗艦級地段。
    * **社區標準 (Community Standard)**：平衡品質、便利與生活態度的日常型消費核心。
    """)
with col_def2:
    st.markdown("""
    * **高效普及 (Efficiency Access)**：強調垂直供應鏈效率與快速通路的擴張型選址。
    * **精英級密度 ($Density^{0.7}$)**：非線性衰減運算，將競爭壓力轉化為市場流量驗證紅利。
    * **消費動能 (Spending Power)**：普查區月均基礎家庭收入，決定獲利天花板。
    """)

st.divider()

# --- 4. 訪問權限 ---
if "auth" not in st.session_state: st.session_state["auth"] = False
if not st.session_state["auth"]:
    pwd = st.text_input("輸入 2026 戰略通訊碼:", type="password")
    if st.button("驗證進入"):
        if pwd == st.secrets["APP_PASSWORD"]: st.session_state["auth"] = True; st.rerun()
        else: st.error("❌ 驗證失敗。")
    st.stop()

# --- 5. 側邊欄：環境參數 ---
st.sidebar.header("📍 選址戰略數據")
coord_input = st.sidebar.text_input("座標 (Lat, Lng):", placeholder="33.8581, -118.0804")

zoning_map = {"商業/商場": 1.0, "混合分區": 0.7, "純住宅區 (法律禁止)": 0.0}
zoning_factor = zoning_map[st.sidebar.selectbox("🏗️ 地段分區:", options=list(zoning_map.keys()))]

visibility = st.sidebar.slider("👁️ 能見度評分 (1-10):", 1, 10, 7)

seat_map = {"5人以下 (高效型)": 1.0, "6-20人 (標準型)": 1.2, "21-30人 (旗艦型)": 1.5}
seat_multiplier = seat_map[st.sidebar.radio("🪑 預計空間規模:", options=list(seat_map.keys()), index=1)]

CENSUS_KEY = st.secrets["CENSUS_KEY"]
GOOGLE_KEY = st.secrets["GOOGLE_KEY"]

# --- 6. 診斷引擎 ---
if st.sidebar.button("啟動選址戰略診斷"):
    if zoning_factor == 0: st.error("🛑 法律排除：純住宅區禁止經營。")
    elif not coord_input: st.warning("請提供座標。")
    else:
        try:
            parts = coord_input.split(','); lat, lng = float(parts[0].strip()), float(parts[1].strip())
            with st.spinner("正在進行精英演算與排序..."):
                # Google & Census API
                p_url = f"https://maps.googleapis.com/maps/api/place/nearbysearch/json?location={lat},{lng}&radius=3218&keyword=bubble+tea|boba&key={GOOGLE_KEY}"
                density = len(requests.get(p_url).json().get('results', []))

                c_geo_url = f"https://geocoding.geo.census.gov/geocoder/geographies/coordinates?x={lng}&y={lat}&benchmark=Public_AR_Current&vintage=Current_Current&format=json"
                tract = requests.get(c_geo_url).json()['result']['geographies']['Census Tracts'][0]
                
                # 族裔細分代碼: 華(02E), 韓(09E), 越(15E), 墨(004E), 菲(005E), 白(002E)
                fields = "B01003_001E,B19013_001E,B03002_003E,B03001_004E,B01001_011E,B01001_012E,B01001_035E,B01001_036E,B02015_002E,B02015_009E,B02015_015E,B02015_005E,B01001_010E,B01001_034E"
                census_url = f"https://api.census.gov/data/2022/acs/acs5?get={fields}&for=tract:{tract['TRACT']}&in=state:{tract['STATE']}%20county:{tract['COUNTY']}&key={CENSUS_KEY}"
                c = requests.get(census_url).json()[1]

                pop = int(c[0]) if c[0] else 1; spending_power = (int(c[1]) if c[1] else 85000) / 12
                
                # 族裔與年齡 (由高到低排序邏輯)
                eth_data = {
                    "華裔/台灣裔": int(c[8])/pop, "墨西哥裔/西裔": int(c[3])/pop, "東南亞裔 (菲/越)": (int(c[10])+int(c[11]))/pop,
                    "東亞裔 (韓/日)": int(c[9])/pop, "南亞裔": 0.05, "白人": int(c[2])/pop
                }
                sorted_eth = sorted(eth_data.items(), key=lambda x: x[1], reverse=True)

                age_data = {
                    "18-24 歲 (視覺驅動)": (int(c[12]) + int(c[13])) / pop,
                    "25-34 歲 (社交主力)": (int(c[4]) + int(c[5]) + int(c[6]) + int(c[7])) / pop,
                    "35 歲以上 (品質穩定)": 1 - ((int(c[12]) + int(c[13]) + int(c[4]) + int(c[5]) + int(c[6]) + int(c[7])) / pop)
                }
                sorted_age = sorted(age_data.items(), key=lambda x: x[1], reverse=True)
                
                social_r = age_data["25-34 歲 (社交主力)"]

            # --- SFS 演算 ---
            target_index = (eth_data["華裔/台灣裔"] * 2.0) + (eth_data["墨西哥裔/西裔"] * 1.5) + (social_r * 2.5)
            market_potential = (spending_power * 0.5) + (spending_power * target_index * 0.5)
            final_sfs = (market_potential * visibility * zoning_factor * seat_multiplier) / (math.pow(density, 0.7) + 1)

            # --- 7. 戰略位置判定與 15% 差距邏輯 ---
            T_HOT, T_STD, T_EFF = 15000, 8500, 4500
            if final_sfs >= T_HOT: level, color = "熱區指標 (Hotspot Index)", "gold"
            elif final_sfs >= T_STD: level, color = "社區標準 (Community Standard)", "orange"
            elif final_sfs >= T_EFF: level, color = "高效普及 (Efficiency Access)", "blue"
            else: level, color = "戰略排除 (Exclusion)", "red"

            # 差距分析
            gap_info = "📍 戰略穩定：明確維持該戰略位置。"
            if level == "社區標準 (Community Standard)":
                gap = (T_HOT - final_sfs) / T_HOT
                if gap <= 0.15: gap_info = f"📈 **潛力躍升**：距離『熱區指標』僅差 {gap:.1%}。"
            elif level == "高效普及 (Efficiency Access)":
                gap = (T_STD - final_sfs) / T_STD
                if gap <= 0.15: gap_info = f"📈 **潛力躍升**：距離『社區標準』僅差 {gap:.1%}。"

            # 消費行為預判
            if spending_power < 6000 and density > 15:
                behavior = "價格導向型 (Price-Driven)"; bev_detail = "受低價或促銷驅動，品牌忠誠度低。對標：全球蜜雪。"
            elif density > 18:
                behavior = "快速消費型 (Fast Consumption)"; bev_detail = "路過買了就走，能見度優先於美學。建議優化快速點餐流程。"
            elif spending_power > 8000 and social_r > 0.22:
                behavior = "社交美學導向 (Social Aesthetics)"; bev_detail = "具備高品牌溢價承受力，重視聯名識別。對標：茶姬。"
            else:
                behavior = "品質生活導向"; bev_detail = "社區穩定消費，重視品質與便利。對標：星巴克。"

            # --- 最終報告呈現 ---
            st.subheader("📊 Sharetea 2026 選址戰略診斷結果")
            m1, m2, m3, m4 = st.columns(4)
            m1.metric("SFS 戰略總分", f"{final_sfs:.0f}")
            m2.metric("戰略位置", level)
            m3.metric("月消費動能", f"${spending_power:,.0f}")
            m4.metric("周邊競業數", f"{density} 家")

            st.markdown(f"#### 🔍 分級落點與門檻：{level} (指標門檻: {T_HOT} / {T_STD} / {T_EFF})")
            st.divider()

            l_col, r_col = st.columns(2)
            with l_col:
                st.markdown(f"### 🎯 戰略差距分析\n{gap_info}")
                st.markdown(f"### 🛍️ 消費行為與預判\n* **預判模式**：{behavior}\n* **行為細部解析**：{bev_detail}")
                st.info(f"🏆 **綜合建議**：\n對標『{level.split(' ')[0]}』。若為高效普及區，應強化供應鏈與外送效率；若為熱區指標，應全面導入 Miffy 旗艦美學。")

            with r_col:
                st.markdown("### 👥 客群結構 (依比例高到低排列)")
                eth_sorted_df = pd.DataFrame(sorted_eth, columns=["族群", "比例"]).style.format({"比例": "{:.1%}"})
                st.table(eth_sorted_df)
                
                st.markdown("### 🎂 年齡組成 (依比例高到低排列)")
                age_sorted_df = pd.DataFrame(sorted_age, columns=["年齡層", "比例"]).style.format({"比例": "{:.1%}"})
                st.table(age_sorted_df)

        except Exception as e: st.error(f"❌ 診斷雜訊: {e}")

st.caption("Produced by Marketing Designer. v3.9.1 Build 2026.")
