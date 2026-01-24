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

# --- 2. 名詞定義 (Reducing Noise. Increasing Clarity) ---
st.title(" Sharetea Express 決策引擎 v7.1")
st.markdown("<h4 style='color: #8B949E; margin-bottom: 25px;'>Reducing Noise. Increasing Clarity.</h4>", unsafe_allow_html=True)

st.subheader("📚 2026 戰略體系名詞定義")
d1, d2, d3 = st.columns(3)
with d1:
    st.markdown("<div class='definition-box'><b>● SFS 戰略總分</b><br>綜合演算得分，反映獲利潛力與地段適配度。</div>", unsafe_allow_html=True)
    st.markdown("<div class='definition-box' style='border-left-color: #D29922;'><b>● 熱區指標 (A+)</b><br>門檻 15000。高溢價，精品化核心。</div>", unsafe_allow_html=True)
with d2:
    st.markdown("<div class='definition-box' style='border-left-color: #1F6FEB;'><b>● 社區標準 (B)</b><br>門檻 8500。日常獲利與穩定性指標。</div>", unsafe_allow_html=True)
    st.markdown("<div class='definition-box' style='border-left-color: #8B949E;'><b>● 高效普及 (C)</b><br>動態門檻。側重市佔擴張與極致效率。</div>", unsafe_allow_html=True)
with d3:
    st.markdown("<div class='definition-box' style='border-left-color: #FF4B4B;'><b>● 戰略排除 (Exclusion)</b><br>低於基準線則封鎖數據，確保精準開發。</div>", unsafe_allow_html=True)
    st.markdown("<div class='definition-box' style='border-left-color: #00D166;'><b>● 月均基礎消費力</b><br>區域獲利天花板，決定單價天花板。</div>", unsafe_allow_html=True)

st.divider()

# --- 3. 側邊欄與 Secrets 讀取 ---
st.sidebar.header("📍 選址數據輸入")
coord_input = st.sidebar.text_input("座標 (Lat, Lng):", placeholder="34.1425, -118.0483")
loc_type = st.sidebar.selectbox("🏗️ 地段屬性:", ["Shopping Mall", "Food Court", "Community", "Plaza", "Main Street"])
seat_mult_map = {"高效型": 1.0, "標準型": 1.2, "旗艦型": 1.5}
seat_choice = st.sidebar.radio("🪑 空間規模:", list(seat_mult_map.keys()))
seat_mult = seat_mult_map[seat_choice]

# API Key 雙軌機制：優先讀取後端 Secrets，若無則開放前端輸入
G_KEY = st.secrets.get("GOOGLE_KEY")
secret_gemini_key = st.secrets.get("GEMINI_KEY")

st.sidebar.divider()
if not secret_gemini_key:
    user_gemini_key = st.sidebar.text_input("🔑 輸入 Gemini API Key:", type="password")
else:
    user_gemini_key = secret_gemini_key

# --- 4. 輔助函數：AI 雙階段判讀 ---
def get_ai_diagnostic(context, key):
    if not key:
        return "⚠️ 未偵測到 API Key，請檢查 Secrets 設定或手動輸入。"
    try:
        # 去除可能存在的空格
        genai.configure(api_key=key.strip())
        model = genai.GenerativeModel('gemini-1.5-flash')
        prompt = f"""
        身為 Marketing Designer 戰略顧問，針對以下選址數據執行兩大任務：
        數據背景：{context}
        
        1. 【地圖評分翻譯】：是什麼地理與環境特徵(例如建築轉角、人流動線、鄰里質感)導致該區在地圖快照中呈現目前的評分結果？
        2. 【轉型執行建議】：若要針對該點位進行轉型(例如從高效普及 C 轉為社區標準 B)，應如何具體執行品牌力介入計畫？
        
        請提供中文解讀並附帶專業商務英文翻譯。
        """
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"⚠️ AI 診斷連接異常: {str(e)}"

# --- 5. 核心演算流程 ---
if st.sidebar.button("執行精英診斷"):
    if not coord_input:
        st.warning("請輸入座標。")
    else:
        try:
            # 解析座標
            parts = coord_input.split(',')
            lat, lng = float(parts[0].strip()), float(parts[1].strip())
            
            # 初始化數據
            density, spending_power = 12, 8200
            eth_dict = {
                "華裔/台灣裔": 0.35, "墨西哥裔/西裔": 0.30, 
                "東南亞裔": 0.10, "東亞裔": 0.08, "白人": 0.12, "南亞裔": 0.05
            }
            age_dict = {"18-24 歲 (視覺)": 0.2, "25-34 歲 (社交)": 0.35, "35 歲以上 (品質)": 0.45}
            seg_s = age_dict["25-34 歲 (社交)"]

            # 門檻判定與權重
            threshold_map = {"Shopping Mall": 6500, "Food Court": 6000, "Main Street": 5500, "Plaza": 4500, "Community": 4000}
            weight_map = {"Shopping Mall": 0.85, "Food Court": 0.95, "Main Street": 1.0, "Plaza": 1.15, "Community": 1.25}
            T_EX, env_factor = threshold_map[loc_type], weight_map[loc_type]

            # SFS 核心演算
            target_index = (eth_dict["華裔/台灣裔"] * 2.0) + (eth_dict["墨西哥裔/西裔"] * 2.0) + (seg_s * 2.5)
            final_sfs = ((spending_power * target_index) * 7 * env_factor * seat_mult) / (math.pow(density, 0.7) + 1)

            if final_sfs < T_EX:
                st.error(f"🛑 戰略排除：SFS {final_sfs:.0f} 未達地段基準 ({T_EX})。")
            else:
                # 分級與差距分析
                level = "熱區指標 (A+)" if final_sfs >= 15000 else "社區標準 (B)" if final_sfs >= 8500 else "高效普及 (C)"
                next_threshold = 15000 if "社區" in level else 8500 if "高效" in level else 15000
                gap_val = (next_threshold - final_sfs) / next_threshold

                tab1, tab2, tab3 = st.tabs(["💎 診斷報告", "👥 客群結構 (高→低)", "🤖 AI 戰略翻譯"])

                with tab1:
                    # 靜態地圖
                    if G_KEY:
                        st.image(f"https://maps.googleapis.com/maps/api/staticmap?center={lat},{lng}&zoom=17&size=600x400&scale=2&key={G_KEY}", width=700, caption="📍 地理環境視覺稽核")
                    else:
                        st.warning("Google Maps API Key 未配置，無法顯示地圖。")
                    
                    # 核心數據矩陣
                    m1, m2, m3, m4, m5 = st.columns(5)
                    m1.metric("SFS 總分", f"{final_sfs:.0f}")
                    m2.metric("位置分級", level.split(' ')[0])
                    m3.metric("分級差距", f"{gap_val:.1%}")
                    m4.metric("月消費力", f"${spending_power:,.0f}")
                    m5.metric("周邊競業", f"{density}")
                    
                    st.divider()
                    st.info(f"**🧬 戰略差距分析：** 目前距離 {level.split(' ')[0]} 級門檻有 {gap_val:.1%} 空間。")
                    behavior = "社交美學導向" if seg_s > 0.30 else "日常品質導向"
                    st.success(f"**💡 消費行為預判：** 該區客群呈現 **{behavior}** 特徵。")

                with tab2:
                    c1, c2 = st.columns(2)
                    with c1:
                        st.write("##### 🎂 年齡組成細分 (高→低)")
                        st.table(pd.DataFrame(sorted(age_dict.items(), key=lambda x:x[1], reverse=True), columns=["年齡層", "比例"]).style.format({"比例":"{:.1%}"}))
                    with c2:
                        st.write("##### 👥 族群細分 (高→低)")
                        st.table(pd.DataFrame(sorted(eth_dict.items(), key=lambda x:x[1], reverse=True), columns=["族群", "比例"]).style.format({"比例":"{:.1%}"}))

                with tab3:
                    with st.spinner("🤖 Gemini 正在解析地理特徵與轉型路徑..."):
                        ctx = f"SFS:{final_sfs:.0f}, 地段:{loc_type}, 分級:{level}, 差距:{gap_val:.1%}"
                        st.markdown("### 🤖 Gemini AI 戰略翻譯診斷")
                        # 呼叫診斷函數
                        st.info(get_ai_diagnostic(ctx, user_gemini_key))

        except Exception as e:
            st.error(f"分析異常: {e}")

st.caption("Produced by Marketing Designer. v7.1.0")

