import streamlit as st
import requests
import pandas as pd
import math

# --- 1. UI 與 品牌美學配置 ---
st.set_page_config(page_title="Sharetea 2026 Strategy Suite", layout="wide")
st.markdown("""
    <style>
    .stApp { background-color: #0E1117; color: #E6EDF3; }
    [data-testid="stSidebar"] { background-color: #161B22; border-right: 1px solid #30363D; }
    h1, h2, h3, h4 { font-family: 'Inter', sans-serif; letter-spacing: -0.8px; }
    div[data-testid="metric-container"] {
        background-color: #1C2128; border: 1px solid #30363D; padding: 20px; border-radius: 12px;
    }
    .definition-box {
        background-color: #1C2128; border-left: 5px solid #238636;
        padding: 15px; margin-bottom: 15px; border-radius: 0 8px 8px 0;
    }
    .stButton>button {
        background: linear-gradient(135deg, #238636 0%, #2ea043 100%);
        color: white; border-radius: 8px; font-weight: 600; width: 100%; height: 3.5em;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 2. 戰略名詞定義 (展開設計) ---
st.title("🧋 Sharetea Express 決策引擎 v5.1")
st.markdown("<h5 style='color: #8B949E; margin-bottom: 25px;'>Reducing Noise. Increasing Clarity.</h5>", unsafe_allow_html=True)

st.subheader("📚 戰略體系名詞定義")
def_c1, def_c2, def_c3 = st.columns(3)
with def_c1:
    st.markdown("<div class='definition-box'><b>● SFS 戰略總分</b><br>綜合 27 組演算 (座位x區域x行為) 的得分，反映 9.5 級獲利潛力。</div>", unsafe_allow_html=True)
    st.markdown("<div class='definition-box' style='border-left-color: #D29922;'><b>● 熱區指標 (Hotspot)</b><br>具備高昂美學溢價、高坪效與社交影響力的旗艦級地段。</div>", unsafe_allow_html=True)
with def_c2:
    st.markdown("<div class='definition-box' style='border-left-color: #1F6FEB;'><b>● 社區標準 (Community)</b><br>平衡品質、便利與生活態度的日常型消費核心。</div>", unsafe_allow_html=True)
    st.markdown("<div class='definition-box' style='border-left-color: #8B949E;'><b>● 高效普及 (Efficiency)</b><br>強調垂直供應鏈效率與快速通路的擴張型選址。</div>", unsafe_allow_html=True)
with def_c3:
    st.markdown("<div class='definition-box' style='border-left-color: #FF4B4B;'><b>● 競業密度 ($Density^{0.7}$)</b><br>非線性衰減運算，將競爭壓力轉化為流量驗證紅利。</div>", unsafe_allow_html=True)
    st.markdown("<div class='definition-box' style='border-left-color: #00D166;'><b>● 月均基礎消費力</b><br>決定該區域獲利天花板。</div>", unsafe_allow_html=True)

st.divider()

# --- 3. 數據輸入 ---
if "auth" not in st.session_state: st.session_state["auth"] = False
if not st.session_state["auth"]:
    pwd = st.text_input("🔑 輸入 2026 戰略代碼:", type="password")
    if st.button("啟動系統"):
        if pwd == st.secrets["APP_PASSWORD"]: st.session_state["auth"] = True; st.rerun()
        else: st.error("驗證失敗。")
    st.stop()

st.sidebar.header("📍 選址數據輸入")
coord_input = st.sidebar.text_input("座標 (Lat, Lng):", placeholder="33.8581, -118.0804")
zoning_factor = {"商業/商場": 1.0, "混合分區": 0.7, "住宅區": 0.0}[st.sidebar.selectbox("🏗️ 地段分區:", ["商業/商場", "混合分區", "住宅區"])]
visibility = st.sidebar.slider("👁️ 能見度評分 (1-10):", 1, 10, 7)
seat_mult = {"高效型": 1.0, "標準型": 1.2, "旗艦型": 1.5}[st.sidebar.radio("🪑 空間規模:", ["高效型", "標準型", "旗艦型"])]

C_KEY, G_KEY = st.secrets["CENSUS_KEY"], st.secrets["GOOGLE_KEY"]

# --- 4. 核心數據抓取與診斷 ---
if st.sidebar.button("啟動動態診斷"):
    if not coord_input: st.warning("請先提供座標數據。")
    else:
        try:
            parts = coord_input.split(','); lat, lng = float(parts[0].strip()), float(parts[1].strip())
            with st.spinner("✨ 正在從 Google 與 US Census 抓取即時數據..."):
                # (1) Google API - 競業密度
                p_url = f"https://maps.googleapis.com/maps/api/place/nearbysearch/json?location={lat},{lng}&radius=3218&keyword=bubble+tea|boba&key={G_KEY}"
                density = len(requests.get(p_url).json().get('results', []))

                # (2) Census API - 獲取 Tract ID
                c_geo_url = f"https://geocoding.geo.census.gov/geocoder/geographies/coordinates?x={lng}&y={lat}&benchmark=Public_AR_Current&vintage=Current_Current&format=json"
                tract_res = requests.get(c_geo_url).json()['result']['geographies']['Census Tracts'][0]
                tract, county, state = tract_res['TRACT'], tract_res['COUNTY'], tract_res['STATE']

                # (3) Census ACS 5數據 - 族裔與年齡
                fields = "B01003_001E,B19013_001E,B03002_003E,B03001_004E,B01001_011E,B01001_012E,B01001_035E,B01001_036E,B02015_002E,B02015_005E,B02015_015E,B02015_009E,B02015_007E,B01001_010E,B01001_034E"
                census_url = f"https://api.census.gov/data/2022/acs/acs5?get={fields}&for=tract:{tract}&in=state:{state}%20county:{county}&key={C_KEY}"
                c = requests.get(census_url).json()[1]

                pop = int(c[0]) if c[0] else 1
                spending_power = (int(c[1]) if c[1] else 85000) / 12
                
                # 動態族裔組成
                eth_dict = {
                    "華裔/台灣裔": int(c[8])/pop, "墨西哥裔/西裔": int(c[3])/pop, "東南亞裔 (菲/越)": (int(c[9])+int(c[10]))/pop,
                    "東亞裔 (韓)": int(c[11])/pop, "南亞裔 (印)": int(c[12])/pop, "白人": int(c[2])/pop
                }
                # 動態年齡組成
                seg_v = (int(c[13]) + int(c[14])) / pop # 18-24 視覺
                seg_s = (int(c[4]) + int(c[5]) + int(c[6]) + int(c[7])) / pop # 25-34 社交
                seg_q = 1 - (seg_v + seg_s)
                age_dict = {"18-24 歲 (視覺)": seg_v, "25-34 歲 (社交)": seg_s, "35 歲以上 (品質)": seg_q}

            # SFS 演算
            target_index = (eth_dict["華裔/台灣裔"] * 2.0) + (eth_dict["墨西哥裔/西裔"] * 1.5) + (seg_s * 2.5)
            final_sfs = ((spending_power * 0.5 + spending_power * target_index * 0.5) * visibility * zoning_factor * seat_mult) / (math.pow(density, 0.7) + 1)

            # 戰略門檻與差距
            T_A, T_B, T_C = 15000, 8500, 4500
            if final_sfs >= T_A: level, color = "熱區指標 (A+)", "gold"
            elif final_sfs >= T_B: level, color = "社區標準 (B)", "orange"
            elif final_sfs >= T_C: level, color = "高效普及 (C)", "blue"
            else: level, color = "戰略排除", "red"

            gap_to_a, gap_to_b = (T_A - final_sfs) / T_A, (T_B - final_sfs) / T_B

            # --- 🚀 報告輸出 ---
            st.subheader("📊 Sharetea 2026 選址診斷摘要")
            m1, m2, m3, m4, m5 = st.columns(5)
            m1.metric("SFS 戰略總分", f"{final_sfs:.0f}")
            m2.metric("位置分級落點", level.split(' ')[0])
            m3.metric("月基礎消費力", f"${spending_power:,.0f}")
            m4.metric("周邊競業數", f"{density} 家")
            m5.metric("分級差距分析", f"{gap_to_a:.1%}" if level.startswith("社區") else f"{gap_to_b:.1%}")

            st.divider()
            l_col, r_col = st.columns(2)
            
            with l_col:
                # 核心 IF/THEN 執行清單
                curr_goal, curr_adv = "戰略診斷中", "穩定品質。"
                next_adv = "強力建議維持現況，轉型可透過小規模增加品牌力評估。"

                if level.startswith("高效普及 (C)"):
                    if seg_q > 0.60: curr_goal, curr_adv = "Maintain_Benchmark (維持標竿)", "優化『低糖/高品質原葉茶』配方。強化供應鏈效率。"
                    elif seg_s > 0.15 or gap_to_b < 0.15: 
                        curr_goal, curr_adv = "Pivot_to_B (轉型路徑)", "啟動『品牌力介入』。局部店裝升級，利用社交族群提升質感."
                        next_adv = "🚀 **建議由『高效普及 (C)』轉型為『社區標準 (B)』**。"
                
                elif level.startswith("社區標準 (B)"):
                    if (seg_s + seg_v) > 0.30: curr_goal, curr_adv = "Social_Premium (社交溢價)", "強化空間體驗。推出『原葉精品系列』增加視覺記憶點."
                    elif gap_to_a < 0.10: curr_goal, curr_adv = "Target_Flagship (對標旗艦)", "導入『Miffy 聯名』等旗艦視覺元素."
                    if spending_power < 6500 or density > 15: next_adv = "🚀 **建議由『社區標準 (B)』轉向『高效普及 (C)』**。"

                st.success(f"### 📋 當前執行清單：{curr_goal}\n\n{curr_adv}")
                st.info(f"### 🧬 轉型的下一層建議\n\n{next_adv}")

            with r_col:
                st.markdown("### 🎂 年齡組成細分 (由高至低排列)")
                st.table(pd.DataFrame(sorted(age_dict.items(), key=lambda x:x[1], reverse=True), columns=["年齡層", "比例"]).style.format({"比例": "{:.1%}"}))
                st.markdown("### 👥 族裔組成細分 (由高至低排列)")
                st.table(pd.DataFrame(sorted(eth_dict.items(), key=lambda x:x[1], reverse=True), columns=["族裔", "比例"]).style.format({"比例": "{:.1%}"}))

        except Exception as e: st.error(f"數據抓取異常，請核對座標。 (錯誤: {e})")

st.caption("Produced by Marketing Designer. v5.1.1 Build 2026.")
