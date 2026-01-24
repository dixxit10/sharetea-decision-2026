import streamlit as st
import requests
import pandas as pd
import math

# --- 1. UI 與 品牌視覺配置 ---
st.set_page_config(page_title="Sharetea Express 決策引擎 v4.3", layout="wide")

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

# --- 2. 戰略名詞定義 (展開設計：無收合) ---
st.title("🧋 Sharetea Express 決策引擎 v4.3")
st.markdown("<h5 style='color: #8B949E !important;'>2026 核心戰略：Reducing Noise. Increasing Clarity.</h5>", unsafe_allow_html=True)

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
    * **精英級密度 ($Density^{0.7}$)**：將競爭壓力轉化為流量紅利的非線性衰減運算。
    * **月均基礎消費力**：普查區月均基礎家庭收入，決定獲利天花板。
    """)

st.divider()

# --- 3. 訪問權限管理 ---
if "auth" not in st.session_state: st.session_state["auth"] = False
if not st.session_state["auth"]:
    pwd = st.text_input("輸入 2026 戰略通訊碼:", type="password")
    if st.button("驗證進入"):
        if pwd == st.secrets["APP_PASSWORD"]: st.session_state["auth"] = True; st.rerun()
        else: st.error("❌ 驗證失敗。")
    st.stop()

# --- 4. 側邊欄：戰略數據輸入 ---
st.sidebar.header("📍 選址環境參數")
coord_input = st.sidebar.text_input("座標 (Lat, Lng):", placeholder="33.8581, -118.0804")

zoning_map = {"商業/商場": 1.0, "混合分區": 0.7, "純住宅區 (排除)": 0.0}
zoning_factor = zoning_map[st.sidebar.selectbox("🏗️ 地段分區:", options=list(zoning_map.keys()))]

visibility = st.sidebar.slider("👁️ 能見度評分 (1-10):", 1, 10, 7)

seat_map = {"5人以下 (高效型)": 1.0, "6-20人 (標準型)": 1.2, "21-30人 (旗艦型)": 1.5}
seat_multiplier = seat_map[st.sidebar.radio("🪑 空間規模:", options=list(seat_map.keys()), index=1)]

CENSUS_KEY = st.secrets["CENSUS_KEY"]
GOOGLE_KEY = st.secrets["GOOGLE_KEY"]

# --- 5. 核心診斷引擎 ---
if st.sidebar.button("啟動選址戰略診斷"):
    if zoning_factor == 0: st.error("🛑 法律排除：純住宅區禁止經營。")
    elif not coord_input: st.warning("請先提供座標數據。")
    else:
        try:
            parts = coord_input.split(','); lat, lng = float(parts[0].strip()), float(parts[1].strip())
            with st.spinner("正在解析 27 組演算數據與排序..."):
                # API 調用與數據解析
                p_url = f"https://maps.googleapis.com/maps/api/place/nearbysearch/json?location={lat},{lng}&radius=3218&keyword=bubble+tea&key={GOOGLE_KEY}"
                density = len(requests.get(p_url).json().get('results', []))
                
                c_geo_url = f"https://geocoding.geo.census.gov/geocoder/geographies/coordinates?x={lng}&y={lat}&benchmark=Public_AR_Current&vintage=Current_Current&format=json"
                tract_info = requests.get(c_geo_url).json()['result']['geographies']['Census Tracts'][0]
                
                fields = "B01003_001E,B19013_001E,B03002_003E,B03001_004E,B01001_011E,B01001_012E,B01001_035E,B01001_036E,B02015_002E,B02015_009E,B02015_015E,B02015_005E,B01001_010E,B01001_034E,B02015_007E"
                census_url = f"https://api.census.gov/data/2022/acs/acs5?get={fields}&for=tract:{tract_info['TRACT']}&in=state:{tract_info['STATE']}%20county:{tract_info['COUNTY']}&key={CENSUS_KEY}"
                c = requests.get(census_url).json()[1]

                pop = int(c[0]) if c[0] else 1; spending_power = (int(c[1]) if c[1] else 85000) / 12
                
                # 族群排序
                eth_dict = {"華裔/台灣裔": int(c[8])/pop, "墨西哥裔/西裔": int(c[3])/pop, "東南亞裔": (int(c[10])+int(c[11]))/pop, "東亞裔": int(c[9])/pop, "南亞裔": int(c[14])/pop, "白人": int(c[2])/pop}
                sorted_eth = sorted(eth_dict.items(), key=lambda x: x[1], reverse=True)

                # 年齡排序
                seg_v, seg_s = (int(c[12])+int(c[13]))/pop, (int(c[4])+int(c[5])+int(c[6])+int(c[7]))/pop
                seg_q = 1 - (seg_v + seg_s)
                age_dict = {"18-24 歲 (視覺驅動)": seg_v, "25-34 歲 (社交主力)": seg_s, "35 歲以上 (品質穩定)": seg_q}
                sorted_age = sorted(age_dict.items(), key=lambda x: x[1], reverse=True)

            # --- SFS 演算 ---
            target_index = (eth_dict["華裔/台灣裔"] * 2.0) + (eth_dict["墨西哥裔/西裔"] * 1.5) + (seg_s * 2.5)
            final_sfs = ((spending_power * 0.5 + spending_power * target_index * 0.5) * visibility * zoning_factor * seat_multiplier) / (math.pow(density, 0.7) + 1)

            # --- 6. 戰略分級與 15% 差距分析 ---
            T_HOT, T_STD, T_EFF = 15000, 8500, 4500
            if final_sfs >= T_HOT: level, color = "熱區指標 (Hotspot Index)", "gold"
            elif final_sfs >= T_STD: level, color = "社區標準 (Community Standard)", "orange"
            elif final_sfs >= T_EFF: level, color = "高效普及 (Efficiency Access)", "blue"
            else: level, color = "戰略排除 (Exclusion)", "red"

            gap_to_hot, gap_to_std = (T_HOT - final_sfs) / T_HOT, (T_STD - final_sfs) / T_STD
            gap_info = f"📍 當前落點距離指標門檻：{gap_to_hot:.1%}" if level.startswith("社區") else f"📍 當前落點距離指標門檻：{gap_to_std:.1%}"

            # --- 7. 執行清單與轉型建議 (戰略觸發器) ---
            curr_goal, curr_adv, next_goal, next_adv = "戰略診斷中", "穩定品質", "路徑評估中", "維持現狀"

            if level.startswith("高效普及"):
                if seg_q > 0.60:
                    curr_goal, curr_adv = "維持標竿 (Maintain Benchmark)", "優化『低糖/少冰』與『高品質原葉茶』配方。強化供應鏈效率，建立『高品質日常飲』護城河。"
                if seg_s > 0.15 or gap_to_std < 0.15:
                    next_goal, next_adv = "轉型路徑 (Pivot to B)", "啟動『品牌力介入』計畫。局部店裝升級以提升質感，利用 25-34 歲族群的社交影響力進行轉化。"
            
            elif level.startswith("社區標準"):
                if (seg_s + seg_v) > 0.30:
                    curr_goal, curr_adv = "社交溢價 (Social Premium)", "強化空間體驗與限定產品。針對社交主力推出『原葉精品系列』，增加店內視覺記憶點。"
                if gap_to_hot < 0.10:
                    next_goal, next_adv = "對標旗艦 (Target Flagship)", "導入『旗艦級視覺元素』(如：Miffy 聯名)。針對 18-24 歲族群進行話題性行銷，提升指標性。"

            # --- 🚀 最終報告輸出 ---
            st.subheader("📊 Sharetea 2026 選址戰略診斷結果")
            c1, c2, c3, c4 = st.columns(4); c1.metric("SFS 戰略總分", f"{final_sfs:.0f}"); c2.metric("戰略位置分級", level.split(' ')[0]); c3.metric("月消費動能", f"${spending_power:,.0f}"); c4.metric("周邊競業數", f"{density} 家")

            st.markdown(f"#### 🔍 戰略分級落點門檻：{level} (指標門檻: {T_HOT} / {T_STD} / {T_EFF})")
            st.divider()

            l_col, r_col = st.columns(2)
            with l_col:
                st.markdown(f"### 🎯 戰略差距分析\n{gap_info}")
                st.markdown(f"### 🛍️ 消費行為預判\n* **主導模式**：{'社交美學' if (seg_s + seg_v) > 0.25 else '品質穩定'}\n* **消費力評級**：{'標竿級' if spending_power > 7500 else '普及級'}")
                st.success(f"🏆 **執行清單：{curr_goal}**\n\n{curr_adv}")
                st.info(f"🚀 **轉型的下一層建議：{next_goal}**\n\n{next_adv}")

            with r_col:
                st.markdown("### 🎂 年齡組成 (依比例排序)")
                st.table(pd.DataFrame(sorted_age, columns=["年齡層", "比例"]).style.format({"比例": "{:.1%}"}))
                st.markdown("### 👥 族群細分 (依比例排序)")
                st.table(pd.DataFrame(sorted_eth, columns=["族群", "比例"]).style.format({"比例": "{:.1%}"}))

        except Exception as e: st.error(f"❌ 診斷雜訊: {e}")

st.caption("Produced by Marketing Designer. v4.3.1 Build 2026.")
