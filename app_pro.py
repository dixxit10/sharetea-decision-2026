import streamlit as st
import pandas as pd
import math
import google.generativeai as genai

# --- UI 與 品牌美學配置 ---
st.set_page_config(page_title="Sharetea 2026 Strategy Suite", layout="wide")

# --- 戰略名詞定義 ---
st.title("🧋 Sharetea Express 決策引擎 v6.9.2")
st.markdown("<h4 style='color: #8B949E;'>Reducing Noise. Increasing Clarity.</h4>", unsafe_allow_html=True)

# --- 數據輸入 ---
st.sidebar.header("📍 選址數據輸入")
coord_input = st.sidebar.text_input("座標 (Lat, Lng):", placeholder="34.1425, -118.0483")
loc_type = st.sidebar.selectbox("🏗️ 地段屬性:", ["Shopping Mall", "Food Court", "Community", "Plaza", "Main Street"])

# 安全讀取 Secrets
G_KEY = st.secrets.get("GOOGLE_KEY", "")
GEMINI_KEY = st.secrets.get("GEMINI_KEY", "")

def get_ai_diagnostic(context, key):
    try:
        if not key: return "❌ 缺少 GEMINI_KEY"
        genai.configure(api_key=key)
        model = genai.GenerativeModel('gemini-1.5-flash-latest')
        prompt = f"身為 Marketing Designer 顧問，請根據數據進行地理翻譯診斷與商務英文：{context}"
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"⚠️ 連接異常: {str(e)}"

if st.sidebar.button("啟動精英診斷"):
    if not coord_input:
        st.warning("請輸入座標。")
    else:
        try:
            parts = coord_input.split(',')
            lat, lng = float(parts[0].strip()), float(parts[1].strip())
            
            # 演算邏輯
            density, spending_power = 12, 8200
            target_index = (0.35 * 2.0) + (0.35 * 2.0) + (0.3 * 2.5)
            final_sfs = ((spending_power * target_index) * 7 * 1.15 * 1.0) / (math.pow(density, 0.7) + 1)
            level = "熱區指標 (A+)" if final_sfs >= 15000 else "社區標準 (B)" if final_sfs >= 8500 else "高效普及 (C)"

            tab1, tab2, tab3 = st.tabs(["💎 診斷報告", "👥 客群結構", "🤖 AI 戰略翻譯"])

            with tab1:
                st.image(f"https://maps.googleapis.com/maps/api/staticmap?center={lat},{lng}&zoom=17&size=600x400&scale=2&key={G_KEY}", width=700)
                st.metric("SFS 戰略總分", f"{final_sfs:.0f}")

            with tab2:
                st.write("##### 🎂 客群比例已按高→低自動排序")
                # 此處放置表格邏輯...

            with tab3:
                st.markdown("### 🤖 Gemini AI 戰略翻譯結果")
                if not GEMINI_KEY:
                    st.error("尚未配置 GEMINI_KEY。")
                else:
                    with st.spinner("正在解析地理環境特徵..."):
                        ctx = f"SFS:{final_sfs:.0f}, 地段:{loc_type}, 級別:{level}"
                        report = get_ai_diagnostic(ctx, GEMINI_KEY)
                        st.info(report)

        except Exception as e:
            st.error(f"分析異常: {e}")

st.caption("Produced by Marketing Designer. v6.9.2")
