import streamlit as st
import requests
import pandas as pd
import math

# --- 1. UI 介面美化配置 (Designer Edition) ---
st.set_page_config(page_title="Sharetea Express 2026 Strategy", layout="wide")

st.markdown("""
    <style>
    /* 全域背景與字體 */
    .stApp { background-color: #0E1117; color: #E6EDF3; }
    h1, h2, h3 { font-family: 'Inter', sans-serif; letter-spacing: -0.5px; }
    
    /* 側邊欄美化 */
    [data-testid="stSidebar"] { background-color: #161B22; border-right: 1px solid #30363D; }
    
    /* Metric 卡片美化 */
    div[data-testid="metric-container"] {
        background-color: #1C2128; border: 1px solid #30363D; padding: 15px; border-radius: 12px;
    }
    
    /* 按鈕與標籤美化 */
    .stButton>button {
        background: linear-gradient(135deg, #238636 0%, #2ea043 100%);
        color: white; border: none; border-radius: 8px; padding: 0.6em 2em;
        font-weight: 600; width: 100%; transition: all 0.3s ease;
    }
    .stButton>button:hover { transform: translateY(-2px); box-shadow: 0 4px 12px rgba(46, 160, 67, 0.4); }
    
    /* 標籤頁 (Tabs) 美化 */
    .stTabs [data-baseweb="tab-list"] { gap: 24px; }
    .stTabs [data-baseweb="tab"] { height: 50px; white-space: pre-wrap; font-weight: 600; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. 戰略標語與名詞定義 ---
st.title("🧋 Sharetea Express 決策引擎")
st.markdown("<h4 style='color: #8B949E; margin-bottom: 25px;'>2026 Strategy: Reducing Noise. Increasing Clarity.</h4>", unsafe_allow_html=True)

# 展開式定義 (UI 升級為 Column 顯示)
st.subheader("📚 戰略體系定義")
def_c1, def_c2, def_c3 = st.columns(3)
with def_c1:
    st.info("**熱區指標 (Hotspot Index)**\n\n具備高昂美學溢價、高坪效與社交影響力的旗艦級地段。")
with def_c2:
    st.warning("**社區標準 (Community Standard)**\n\n平衡品質、便利與生活態度的日常型消費核心。")
with def_c3:
    st.success("**高效普及 (Efficiency Access)**\n\n強調垂直供應鏈效率與快速通路的擴張型選址。")

st.divider()

# --- 3. 權限驗證 ---
if "auth" not in st.session_state: st.session_state["auth"] = False
if not st.session_state["auth"]:
    with st.container():
        pwd = st.text_input("🔑 請輸入 2026 戰略通訊碼:", type="password")
        if st.button("啟動系統"):
            if pwd == st.secrets["APP_PASSWORD"]: st.session_state["auth"] = True; st.rerun()
            else: st.error("驗證失敗，請聯繫 Marketing Designer。")
    st.stop()

# --- 4. 數據輸入 (側邊欄) ---
st.sidebar.header("📍 選址參數輸入")
coord_input = st.sidebar.text_input("座標 (Lat, Lng):", placeholder="33.8581, -118.0804")
zoning_factor = {"商業/商場": 1.0, "混合分區": 0.7, "住宅區": 0.0}[st.sidebar.selectbox("🏗️ 地段分區:", ["商業/商場", "混合分區", "住宅區"])]
visibility = st.sidebar.slider("👁️ 能見度評分 (Visibility):", 1, 10, 7)
seat_mult = {"高效型": 1.0, "標準型": 1.2, "旗艦型": 1.5}[st.sidebar.radio("🪑 空間規模:", ["高效型", "標準型", "旗艦型"])]

CENSUS_KEY, GOOGLE_KEY = st.secrets["CENSUS_KEY"], st.secrets["GOOGLE_KEY"]

# --- 5. 核心診斷流程 ---
if st.sidebar.button("執行戰略診斷"):
    if zoning_factor == 0: st.error("🛑 法律排除：住宅區禁止經營。")
    elif not coord_input: st.warning("請提供座標數據。")
    else:
        try:
            parts = coord_input.split(','); lat, lng = float(parts[0].strip()), float(parts[1].strip())
            with st.spinner("✨ 正在除噪並計算 27 組演算數據..."):
                # [API 數據獲取邏輯保持不變，略過以簡化]
                density = 12 # 範例數據
                spending_power = 8200 # 範例數據
                pop = 5000; chinese_r, mexican_r = 0.35, 0.25
                seg_v, seg_s, seg_q = 0.15, 0.25, 0.60
                eth_dict = {"華裔/台灣裔": chinese_r, "墨西哥裔/西裔": mexican_r, "東南亞裔": 0.15, "東亞裔": 0.1, "南亞裔": 0.05, "白人": 0.1}
                age_dict = {"18-24 歲 (視覺)": seg_v, "25-34 歲 (社交)": seg_s, "35 歲以上 (品質)": seg_q}

            # 演算核心
            target_index = (chinese_r * 2.0) + (mexican_r * 1.5) + (seg_s * 2.5)
            final_sfs = ((spending_power * 0.5 + spending_power * target_index * 0.5) * visibility * zoning_factor * seat_mult) / (math.pow(density, 0.7) + 1)

            # 分級門檻 (15% 彈性)
            T_HOT, T_STD, T_EFF = 15000, 8500, 4500
            if final_sfs >= T_HOT: level, color = "熱區指標", "gold"
            elif final_sfs >= T_STD: level, color = "社區標準", "orange"
            elif final_sfs >= T_EFF: level, color = "高效普及", "blue"
            else: level, color = "戰略排除", "red"

            gap_to_hot, gap_to_std = (T_HOT - final_sfs) / T_HOT, (T_STD - final_sfs) / T_STD

            # --- 🚀 戰略排版 (Tabs 分層) ---
            tab1, tab2, tab3 = st.tabs(["📊 診斷摘要", "👥 客群畫像", "📝 執行指令"])

            with tab1:
                st.markdown(f"### 戰略落點：{level}")
                m1, m2, m3, m4 = st.columns(4)
                m1.metric("SFS 戰略總分", f"{final_sfs:.0f}")
                m2.metric("消費動能評級", "標竿級" if spending_power > 7500 else "普及級")
                m3.metric("月消費實力", f"${spending_power:,.0f}")
                m4.metric("競業密度", f"{density} 家")
                
                st.markdown("#### 📐 分級指標落點門檻")
                st.progress(min(final_sfs / T_HOT, 1.0), text=f"當前進度 (目標 {T_HOT})")
                st.caption(f"📍 熱區指標: {T_HOT} | 社區標準: {T_STD} | 高效普及: {T_EFF}")

            with tab2:
                col_age, col_eth = st.columns(2)
                with col_age:
                    st.markdown("##### 🎂 年齡組成排序")
                    st.table(pd.DataFrame(sorted(age_dict.items(), key=lambda x:x[1], reverse=True), columns=["年齡層", "比例"]).style.format({"比例": "{:.1%}"}))
                with col_eth:
                    st.markdown("##### 👥 族群細分排序")
                    st.table(pd.DataFrame(sorted(eth_dict.items(), key=lambda x:x[1], reverse=True), columns=["族群", "比例"]).style.format({"比例": "{:.1%}"}))

            with tab3:
                # 執行邏輯觸發
                curr_goal, curr_adv, next_adv = "戰略守成", "穩定日常品質。", "強力建議維持現況，轉型可透過小規模增加品牌力依照營業額再重新診斷評估。"
                if level == "高效普及":
                    if seg_q > 0.60: curr_goal, curr_adv = "維持標竿", "優化『低糖/高品質原葉茶』。"
                    if seg_s > 0.15 or gap_to_std < 0.15: next_adv = "啟動『品牌力介入』與局部店裝升級。"
                elif level == "社區標準":
                    if (seg_s + seg_v) > 0.30: curr_goal, curr_adv = "社交溢價", "強化空間體驗與視覺記憶點。"
                    if gap_to_hot < 0.10: next_adv = "導入『旗艦級視覺 (Miffy 聯名)』。"

                st.success(f"**當前執行清單：{curr_goal}**\n\n{curr_adv}")
                st.info(f"**轉型的下一層建議：**\n\n{next_adv}")

        except Exception as e: st.error(f"分析異常: {e}")

st.caption("Marketing Designer Executive Suite v4.5.")
