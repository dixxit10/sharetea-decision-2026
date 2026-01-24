import streamlit as st
import requests
import pandas as pd
import math
import google.generativeai as genai

# --- 1. UI 與 品牌美學配置 ---
st.set_page_config(page_title="Sharetea 2026 Strategy Suite", layout="wide")
st.markdown("""
    <style>
    .stApp { background-color: #0E1117; color: #E6EDF3; }
    [data-testid="stSidebar"] { background-color: #161B22; border-right: 1px solid #30363D; }
    h1, h2, h3, h4 { font-family: 'Inter', sans-serif; letter-spacing: -0.8px; }
    div[data-testid="metric-container"] { background-color: #1C2128; border: 1px solid #30363D; padding: 20px; border-radius: 12px; }
    .definition-box { background-color: #1C2128; border-left: 5px solid #238636; padding: 15px; margin-bottom: 15px; border-radius: 0 8px 8px 0; }
    .stButton>button { background: linear-gradient(135deg, #238636 0%, #2ea043 100%); color: white; border-radius: 8px; font-weight: 600; width: 100%; height: 3.5em; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. 名詞定義 (展開設計：落實減少雜訊，增加清晰度) ---
st.title("🧋 Sharetea Express 決策引擎 v6.3")
st.markdown("<h5 style='color: #8B949E; margin-bottom: 25px;'>Reducing Noise. Increasing Clarity.</h5>", unsafe_allow_html=True)

st.subheader("📚 2026 戰略體系定義")
def_c1, def_c2, def_c3 = st.columns(3)
with def_c1:
    st.markdown("<div class='definition-box'><b>● SFS 戰略總分</b><br>綜合演算得分，反映獲利潛力與地段適配度。</div>", unsafe_allow_html=True)
    st.markdown("<div class='definition-box' style='border-left-color: #D29922;'><b>● 熱區指標 (A+)</b><br>門檻 15000。高美學溢價，對標精品品牌。</div>", unsafe_allow_html=True)
with def_c2:
    st.markdown("<div class='definition-box' style='border-left-color: #1F6FEB;'><b>● 社區標準 (B)</b><br>門檻 8500。平衡品質與便利的日常核心。</div>", unsafe_allow_html=True)
    st.markdown("<div class='definition-box' style='border-left-color: #8B949E;'><b>● 高效普及 (C)</b><br>動態門檻。強調效率與普及擴張計畫。</div>", unsafe_allow_html=True)
with def_c3:
    st.markdown("<div class='definition-box' style='border-left-color: #FF4B4B;'><b>● 戰略排除 (Exclusion)</b><br>依地段屬性動態判定，低於門檻則封鎖數據。</div>", unsafe_allow_html=True)
    st.markdown("<div class='definition-box' style='border-left-color: #00D166;'><b>● 月均基礎消費力</b><br>由收入決定該區產品單價與獲利天花板。</div>", unsafe_allow_html=True)

st.divider()

# --- 3. 數據輸入 (簡化：取消手動 Visibility，由地段屬性決定) ---
st.sidebar.header("📍 選址數據輸入")
coord_input = st.sidebar.text_input("座標 (Lat, Lng):", placeholder="34.1425, -118.0483")
loc_type = st.sidebar.selectbox("🏗️ 地段屬性:", ["Shopping Mall", "Food Court", "Community", "Plaza", "Main Street"])
seat_mult = {"高效型": 1.0, "標準型": 1.2, "旗艦型": 1.5}[st.sidebar.radio("🪑 空間規模:", ["高效型", "標準型", "旗艦型"])]

C_KEY, G_KEY, GEMINI_KEY = st.secrets["CENSUS_KEY"], st.secrets["GOOGLE_KEY"], st.secrets["GEMINI_KEY"]

# --- 4. 輔助函數：地圖與 AI 診斷 ---
def get_map_snapshot(lat, lng, key):
    return f"https://maps.googleapis.com/maps/api/staticmap?center={lat},{lng}&zoom=16&size=800x400&maptype=roadmap&markers=color:red%7C{lat},{lng}&key={key}"

def get_ai_interpretation(context, key):
    genai.configure(api_key=key)
    model = genai.GenerativeModel('gemini-1.5-flash')
    prompt = f"""身為 Marketing Designer 戰略顧問，請結合以下數據與地圖快照特徵進行『人工翻譯診斷』：
    數據：{context}
    請解讀：為什麼地理環境會導致這個 SFS 評分？這是一個普及點還是精品溢價點？並給出具體行銷行動指引與商務英文翻譯。"""
    return model.generate_content(prompt).text

# --- 5. 核心診斷流程 ---
if st.sidebar.button("啟動終極戰略診斷"):
    if not coord_input: st.warning("請輸入座標。")
    else:
        try:
            parts = coord_input.split(','); lat, lng = float(parts[0].strip()), float(parts[1].strip())
            
            with st.spinner("✨ 數據除噪與視覺合成中..."):
                # [此處保留 API 動態抓取邏輯]
                density, spending_power = 12, 8200
                eth_dict = {"華裔/台灣裔": 0.35, "墨西哥裔/西裔": 0.35, "東南亞裔": 0.1, "南亞裔": 0.05, "東亞裔": 0.05, "白人": 0.1}
                seg_v, seg_s = 0.20, 0.30
                seg_q = 1 - (seg_v + seg_s)
                
                # 動態門檻矩陣
                threshold_map = {
                    "Shopping Mall": {"ex": 6500, "weight": 0.85}, "Food Court": {"ex": 6000, "weight": 0.95},
                    "Main Street": {"ex": 5500, "weight": 1.00}, "Plaza": {"ex": 4500, "weight": 1.15},
                    "Community": {"ex": 4000, "weight": 1.25}
                }
                T_EX, env_factor = threshold_map[loc_type]["ex"], threshold_map[loc_type]["weight"]

                # SFS 演算：華裔=西裔(2.0), 社交主力(2.5)
                target_index = (eth_dict["華裔/台灣裔"] * 2.0) + (eth_dict["墨西哥裔/西裔"] * 2.0) + (seg_s * 2.5)
                final_sfs = ((spending_power * target_index) * 7 * env_factor * seat_mult) / (math.pow(density, 0.7) + 1)

            if final_sfs < T_EX:
                st.error(f"🛑 戰略排除：SFS {final_sfs:.0f} 未達地段擴張基準 ({T_EX})。數據已封鎖。")
                st.stop()

            # 分級與差距
            level = "熱區指標 (A+)" if final_sfs >= 15000 else "社區標準 (B)" if final_sfs >= 8500 else "高效普及 (C)"
            gap_info = f"{(15000-final_sfs)/15000:.1%}" if level.startswith("社區") else f"{(8500-final_sfs)/8500:.1%}"

            # --- 🚀 報告呈現 ---
            tab1, tab2, tab3 = st.tabs(["💎 診斷報告", "👥 客群結構", "🤖 AI 戰略解釋"])

            with tab1:
                # 靜態地圖展示
                st.image(get_map_snapshot(lat, lng, G_KEY), use_container_width=True)
                
                # 核心指標：SFS, 分級, 差距, 消費力, 競業數
                m1, m2, m3, m4, m5 = st.columns(5)
                m1.metric("SFS 戰略總分", f"{final_sfs:.0f}")
                m2.metric("位置分級", level.split(' ')[0])
                m3.metric("分級差距", gap_info)
                m4.metric("月基礎消費力", f"${spending_power:,.0f}")
                m5.metric("周邊競業數", f"{density} 家")

                # 戰略差距分析與指令
                st.divider()
                curr_goal, curr_adv = "戰略守成", "維持現狀。"
                next_adv = "強力建議維持現況，轉型可透過小規模增加品牌力依照營業額再重新診斷評估。"

                if level.startswith("高效普及"):
                    if seg_q > 0.60: curr_goal, curr_adv = "Maintain_Benchmark (維持標竿)", "優化『低糖/少冰』配方，建立高品質護城河。"
                    elif seg_s > 0.15: 
                        curr_goal, curr_adv = "Pivot_to_B (轉型路徑)", "啟動『品牌力介入』，提升店裝質感。"
                        next_adv = "🚀 **建議由『高效普及 (C)』轉型為『社區標準 (B)』**。"
                elif level.startswith("社區標準"):
                    if (seg_s + seg_v) > 0.30: curr_goal, curr_adv = "Social_Premium (社交溢價)", "強化空間體驗，推出精品系列。"
                    if loc_type in ["Shopping Mall", "Food Court"]: next_adv = "🚀 **建議由『社區標準 (B)』轉向『高效普及 (C)』以保獲利**。"

                st.success(f"### 📋 當前執行清單：{curr_goal}\n\n{curr_adv}")
                st.info(f"### 🧬 轉型的下一層建議\n\n{next_adv}")
                
                # 消費行為與預判
                behavior = "社交美學導向" if (seg_s + seg_v) > 0.28 else "品質穩定導向"
                st.markdown(f"**💡 消費行為與預判：** 該地段呈現 **{behavior}** 特徵。")

            with tab2:
                # 族裔與年齡表格 (由高至低排序)
                c_age, c_eth = st.columns(2)
                with c_age:
                    st.write("##### 🎂 年齡組成細分 (高→低)")
                    st.table(pd.DataFrame(sorted(age_dict.items(), key=lambda x:x[1], reverse=True), columns=["年齡層", "比例"]).style.format({"比例":"{:.1%}"}))
                with c_eth:
                    st.write("##### 👥 族群細分 (高→低)")
                    st.table(pd.DataFrame(sorted(eth_dict.items(), key=lambda x:x[1], reverse=True), columns=["族群", "比例"]).style.format({"比例":"{:.1%}"}))

            with tab3:
                # AI 人工翻譯與診斷
                if st.button("生成 AI 戰略解釋報告"):
                    context = f"SFS:{final_sfs:.0f}, 地段:{loc_type}, 社交主力:{seg_s:.1%}, 門檻差距:{gap_info}"
                    st.markdown(get_ai_interpretation(context, GEMINI_KEY))

        except Exception as e: st.error(f"分析異常: {e}")

st.caption("Produced by Marketing Designer. v6.3.1")
