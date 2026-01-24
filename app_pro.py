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
    div[data-testid="metric-container"] { background-color: #1C2128; border: 1px solid #30363D; padding: 20px; border-radius: 12px; }
    .definition-box { background-color: #1C2128; border-left: 5px solid #238636; padding: 15px; margin-bottom: 15px; border-radius: 0 8px 8px 0; }
    .stButton>button { background: linear-gradient(135deg, #238636 0%, #2ea043 100%); color: white; border-radius: 8px; font-weight: 600; width: 100%; height: 3.5em; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. 戰略名詞定義 ---
st.title("🧋 Sharetea Express 決策引擎 v6.7")
st.markdown("<h4 style='color: #8B949E; margin-bottom: 25px;'>Reducing Noise. Increasing Clarity.</h4>", unsafe_allow_html=True)

st.subheader("📚 2026 戰略體系定義")
c1, c2, c3 = st.columns(3)
with c1:
    st.markdown("<div class='definition-box'><b>● SFS 戰略總分</b><br>核心指標，反映該地段的獲利與開發潛力。</div>", unsafe_allow_html=True)
    st.markdown("<div class='definition-box' style='border-left-color: #D29922;'><b>● 熱區指標 (A+)</b><br>門檻 15000。高美學溢價，對標精品品牌。</div>", unsafe_allow_html=True)
with c2:
    st.markdown("<div class='definition-box' style='border-left-color: #1F6FEB;'><b>● 社區標準 (B)</b><br>門檻 8500。平衡品質與便利，為日常消費核心。</div>", unsafe_allow_html=True)
    st.markdown("<div class='definition-box' style='border-left-color: #8B949E;'><b>● 高效普及 (C)</b><br>動態門檻。側重效率與垂直擴張計畫。</div>", unsafe_allow_html=True)
with c3:
    st.markdown("<div class='definition-box' style='border-left-color: #FF4B4B;'><b>● 戰略排除 (Exclusion)</b><br>門檻判定。低於基準則封鎖數據顯示。</div>", unsafe_allow_html=True)
    st.markdown("<div class='definition-box' style='border-left-color: #00D166;'><b>● 月基礎消費力</b><br>區域獲利天花板，決定產品客單價。</div>", unsafe_allow_html=True)

st.divider()

# --- 3. 數據輸入 ---
st.sidebar.header("📍 選址數據輸入")
coord_input = st.sidebar.text_input("座標 (Lat, Lng):", placeholder="34.1425, -118.0483")
loc_type = st.sidebar.selectbox("🏗️ 地段屬性:", ["Shopping Mall", "Food Court", "Community", "Plaza", "Main Street"])
seat_mult = {"高效型": 1.0, "標準型": 1.2, "旗艦型": 1.5}[st.sidebar.radio("🪑 預計規模:", ["高效型", "標準型", "旗艦型"])]

# API 金鑰讀取
G_KEY = st.secrets.get("GOOGLE_KEY")
GEMINI_KEY = st.secrets.get("GEMINI_KEY")

# --- 4. 輔助函數 ---
def get_map_snapshot(lat, lng, key):
    # 高解析度地圖輸出 (scale=2)
    return f"https://maps.googleapis.com/maps/api/staticmap?center={lat},{lng}&zoom=17&size=600x400&scale=2&maptype=roadmap&markers=color:red%7C{lat},{lng}&key={key}"

def get_ai_diagnostic(context, key):
    try:
        genai.configure(api_key=key)
        # 修正：移除 -latest 尾碼，使用標準穩定版名稱
        model = genai.GenerativeModel('gemini-1.5-flash') 
        prompt = f"""
        身為 Marketing Designer 戰略顧問，解讀以下數據並提供『地理環境翻譯診斷』與英文翻譯：
        {context}
        1. 為什麼地理環境(如轉角、停車場)導致此評分？
        2. 這是一個普及點還是精品點？給出一個行銷指令。
        3. 專業商務英文翻譯。
        """
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"AI 診斷生成失敗，請檢查 API 權限或連結情況。 (Error: {str(e)})"

# --- 5. 核心診斷流程 ---
if st.sidebar.button("啟動精英診斷"):
    if not coord_input:
        st.warning("請輸入座標。")
    else:
        try:
            # 解析座標
            parts = coord_input.split(',')
            lat, lng = float(parts[0].strip()), float(parts[1].strip())
            
            with st.spinner("✨ 數據合成與地圖渲染中..."):
                # [模擬數據 - 實務開發請確保串接 API]
                density, spending_power = 12, 8200
                eth_dict = {"華裔/台灣裔": 0.35, "墨西哥裔/西裔": 0.35, "東南亞裔": 0.1, "白人": 0.2}
                seg_v, seg_s = 0.20, 0.30
                seg_q = 1 - (seg_v + seg_s)
                age_dict = {"18-24 歲 (視覺驅動)": seg_v, "25-34 歲 (社交主力)": seg_s, "35 歲以上 (品質穩定)": seg_q}

                # 動態門檻
                threshold_map = {
                    "Shopping Mall": {"ex": 6500, "weight": 0.85}, "Food Court": {"ex": 6000, "weight": 0.95},
                    "Main Street": {"ex": 5500, "weight": 1.00}, "Plaza": {"ex": 4500, "weight": 1.15},
                    "Community": {"ex": 4000, "weight": 1.25}
                }
                T_EX = threshold_map[loc_type]["ex"]
                env_factor = threshold_map[loc_type]["weight"]
                
                # SFS 公式：華裔=西裔(2.0), 社交主力(2.5)
                target_index = (eth_dict["華裔/台灣裔"] * 2.0) + (eth_dict["墨西哥裔/西裔"] * 2.0) + (seg_s * 2.5)
                final_sfs = ((spending_power * target_index) * 7 * env_factor * seat_mult) / (math.pow(density, 0.7) + 1)

            # --- 戰略排除硬邏輯 ---
            if final_sfs < T_EX:
                st.error(f"🛑 戰略排除：SFS {final_sfs:.0f} 未達基準 ({T_EX})。數據已封鎖。")
            else:
                level = "熱區指標 (A+)" if final_sfs >= 15000 else "社區標準 (B)" if final_sfs >= 8500 else "高效普及 (C)"
                gap_info = f"{(15000-final_sfs)/15000:.1%}" if "社區" in level else f"{(8500-final_sfs)/8500:.1%}"

                # --- 分頁呈現 ---
                tab1, tab2, tab3 = st.tabs(["💎 診斷報告", "👥 客群畫像 (高→低)", "🤖 AI 戰略翻譯結果"])

                with tab1:
                    st.image(get_map_snapshot(lat, lng, G_KEY), width=700, caption="📍 地理環境視覺稽核 (High-DPI Zoom 17)")
                    m1, m2, m3, m4 = st.columns(4)
                    m1.metric("SFS 總分", f"{final_sfs:.0f}")
                    m2.metric("位置分級", level.split(' ')[0])
                    m3.metric("月消費力", f"${spending_power:,.0f}")
                    m4.metric("分級差距", gap_info)
                    
                    st.divider()
                    behavior = "社交美學導向" if (seg_s + seg_v) > 0.28 else "品質穩定導向"
                    st.success(f"**💡 消費行為預判：** 該地段呈現 **{behavior}** 特徵。")

                with tab2:
                    c_age, c_eth = st.columns(2)
                    with c_age:
                        st.write("##### 🎂 年齡組成 (由高至低)")
                        st.table(pd.DataFrame(sorted(age_dict.items(), key=lambda x:x[1], reverse=True), columns=["年齡層", "比例"]).style.format({"比例":"{:.1%}"}))
                    with c_eth:
                        st.write("##### 👥 族裔結構 (由高至低)")
                        st.table(pd.DataFrame(sorted(eth_dict.items(), key=lambda x:x[1], reverse=True), columns=["族裔", "比例"]).style.format({"比例":"{:.1%}"}))

                with tab3:
                    with st.spinner("🤖 Gemini 正在翻譯地理特徵與得分因果..."):
                        context_str = f"SFS:{final_sfs:.0f}, 地段:{loc_type}, 社交主力:{seg_s:.1%}, 分級:{level}"
                        st.markdown("### 🤖 Gemini AI 戰略敘事診斷")
                        # 顯示自動生成的 AI 診斷
                        st.info(get_ai_diagnostic(context_str, GEMINI_KEY))

        except Exception as e:
            st.error(f"分析異常: {e}")

st.caption("Marketing Designer Suite v6.7.1")
