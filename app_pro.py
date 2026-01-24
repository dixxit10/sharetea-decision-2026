import streamlit as st
import requests
import pandas as pd
import math

# --- 1. UI 介面配置  ---
st.set_page_config(page_title="Sharetea Express 決策引擎 v3", layout="wide")

# --- 2. CSS 樣式  ---
st.markdown("""
    <style>
    .stApp { background-color: #0E1117; color: #FFFFFF; }
    [data-testid="stSidebar"] { background-color: #161B22; border-right: 1px solid #30363D; }
    h1, h2, h3, h4, p { color: #FFFFFF !important; font-family: 'Inter', sans-serif; }
    .stMetric [data-testid="stMetricValue"] { color: #00D166 !important; }
    .stButton>button {
        background-color: #238636; color: white; border-radius: 8px;
        border: none; width: 100%; transition: 0.3s; height: 3em;
    }
    .stButton>button:hover { background-color: #2ea043; border: 1px solid #FFFFFF; }
    .stAlert { background-color: rgba(255, 75, 75, 0.1); color: #FF4B4B; border: 1px solid #FF4B4B; }
    </style>
    """, unsafe_allow_html=True)

# --- 3. 戰略定義區 ---
st.title("🧋 Sharetea Express 決策引擎 v3")
st.markdown("<h5 style='color: #8B949E !important;'>基於 2026 品牌全球擴張戰略：Reducing Noise. Increasing Clarity.</h5>", unsafe_allow_html=True)

st.markdown("---")
st.subheader("🎯 決策引擎名詞定義與權重邏輯")

col_def1, col_def2 = st.columns(2)
with col_def1:
    st.markdown("""
    #### 📊 核心指標說明
    * **SFS (Strategic Fit Score)**：衡量地點與品牌契合度，反映 **9.5 級獲利** 潛力。
    * **市場潛力 (Market Potential)**：平衡「基礎購買力 (60%)」與「標竿客群加權 (40%)」，消除數據過度擬合。
    * **非線性密度衰減**：採用開根號處理競爭數，真實反映都會區的群聚效應。
    """)
with col_def2:
    st.markdown("""
    #### ⚖️ 2026 戰略加權
    * **族裔加權**：亞裔 (1.5x)、西裔 (1.0x)。
    * **社交年齡加權**：26-35 歲族群加權 **2.5x**。
    * **座位獲利槓桿**：座位數越多，獲利天花板越高 (最高 1.5x)。
    """)

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

# --- 5. 側邊欄：數據輸入 ---
st.sidebar.header("📍 選址數據輸入")
coord_input = st.sidebar.text_input("貼上座標 (Lat, Lng):", placeholder="33.8581, -118.0804")

# 地段權重映射
zoning_map = {"商業/商場": 1.0, "混合分區": 0.7, "純住宅區": 0.0}
selected_zoning = st.sidebar.selectbox("🏗️ 地段分區:", options=list(zoning_map.keys()))
zoning_factor = zoning_map[selected_zoning]

visibility = st.sidebar.slider("👁️ 能見度評分 (1-10):", 1, 10, 7)

# 座位獲利槓桿映射
seat_map = {"5人以下 (Small)": (1, 1.0), "6-20人 (Standard)": (2, 1.2), "21-30人 (Flagship)": (3, 1.5)}
selected_seat = st.sidebar.radio("🪑 預計座位規模:", options=list(seat_map.keys()), index=1)
seat_grade, seat_multiplier = seat_map[selected_seat]

CENSUS_KEY = st.secrets["CENSUS_KEY"]
GOOGLE_KEY = st.secrets["GOOGLE_KEY"]

# --- 6. 執行診斷邏輯 ---
if st.sidebar.button("啟動戰略診斷"):
    if zoning_factor == 0:
        st.error("🛑 法律排除：純住宅區無法開法經營，已終止診斷。")
    elif not coord_input:
        st.warning("請先輸入座標數據。")
    else:
        try:
            # 座標解析
            parts = coord_input.split(',')
            lat, lng = float(parts[0].strip()), float(parts[1].strip())
            
            with st.spinner("正在解析地理數據雜訊..."):
                # (1) Google Places API (精準競業)
                keywords = "bubble+tea|boba|milk+tea|tea+house"
                place_url = f"https://maps.googleapis.com/maps/api/place/nearbysearch/json?location={lat},{lng}&radius=3218&keyword={keywords}&key={GOOGLE_KEY}"
                density = len(requests.get(place_url).json().get('results', []))

                # (2) Census Geocoder
                c_geo_url = f"https://geocoding.geo.census.gov/geocoder/geographies/coordinates?x={lng}&y={lat}&benchmark=Public_AR_Current&vintage=Current_Current&format=json"
                tract_data = requests.get(c_geo_url).json()['result']['geographies']['Census Tracts'][0]
                
                # (3) Census Data API
                fields = "B01003_001E,B19013_001E,B03002_003E,B03002_004E,B03002_006E,B03001_003E,B01001_011E,B01001_012E,B01001_035E,B01001_036E"
                census_url = f"https://api.census.gov/data/2022/acs/acs5?get={fields}&for=tract:{tract_data['TRACT']}&in=state:{tract_data['STATE']}%20county:{tract_data['COUNTY']}&key={CENSUS_KEY}"
                c_res = requests.get(census_url).json()

                # 數據提取
                if len(c_res) < 2:
                    spending_power, asian_r, hispanic_r, age_r = 8000, 0.4, 0.3, 0.2
                    top_3_eth = [("亞裔", 0.4), ("西裔", 0.3), ("白人", 0.2)]
                else:
                    c = c_res[1]
                    total_pop = int(c[0]) if c[0] else 1
                    income = int(c[1]) if (c[1] and int(c[1]) > 0) else 85000
                    spending_power = income / 12
                    eth_map = {"亞裔": int(c[4])/total_pop, "西裔": int(c[5])/total_pop, "白人": int(c[2])/total_pop}
                    top_3_eth = sorted(eth_map.items(), key=lambda x: x[1], reverse=True)[:3]
                    asian_r, hispanic_r, age_r = eth_map["亞裔"], eth_map["西裔"], sum(int(c[i]) for i in range(6, 10)) / total_pop

            # --- SFS 運算---
            target_index = (asian_r * 1.5) + (hispanic_r * 1.0) + (age_r * 2.5)
            # 解決重疊加權：基礎消費力與標竿客群加權平衡
            market_potential = (spending_power * 0.6) + (spending_power * target_index * 0.4)
            
            # 使用開根號處理密度，減少都會區的競爭懲罰
            final_sfs = (market_potential * visibility * zoning_factor * seat_multiplier) / (math.sqrt(density) + 1)

            # --- 分級與報告 ---
            if final_sfs >= 9000: grade, color = "Grade A+ (旗艦標竿)", "gold"
            elif final_sfs >= 5500: grade, color = "Grade B (優質標準)", "orange"
            else: grade, color = "Grade C (普及成長)", "blue"

            st.subheader("📊 診斷中心即時報告")
            m1, m2, m3 = st.columns(3)
            m1.metric("SFS 戰略分數", f"{final_sfs:.0f}")
            m2.metric("戰略分級", grade)
            m3.metric("月均消費動能", f"${spending_power:,.0f}")
            
            st.divider()
            c_l, c_r = st.columns([2, 1])
            with c_l:
                st.success(f"🏆 診斷結論：該地點展現了 **{grade}** 的潛力。")
                st.write("📈 **2026 戰略分級參考表**")
                st.table(pd.DataFrame({
                    "等級": ["Grade A+ (標竿)", "Grade B (標準)", "Grade C (成長)", "Grade F (排除)"],
                    "門檻 (SFS)": ["> 9,000", "5,500 - 9,000", "2,500 - 5,500", "< 2,500"],
                    "當前狀態": ["🎯" if grade.startswith(g) else "" for g in ["Grade A+", "Grade B", "Grade C", "Grade F"]]
                }))
            with c_r:
                st.write("👥 **區域客群特徵**")
                eth_df = pd.DataFrame(top_3_eth, columns=["Ethnicity", "Ratio"])
                st.bar_chart(eth_df.set_index("Ethnicity"))
                st.caption(f"社交主力 (26-35): {age_r:.1%} | 座位加權: {seat_multiplier}x")

        except Exception as e:
            st.error(f"❌ 診斷雜訊 (請核對座標與網路狀態): {e}")

st.caption("Produced by Marketing Designer. Standard v33 Core Engine. 2026 Strategy Roadmap.")
