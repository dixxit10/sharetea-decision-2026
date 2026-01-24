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

# --- 2. 戰略名詞定義 (增加清晰度) ---
st.title("🧋 Sharetea Express 決策引擎 v6.9")
st.markdown("<h4 style='color: #8B949E; margin-bottom: 25px;'>Reducing Noise. Increasing Clarity.</h4>", unsafe_allow_html=True)

st.subheader("📚 2026 戰略體系定義")
def_c1, def_c2, def_c3 = st.columns(3)
with def_c1:
    st.markdown("<div class='definition-box'><b>● SFS 戰略總分</b><br>綜合演算得分，反映獲利潛力與地段適配度。</div>", unsafe_allow_html=True)
    st.markdown("<div class='definition-box' style='border-left-color: #D29922;'><b>● 熱區指標 (A+)</b><br>門檻 15000。精品化戰略核心。</div>", unsafe_allow_html=True)
with def_c2:
    st.markdown("<div class='definition-box' style='border-left-color: #1F6FEB;'><b>● 社區標準 (B)</b><br>門檻 8500。日常穩定獲利核心。</div>", unsafe_allow_html=True)
    st.markdown("<div class='definition-box' style='border-left-color: #8B949E;'><b>● 高效普及 (C)</b><br>動態門檻。擴張與市佔率戰略。</div>", unsafe_allow_html=True)
with def_c3:
    st.markdown("<div class='definition-box' style='border-left-color: #FF4B4B;'><b>● 戰略排除 (Exclusion)</b><br>低於基準線則封鎖數據，確保精準開發。</div>", unsafe_allow_html=True)
    st.markdown("<div class='definition-box' style='border-left-color: #00D166;'><b>● 月均基礎消費力</b><br>區域獲利天花板。</div>", unsafe_allow_html=True)

st.divider()

# --- 3. 數據輸入 (確保變數優先定義) ---
st.sidebar.header("📍 選址數據輸入")
# 這裡先定義變數，確保後面的 if 邏輯能抓到它
coord_input = st.sidebar.text_input("座標 (Lat, Lng):", placeholder="34.1425, -118.0483")
loc_type = st.sidebar.selectbox("🏗️ 地段屬性:", ["Shopping Mall", "Food Court", "Community", "Plaza", "Main Street"])
seat_mult_map = {"高效型": 1.0, "標準型": 1.2, "旗艦型": 1.5}
seat_choice = st.sidebar.radio("🪑 空間規模:", list(seat_mult_map.keys()))
seat_mult = seat_mult_map[seat_choice]

# API Keys
G_KEY = st.secrets.get("GOOGLE_KEY")
GEMINI_KEY = st.secrets.get("GEMINI_KEY")

# --- 4. 戰略演算與 AI 函數 ---
def get_ai_diagnostic(context, key):
    try:
        genai.configure(api_key=key)
        # 自動搜尋可用模型以避免 404
        models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        target_model = 'gemini-1.5-flash' if 'models/gemini-1.5-flash' in models else 'gemini-pro'
        
        model = genai.GenerativeModel(target_model)
        prompt = f"身為 Marketing Designer 戰略顧問，解讀以下選址數據並對照地理環境快照，提供『人工翻譯診斷』與英文翻譯：{context}"
        return model.generate_content(prompt).text
    except: return "AI 診斷連接中，請稍候..."

# --- 5. 核心診斷流程 ---
if st.sidebar.button("啟動精英診斷"):
    if not coord_input:
        st.warning("請在側邊欄輸入正確座標。")
    else:
        try:
            parts = coord_input.split(',')
            lat, lng = float(parts[0].strip()), float(parts[1].strip())
            
            # [模擬數據 - 實務請串接 API]
            density, spending_power = 12, 8200
            eth_dict = {"華裔/台灣裔": 0.35, "墨西哥裔/西裔": 0.35, "東南亞裔": 0.1, "南亞裔": 0.05, "東亞裔": 0.05, "白人": 0.1}
            age_dict = {"18-24 歲 (視覺)": 0.2, "25-34 歲 (社交)": 0.3, "35 歲以上 (品質)": 0.5}
            seg_s = 0.3

            # 門檻與權重
            threshold_map = {"Shopping Mall": 6500, "Food Court": 6000, "Main Street": 5500, "Plaza": 4500, "Community": 4000}
            weight_map = {"Shopping Mall": 0.85, "Food Court": 0.95, "Main Street": 1.0, "Plaza": 1.15, "Community": 1.25}
            
            T_EX = threshold_map[loc_type]
            env_factor = weight_map[loc_type]

            # SFS 演算
            # $$SFS = \frac{\left( \text{Spending Power} \times \text{Target Index} \right) \times 7 \times \text{Env Factor} \times \text{Seat Mult}}{\text{Density}^{0.7} + 1}$$
            target_index = (0.35 * 2.0) + (0.35 * 2.0) + (0.3 * 2.5)
            final_sfs = ((spending_power * target_index) * 7 * env_factor * seat_mult) / (math.pow(density, 0.7) + 1)

            if final_sfs < T_EX:
                st.error(f"🛑 戰略排除：SFS {final_sfs:.0f} 未達基準 ({T_EX})。")
            else:
                level = "熱區指標 (A+)" if final_sfs >= 15000 else "社區標準 (B)" if final_sfs >= 8500 else "高效普及 (C)"
                gap_val = (15000-final_sfs)/15000 if "社區" in level else (8500-final_sfs)/8500
                
                # --- 分頁呈現 ---
                tab1, tab2, tab3 = st.tabs(["💎 診斷報告", "👥 客群結構", "🤖 AI 戰略翻譯"])

                with tab1:
                    # 地圖快
