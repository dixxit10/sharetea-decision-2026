import streamlit as st
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

# --- 2. 戰略名詞定義 ---
st.title("🧋 Sharetea Express 決策引擎 v7.1")
st.markdown("<h4 style='color: #8B949E; margin-bottom: 25px;'>Reducing Noise. Increasing Clarity.</h4>", unsafe_allow_html=True)

# --- 3. 側邊欄：API 與 數據輸入 ---
st.sidebar.header("🔑 權限驗證")
# 在前端顯示 Gemini API Key 輸入框
user_gemini_key = st.sidebar.text_input("輸入 Gemini API Key:", type="password", help="請輸入您的 Google AI Studio API Key")

st.sidebar.divider()
st.sidebar.header("📍 選址數據輸入")
coord_input = st.sidebar.text_input("座標 (Lat, Lng):", placeholder="34.1425, -118.0483")
loc_type = st.sidebar.selectbox("🏗️ 地段屬性:", ["Shopping Mall", "Food Court", "Community", "Plaza", "Main Street"])
seat_mult_map = {"高效型": 1.0, "標準型": 1.2, "旗艦型": 1.5}
seat_choice = st.sidebar.radio("🪑 預計規模:", list(seat_mult_map.keys()))
seat_mult = seat_mult_map[seat_choice]

# 後端隱藏的 Secrets (用於地圖與內部權重)
G_KEY = st.secrets.get("GOOGLE_KEY") 

# --- 4. 核心運算邏輯 ---
def get_ai_diagnostic(context, api_key):
    if not api_key:
        return "❌ 請在側邊欄輸入 Gemini API Key 以啟動 AI 診斷。"
    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-1.5-flash')
        prompt = f"""
        身為 Marketing Designer 戰略顧問，針對以下數據執行兩大判讀任務：
        數據背景：{context}
        
        1. 【地圖評分翻譯】：是什麼地理與環境特徵(例如建築轉角、人流動線、鄰里質感)導致該區在地圖快照中呈現目前的評分？
        2. 【轉型執行建議】：若要針對該點位進行轉型(例如從高效普及 C 轉為社區標準 B)，應如何具體執行品牌力介入計畫？
        
        請提供中文解讀並附帶專業商務英文。
        """
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"⚠️ AI 連接診斷異常: {str(e)}"

# --- 5. 戰略儀表板渲染 ---
st.subheader("📚 2026 戰略體系定義")
def_c1, def_c2, def_c3 = st.columns(3)
with def_c1:
    st.markdown("<div class='definition-box'><b>● SFS 戰略總分</b><br>核心指標，反映獲利潛力與地段適配度。</div>", unsafe_allow_html=True)
with def_c2:
    st.markdown("<div class='definition-box' style='border-left-color: #1F6FEB;'><b>● 社區標準 (B)</b><br>門檻 8500。日常獲利與穩定性指標。</div>", unsafe_allow_html=True)
with def_c3:
    st.markdown("<div class='definition-box' style='border-left-color: #FF4B4B;'><b>● 戰略排除 (Exclusion)</b><br>低於基準則封鎖數據顯示。</div>", unsafe_allow_html=True)

st.divider()

if st.sidebar.button("執行 2026 精英診斷"):
    if not coord_input:
        st.warning("請輸入座標。")
    else:
        try:
            # 解析座標
            parts = coord_input.split(',')
            lat, lng = float(parts[0].strip()), float(parts[1].strip())
            
            # 戰略模擬參數 (可根據需求從 Secrets 讀取權重)
            density, spending_power = 12, 8200
            eth_dict = {"華裔/台灣裔": 0.35, "墨西哥裔/西裔": 0.35, "其他": 0.30}
            seg_s = 0.3  # 25-34 歲社交客群比例
            
            threshold_map = {"Shopping Mall": 6500, "Food Court": 6000, "Main Street": 5500, "Plaza": 4500, "Community": 4000}
            weight_map = {"Shopping Mall": 0.85, "Food Court": 0.95, "Main Street": 1.0, "Plaza": 1.15, "Community": 1.25}
            T_EX, env_factor = threshold_map[loc_type], weight_map[loc_type]

            # SFS 演算
            target_index = (eth_dict["華裔/台灣裔"] * 2.0) + (eth_dict["墨西哥裔/西裔"] * 2.0) + (seg_s * 2.5)
            final_sfs = ((spending_power * target_index) * 7 * env_factor * seat_mult) / (math.pow(density, 0.7) + 1)

            if final_sfs < T_EX:
                st.error(f"🛑 戰略排除 (Exclusion)：SFS {final_sfs:.0f} 未達地段基準 ({T_EX})。")
            else:
                level = "熱區指標 (A+)" if final_sfs >= 15000 else "社區標準 (B)" if final_sfs >= 8500 else "高效普及 (C)"
                
                tab1, tab2, tab3 = st.tabs(["💎 診斷報告", "👥 客群結構", "🤖 AI 戰略解釋"])

                with tab1:
                    # 使用後端 G_KEY 渲染地圖
                    if G_KEY:
                        st.image(f"https://maps.googleapis.com/maps/api/staticmap?center={lat},{lng}&zoom=17&size=600x400&scale=2&key={G_KEY}", width=700)
                    else:
                        st.error("Google Maps API Key 未設定。")
                    
                    m1, m2, m3 = st.columns(3)
                    m1.metric("SFS 總分", f"{final_sfs:.0f}")
                    m2.metric("位置分級", level.split(' ')[0])
                    m3.metric("月消費力", f"${spending_power:,.0f}")

                with tab3:
                    with st.spinner("🤖 Gemini 正在解析地理因果..."):
                        ctx = f"SFS:{final_sfs:.0f}, 地段:{loc_type}, 級別:{level}"
                        # 使用前端傳入的 user_gemini_key
                        st.markdown(get_ai_diagnostic(ctx, user_gemini_key))

        except Exception as e:
            st.error(f"分析異常: {e}")

st.caption("Produced by Marketing Designer. v7.1.0 | Reducing Noise. Increasing Clarity.")
