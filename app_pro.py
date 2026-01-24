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

# --- 2. 戰略體系規則定義 (名詞定義項目) ---
st.title("🧋 Sharetea Express 決策引擎 v8.1")
st.markdown("<h4 style='color: #8B949E;'>Reducing Noise. Increasing Clarity.</h4>", unsafe_allow_html=True)

with st.expander("📚 查看 2026 戰略體系完整規則定義", expanded=False):
    st.markdown("### 🧬 SFS 戰略總分演算規則")
    st.latex(r"SFS = \frac{(Spending Power \times Target Index) \times 7 \times Env Factor \times Scale Mult \times \mathbf{Pressure Coeff}}{Density^{0.7} + 1}")
    
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("""
        **● 月均基礎消費力 (Spending Power)** 普查區月均收入，決定單價天花板與獲利空間。
        
        **● 戰略目標指數 (Target Index)** 針對品牌基因設定權重：華裔/東亞裔 (2.5x) 與 25-34 歲社交核心客群 (2.0x) 為關鍵因子。
        """)
    with c2:
        st.markdown("""
        **● 空間壓力係數 (Pressure Coeff)** 核心質量檢索。當人均面積低於 25 sq. ft. 時 (如 460 呎放 20 席)，系統自動判定為「壓迫感雜訊」，對 SFS 進行 0.75x 的降權懲罰。
        """)

st.divider()

# --- 3. 數據輸入與坪數對照邏輯 (0-5, 6-12, 13-20 項目) ---
st.sidebar.header("📍 選址數據輸入")
coord_input = st.sidebar.text_input("座標 (Lat, Lng):", placeholder="34.1425, -118.0483")
loc_type = st.sidebar.selectbox("🏗️ 地段屬性:", ["Shopping Mall", "Food Court", "Community", "Plaza", "Main Street"])

st.sidebar.markdown("---")
# 坪數對照輸入 (200 - 460 sq. ft. 顧客活動區項目)
cust_area = st.sidebar.slider("顧客活動區面積 (sq. ft.):", 200, 460, 300)
seat_choice = st.sidebar.radio("🪑 預計規模 (座位數):", ["0-5席", "6-12席", "13-20席"])

# 🧬 空間壓力與加權對照邏輯
est_seats = 5 if "0-5" in seat_choice else 12 if "6-12" in seat_choice else 20
area_per_seat = cust_area / est_seats

# 修正：根據人均面積判定壓力 (13席舒服 ~35sqft / 20席壓迫 ~23sqft)
if area_per_seat >= 30: 
    pressure_coeff, seat_mult, quality_label = 1.2, 1.5, "✨ 精品呼吸感 (A+ 潛力)"
elif 25 <= area_per_seat < 30:
    pressure_coeff, seat_mult, quality_label = 1.0, 1.2, "✅ 標準質感"
else:
    pressure_coeff, seat_mult, quality_label = 0.75, 1.0, "⚠️ 空間過載 (壓迫感雜訊)"

st.sidebar.info(f"🧬 人均空間：{area_per_seat:.1f} sq. ft.\n💎 空間質量：{quality_label}")

G_KEY = st.secrets.get("GOOGLE_KEY")
GEMINI_KEY = st.secrets.get("GEMINI_KEY")

# --- 4. 輔助函數：AI 雙階段診斷 (成因與轉型項目) ---
def get_ai_diagnostic(context, api_key):
    if not api_key: return "❌ 尚未配置 GEMINI_KEY"
    try:
        genai.configure(api_key=api_key.strip())
        model = genai.GenerativeModel('gemini-1.5-flash')
        prompt = f"""
        以 Marketing Designer 戰略角度針對以下數據進行兩大判讀：
        數據背景：{context}
        1.【評分地理成因】：分析地圖地理特徵（轉角、鄰里感）如何導致目前的 SFS 評分。
        2.【轉型執行建議】：針對目前的空間質量({quality_label})，具體該如何執行品牌美學介入以實現等級提升？
        """
        return model.generate_content(prompt).text
    except Exception as e: return f"⚠️ AI 診斷連接中... (Error: {str(e)})"

# --- 5. 核心執行 ---
if st.sidebar.button("執行 2026 精英診斷"):
    if not coord_input:
        st.warning("請輸入座標。")
    else:
        try:
            parts = coord_input.split(',')
            lat, lng = float(parts[0].strip()), float(parts[1].strip())
            
            # 戰略參數：族群包含華裔/西裔/東南亞/南亞/白人/東亞
            density, spending_power = 12, 8200
            eth_dict = {"華裔/東亞裔": 0.35, "墨西哥裔/西裔": 0.30, "東南亞裔": 0.15, "南亞裔": 0.10, "白人": 0.10}
            age_dict = {"18-24 歲 (視覺)": 0.25, "25-34 歲 (社交主力)": 0.40, "35 歲以上": 0.35}
            
            # SFS 核心演算 (位置分級項目)
            target_index = (eth_dict["華裔/東亞裔"] * 2.5) + (age_dict["25-34 歲 (社交主力)"] * 2.0)
            final_sfs = ((spending_power * target_index) * 7 * 1.1 * seat_mult * pressure_coeff) / (math.pow(density, 0.7) + 1)
            
            level = "熱區指標 (P)" if final_sfs >= 15000 else "社區標準 (S)" if final_sfs >= 8500 else "高效普及 (X)"
            gap_pct = max(0, (15000 - final_sfs) / 15000)

            # --- 畫面呈現 (靜態地圖項目) ---
            m_col1, m_col2 = st.columns([2, 1])
            with m_col1:
                st.subheader("🖼️ 區域戰略靜態地圖 (High-DPI)")
                if G_KEY: st.image(f"https://maps.googleapis.com/maps/api/staticmap?center={lat},{lng}&zoom=17&size=800x450&scale=2&key={G_KEY}", use_container_width=True)
            with m_col2:
                st.subheader("📊 關鍵數據指標")
                st.metric("SFS 戰略總分", f"{final_sfs:.0f}")
                st.metric("位置分級", level)
                st.metric("分級差距 (Gap)", f"{gap_pct:.1%}")
                st.metric("空間質感診斷", quality_label)
                st.metric("周邊競業數", f"{density} 間")

            st.divider()

            d_col1, d_col2 = st.columns(2)
            with d_col1:
                # 族群與年齡高低排序項目
                st.subheader("👥 客群結構與族群細分 (高→低)")
                st.table(pd.DataFrame(sorted(eth_dict.items(), key=lambda x:x[1], reverse=True), columns=["族裔類別", "佔比"]).style.format({"佔比":"{:.1%}"}))
                st.subheader("⏳ 年齡組成細分 (高→低)")
                st.bar_chart(pd.DataFrame(sorted(age_dict.items(), key=lambda x:x[1], reverse=True), columns=["年齡段", "比例"]).set_index("年齡段"))

            with d_col2:
                # 消費行為與預判項目
                st.subheader("🧠 消費行為與預判")
                behavior = "目的地社交消費 (目的性流量)" if final_sfs > 10000 else "隨機性便利消費 (隨機性流量)"
                st.success(f"**行為模式：** {behavior}")
                st.info(f"**戰略差距分析：** 目前空間質感為 {quality_label}，人均面積 {area_per_seat:.1f} sq. ft.。")
                st.warning(f"**轉型指引：** 距離下一級門檻有 {gap_pct:.1%} 空間。建議優先優化模組化家具佈局以減少視覺雜訊。")

            st.divider()
            st.subheader("🤖 Gemini：AI 深度戰略診斷 (兩階段任務)")
            with st.spinner("分析中..."):
                ctx = f"SFS:{final_sfs:.0f}, 級別:{level}, 空間質量:{quality_label}, 人均面積:{area_per_seat:.1f}"
                st.write(get_ai_diagnostic(ctx, GEMINI_KEY))

        except Exception as e: st.error(f"分析異常: {e}")

st.caption("Produced by Marketing Designer. v8.1.0 | Reducing Noise. Increasing Clarity.")
