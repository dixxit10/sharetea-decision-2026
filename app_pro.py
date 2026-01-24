import streamlit as st
import pandas as pd
import math
import google.generativeai as genai

# --- 1. UI 與 品牌美學配置 ---
st.set_page_config(page_title="Sharetea 2026 Strategy Suite", layout="wide")
st.markdown("""
    <style>
    .stApp { background-color: #0E1117; color: #E6EDF3; }
    div[data-testid="metric-container"] { background-color: #1C2128; border: 1px solid #30363D; padding: 20px; border-radius: 12px; }
    .definition-box { background-color: #1C2128; border-left: 5px solid #238636; padding: 15px; margin-bottom: 15px; border-radius: 0 8px 8px 0; }
    .stButton>button { background: linear-gradient(135deg, #238636 0%, #2ea043 100%); color: white; border-radius: 8px; font-weight: 600; width: 100%; height: 3.5em; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. 戰略名詞定義 ---
st.title("🧋 Sharetea Express 決策引擎 v6.9.3")
st.markdown("<h4 style='color: #8B949E; margin-bottom: 25px;'>Reducing Noise. Increasing Clarity.</h4>", unsafe_allow_html=True)

st.subheader("📚 2026 戰略體系定義")
def_c1, def_c2, def_c3 = st.columns(3)
with def_c1:
    st.markdown("<div class='definition-box'><b>● SFS 戰略總分</b><br>核心指標，反映該地段的獲利與開發潛力。</div>", unsafe_allow_html=True)
    st.markdown("<div class='definition-box' style='border-left-color: #D29922;'><b>● 熱區指標 (A+)</b><br>門檻 15000。高溢價，精品化戰略核心。</div>", unsafe_allow_html=True)
with def_c2:
    st.markdown("<div class='definition-box' style='border-left-color: #1F6FEB;'><b>● 社區標準 (B)</b><br>門檻 8500。平衡品質與便利，日常獲利核心。</div>", unsafe_allow_html=True)
    st.markdown("<div class='definition-box' style='border-left-color: #8B949E;'><b>● 高效普及 (C)</b><br>動態門檻。側重效率與擴張計畫。</div>", unsafe_allow_html=True)
with def_c3:
    st.markdown("<div class='definition-box' style='border-left-color: #FF4B4B;'><b>● 戰略排除 (Exclusion)</b><br>門檻判定。低於基準則封鎖數據顯示。</div>", unsafe_allow_html=True)
    st.markdown("<div class='definition-box' style='border-left-color: #00D166;'><b>● 月基礎消費力</b><br>區域獲利天花板，決定產品客單價。</div>", unsafe_allow_html=True)

st.divider()

# --- 3. 數據輸入 ---
st.sidebar.header("📍 選址數據輸入")
coord_input = st.sidebar.text_input("座標 (Lat, Lng):", placeholder="34.1425, -118.0483")
loc_type = st.sidebar.selectbox("🏗️ 地段屬性:", ["Shopping Mall", "Food Court", "Community", "Plaza", "Main Street"])
seat_mult_map = {"高效型": 1.0, "標準型": 1.2, "旗艦型": 1.5}
seat_choice = st.sidebar.radio("🪑 預計規模:", list(seat_mult_map.keys()))
seat_mult = seat_mult_map[seat_choice]

G_KEY = st.secrets.get("GOOGLE_KEY")
GEMINI_KEY = st.secrets.get("GEMINI_KEY")

# --- 4. 強化版 AI 診斷：自動修復 404 錯誤 ---
def get_ai_diagnostic(context, key):
    try:
        genai.configure(api_key=key)
        # 動態列出可用模型以避免路徑錯誤
        available_models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        
        # 優先搜尋 1.5 Flash 
        target_model = None
        for m_name in ['models/gemini-1.5-flash', 'gemini-1.5-flash', 'models/gemini-pro']:
            if m_name in available_models:
                target_model = m_name
                break
        
        if not target_model: return "⚠️ 未找到可用 AI 模型。"

        model = genai.GenerativeModel(target_model)
        prompt = f"身為 Marketing Designer 顧問，請根據以下數據進行『地理環境翻譯診斷』與專業商務英文翻譯：{context}"
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"⚠️ AI 診斷異常：{str(e)}"

# --- 5. 核心診斷流程 ---
if st.sidebar.button("啟動精英診斷"):
    if not coord_input:
        st.warning("請輸入座標。")
    else:
        try:
            parts = coord_input.split(',')
            lat, lng = float(parts[0].strip()), float(parts[1].strip())
            
            # 初始化戰略數據
            density, spending_power = 12, 8200
            eth_dict = {"華裔/台灣裔": 0.35, "墨西哥裔/西裔": 0.35, "東南亞裔": 0.1, "南亞裔": 0.05, "東亞裔": 0.05, "白人": 0.1}
            age_dict = {"18-24 歲 (視覺驅動)": 0.2, "25-34 歲 (社交主力)": 0.3, "35 歲以上 (品質穩定)": 0.5}
            seg_s = 0.3

            # 地段門檻與環境因子
            threshold_map = {"Shopping Mall": 6500, "Food Court": 6000, "Main Street": 5500, "Plaza": 4500, "Community": 4000}
            weight_map = {"Shopping Mall": 0.85, "Food Court": 0.95, "Main Street": 1.0, "Plaza": 1.15, "Community": 1.25}
            T_EX, env_factor = threshold_map[loc_type], weight_map[loc_type]

            # SFS 核心演算 (華裔=西裔=2.0)
            target_index = (0.35 * 2.0) + (0.35 * 2.0) + (seg_s * 2.5)
            final_sfs = ((spending_power * target_index) * 7 * env_factor * seat_mult) / (math.pow(density, 0.7) + 1)

            if final_sfs < T_EX:
                st.error(f"🛑 戰略排除：SFS {final_sfs:.0f} 未達地段基準 ({T_EX})。")
            else:
                level = "熱區指標 (A+)" if final_sfs >= 15000 else "社區標準 (B)" if final_sfs >= 8500 else "高效普及 (C)"
                gap_val = (15000-final_sfs)/15000 if "社區" in level else (8500-final_sfs)/8500

                tab1, tab2, tab3 = st.tabs(["💎 診斷報告", "👥 客群畫像 (高→低排序)", "🤖 AI 戰略翻譯結果"])

                with tab1:
                    # 地圖快照 (High-DPI Zoom 17)
                    st.image(f"https://maps.googleapis.com/maps/api/staticmap?center={lat},{lng}&zoom=17&size=600x400&scale=2&key={G_KEY}", width=700, caption="📍 地理環境視覺稽核")
                    
                    m1, m2, m3, m4, m5 = st.columns(5)
                    m1.metric("SFS 總分", f"{final_sfs:.0f}")
                    m2.metric("位置分級", level.split(' ')[0])
                    m3.metric("分級差距", f"{gap_val:.1%}")
                    m4.metric("月消費力", f"${spending_power:,.0f}")
                    m5.metric("周邊競業", f"{density}")
                    
                    st.divider()
                    behavior = "社交美學導向" if seg_s > 0.28 else "品質穩定導向"
                    st.success(f"**💡 消費行為預判：** 該地段呈現 **{behavior}** 特徵。")
                    st.info(f"**🧬 戰略差距分析：** 距離上一級門檻仍有 {gap_val:.1%} 的升級空間。")

                with tab2:
                    c1, c2 = st.columns(2)
                    with c1:
                        st.write("##### 🎂 年齡組成細分 (由高至低)")
                        st.table(pd.DataFrame(sorted(age_dict.items(), key=lambda x:x[1], reverse=True), columns=["年齡層", "比例"]).style.format({"比例":"{:.1%}"}))
                    with c2:
                        st.write("##### 👥 族群細分 (由高至低)")
                        st.table(pd.DataFrame(sorted(eth_dict.items(), key=lambda x:x[1], reverse=True), columns=["族裔", "比例"]).style.format({"比例":"{:.1%}"}))

                with tab3:
                    with st.spinner("🤖 Gemini 正在自動轉譯地理特徵..."):
                        ctx = f"SFS:{final_sfs:.0f}, 地段:{loc_type}, 級別:{level}, 社交客群佔比:{seg_s:.1%}"
                        st.markdown("### 🤖 Gemini AI 戰略翻譯診斷")
                        st.info(get_ai_diagnostic(ctx, GEMINI_KEY))

        except Exception as e:
            st.error(f"分析異常: {e}")

st.caption("Produced by Marketing Designer. v6.9.3 Build 2026.")
