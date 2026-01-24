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
st.title("🧋 Sharetea Express 決策引擎 v7.9.1")
st.markdown("<h4 style='color: #8B949E;'>Reducing Noise. Increasing Clarity.</h4>", unsafe_allow_html=True)

with st.expander("📚 查看 2026 戰略體系完整規則定義", expanded=False):
    st.markdown("### 🧬 SFS 戰略總分演算規則")
    st.markdown("""
    **SFS (Strategic Finance Score)** 是量化地段潛力的核心指標。演算規則結合了族裔適配度、核心客群比例與地段溢價因子。
    """)
    # LaTeX 公式呈現
    st.latex(r"SFS = \frac{(Spending Power \times Target Index) \times 7 \times Env Factor \times Scale Mult \times \mathbf{Pressure Coeff}}{Density^{0.7} + 1}")
    
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("""
        **● 月均基礎消費力 (Spending Power)** 根據 Census API 抓取的該普查區中位數收入，決定單價天花板與溢價空間。
        
        **● 戰略目標指數 (Target Index)** 針對品牌基因設定權重：華裔/東亞裔 (2.5x) 與 25-34 歲社交核心客群 (2.0x) 為最關鍵因子。
        """)
    with c2:
        st.markdown("""
        **● 空間壓力係數 (Pressure Coeff)** 核心優化邏輯。當人均活動面積低於 12 sq. ft. 時，系統自動視為「美學雜訊」，對 SFS 進行降權懲罰。
        """)

    st.markdown("---")
    st.markdown("### 🏆 位置分級與戰略意義")
    st.markdown("""
    * **熱區指標 (Prime) [15,000+]**：具備『目的地消費』屬性，跨區食客流、高社交溢價。
    * **社區標準 (Community) [8,500+]**：日常獲利型地段，家長與專業人士為核心，品牌忠誠度高。
    * **高效普及 (eXpress) [< 8,500]**：機能性地段。依賴便利流量與高周轉率。
    """)

st.divider()

# --- 3. 數據輸入與 Secrets ---
st.sidebar.header("📍 選址數據輸入")
coord_input = st.sidebar.text_input("座標 (Lat, Lng):", placeholder="34.1425, -118.0483")
loc_type = st.sidebar.selectbox("🏗️ 地段屬性:", ["Shopping Mall", "Food Court", "Community", "Plaza", "Main Street"])

# 空間參數輸入
st.sidebar.markdown("---")
cust_area = st.sidebar.slider("顧客活動區面積 (sq. ft.):", 200, 800, 300)
seat_mult_map = {"0-4席": 1.0, "10-15席": 1.2, "20+席": 1.5}
seat_choice = st.sidebar.radio("🪑 預計座位數:", list(seat_mult_map.keys()))
seat_mult = seat_mult_map[seat_choice]

G_KEY = st.secrets.get("GOOGLE_KEY")
GEMINI_KEY = st.secrets.get("GEMINI_KEY")

# --- 4. 輔助函數：AI 診斷 (專注流量本質) ---
def get_ai_diagnostic(context, api_key):
    if not api_key: return "❌ 尚未配置 GEMINI_KEY"
    try:
        genai.configure(api_key=api_key.strip())
        model = genai.GenerativeModel('gemini-1.5-flash') # 修正為穩定版本
        prompt = f"""
        以 Marketing Designer 戰略角度針對以下數據判讀：
        數據背景：{context}
        請提供中文分析：
        1.【流量本質】：區分隨機便利型或目的地社交流量。分析地圖地理特徵。
        2.【空間質感診斷】：針對人均面積與空間壓力係數，評估該選址是否會產生體驗雜訊。
        3.【戰略轉型】：提供 Community 與 eXpress 之間的互轉指令。
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
            
            # --- 🧬 空間壓力係數演算 (Spatial Pressure Logic) ---
            # 根據選擇提取估算座位數
            seat_count_est = 4 if "0-4" in seat_choice else 15 if "10-15" in seat_choice else 25
            area_per_seat = cust_area / seat_count_est
            
            # 定義係數：人均低於 12sqft 視為過載(懲罰)，高於 18sqft 視為呼吸感(溢價)
            if area_per_seat < 12:
                pressure_coeff = 0.75  # 空間噪音懲罰
                quality_label = "⚠️ 空間過載 (體驗雜訊高)"
            elif 12 <= area_per_seat < 18:
                pressure_coeff = 1.0   # 標準水平
                quality_label = "✅ 空間適中 (標準平衡)"
            else:
                pressure_coeff = 1.1   # 呼吸感溢價
                quality_label = "✨ 空間舒適 (精品化潛力)"

            target_index = (eth_dict["華裔/東亞裔"] * 2.5) + (age_dict["25-34 歲社交"] * 2.0)
            
            # 整合壓力係數至 SFS
            final_sfs = ((spending_power * target_index) * 7 * 1.1 * seat_mult * pressure_coeff) / (math.pow(density, 0.7) + 1)
            
            level = "熱區指標 (P)" if final_sfs >= 15000 else "社區標準 (S)" if final_sfs >= 8500 else "高效普及 (X)"
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
                st.metric("空間質量", quality_label) # 新增空間質量監控
                st.metric("分級差距 (Gap)", f"{gap_pct:.1%}")
                st.metric("月均基礎消費力", f"${spending_power:,.0f}")

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
                st.info(f"**空間質感：** 人均活動面積 {area_per_seat:.1f} sq. ft.。這將直接影響品牌『清晰度』的傳達。")
                st.warning(f"**戰略差距分析：** 距離下一級門檻有 {gap_pct:.1%} 成長空間。建議針對當前空間壓力實施模組化家具優化。")

            st.divider()
            st.subheader("🤖 Gemini：AI 深度戰略診斷")
            with st.spinner("分析中..."):
                ctx = f"SFS:{final_sfs:.0f}, 級別:{level}, 空間質感:{quality_label}, 人均面積:{area_per_seat:.1f}sqft"
                st.write(get_ai_diagnostic(ctx, GEMINI_KEY))

        except Exception as e: st.error(f"分析異常: {e}")

st.caption("Produced by Marketing Designer. v7.9.1 | Reducing Noise. Increasing Clarity.")
