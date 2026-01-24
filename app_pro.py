import streamlit as st
import requests
import pandas as pd
import math

# --- 1. UI 介面配置 (標竿美學) ---
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
        border: none; width: 100%; transition: 0.3s; height: 3.5em; font-weight: bold;
    }
    .stButton>button:hover { background-color: #2ea043; border: 1px solid #FFFFFF; }
    .stAlert { background-color: rgba(255, 75, 75, 0.1); color: #FF4B4B; border: 1px solid #FF4B4B; }
    </style>
    """, unsafe_allow_html=True)

# --- 3. 戰略核心定義 ---
st.title("🧋 Sharetea Express 決策引擎 v3")
st.markdown("<h5 style='color: #8B949E !important;'>2026 戰略：Reducing Noise. Increasing Clarity.</h5>", unsafe_allow_html=True)

st.markdown("---")
st.subheader("🎯 5 大精英演算支柱 (Strategic Pillars)")

col_def1, col_def2 = st.columns(2)
with col_def1:
    st.markdown("""
    * **精英級密度 ($Density^{0.7}$)**：修正線性殺傷力，找回都會精華區流量紅利。
    * **混合購買力平衡**：50/50 分配基礎收入與標竿客群加權，消除數據擬合雜訊。
    * **社交人格索引**：鎖定 26-35 歲核心族群，加權 **2.5x**。
    """)
with col_def2:
    st.markdown("""
    * **獲利槓桿 (Seats)**：旗艦規模加權 **1.5x**，對標「熱區指標」價值。
    * **口味戰略標籤**：亞裔/西裔權重對等 (1.5x)，但標示特定族群以指導產品開發。
    """)

st.markdown("#### 🚀 核心演算公式")
st.latex(r'''SFS = \frac{\text{Market Potential} \times \text{Visibility} \times \text{Zoning} \times \text{Seat Multiplier}}{\text{Density}^{0.7} + 1}''')
st.divider()

# --- 4. 訪問權限 ---
if "auth" not in st.session_state:
    st.session_state["auth"] = False

if not st.session_state["auth"]:
    pwd = st.text_input("請輸入 2026 戰略通訊碼:", type="password")
    if st.button("驗證進入"):
        if pwd == st.secrets["APP_PASSWORD"]: 
            st.session_state["auth"] = True
            st.rerun()
        else:
            st.error("❌ 密碼錯誤，請聯繫行銷設計部門。")
    st.stop()

# --- 5. 側邊欄輸入 ---
st.sidebar.header("📍 選址環境參數")
coord_input = st.sidebar.text_input("貼上座標 (Lat, Lng):", placeholder="33.8581, -118.0804")

zoning_map = {"商業/商場": 1.0, "混合分區": 0.7, "純住宅區 (法律禁止)": 0.0}
selected_zoning = st.sidebar.selectbox("🏗️ 地段分區:", options=list(zoning_map.keys()))
zoning_factor = zoning_map[selected_zoning]

visibility = st.sidebar.slider("👁️ 能見度/人流評分 (1-10):", 1, 10, 7)

seat_map = {"5人以下 (Small)": 1.0, "6-20人 (Standard)": 1.2, "21-30人 (Flagship)": 1.5}
selected_seat = st.sidebar.radio("🪑 預計座位規模:", options=list(seat_map.keys()), index=1)
seat_multiplier = seat_map[selected_seat]

CENSUS_KEY = st.secrets["CENSUS_KEY"]
GOOGLE_KEY = st.secrets["GOOGLE_KEY"]

# --- 6. 診斷引擎 ---
if st.sidebar.button("啟動精英戰略診斷"):
    if zoning_factor == 0:
        st.error("🛑 **法律限制排除**：該地點為純住宅區，無法取得營業許可。")
    elif not coord_input:
        st.warning("請先提供座標數據。")
    else:
        try:
            parts = coord_input.split(',')
            lat, lng = float(parts[0].strip()), float(parts[1].strip())
            
            with st.spinner("正在進行 27 組演算法蒸餾..."):
                # (1) Google API
                place_url = f"https://maps.googleapis.com/maps/api/place/nearbysearch/json?location={lat},{lng}&radius=3218&keyword=bubble+tea|boba|milk+tea&key={GOOGLE_KEY}"
                density = len(requests.get(place_url).json().get('results', []))

                # (2) Census Geocoder
                c_geo_url = f"https://geocoding.geo.census.gov/geocoder/geographies/coordinates?x={lng}&y={lat}&benchmark=Public_AR_Current&vintage=Current_Current&format=json"
                tract = requests.get(c_geo_url).json()['result']['geographies']['Census Tracts'][0]
                
                # (3) Census Data (含細分族裔與精確年齡)
                fields = "B01003_001E,B19013_001E,B03002_003E,B03001_003E,B01001_011E,B01001_012E,B01001_013E,B02015_002E,B02015_017E,B02015_009E,B02015_015E,B03002_006E"
                census_url = f"https://api.census.gov/data/2022/acs/acs5?get={fields}&for=tract:{tract['TRACT']}&in=state:{tract['STATE']}%20county:{tract['COUNTY']}&key={CENSUS_KEY}"
                c_res = requests.get(census_url).json()[1]

                # 數據解析
                pop = int(c_res[0]) if c_res[0] else 1
                spending_power = (int(c_res[1]) if c_res[1] else 88000) / 12
                white_r, hispanic_r, asian_r = int(c_res[2])/pop, int(c_res[3])/pop, int(c_res[11])/pop
                age_26_35_r = (int(c_res[4]) + int(c_res[5])) / pop
                
                # 細分亞裔 (用於口味策略)
                chinese_taiwan_r = (int(c_res[7]) + int(c_res[8])) / pop
                se_asian_r = (int(c_res[9]) + int(c_res[10])) / pop

            # --- SFS 精英運算 ---
            target_index = (asian_r * 1.5) + (hispanic_r * 1.5) + (age_26_35_r * 2.5)
            market_potential = (spending_power * 0.5) + (spending_power * target_index * 0.5)
            final_sfs = (market_potential * visibility * zoning_factor * seat_multiplier) / (math.pow(density, 0.7) + 1)

            # --- 戰略位置判定 ---
            if final_sfs >= 15000: grade, color, pos = "Grade A+ (熱區指標)", "gold", "Flagship"
            elif final_sfs >= 8500: grade, color, pos = "Grade B (社區標準)", "orange", "Standard"
            else: grade, color, pos = "Grade C (高效普及)", "blue", "Efficiency"

            # --- 口味與年齡戰略 ---
            flavor_label = "華裔/台灣裔核心" if chinese_taiwan_r > se_asian_r else "西裔/東南亞裔核心"
            flavor_strategy = "主打原葉茶與低糖配方" if "華裔" in flavor_label else "主打視覺系果茶與高甜度配料"

            # --- 報告輸出 ---
            st.subheader("📊 診斷中心即時報告")
            m1, m2, m3, m4 = st.columns(4)
            m1.metric("SFS 戰略分數", f"{final_sfs:.0f}")
            m2.metric("戰略位置", grade)
            m3.metric("口味戰略標籤", flavor_label)
            m4.metric("周邊競業", f"{density} 家")

            st.divider()
            c_l, c_r = st.columns([2, 1])
            with c_l:
                st.success(f"🎨 **Marketing Designer 執行指令：**\n\n**【定位】** 該店對標 **{pos}** 級別。\n\n**【口味策略】** {flavor_strategy}。\n\n**【年齡策略】** 針對 26-35 歲社交主力提供 **Miffy 聯名** 高質感周邊。")
                st.table(pd.DataFrame({
                    "戰略等級": ["Grade A+ (熱區指標)", "Grade B (社區標準)", "Grade C (高效普及)"],
                    "核心價值": ["美學識別 / 高坪效", "品質便利 / 生活態度", "高擴張 / 垂直供應鏈"],
                    "對標品牌": ["茶姬 / 喜茶", "星巴克", "全球蜜雪"],
                    "狀態": ["🎯" if grade.startswith(g) else "" for g in ["Grade A+", "Grade B", "Grade C"]]
                }))
            with c_r:
                st.write("👥 **區域人口組成**")
                eth_df = pd.DataFrame({"Ethnicity": ["亞裔", "西裔", "白人"], "Ratio": [asian_r, hispanic_r, white_r]})
                st.bar_chart(eth_df.set_index("Ethnicity"))
                st.caption(f"社交主力 (26-35): {age_26_35_r:.1%}")

        except Exception as e:
            st.error(f"❌ 診斷雜訊: {e}")

st.caption("Produced by Marketing Designer. Standard v33 Core Engine. 2026 Strategy Roadmap.")
