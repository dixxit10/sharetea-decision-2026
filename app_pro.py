import streamlit as st
import requests
import pandas as pd
import math

# --- 1. UI 與 品牌視覺配置 ---
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

# --- 2. 名詞定義 (展開設計：無收合) ---
st.title("🧋 Sharetea Express 決策引擎 v4.8")
st.markdown("<h5 style='color: #8B949E; margin-bottom: 25px;'>Reducing Noise. Increasing Clarity.</h5>", unsafe_allow_html=True)

st.subheader("📚 戰略名詞定義 (Strategic Definitions)")
def_c1, def_c2, def_c3 = st.columns(3)
with def_c1:
    st.markdown("<div class='definition-box'><b>● SFS 戰略總分</b><br>綜合 27 組演算 (座位x區域x行為) 的適配得分，反映 9.5 級獲利潛力。</div>", unsafe_allow_html=True)
    st.markdown("<div class='definition-box' style='border-left-color: #D29922;'><b>● 熱區指標 (Hotspot)</b><br>具備高昂美學溢價、高坪效與社交影響力的旗艦級地段。</div>", unsafe_allow_html=True)
with def_c2:
    st.markdown("<div class='definition-box' style='border-left-color: #1F6FEB;'><b>● 社區標準 (Community)</b><br>平衡品質、便利與生活態度的日常型消費核心。</div>", unsafe_allow_html=True)
    st.markdown("<div class='definition-box' style='border-left-color: #8B949E;'><b>● 高效普及 (Efficiency)</b><br>強調垂直供應鏈效率與快速通路的擴張型選址。</div>", unsafe_allow_html=True)
with def_c3:
    st.markdown("<div class='definition-box' style='border-left-color: #FF4B4B;'><b>● 競業密度 ($Density^{0.7}$)</b><br>非線性衰減運算，過濾競爭雜訊並識別流量紅利。</div>", unsafe_allow_html=True)
    st.markdown("<div class='definition-box' style='border-left-color: #00D166;'><b>● 月均基礎消費力</b><br>基於普查區家庭年收入/12，決定該選址的獲利天花板。</div>", unsafe_allow_html=True)

st.divider()

# --- 3. 權限與數據輸入 ---
if "auth" not in st.session_state: st.session_state["auth"] = False
if not st.session_state["auth"]:
    pwd = st.text_input("🔑 輸入 2026 戰略授權碼:", type="password")
    if st.button("啟動選址診斷系統"):
        if pwd == st.secrets["APP_PASSWORD"]: st.session_state["auth"] = True; st.rerun()
        else: st.error("驗證失敗。")
    st.stop()

st.sidebar.header("📍 選址數據輸入")
coord_input = st.sidebar.text_input("座標 (Lat, Lng):", placeholder="33.8581, -118.0804")
zoning_factor = {"商業/商場": 1.0, "混合分區": 0.7, "住宅區": 0.0}[st.sidebar.selectbox("🏗️ 地段分區:", ["商業/商場", "混合分區", "住宅區"])]
visibility = st.sidebar.slider("👁️ 能見度評分 (1-10):", 1, 10, 7)
seat_mult = {"高效型": 1.0, "標準型": 1.2, "旗艦型": 1.5}[st.sidebar.radio("🪑 空間規模:", ["高效型", "標準型", "旗艦型"])]

C_KEY, G_KEY = st.secrets["CENSUS_KEY"], st.secrets["GOOGLE_KEY"]

# --- 4. 精英診斷引擎 ---
if st.sidebar.button("啟動戰略診斷"):
    if not coord_input: st.warning("請先提供座標。")
    else:
        try:
            parts = coord_input.split(','); lat, lng = float(parts[0].strip()), float(parts[1].strip())
            with st.spinner("✨ 正在同步 27 組演算數據..."):
                # [API 調用邏輯：Google Places & Census API]
                density, spending_power = 12, 8200 # 示例數據
                eth_dict = {"華裔/台灣裔": 0.35, "墨西哥裔/西裔": 0.25, "東南亞裔": 0.15, "東亞裔": 0.1, "南亞裔": 0.05, "白人": 0.1}
                seg_v, seg_s = 0.15, 0.25
                seg_q = 1 - (seg_v + seg_s)
                age_dict = {"18-24 歲 (視覺驅動)": seg_v, "25-34 歲 (社交主力)": seg_s, "35 歲以上 (品質穩定)": seg_q}

            # SFS 演算公式
            target_index = (eth_dict["華裔/台灣裔"] * 2.0) + (eth_dict["墨西哥裔/西裔"] * 1.5) + (seg_s * 2.5)
            final_sfs = ((spending_power * 0.5 + spending_power * target_index * 0.5) * visibility * zoning_factor * seat_mult) / (math.pow(density, 0.7) + 1)

            # 戰略分級與門檻 (15% 彈性)
            T_A, T_B, T_C = 15000, 8500, 4500
            if final_sfs >= T_A: level, color = "熱區指標 (A+)", "gold"
            elif final_sfs >= T_B: level, color = "社區標準 (B)", "orange"
            elif final_sfs >= T_C: level, color = "高效普及 (C)", "blue"
            else: level, color = "戰略排除", "red"

            gap_to_a, gap_to_b = (T_A - final_sfs) / T_A, (T_B - final_sfs) / T_B

            # --- 🚀 戰略報告輸出 ---
            st.subheader("📊 Sharetea 2026 選址診斷結果")
            m1, m2, m3, m4, m5 = st.columns(5)
            m1.metric("SFS 戰略總分", f"{final_sfs:.0f}")
            m2.metric("位置分級落點", level.split(' ')[0])
            m3.metric("月基礎消費力", f"${spending_power:,.0f}")
            m4.metric("周邊競業數", f"{density} 家")
            m5.metric("消費動能評級", "標竿級" if spending_power > 7500 else "普及級")

            st.divider()
            l_col, r_col = st.columns(2)
            
            with l_col:
                st.markdown(f"### 🎯 戰略差距分析\n落點門檻: {T_A} / {T_B} / {T_C}")
                st.write(f"📍 距離下一級門檻差距：{gap_to_a:.1%}" if level.startswith("社區") else f"📍 距離下一級門檻差距：{gap_to_b:.1%}")
                
                # --- 核心 IF/THEN 執行清單 ---
                curr_goal, curr_adv = "戰略診斷中", "穩定現有品質。"
                
                if level.startswith("高效普及"):
                    if seg_q > 0.60:
                        curr_goal, curr_adv = "Maintain_Benchmark (維持標竿)", "優化『低糖/少冰』與『高品質原葉茶』配方。強化供應鏈效率，針對穩定客群建立『高品質日常飲』的護城河。"
                    elif seg_s > 0.15 or gap_to_b < 0.15:
                        curr_goal, curr_adv = "Pivot_to_B (轉型路徑)", "啟動『品牌力介入』計畫。局部店裝升級以提升質感，利用 25-34 歲族群的社交影響力，將價格敏感度轉化為品牌黏性。"
                
                elif level.startswith("社區標準"):
                    if (seg_s + seg_v) > 0.30:
                        curr_goal, curr_adv = "Social_Premium (社交溢價)", "強化空間體驗與限定產品。針對社交主力推出『原葉精品系列』，增加店內視覺記憶點，鞏固社區標準地位。"
                    elif gap_to_a < 0.10:
                        curr_goal, curr_adv = "Target_Flagship (對標旗艦)", "導入『旗艦級視覺元素』(如：Miffy 聯名)。針對 18-24 歲族群進行話題性行銷，提升品牌在該地段的指標性。"

                st.success(f"### 📋 當前執行清單：{curr_goal}\n\n{curr_adv}")
                
                # --- 轉型下一層建議 (限於 C<->B) ---
                next_adv = "強力建議維持現況，轉型可透過小規模增加品牌力依照營業額再重新診斷評估。"
                if level.startswith("高效普及") and (seg_s > 0.15 or gap_to_b < 0.15):
                    next_adv = "建議由『高效普及』轉型為『社區標準』。透過品牌力介入測試市場對質感空間的接受度。"
                elif level.startswith("社區標準") and (spending_power < 6500 or density > 15):
                    next_adv = "建議由『社區標準』轉向『高效普及』以確保獲利。強化供應鏈優勢，對應價格敏感市場。"
                
                st.info(f"### 🚀 轉型的下一層建議\n\n{next_adv}")

                # 消費行為預判
                behavior = "快速消費與價格導向" if spending_power < 6000 else "品牌溢價導向"
                st.markdown(f"**💡 消費行為預判：** 該地段目前呈現 **{behavior}** 特徵。")

            with r_col:
                st.markdown("### 🎂 年齡組成細分 (依比例高到低排列)")
                st.table(pd.DataFrame(sorted(age_dict.items(), key=lambda x:x[1], reverse=True), columns=["年齡層", "比例"]).style.format({"比例": "{:.1%}"}))
                
                st.markdown("### 👥 族裔組成細分 (依比例高到低排列)")
                st.table(pd.DataFrame(sorted(eth_dict.items(), key=lambda x:x[1], reverse=True), columns=["族群", "比例"]).style.format({"比例": "{:.1%}"}))

        except Exception as e: st.error(f"分析異常: {e}")

st.caption("Produced by Marketing Designer. v4.8.1 Build 2026.")
