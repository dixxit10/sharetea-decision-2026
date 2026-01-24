import streamlit as st
import requests
import pandas as pd

# --- UI 介面配置 ---
st.set_page_config(page_title="Sharetea Express 決策引擎 v3", layout="wide")

# --- CSS ---
st.markdown("""
    <style>
    /* 全域底色與文字顏色 */
    .stApp {
        background-color: #0E1117; /* 深色底 */
        color: #FFFFFF;
    }
    
    /* 側邊欄 */
    [data-testid="stSidebar"] {
        background-color: #161B22; /* 稍淡的灰色輔助色 */
        border-right: 1px solid #30363D;
    }
    
    /* 數據卡片 */
    .metric-card {
        background: rgba(255, 255, 255, 0.05); /* 極低透明白，呈現深灰質感 */
        padding: 20px;
        border-radius: 12px;
        backdrop-filter: blur(20px);
        border: 1px solid rgba(255, 255, 255, 0.1);
        margin-bottom: 10px;
    }
    
    /* 文字 */
    h1, h2, h3, p {
        color: #FFFFFF !important;
        font-family: 'Inter', 'Helvetica Neue', sans-serif;
    }
    
    /* 重點提示色：綠色與紅色 */
    .stMetric [data-testid="stMetricValue"] {
        color: #00D166 !important; /* 時尚綠 */
    }
    
    /* 自定義按鈕樣式 */
    .stButton>button {
        background-color: #238636; /* 綠色按鈕 */
        color: white;
        border-radius: 8px;
        border: none;
        width: 100%;
    }
    
    /* 警告與錯誤訊息顏色 */
    .stAlert {
        background-color: rgba(255, 75, 75, 0.1);
        color: #FF4B4B;
        border: 1px solid #FF4B4B;
    }
    </style>
    """, unsafe_allow_html=True)

st.title("🧋 Sharetea Express 決策引擎 v3")
# --- 名詞定義 ---
st.markdown("---")
st.subheader("🎯 決策引擎名詞定義與權重邏輯")

col_def1, col_def2 = st.columns(2)

with col_def1:
    st.markdown("""
    #### 📊 核心指標說明
    * **SFS (Strategic Fit Score) 戰略適配分**：衡量地點與 **Sharetea** 品牌定位的契合度，最高 10 分，反映 **9.5 級標竿** 潛力。
    * **購買力**：區域家庭年收入中位數，代表當地基礎消費動能。
    * **競爭密度**：1.5 英里內的同類店鋪數量，反映市場稀釋效應。
    * **人員評分**：實際考察店面能見度、真實人流綜合評分。
    * **預計座位數**：計算顧客活動空間 (扣除廚房、櫃檯後)。
    """)

with col_def2:
    st.markdown("""
    #### ⚖️ 2026 戰略加權邏輯
    為了最大化 **品牌擴張** 的競爭力，系統導入以下關鍵權重：
    * **Ethnic Weight (族裔權重)**：亞裔、西裔密集區加權 **1.5x**，鎖定品牌核心客群。
    * **Age Weight (年齡權重)**：26-35 歲社交活躍族群加權 **2.5x**，支撐高毛利新品。
    """)

# 公式
st.markdown("#### 運算公式")
st.latex(r'''SFS = \frac{\text{Spending Power} \times \text{Visibility} \times \text{Ethnic Weight} \times \text{Age Weight}}{\text{Density} + 1}''')

st.divider()

# --- 內部訪問權限 ---
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
st.sidebar.header("📍 緯度、經度座標數據輸入(僅限美國區域)")
coord_input = st.sidebar.text_input("貼上店鋪的緯度, 經度座標( Google ):", placeholder="33.8581, -118.0804")

zoning_factor = st.sidebar.selectbox("🏗️ 地段權重 (Zoning)", 
                                    options=[(1.0, "商業/商場 (1.0)"), (0.7, "混合分區 (0.7)"), (0.0, "純住宅區 (0.0)")])[0]
visibility = st.sidebar.slider("👁️ 人員評分 (1-10):", 1, 10, 7)
seat_grade = st.sidebar.radio("🪑 預計座位數等級:", [1, 2, 3], index=1, help="1:<5, 2:6-20, 3:21-30")

CENSUS_KEY = st.secrets["CENSUS_KEY"]
GOOGLE_KEY = st.secrets["GOOGLE_KEY"]

if st.sidebar.button("啟動戰略診斷"):
    if not coord_input:
        st.warning("請先貼上座標。")
    else:
        try:
            # 第一階段：座標解析
            parts = coord_input.split(',')
            lat = float(parts[0].strip())
            lng = float(parts[1].strip())
            
            with st.spinner("正在解析地理數據雜訊..."):
                # 1. Google Places API
                place_url = f"https://maps.googleapis.com/maps/api/place/nearbysearch/json?location={lat},{lng}&radius=2414&keyword=bubble+tea&key={GOOGLE_KEY}"
                density = len(requests.get(place_url).json().get('results', []))

                # 2. Census API
                c_geo_url = f"https://geocoding.geo.census.gov/geocoder/geographies/coordinates?x={lng}&y={lat}&benchmark=Public_AR_Current&vintage=Current_Current&format=json"
                c_geo_res = requests.get(c_geo_url).json()
                tract = c_geo_res['result']['geographies']['Census Tracts'][0]
                
                fields = "B01003_001E,B19013_001E,B03002_003E,B03002_004E,B03002_006E,B03001_003E,B01001_011E,B01001_012E,B01001_035E,B01001_036E"
                census_url = f"https://api.census.gov/data/2022/acs/acs5?get={fields}&for=tract:{tract['TRACT']}&in=state:{tract['STATE']}%20county:{tract['COUNTY']}&key={CENSUS_KEY}"
                census_response = requests.get(census_url).json()

                # 第三階段：數據處理與人口分析
                if len(census_response) < 2:
                    spending_power, asian_r, hispanic_r, age_r = 8500, 0.45, 0.35, 0.18 
                    top_3_eth = [("亞裔 (Asian)", 0.45), ("西裔 (Hispanic)", 0.35), ("白人 (White)", 0.15)]
                else:
                    c = census_response[1]
                    total_pop = int(c[0]) if c[0] else 1
                    income = int(c[1]) if (c[1] and int(c[1]) > 0) else 88000 
                    spending_power = income / 12
                    eth_map = {"亞裔 (Asian)": int(c[4])/total_pop, "西裔 (Hispanic)": int(c[5])/total_pop, "白人 (White)": int(c[2])/total_pop, "非裔 (Black)": int(c[3])/total_pop}
                    top_3_eth = sorted(eth_map.items(), key=lambda x: x[1], reverse=True)[:3]
                    asian_r, hispanic_r = eth_map["亞裔 (Asian)"], eth_map["西裔 (Hispanic)"]
                    age_r = sum(int(c[i]) for i in range(6, 10)) / total_pop

            # --- 第四階段：SFS 運算 ---
            ethnic_weight = 1 + (asian_r * 1.5) + (hispanic_r * 1.0)
            age_weight = 1 + (age_r * 2.5)
            final_sfs = (spending_power * visibility * zoning_factor * ethnic_weight * age_weight) / (density + 1)

            # 第五階段：分級與門檻
            if zoning_factor == 0 or final_sfs < 3000:
                grade, next_t, next_label, color = "Grade F", 3000, "Grade C", "red"
            elif final_sfs >= 13000 and seat_grade >= 2:
                grade, next_t, next_label, color = "Grade A+", None, None, "gold"
            elif 8500 <= final_sfs < 13000:
                grade, next_t, next_label, color = "Grade B", 13000, "Grade A+", "orange"
            else:
                grade, next_t, next_label, color = "Grade C", 8500, "Grade B", "blue"

            # --- 輸出報告 ---
            st.subheader("📊 診斷中心即時報告")
            m1, m2, m3 = st.columns(3)
            m1.metric("SFS 戰略適配分", f"{final_sfs:.0f}")
            m2.metric("當前分級", grade)
            m3.metric("月消費力預估", f"${spending_power:,.0f}")

            st.divider()
            
            # 槓桿建議與視覺化
            c_left, c_right = st.columns([2, 1])
            with c_left:
                if next_t:
                    gap = (next_t - final_sfs) / next_t
                    if gap <= 0.15:
                        st.success(f"💡 **槓桿建議：具備躍升潛力**\n\n距離 {next_label} 僅差 {gap:.1%}。建議透過提升視角評分 (如聯名、改裝設計) 爭取預算。")
                    else:
                        st.info(f"📍 **戰略定位：明確標示為當前等級**\n\n目前差距 {gap:.1%}，建議專注維持獲利效率。")
                else:
                    st.success("🏆 **標竿守成：已達旗艦巔峰**\n\n建議全面執行 8.5 級標竿美學方案。")

                st.write("\n📈 **2026 戰略分級參考量表**")
                scale_df = pd.DataFrame({
                    "等級": ["Grade A+ (旗艦標竿)", "Grade B (優質標準)", "Grade C (普及成長)", "Grade F (戰略排除)"],
                    "門檻 (SFS)": ["> 13,000", "8,500 - 13,000", "3,000 - 8,500", "< 3,000"],
                    "目前狀態": ["🎯 達標" if grade == "Grade A+" else "", "🎯 達標" if grade == "Grade B" else "", "🎯 達標" if grade == "Grade C" else "", "🛑 警告" if grade == "Grade F" else ""]
                })
                st.table(scale_df)

            with c_right:
                st.write("👥 **族群組成前三名**")
                eth_df = pd.DataFrame(top_3_eth, columns=["Ethnicity", "Ratio"])
                st.bar_chart(eth_df.set_index("Ethnicity"))
                st.caption(f"亞裔+西裔加權: {ethnic_weight:.2f}")
                st.caption(f"社交主力 (26-35): {age_r:.1%}")

        except Exception as e:
            st.error(f"❌ 診斷中斷 (格式錯誤、每日流量限制，聯繫行銷部門): {e}")

# --- 腳註 ---

st.caption("Produced by Marketing Designer. Standard v33 Core Engine. 2026 Strategy Roadmap.")



