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

# --- 2. 戰略名詞定義 (Reducing Noise. Increasing Clarity) ---
st.title("Sharetea Express 決策引擎 v7.1")
st.markdown("<h4 style='color: #8B949E; margin-bottom: 25px;'>Reducing Noise. Increasing Clarity.</h4>", unsafe_allow_html=True)

st.subheader("📚 2026 戰略體系定義")
def_c1, def_c2, def_c3 = st.columns(3)
with def_c1:
    st.markdown("<div class='definition-box'><b>● SFS 戰略總分</b><br>核心指標，反映獲利潛力與地段適配度。</div>", unsafe_allow_html=True)
with def_c2:
    st.markdown("<div class='definition-box' style='border-left-color: #1F6FEB;'><b>● 社區標準 (B)</b><br>門檻 8500。日常獲利與穩定性指標。</div>", unsafe_allow_html=True)
with def_c3:
    st.markdown("<div class='definition-box' style='border-left-color: #FF4B4B;'><b>● 戰略排除 (Exclusion)</b><br>低於基準則封鎖數據顯示。</div>", unsafe_allow_html=True)

st.divider()

# --- 3. 數據輸入與 Secrets 讀取 ---
st.sidebar.header("📍 選址數據輸入")
coord_input = st.sidebar.text_input("座標 (Lat, Lng):", placeholder="34.1425, -118.0483")
loc_type = st.sidebar.selectbox("🏗️ 地段屬性:", ["Shopping Mall", "Food Court", "Community", "Plaza", "Main Street"])
seat_mult_map = {"高效型": 1.0, "標準型": 1.2, "旗艦型": 1.5}
seat_choice = st.sidebar.radio("🪑 預計規模:", list(seat_mult_map.keys()))
seat_mult = seat_mult_map[seat_choice]

# 使用 .get 安全讀取 Secrets，避免 Missing Key 導致崩潰
G_KEY = st.secrets.get("GOOGLE_KEY")
GEMINI_KEY = st.secrets.get("GEMINI_KEY")
CENSUS_KEY = st.secrets.get("CENSUS_KEY") # 剛才噴錯的地方現在已受保護

# --- 4. 輔助函數：AI 診斷 ---
def get_ai_diagnostic(context, api_key):
    if not api_key:
        return "❌ 尚未配置 GEMINI_KEY，請檢查 Streamlit Secrets。"
    try:
        genai.configure(api_key=api_key.strip())
        # 更新模型名稱為 gemini-2.5-pro
        model = genai.GenerativeModel('gemini-2.5-pro')
        
        prompt = f"""
        身為 Marketing Designer 戰略顧問，針對以下選址數據執行任務：
        數據背景：{context}
        
        1. 【地圖評分翻譯】：地理特徵與環境質感判讀。
        2. 【轉型執行建議】：品牌力介入具體計畫。
        
        請提供中文解讀並附帶專業商務英文。
        """
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"⚠️ AI 診斷異常 (可能模型名稱暫不支援): {str(e)}"

# --- 5. 核心演算與報告呈現 ---
if st.sidebar.button("執行 2026 精英診斷"):
    if not coord_input:
        st.warning("請輸入座標。")
    else:
        try:
            parts = coord_input.split(',')
            lat, lng = float(parts[0].strip()), float(parts[1].strip())
            
            # 戰略模擬數據
            density, spending_power = 12, 8200
            eth_dict = {"華裔/台灣裔": 0.35, "墨西哥裔/西裔": 0.35, "東南亞裔": 0.10, "其他": 0.20}
            age_dict = {"18-24 歲": 0.2, "25-34 歲 (社交)": 0.35, "35 歲以上": 0.45}
            seg_s = age_dict["25-34 歲 (社交)"]

            threshold_map = {"Shopping Mall": 6500, "Food Court": 6000, "Main Street": 5500, "Plaza": 4500, "Community": 4000}
            weight_map = {"Shopping Mall": 0.85, "Food Court": 0.95, "Main Street": 1.0, "Plaza": 1.15, "Community": 1.25}
            T_EX, env_factor = threshold_map[loc_type], weight_map[loc_type]

            # SFS 演算
            target_index = (eth_dict["華裔/台灣裔"] * 2.0) + (eth_dict["墨西哥裔/西裔"] * 2.0) + (seg_s * 2.5)
            final_sfs = ((spending_power * target_index) * 7 * env_factor * seat_mult) / (math.pow(density, 0.7) + 1)

            if final_sfs < T_EX:
                st.error(f"🛑 戰略排除 (Exclusion)：SFS {final_sfs:.0f} 未達基準 ({T_EX})。")
            else:
                level = "熱區指標 (A+)" if final_sfs >= 15000 else "社區標準 (B)" if final_sfs >= 8500 else "高效普及 (C)"
                next_tier = 15000 if final_sfs < 15000 else 15000
                gap_val = (next_tier - final_sfs) / next_tier if final_sfs < next_tier else 0

                tab1, tab2, tab3 = st.tabs(["💎 診斷報告", "👥 客群結構", "🤖 AI 戰略解釋"])

                with tab1:
                    if G_KEY:
                        st.image(f"https://maps.googleapis.com/maps/api/staticmap?center={lat},{lng}&zoom=17&size=600x400&scale=2&key={G_KEY}", width=700)
                    else:
                        st.error("Google Maps API Key 未配置。")
                    
                    m1, m2, m3, m4 = st.columns(4)
                    m1.metric("SFS 總分", f"{final_sfs:.0f}")
                    m2.metric("位置分級", level.split(' ')[0])
                    m3.metric("分級差距", f"{gap_val:.1%}")
                    m4.metric("月消費力", f"${spending_power:,.0f}")

                with tab3:
                    with st.spinner("🤖 Gemini 2.5 Pro 正在分析..."):
                        ctx = f"SFS:{final_sfs:.0f}, 地段:{loc_type}, 級別:{level}"
                        st.markdown(get_ai_diagnostic(ctx, GEMINI_KEY))

        except Exception as e:
            st.error(f"分析異常: {e}")

st.caption("Produced by Marketing Designer. v7.1.0 | Reducing Noise. Increasing Clarity.")

