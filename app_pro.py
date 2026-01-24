import streamlit as st
import requests
import pandas as pd
import math

# --- 1. UI 品牌視覺與美學配置 ---
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

# --- 2. 戰略名詞定義 (展開設計：無收合) ---
st.title("🧋 Sharetea Express 決策引擎 v5.7")
st.markdown("<h5 style='color: #8B949E; margin-bottom: 25px;'>Reducing Noise. Increasing Clarity.</h5>", unsafe_allow_html=True)

st.subheader("📚 2026 戰略體系名詞定義")
def_c1, def_c2, def_c3 = st.columns(3)
with def_c1:
    st.markdown("<div class='definition-box'><b>● SFS 戰略總分</b><br>綜合 27 組演算，過濾環境雜訊後的獲利得分指標。</div>", unsafe_allow_html=True)
    st.markdown("<div class='definition-box' style='border-left-color: #D29922;'><b>● 熱區指標 (Hotspot Index)</b><br>A+ (15000) 門檻。高美學溢價，對標精品品牌。</div>", unsafe_allow_html=True)
with def_c2:
    st.markdown("<div class='definition-box' style='border-left-color: #1F6FEB;'><b>● 社區標準 (Community Standard)</b><br>B (8500) 門檻。平衡品質與便利的日常核心。</div>", unsafe_allow_html=True)
    st.markdown("<div class='definition-box' style='border-left-color: #8B949E;'><b>● 高效普及 (Efficiency Access)</b><br>C (動態) 門檻。強調供應鏈效率與快速通路。</div>", unsafe_allow_html=True)
with def_c3:
    st.markdown("<div class='definition-box' style='border-left-color: #FF4B4B;'><b>● 戰略排除 (Exclusion)</b><br>依地段屬性動態判定。低於門檻則封鎖數據顯示。</div>", unsafe_allow_html=True)
    st.markdown("<div class='definition-box' style='border-left-color: #00D166;'><b>● 月均基礎消費力</b><br>普查區家庭年收入/12，決定該區獲利天花板。</div>", unsafe_allow_html=True)

st.divider()

# --- 3. 數據輸入 ---
if "auth" not in st.session_state: st.session_state["auth"] = False
if not st.session_state["auth"]:
    pwd = st.text_input("🔑 輸入 2026 戰略授權碼:", type="password")
    if st.button("啟動系統"):
        if pwd == st.secrets["APP_PASSWORD"]: st.session_state["auth"] = True; st.rerun()
    st.stop()

st.sidebar.header("📍 選址數據輸入")
coord_input = st.sidebar.text_input("座標 (Lat, Lng):", placeholder="34.1425, -118.0483")
loc_type = st.sidebar.selectbox("🏗️ 地段屬性:", ["Shopping Mall", "Food Court", "Community", "Plaza", "Main Street"])
visibility = st.sidebar.slider("👁️ 能見度評分 (1-10):", 1, 10, 7)
seat_mult = {"高效型": 1.0, "標準型": 1.2, "旗艦型": 1.5}[st.sidebar.radio("🪑 空間規模:", ["高效型", "標準型", "旗艦型"])]

C_KEY, G_KEY = st.secrets["CENSUS_KEY"], st.secrets["GOOGLE_KEY"]

# --- 4. 戰略權重與動態門檻 (v5.7 普及版) ---
threshold_map = {
    "Shopping Mall": {"ex": 6500, "weight": 0.85},
    "Food Court": {"ex": 6000, "weight": 0.95},
    "Main Street": {"ex": 5500, "weight": 1.00},
    "Plaza": {"ex": 4500, "weight": 1.15},    # 提升權重支持普及
    "Community": {"ex": 4000, "weight": 1.25}  # 最高權重作為孵化器
}
T_EX = threshold_map[loc_type]["ex"]
env_factor = threshold_map[loc_type]["weight"]

# --- 5. 核心診斷流程 ---
if st.sidebar.button("啟動精英診斷"):
    if not coord_input: st.warning("請先提供座標數據。")
    else:
        try:
            parts = coord_input.split(','); lat, lng = float(parts[0].strip()), float(parts[1].strip())
            with st.spinner("🔍 數據動態解析與除噪中..."):
                # Google API - 競業密度
                p_url = f"https://maps.googleapis.com/maps/api/place/nearbysearch/json?location={lat},{lng}&radius=3218&keyword=bubble+tea|boba&key={G_KEY}"
                density = len(requests.get(p_url).json().get('results', []))

                # Census API - 人口與收入數據
                c_geo_url = f"https://geocoding.geo.census.gov/geocoder/geographies/coordinates?x={lng}&y={lat}&benchmark=Public_AR_Current&vintage=Current_Current&format=json"
                tract_res = requests.get(c_geo_url).json()['result']['geographies']['Census Tracts'][0]
                
                fields = "B01003_001E,B19013_001E,B03002_003E,B03001_004E,B01001_011E,B01001_012E,B01001_035E,B01001_036E,B02015_002E,B02015_009E,B02015_015E,B01001_010E,B01001_034E"
                census_url = f"https://api.census.gov/data/2022/acs/acs5?get={fields}&for=tract:{tract_res['TRACT']}&in=state:{tract_res['STATE']}%20county:{tract_res['COUNTY']}&key={C_KEY}"
                c = requests.get(census_url).json()[1]

                pop = int(c[0]) if c[0] else 1; spending_power = (int(c[1]) if c[1] else 85000) / 12
                
                # 動態客群排序邏輯
                eth_dict = {"華裔/台灣裔": int(c[8])/pop, "墨西哥裔/西裔": int(c[3])/pop, "東南亞裔": (int(c[9])+int(c[10]))/pop, "白人": int(c[2])/pop}
                sorted_eth = sorted(eth_dict.items(), key=lambda x:x[1], reverse=True)

                seg_v, seg_s = (int(c[11])+int(c[12]))/pop, (int(c[4])+int(c[5])+int(c[6])+int(c[7]))/pop
                seg_q = 1 - (seg_v + seg_s)
                age_dict = {"18-24 歲 (視覺驅動)": seg_v, "25-34 歲 (社交主力)": seg_s, "35 歲以上 (品質穩定)": seg_q}
                sorted_age = sorted(age_dict.items(), key=lambda x:x[1], reverse=True)

            # SFS 終極演算公式
            # Target Index: 華裔(2.0) = 西裔(2.0)，社交主力(2.5)
            target_index = (eth_dict["華裔/台灣裔"] * 2.0) + (eth_dict["墨西哥裔/西裔"] * 2.0) + (seg_s * 2.5)
            final_sfs = ((spending_power * target_index) * visibility * env_factor * seat_mult) / (math.pow(density, 0.7) + 1)

            # --- 🚀 戰略排除硬過濾 ---
            if final_sfs < T_EX:
                st.error(f"🛑 戰略排除 (Exclusion)：此地段 SFS 為 {final_sfs:.0f}，低於該地段擴張基準 ({T_EX})。獲利潛力不足，已自動封鎖數據顯示。")
                st.stop()

            # 分級判定
            T_A, T_B = 15000, 8500
            level = "熱區指標 (A+)" if final_sfs >= T_A else "社區標準 (B)" if final_sfs >= T_B else "高效普及 (C)"
            gap_info = f"📍 距離下一級門檻差距：{(T_A-final_sfs)/T_A:.1%}" if level.startswith("社區") else f"📍 距離下一級門檻差距：{(T_B-final_sfs)/T_B:.1%}"

            # --- 6. 報告呈現 ---
            st.subheader(f"📊 Sharetea 2026 選址診斷結果：{level}")
            m1, m2, m3, m4, m5 = st.columns(5)
            m1.metric("SFS 戰略總分", f"{final_sfs:.0f}")
            m2.metric("消費動能評級", "標竿級" if spending_power > 7500 else "普及級")
            m3.metric("月基礎消費力", f"${spending_power:,.0f}")
            m4.metric("周邊競業數", f"{density} 家")
            m5.metric("排除基準線", f"{T_EX}")

            st.divider()
            l_col, r_col = st.columns(2)
            
            with l_col:
                st.markdown(f"### 🎯 戰略差距分析\n{gap_info} (門檻: {T_A}/{T_B}/{T_EX})")
                
                # --- 核心 IF/THEN 執行指令 ---
                curr_goal, curr_adv = "戰略診斷中", "穩定品質。"
                next_adv = "強力建議維持現況，轉型可透過小規模增加品牌力依照營業額再重新診斷評估。"

                if level.startswith("高效普及 (C)"):
                    if seg_q > 0.60:
                        curr_goal, curr_adv = "Maintain_Benchmark (維持標竿)", "優化『低糖/少冰』與『高品質原葉茶』配方。強化效率，針對穩定客群建立高品質護城河。"
                    elif seg_s > 0.15 or (T_B - final_sfs)/T_B < 0.15:
                        curr_goal, curr_adv = "Pivot_to_B (轉型路徑)", "啟動『品牌力介入』計畫。局部店裝升級提升質感，利用 25-34 歲社交族群影響力轉化品牌黏性。"
                    # 轉型下一層建議：C 建議 B
                    if seg_s > 0.15: next_adv = "🚀 **建議由『高效普及 (C)』轉型為『社區標準 (B)』**：利用核心社交族群溢價意願進行店裝與品牌力介入。"

                elif level.startswith("社區標準 (B)"):
                    if (seg_s + seg_v) > 0.30:
                        curr_goal, curr_adv = "Social_Premium (社交溢價)", "強化空間體驗與限定產品。推出『原葉精品系列』，增加視覺記憶點，鞏固地位。"
                    elif (T_A - final_sfs)/T_A < 0.10:
                        curr_goal, curr_adv = "Target_Flagship (對標旗艦)", "導入『Miffy 聯名』等旗艦級視覺元素。針對 18-24 視覺驅動族群進行行銷。"
                    # 轉型下一層建議：B 建議 C (針對高壓環境)
                    if loc_type in ["Shopping Mall", "Food Court"] or spending_power < 6500:
                        next_adv = "🚀 **建議由『社區標準 (B)』轉向『高效普及 (C)』**：環境競爭過熱。強化『垂直供應鏈』優勢，轉向快速消費模式。"

                st.success(f"### 📋 當前執行指令：{curr_goal}\n\n{curr_adv}")
                st.info(f"### 🧬 轉型的下一層路徑建議\n\n{next_adv}")

                # 消費行為與預判
                behavior = "社交美學導向" if (seg_s + seg_v) > 0.28 else "品質穩定導向"
                st.markdown(f"**💡 消費行為預判：** 該地段目前呈現 **{behavior}** 與 **快速消費** 特徵。")

            with r_col:
                st.markdown("### 🎂 年齡組成細分 (依比例排序)")
                st.table(pd.DataFrame(sorted_age, columns=["年齡層", "比例"]).style.format({"比例": "{:.1%}"}))
                st.markdown("### 👥 族裔組成細分 (依比例排序)")
                st.table(pd.DataFrame(sorted_eth, columns=["族裔", "比例"]).style.format({"比例": "{:.1%}"}))

        except Exception as e: st.error(f"分析中斷，請核對 API 或座標。 (錯誤: {e})")

st.caption("Produced by Marketing Designer. v5.7.1 Build 2026.")
