import streamlit as st
import pandas as pd
import math
import google.generativeai as genai

# --- 1. UI 品牌視覺與美學配置 ---
st.set_page_config(page_title="Sharetea 2026 Strategy Suite", layout="wide")
st.markdown("""
    <style>
    .stApp { background-color: #0E1117; color: #E6EDF3; }
    div[data-testid="metric-container"] { 
        background-color: #1C2128; border: 1px solid #30363D; padding: 20px; border-radius: 12px; 
    }
    .definition-box { background-color: #1C2128; border-left: 5px solid #238636; padding: 15px; margin-bottom: 15px; border-radius: 0 8px 8px 0; }
    .stButton>button { 
        background: linear-gradient(135deg, #238636 0%, #2ea043 100%); color: white; 
        border-radius: 8px; font-weight: 600; width: 100%; height: 3.5em; 
    }
    .strategy-card { background-color: #1C2128; padding: 20px; border-radius: 12px; border: 1px solid #30363D; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. 名詞定義區 (Reducing Noise. Increasing Clarity) ---
st.title("🧋 Sharetea Express 決策引擎 v7.8")
st.markdown("<h4 style='color: #8B949E;'>Reducing Noise. Increasing Clarity.</h4>", unsafe_allow_html=True)

with st.expander("📚 2026 戰略體系名詞定義", expanded=False):
    def_c1, def_c2, def_c3 = st.columns(3)
    with def_c1:
        st.markdown("<div class='definition-box'><b>● SFS 戰略總分</b><br>核心指標，反映獲利潛力與地段適配度。</div>", unsafe_allow_html=True)
    with def_c2:
        st.markdown("<div class='definition-box' style='border-left-color: #1F6FEB;'><b>● 位置分級 (Tiering)</b><br>A+: 熱區指標 | B: 社區標準 | C: 高效普及。</div>", unsafe_allow_html=True)
    with def_c3:
        st.markdown("<div class='definition-box' style='border-left-color: #FF4B4B;'><b>● 戰略差距 (Gap)</b><br>衡量當前點位與下一目標層級的距離。</div>", unsafe_allow_html=True)

st.divider()

# --- 3. 數據輸入與 Secrets 讀取 ---
st.sidebar.header("📍 選址數據輸入")
coord_input = st.sidebar.text_input("座標 (Lat, Lng):", placeholder="34.1425, -118.0483")
loc_type = st.sidebar.selectbox("🏗️ 地段屬性:", ["Shopping Mall", "Food Court", "Community", "Plaza", "Main Street"])
seat_mult_map = {"高效型": 1.0, "標準型": 1.2, "旗艦型": 1.5}
seat_choice = st.sidebar.radio("🪑 預計規模:", list(seat_mult_map.keys()))
seat_mult = seat_mult_map[seat_choice]

G_KEY = st.secrets.get("GOOGLE_KEY")
GEMINI_KEY = st.secrets.get("GEMINI_KEY")
CENSUS_KEY = st.secrets.get("CENSUS_KEY")

# --- 4. 強化版 AI 戰略解釋 (針對流量本質與轉型) ---
def get_ai_diagnostic(context, api_key):
    if not api_key: return "❌ 尚未配置 GEMINI_KEY"
    try:
        genai.configure(api_key=api_key.strip())
        model = genai.GenerativeModel('gemini-3-flash-preview')
        prompt = f"""
        身為 Marketing Designer 戰略顧問，針對以下數據判讀：
        數據背景：{context}

        請針對以下維度提供深度的中文戰略分析（不需翻譯）：
        1. 【流量本質診斷】：
           - 判別是「隨機性/便利性流量」(如零售超市旁) 還是「目的性社交流量」(如 Arcadia 頂級餐飲聚落)。
           - 分析地圖中的地理特徵對品牌質感的影響。
        2. 【競爭紅海與寡占分析】：
           - 分析「集群密度」下的品牌稀釋風險，對標周邊大魔王品牌(如 Mo-Mo-Paradise)。
        3. 【層級躍遷介入計畫】：
           - 若點位為 Grade C，如何針對周邊專業客群(如 Kumon, Pilates) 透過「原葉茶」或「質感包裝」實現轉型 Grade B 的策略？
        """
        return model.generate_content(prompt).text
    except Exception as e: return f"⚠️ AI 診斷異常: {str(e)}"

# --- 5. 核心執行與頁面整合 ---
if st.sidebar.button("執行 2026 精英診斷"):
    if not coord_input:
        st.warning("請輸入座標。")
    else:
        try:
            parts = coord_input.split(',')
            lat, lng = float(parts[0].strip()), float(parts[1].strip())
            
            # 戰略演算參數 (模擬 Arcadia/UCI 邏輯)
            density, spending_power = 12, 8200
            eth_dict = {"華裔/東亞裔": 0.35, "墨西哥裔/西裔": 0.30, "東南亞裔": 0.15, "南亞裔": 0.10, "白人": 0.10}
            age_dict = {"18-24 歲": 0.25, "25-34 歲 (核心社交)": 0.40, "35 歲以上": 0.35}
            
            # SFS 演算邏輯
            target_index = (eth_dict["華裔/東亞裔"] * 2.5) + (age_dict["25-34 歲 (核心社交)"] * 2.0)
            final_sfs = ((spending_power * target_index) * 7 * 1.1 * seat_mult) / (math.pow(density, 0.7) + 1)
            
            # 分級與差距計算
            level = "熱區指標 (A+)" if final_sfs >= 15000 else "社區標準 (B)" if final_sfs >= 8500 else "高效普及 (C)"
            next_tier_val = 15000 if final_sfs < 15000 else 20000
            gap_pct = (next_tier_val - final_sfs) / next_tier_val if final_sfs < next_tier_val else 0

            # --- 畫面佈局 ---
            # A. 靜態地圖與核心指標
            m_col1, m_col2 = st.columns([2, 1])
            with m_col1:
                st.subheader("🖼️ 區域戰略靜態地圖")
                if G_KEY:
                    st.image(f"https://maps.googleapis.com/maps/api/staticmap?center={lat},{lng}&zoom=17&size=800x450&scale=2&key={G_KEY}", use_container_width=True)
            with m_col2:
                st.subheader("📊 關鍵數據指標")
                st.metric("SFS 戰略總分", f"{final_sfs:.0f}")
                st.metric("位置分級", level)
                st.metric("分級差距 (Gap)", f"{gap_pct:.1%}")
                st.metric("月均基礎消費力", f"${spending_power:,.0f}")
                st.metric("周邊競業數", f"{density} 間")

            st.divider()

            # B. 戰略差距分析與客群細分
            d_col1, d_col2 = st.columns(2)
            with d_col1:
                st.subheader("👥 客群結構與族裔細分")
                st.table(pd.DataFrame(eth_dict.items(), columns=["族裔類別", "佔比"]).style.format({"佔比":"{:.1%}"}))
                
                st.subheader("⏳ 年齡組成細分")
                st.bar_chart(pd.DataFrame(age_dict.items(), columns=["年齡段", "比例"]).set_index("年齡段"))

            with d_col2:
                st.subheader("🧠 消費行為與預判")
                behavior_type = "目的地社交消費 (High Value)" if final_sfs > 10000 else "隨機性便利消費 (High Turnover)"
                st.success(f"**主要行為模式：** {behavior_type}")
                st.info(f"**戰略差距分析：**\n目前點位距離下一層級尚有 {gap_pct:.1%} 的成長空間。建議透過強化『專業客群』的品牌介入計畫來縮小差距。")

            st.divider()

            # C. AI 戰略解釋 (升級版)
            st.subheader("🤖 Gemini 3 系列：AI 深度戰略診斷")
            with st.spinner("正在執行 AI 戰略判讀..."):
                ctx = f"SFS:{final_sfs:.0f}, 級別:{level}, 競業:{density}, 消費力:{spending_power}"
                st.write(get_ai_diagnostic(ctx, GEMINI_KEY))

        except Exception as e:
            st.error(f"分析異常: {e}")

st.caption("Produced by Marketing Designer. v7.8.0 | Reducing Noise. Increasing Clarity.")
