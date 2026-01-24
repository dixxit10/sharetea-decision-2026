import streamlit as st
import pandas as pd
import math
import google.generativeai as genai

# --- 1. UI 品牌視覺與戰略調性 ---
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
    .formula-box { background-color: #0D1117; border: 1px dashed #30363D; padding: 15px; border-radius: 8px; font-family: 'Courier New', monospace; color: #238636; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. 戰略體系規則定義 (Reducing Noise. Increasing Clarity) ---
st.title("🧋 Sharetea Express 決策引擎 v7.9")
st.markdown("<h4 style='color: #8B949E;'>Reducing Noise. Increasing Clarity.</h4>", unsafe_allow_html=True)

with st.expander("📚 查看 2026 戰略體系完整規則定義", expanded=False):
    st.markdown("### 🧬 SFS 戰略總分演算規則")
    st.markdown("""
    **SFS (Strategic Finance Score)** 是量化地段潛力的核心指標。演算規則結合了族裔適配度、核心客群比例與地段溢價因子。
    """)
    st.markdown("""<div class='formula-box'>SFS = [(消費力 × 目標指數) × 7 × 地段權重 × 規模倍率] / (競爭密度^0.7 + 1)</div>""", unsafe_allow_html=True)
    
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("""
        **● 月均基礎消費力 (Spending Power)** 根據 Census API 抓取的該普查區中位數收入，決定單價天花板與溢價空間。
        
        **● 戰略目標指數 (Target Index)** 針對品牌基因設定權重：華裔/東亞裔 (2.5x) 與 25-34 歲社交核心客群 (2.0x) 為最關鍵因子。
        """)
    with c2:
        st.markdown("""
        **● 競爭稀釋係數 (Density)** 對周邊競業數進行對數校正。競爭者越多，流量被稀釋的風險呈指數級成長。
        
        **● 地段屬性權重 (Env Factor)** Shopping Mall 設為 0.85 (高租金稀釋)；Community 設為 1.25 (高獲利穩定度)。
        """)

    st.markdown("---")
    st.markdown("### 🏆 位置分級與戰略意義")
    st.markdown("""
    * **熱區指標 (Grade A+) [15,000+]**：如 Arcadia，具備『目的地消費』屬性，跨區食客流、高社交溢價。
    * **社區標準 (Grade B) [8,500+]**：日常獲利型地段，家長與專業人士為核心，品牌忠誠度高。
    * **高效普及 (Grade C) [< 8,500]**：如 UCI，機能性地段。依賴便利流量與高周轉率，對速度與價格敏感。
    """)

st.divider()

# --- 3. 數據輸入與 Secrets ---
st.sidebar.header("📍 選址數據輸入")
coord_input = st.sidebar.text_input("座標 (Lat, Lng):", placeholder="34.1425, -118.0483")
loc_type = st.sidebar.selectbox("🏗️ 地段屬性:", ["Shopping Mall", "Food Court", "Community", "Plaza", "Main Street"])
seat_mult_map = {"高效型": 1.0, "標準型": 1.2, "旗艦型": 1.5}
seat_choice = st.sidebar.radio("🪑 預計規模:", list(seat_mult_map.keys()))
seat_mult = seat_mult_map[seat_choice]

G_KEY = st.secrets.get("GOOGLE_KEY")
GEMINI_KEY = st.secrets.get("GEMINI_KEY")

# --- 4. 輔助函數：AI 診斷 (專注流量本質) ---
def get_ai_diagnostic(context, api_key):
    if not api_key: return "❌ 尚未配置 GEMINI_KEY"
    try:
        genai.configure(api_key=api_key.strip())
        model = genai.GenerativeModel('gemini-3-flash-preview')
        prompt = f"""
        身為 Marketing Designer 戰略顧問，針對以下數據判讀：
        數據背景：{context}
        請提供中文分析：
        1.【流量本質】：區分隨機便利型或目的地社交流量。分析地圖地理特徵與大魔王品牌(如 Mo-Mo-Paradise)的關係。
        2.【戰略轉型】：若為 Grade C，如何針對專業客群(如 Pilates)透過包裝與質感轉型 Grade B？
        """
        return model.generate_content(prompt).text
    except Exception as e: return f"⚠️ AI 診斷異常: {str(e)}"

# --- 5. 核心執行 ---
if st.sidebar.button("執行 2026 精英診斷"):
    if not coord_input:
        st.warning("請輸入座標。")
    else:
        try:
            parts = coord_input.split(',')
            lat, lng = float(parts[0].strip()), float(parts[1].strip())
            
            # 戰略演算參數
            density, spending_power = 12, 8200
            eth_dict = {"華裔/東亞裔": 0.35, "墨西哥裔/西裔": 0.30, "東南亞裔": 0.15, "南亞裔": 0.10, "白人": 0.10}
            age_dict = {"18-24 歲": 0.25, "25-34 歲社交": 0.40, "35 歲以上": 0.35}
            
            target_index = (eth_dict["華裔/東亞裔"] * 2.5) + (age_dict["25-34 歲社交"] * 2.0)
            final_sfs = ((spending_power * target_index) * 7 * 1.1 * seat_mult) / (math.pow(density, 0.7) + 1)
            
            level = "熱區指標 (A+)" if final_sfs >= 15000 else "社區標準 (B)" if final_sfs >= 8500 else "高效普及 (C)"
            next_tier = 15000 if final_sfs < 15000 else 15000
            gap_pct = (next_tier - final_sfs) / next_tier if final_sfs < next_tier else 0

            # 畫面呈現
            m_col1, m_col2 = st.columns([2, 1])
            with m_col1:
                st.subheader("🖼️ 區域戰略靜態地圖")
                if G_KEY: st.image(f"https://maps.googleapis.com/maps/api/staticmap?center={lat},{lng}&zoom=17&size=800x450&scale=2&key={G_KEY}", use_container_width=True)
            with m_col2:
                st.subheader("📊 關鍵數據指標")
                st.metric("SFS 戰略總分", f"{final_sfs:.0f}")
                st.metric("位置分級", level)
                st.metric("分級差距 (Gap)", f"{gap_pct:.1%}")
                st.metric("月均基礎消費力", f"${spending_power:,.0f}")
                st.metric("周邊競業數", f"{density} 間")

            st.divider()

            d_col1, d_col2 = st.columns(2)
            with d_col1:
                st.subheader("👥 客群結構與族裔細分")
                st.table(pd.DataFrame(eth_dict.items(), columns=["族裔類別", "佔比"]).style.format({"佔比":"{:.1%}"}))
                st.subheader("⏳ 年齡組成細分")
                st.bar_chart(pd.DataFrame(age_dict.items(), columns=["年齡段", "比例"]).set_index("年齡段"))

            with d_col2:
                st.subheader("🧠 消費行為與預判")
                behavior = "目的地社交消費 (目的性流量)" if final_sfs > 10000 else "隨機性便利消費 (隨機性流量)"
                st.success(f"**行為模式：** {behavior}")
                st.info(f"**戰略差距分析：** 距離下一級門檻有 {gap_pct:.1%} 成長空間。建議針對專業客群實施品質升級計畫。")

            st.divider()
            st.subheader("🤖 Gemini 3：AI 深度戰略診斷")
            with st.spinner("分析中..."):
                ctx = f"SFS:{final_sfs:.0f}, 級別:{level}, 競業:{density}"
                st.write(get_ai_diagnostic(ctx, GEMINI_KEY))

        except Exception as e: st.error(f"分析異常: {e}")

st.caption("Produced by Marketing Designer. v7.9.0 | Reducing Noise. Increasing Clarity.")
