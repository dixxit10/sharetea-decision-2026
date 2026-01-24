import streamlit as st
import requests
import pandas as pd
import math
import google.generativeai as genai

# --- 1. UI 品牌視覺與美學配置 ---
st.set_page_config(page_title="Sharetea 2026 Strategy Suite", layout="wide")
st.markdown("""
    <style>
    .stApp { background-color: #0E1117; color: #E6EDF3; }
    div[data-testid="metric-container"] { background-color: #1C2128; border: 1px solid #30363D; padding: 20px; border-radius: 12px; }
    .definition-box { background-color: #1C2128; border-left: 5px solid #238636; padding: 15px; margin-bottom: 15px; border-radius: 0 8px 8px 0; }
    .stButton>button { background: linear-gradient(135deg, #238636 0%, #2ea043 100%); color: white; border-radius: 8px; font-weight: 600; width: 100%; height: 3.5em; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. 名詞定義 (展開設計) ---
st.title("🧋 Sharetea Express 決策引擎 v6.5")
st.markdown("<h4 style='color: #8B949E; margin-bottom: 25px;'>Reducing Noise. Increasing Clarity.</h4>", unsafe_allow_html=True)

st.subheader("📚 2026 戰略體系名詞定義")
c1, c2, c3 = st.columns(3)
with c1:
    st.markdown("<div class='definition-box'><b>● SFS 戰略總分</b><br>綜合演算得分，反映獲利潛力與地段適配度。</div>", unsafe_allow_html=True)
    st.markdown("<div class='definition-box' style='border-left-color: #D29922;'><b>● 位置分級</b><br>A+ (15000) / B (8500) / C (動態門檻)。</div>", unsafe_allow_html=True)
with c2:
    st.markdown("<div class='definition-box' style='border-left-color: #1F6FEB;'><b>● 分級差距</b><br>當前得分距離上一級門檻的落點百分比。</div>", unsafe_allow_html=True)
    st.markdown("<div class='definition-box' style='border-left-color: #8B949E;'><b>● 競業密度 ($Density^{0.7}$)</b><br>過濾環境雜訊後的真實競爭壓力。</div>", unsafe_allow_html=True)
with c3:
    st.markdown("<div class='definition-box' style='border-left-color: #FF4B4B;'><b>● 戰略排除 (Exclusion)</b><br>低於基準線則封鎖數據，確保開發精準度。</div>", unsafe_allow_html=True)
    st.markdown("<div class='definition-box' style='border-left-color: #00D166;'><b>● 月基礎消費力</b><br>區域獲利天花板。</div>", unsafe_allow_html=True)

st.divider()

# --- 3. 數據輸入 ---
st.sidebar.header("📍 選址數據輸入")
coord_input = st.sidebar.text_input("座標 (Lat, Lng):", placeholder="34.1425, -118.0483")
loc_type = st.sidebar.selectbox("🏗️ 地段屬性:", ["Shopping Mall", "Food Court", "Community", "Plaza", "Main Street"])
seat_mult = {"高效型": 1.0, "標準型": 1.2, "旗艦型": 1.5}[st.sidebar.radio("🪑 空間規模:", ["高效型", "標準型", "旗艦型"])]

C_KEY, G_KEY, GEMINI_KEY = st.secrets.get("CENSUS_KEY"), st.secrets.get("GOOGLE_KEY"), st.secrets.get("GEMINI_KEY")

# --- 4. 輔助函數 (優化解析度) ---
def get_map_snapshot(lat, lng, key):
    # 使用 scale=2 獲取 Retina 等級高解析度圖片，size 調整為符合排版的 600x400
    return f"https://maps.googleapis.com/maps/api/staticmap?center={lat},{lng}&zoom=17&size=600x400&scale=2&maptype=roadmap&markers=color:red%7C{lat},{lng}&key={key}"

def get_ai_diagnostic(context, key):
    genai.configure(api_key=key)
    model = genai.GenerativeModel('gemini-1.5-flash')
    prompt = f"""身為 Marketing Designer 戰略顧問，解讀以下數據並提供『地理環境翻譯診斷』：
    數據背景：{context}
    1. 為什麼地理環境導致此評分？
    2. 這是一個普及點還是精品點？給出一個行銷指令。
    3. 專業商務英文翻譯。"""
    return model.generate_content(prompt).text

# --- 5. 核心診斷流程 ---
if st.sidebar.button("啟動精英診斷"):
    if not coord_input: st.warning("請輸入座標。")
    else:
        try:
            parts = coord_input.split(',')
            lat, lng = float(parts[0].strip()), float(parts[1].strip())
            
            with st.spinner("✨ 正在校準高解析數據..."):
                # [模擬數據抓取邏輯]
                density, spending_power = 12, 8200
                eth_dict = {"華裔/台灣裔": 0.35, "墨西哥裔/西裔": 0.35, "東南亞裔": 0.1, "白人": 0.2}
                seg_v, seg_s = 0.20, 0.30
                seg_q = 1 - (seg_v + seg_s)
                age_dict = {"18-24 歲 (視覺驅動)": seg_v, "25-34 歲 (社交主力)": seg_s, "35 歲以上 (品質穩定)": seg_q}

                threshold_map = {
                    "Shopping Mall": {"ex": 6500, "weight": 0.85}, "Food Court": {"ex": 6000, "weight": 0.95},
                    "Main Street": {"ex": 5500, "weight": 1.00}, "Plaza": {"ex": 4500, "weight": 1.15},
                    "Community": {"ex": 4000, "weight": 1.25}
                }
                T_EX, env_factor = threshold_map[loc_type]["ex"], threshold_map[loc_type]["weight"]
                
                # SFS 公式 (Visibility 固定為 7)
                target_index = (eth_dict["華裔/台灣裔"] * 2.0) + (eth_dict["墨西哥裔/西裔"] * 2.0) + (seg_s * 2.5)
                final_sfs = ((spending_power * target_index) * 7 * env_factor * seat_mult) / (math.pow(density, 0.7) + 1)

            if final_sfs < T_EX:
                st.error(f"🛑 戰略排除：SFS {final_sfs:.0f} 未達基準 ({T_EX})。已封鎖數據。")
                st.stop()

            level = "熱區指標 (A+)" if final_sfs >= 15000 else "社區標準 (B)" if final_sfs >= 8500 else "高效普及 (C)"
            gap_info = f"{(15000-final_sfs)/15000:.1%}" if "社區" in level else f"{(8500-final_sfs)/8500:.1%}"

            # --- 🚀 報告呈現 ---
            tab1, tab2, tab3 = st.tabs(["💎 診斷報告", "👥 客群結構 (高→低排序)", "🤖 AI 戰略翻譯結果"])

            with tab1:
                # 調整圖片寬度，確保不模糊
                st.image(get_map_snapshot(lat, lng, G_KEY), width=700, caption="📍 地理特徵稽核快照 (Zoom 17)")
                
                m1, m2, m3, m4 = st.columns(4)
                m1.metric("SFS 總分", f"{final_sfs:.0f}")
                m2.metric("位置分級", level.split(' ')[0])
                m3.metric("月消費力", f"${spending_power:,.0f}")
                m4.metric("分級差距", gap_info)

                st.divider()
                # 執行清單
                curr_goal, curr_adv = "戰略診斷中", "穩定品質。"
                next_adv = "強力建議維持現況，轉型可透過小規模品牌力介入評估。"

                if "高效普及" in level:
                    if seg_q > 0.60: curr_goal, curr_adv = "Maintain_Benchmark", "優化『低糖』配方，建立高品質護城河。"
                    elif seg_s > 0.15: 
                        curr_goal, curr_adv = "Pivot_to_B", "啟動品牌力介入，提升質感。"
                        next_adv = "🚀 **建議由『高效普及 (C)』轉型為『社區標準 (B)』**。"
                elif "社區標準" in level:
                    if (seg_s + seg_v) > 0.30: curr_goal, curr_adv = "Social_Premium", "強化空間體驗。"
                    if loc_type in ["Shopping Mall", "Food Court"]: next_adv = "🚀 **建議由『社區標準 (B)』轉向『高效普及 (C)』**。"

                st.success(f"**📋 當前執行清單：{curr_goal}**\n\n{curr_adv}")
                st.info(f"**🧬 轉型建議：** {next_adv}")

            with tab2:
                # 族群與年齡表格 (高→低排序)
                c_age, c_eth = st.columns(2)
                with c_age:
                    st.write("##### 🎂 年齡組成")
                    st.table(pd.DataFrame(sorted(age_dict.items(), key=lambda x:x[1], reverse=True), columns=["年齡層", "佔比"]).style.format({"佔比":"{:.1%}"}))
                with c_eth:
                    st.write("##### 👥 族裔組成")
                    st.table(pd.DataFrame(sorted(eth_dict.items(), key=lambda x:x[1], reverse=True), columns=["族裔", "佔比"]).style.format({"佔比":"{:.1%}"}))

            with tab3:
                # 自動觸發 AI 診斷報告
                with st.spinner("🤖 Gemini 正在翻譯地理環境特徵..."):
                    context_str = f"SFS:{final_sfs:.0f}, 地段:{loc_type}, 社交主力:{seg_s:.1%}, 級別:{level}"
                    ai_diagnostic = get_ai_diagnostic(context_str, GEMINI_KEY)
                    st.markdown("### 🤖 Gemini AI 戰略翻譯報告")
                    st.info(ai_diagnostic)

        except Exception as e:
            st.error(f"分析異常: {e}")

st.caption("Marketing Designer Suite v6.5.1")
