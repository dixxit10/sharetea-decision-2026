import streamlit as st
import requests
import pandas as pd

# --- UI 介面配置 ---
st.set_page_config(page_title="Sharetea Express 決策引擎 v3", layout="wide")

# --- CSS ---
st.markdown("""
    <style>
    .stApp { background-color: #0E1117; color: #FFFFFF; }
    [data-testid="stSidebar"] { background-color: #161B22; border-right: 1px solid #30363D; }
    .metric-card {
        background: rgba(255, 255, 255, 0.05);
        padding: 20px;
        border-radius: 12px;
        backdrop-filter: blur(20px);
        border: 1px solid rgba(255, 255, 255, 0.1);
        margin-bottom: 10px;
    }
    h1, h2, h3, p { color: #FFFFFF !important; font-family: 'Inter', sans-serif; }
    .stMetric [data-testid="stMetricValue"] { color: #00D166 !important; }
    .stButton>button {
        background-color: #238636; color: white; border-radius: 8px;
        border: none; width: 100%; transition: 0.3s;
    }
    .stButton>button:hover { background-color: #2ea043; }
    .stAlert { background-color: rgba(255, 75, 75, 0.1); color: #FF4B4B; border: 1px solid #FF4B4B; }
    </style>
    """, unsafe_allow_html=True)

st.title("🧋 Sharetea Express 決策引擎 v3")

# --- 🎯 名詞定義 ---
st.markdown("---")
st.subheader("🎯 決策引擎名詞定義與權重邏輯")

col_def1, col_def2 = st.columns(2)
with col_def1:
    st.markdown("""
    #### 📊 核心指標說明
    * **SFS (Strategic Fit Score)**：衡量地點與 **Sharetea** 品牌契合度，反映 **9.5 級標竿** 潛力。
    * **購買力**：基於 Census 數據的月均收入，代表基礎消費動能。
    * **競爭密度**：2 英里內的同類店鋪數量，反映市場稀釋效應。
    * **能見度**：人員實際考察之店面曝光與人流綜合評分。
    * **預計座位數**：顧客活動範圍(排除廚房、櫃檯空間)。
    """)
with col_def2:
    st.markdown("""
    #### ⚖️ 2026 戰略加權邏輯
    為了最大化 **都會品牌店** 的競爭力，導入以下權重：
    * **Ethnic Weight (族裔權重)**：亞裔、西裔密集區加權 **1.5x**。
    * **Age Weight (年齡權重)**：26-35 歲社交活躍族群加權 **2.5x**。
    * **資料來源**：美國官方 Census Data API 與 Google 即時數據。
    """)


st.divider()

# --- 訪問權限 ---
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

# --- 側邊欄：數據輸入 ---
st.sidebar.header("📍 店面座標 (僅限美國區域)")
coord_input = st.sidebar.text_input("貼上緯度, 經度 (Google Maps):", placeholder="33.8581, -118.0804")

# --- 🏗️ 地段權重 ---

zoning_options = {
    "商業/商場": 1.0,
    "混合分區": 0.7,
    "純住宅區": 0.0
}

selected_label = st.sidebar.selectbox(
    "🏗️ 地段權重 (Zoning)", 
    options=list(zoning_options.keys())
)
zoning_factor = zoning_options[selected_label]
visibility = st.sidebar.slider("👁️ 能見度評分 (1-10):", 1, 10, 7)
seat_grade = st.sidebar.radio("🪑 預計座位數等級:", [1, 2, 3], index=1, help="1:<5, 2:6-20, 3:21-30")

CENSUS_KEY = st.secrets["CENSUS_KEY"]
GOOGLE_KEY = st.secrets["GOOGLE_KEY"]

if st.sidebar.button("啟動戰略診斷"):
    if not coord_input:
        st.warning("請先貼上座標。")
    else:
        try:
            parts = coord_input.split(',')
            lat, lng = float(parts[0].strip()), float(parts[1].strip())
            
            with st.spinner("正在解析地理數據雜訊..."):
                # --- 1. Google Places API (精準競業掃描) ---
                search_keywords = "bubble+tea|boba|milk+tea|tea+house"
                place_url = f"https://maps.googleapis.com/maps/api/place/nearbysearch/json?location={lat},{lng}&radius=3218&keyword={search_keywords}&key={GOOGLE_KEY}"
                places_res = requests.get(place_url).json()
                density = len(places_res.get('results', []))

                # --- 2. Census Geocoder (座標轉行政區) ---
                c_geo_url = f"https://geocoding.geo.census.gov/geocoder/geographies/coordinates?x={lng}&y={lat}&benchmark=Public_AR_Current&vintage=Current_Current&format=json"
                c_geo_res = requests.get(c_geo_url).json()
                tract_data = c_geo_res['result']['geographies']['Census Tracts'][0]
                
                # --- 3. Census Data API (人口消費力) ---
                fields = "B01003_001E,B19013_001E,B03002_003E,B03002_004E,B03002_006E,B03001_003E,B01001_011E,B01001_012E,B01001_035E,B01001_036E"
                census_url = f"https://api.census.gov/data/2022/acs/acs5?get={fields}&for=tract:{tract_data['TRACT']}&in=state:{tract_data['STATE']}%20county:{tract_data['COUNTY']}&key={CENSUS_KEY}"
                census_response = requests.get(census_url).json()

                # --- 數據處理與人口分析 ---
                if len(census_response) < 2:
                    spending_power, asian_r, hispanic_r, age_r = 8500, 0.45, 0.35, 0.18
                    top_3_eth = [("亞裔", 0.45), ("西裔", 0.35), ("白人", 0.15)]
                else:
                    c = census_response[1]
                    total_pop = int(c[0]) if c[0] else 1
                    income = int(c[1]) if (c[1] and int(c[1]) > 0) else 88000
                    spending_power = income / 12
                    eth_map = {"亞裔": int(c[4])/total_pop, "西裔": int(c[5])/total_pop, "白人": int(c[2])/total_pop, "非裔": int(c[3])/total_pop}
                    top_3_eth = sorted(eth_map.items(), key=lambda x: x[1], reverse=True)[:3]
                    asian_r, hispanic_r = eth_map["亞裔"], eth_map["西裔"]
                    age_r = sum(int(c[i]) for i in range(6, 10)) / total_pop

            # --- SFS 運算 ---
            ethnic_weight = 1 + (asian_r * 1.5) + (hispanic_r * 1.0)
            age_weight = 1 + (age_r * 2.5)
            final_sfs = (spending_power * visibility * zoning_factor * ethnic_weight * age_weight) / (density + 1)

            # --- 分級邏輯 ---
            if zoning_factor == 0 or final_sfs < 3000:
                grade, next_t, next_label, color = "Grade F (排除)", 3000, "Grade C", "red"
            elif final_sfs >= 13000 and seat_grade >= 2:
                grade, next_t, next_label, color = "Grade A+ (標竿)", None, None, "gold"
            elif final_sfs >= 8500:
                grade, next_t, next_label, color = "Grade B (標準)", 13000, "Grade A+", "orange"
            else:
                grade, next_t, next_label, color = "Grade C (成長)", 8500, "Grade B", "blue"

            # --- 輸出報告 ---
            st.subheader("📊 診斷中心即時報告")
            m1, m2, m3 = st.columns(3)
            m1.metric("SFS 戰略適配分", f"{final_sfs:.0f}")
            m2.metric("當前分級", grade)
            m3.metric("月消費力預估", f"${spending_power:,.0f}")
            st.divider()

            c_left, c_right = st.columns([2, 1])
            with c_left:
                if next_t:
                    gap = (next_t - final_sfs) / next_t
                    st.info(f"📍 **戰略分析**：目前距離 {next_label} 尚有 {gap:.1%} 空間，建議優化能見度分值。")
                else:
                    st.success("🏆 **標竿達成**：建議全面執行旗艦品牌設計方案。")
                
                st.write("\n📈 **2026 戰略量表對照**")
                scale_df = pd.DataFrame({
                    "等級": ["Grade A+ (旗艦標竿)", "Grade B (優質標準)", "Grade C (普及成長)", "Grade F (戰略排除)"],
                    "門檻 (SFS)": ["> 13,000", "8,500 - 13,000", "3,000 - 8,500", "< 3,000"],
                    "狀態": ["🎯" if grade.startswith(g) else "" for g in ["Grade A+", "Grade B", "Grade C", "Grade F"]]
                })
                st.table(scale_df)

            with c_right:
                st.write("👥 **區域人口組成**")
                eth_df = pd.DataFrame(top_3_eth, columns=["Ethnicity", "Ratio"])
                st.bar_chart(eth_df.set_index("Ethnicity"))
                st.caption(f"族裔加權: {ethnic_weight:.2f} | 26-35歲占比: {age_r:.1%}")

        except Exception as e:
            st.error(f"❌ 診斷中斷 (系統雜訊): {e}")

st.caption("Produced by Marketing Designer. Standard v33 Core Engine. 2026 Strategy Roadmap.")




