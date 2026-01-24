import streamlit as st
import requests
import pandas as pd
import math

# --- 1. UI 介面配置 (8.5 級標竿美學) ---
st.set_page_config(page_title="Sharetea Express 決策引擎 v3", layout="wide")

# --- 2. CSS 樣式 (時尚深色除噪版) ---
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
    /* 表格樣式優化 */
    .stTable { background-color: transparent; }
    </style>
    """, unsafe_allow_html=True)

# --- 3. 戰略定義區 (直接展開：Clarity 先行) ---
st.title("🧋 Sharetea Express 決策引擎 v3")
st.markdown("<h5 style='color: #8B949E !important;'>2026 戰略核心：Reducing Noise. Increasing Clarity.</h5>", unsafe_allow_html=True)

st.markdown("---")
st.subheader("🎯 決策引擎名詞定義與權重邏輯")

col_def1, col_def2 = st.columns(2)
with col_def1:
    st.markdown("""
    #### 📊 核心指標說明
    * **SFS (Strategic Fit Score)**：衡量選址與 **Sharetea** 品牌契合度，反映 **9.5 級獲利** 潛力。
    * **市場潛力 (Market Potential)**：平衡基礎購買力 (50%) 與標竿客群加權 (50%)，避免數據過度擬合。
    * **精英級密度衰減**：採用 $Density^{0.7}$ 運算，精確權衡都會區的流量紅利與競爭壓力。
    """)
with col_def2:
    st.markdown("""
    #### ⚖️ 2026 戰略加權
    * **核心客群指數**：亞裔 (1.5x)、西裔 (1.0x)、26-35歲社交族群 (2.5x)。
    * **獲利槓桿**：座位規模直接影響獲利天花板 (旗艦店加權 1.5x)。
    * **數據來源**：美國官方 Census Data API (2022 ACS5) 與 Google Places 即時同業數據。
    """)

st.markdown("#### 🚀 2026 精英校準公式")
st.latex(r'''SFS = \frac{\text{Market Potential} \times \text{Visibility} \times \text{Zoning} \times \text{Seat Multiplier}}{\text{Density}^{0.7} + 1}''')
st.divider()

# --- 4. 訪問權限控制 (Security) ---
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

# --- 5. 側邊欄：數據輸入 (隱藏數字，減少雜訊) ---
st.sidebar.header("📍 選址座標與環境參數")
coord_input = st.sidebar.text_input("貼上座標 (緯度, 經度):", placeholder="33.8581, -118.0804")

# 地段權重 (法律排除邏輯)
zoning_map = {"商業/商場": 1.0, "混合分區": 0.7, "純住宅區 (法律禁止)": 0.0}
selected_zoning = st.sidebar.selectbox("🏗️ 地段分區:", options=list(zoning_map.keys()))
zoning_factor = zoning_map[selected_zoning]

visibility = st.sidebar.slider("👁️ 能見度/人流評分 (1-10):", 1, 10, 7)

# 座位規模加權
seat_map = {"5人以下 (Small)": (1, 1.0), "6-20人 (Standard)": (2, 1.2), "21-30人 (Flagship)": (3, 1.5)}
selected_seat = st.sidebar.radio("🪑 預計座位規模:", options=list(seat_map.keys()), index=1)
seat_grade, seat_multiplier = seat_map[selected_seat]

CENSUS_KEY = st.secrets["CENSUS_KEY"]
GOOGLE_KEY = st.secrets["GOOGLE_KEY"]

# --- 6. 執行診斷引擎 ---
if st.sidebar.button("啟動戰略診斷"):
    if zoning_factor == 0:
        st.error("🛑 **法律限制排除**：該地點為純住宅區，無法取得營業許可，已自動終止診斷。")
    elif not coord_input:
        st.warning("請先提供有效的 Google Maps 座標。")
    else:
        try:
            # 解析座標
            parts = coord_input.split(',')
            lat, lng = float(parts[0].strip()), float(parts[1].strip())
            
            with st.spinner("正在解析地理數據雜訊並計算獲利潛力..."):
                # (1) Google Places API (精準競業掃描)
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

                # 數據處理
                if len(c_res) < 2:
                    spending_power, asian_r, hispanic_r, age_r = 8500, 0.45, 0.35, 0.18
                    top_3_eth = [("亞裔", 0.45), ("西裔", 0.35), ("其他", 0.2)]
                else:
                    c = c_res[1]
                    total_pop = int(c[0]) if c[0] else 1
                    income = int(c[1]) if (c[1] and int(c[1]) > 0) else 88000
                    spending_power = income / 12
                    eth_map = {"亞裔": int(c[4])/total_pop, "西裔": int(c[5])/total_pop, "白人": int(c[2])/total_pop}
                    top_3_eth = sorted(eth_map.items(), key=lambda x: x[1], reverse=True)[:3]
                    asian_r, hispanic_r, age_r = eth_map["亞裔"], eth_map["西裔"], sum(int(c[i]) for i in range(6, 10)) / total_pop

            # --- SFS 精英校準運算 ---
            target_index = (asian_r * 1.5) + (hispanic_r * 1.0) + (age_r * 2.5)
            # 市場潛力 50/50 分布，平衡收入與族裔指標
            market_potential = (spending_power * 0.5) + (spending_power * target_index * 0.5)
            
            # 使用 0.7 次方處理密度：在都會區獲利紅利與競爭壓力間取得平衡
            density_factor = math.pow(density, 0.7) + 1
            final_sfs = (market_potential * visibility * zoning_factor * seat_multiplier) / density_factor

            # --- 分級與報告 (拉高門檻以防通膨) ---
            if final_sfs >= 15000: grade, color = "Grade A+ (旗艦標竿)", "gold"
            elif final_sfs >= 8500: grade, color = "Grade B (優質標準)", "orange"
            elif final_sfs >= 4500: grade, color = "Grade C (普及成長)", "blue"
            else: grade, color = "Grade F (戰略排除)", "red"

            # --- 報告輸出 (增加競業數顯示以強化 Clarity) ---
            st.subheader("📊 診斷中心即時報告")
            m1, m2, m3, m4 = st.columns(4)
            m1.metric("SFS 戰略分數", f"{final_sfs:.0f}")
            m2.metric("戰略分級", grade)
            m3.metric("月均消費動能", f"${spending_power:,.0f}")
            m4.metric("周邊競業數", f"{density} 家")
            
            st.divider()
            c_l, c_r = st.columns([2, 1])
            with c_l:
                if grade.startswith("Grade A+"):
                    st.success("🏆 **標竿達成**：該地點具備 9.5 級獲利潛力，建議全面執行都會旗艦店設計方案。")
                elif grade.startswith("Grade B"):
                    st.info(f"📍 **戰略建議**：目前距離旗艦標竿尚有空間，建議優化能見度分值或爭取座位數擴展。")
                else:
                    st.warning("⚠️ **開發警示**：獲利效率受限，建議評估周邊競爭密度是否過高。")
                
                st.write("\n📈 **2026 戰略分級參考表**")
                st.table(pd.DataFrame({
                    "等級": ["Grade A+ (旗艦標竿)", "Grade B (優質標準)", "Grade C (普及成長)", "Grade F (戰略排除)"],
                    "門檻 (SFS)": ["> 15,000", "8,500 - 15,000", "4,500 - 8,500", "< 4,500"],
                    "當前狀態": ["🎯" if grade.startswith(g) else "" for g in ["Grade A+", "Grade B", "Grade C", "Grade F"]]
                }))
            with c_r:
                st.write("👥 **區域客群特徵**")
                eth_df = pd.DataFrame(top_3_eth, columns=["Ethnicity", "Ratio"])
                st.bar_chart(eth_df.set_index("Ethnicity"))
                st.caption(f"社交主力 (26-35): {age_r:.1%} | 獲利權重: {target_index:.2f}")

        except Exception as e:
            st.error(f"❌ 診斷雜訊 (請核對座標與網路狀態): {e}")

st.caption("Produced by Marketing Designer. Standard v33 Core Engine. 2026 Strategy Roadmap.")
