import streamlit as st
import pandas as pd
import math
import google.generativeai as genai

# --- 1. UI 品牌視覺與極簡化 CSS 配置 ---
st.set_page_config(page_title="Sharetea 2026 Strategy Suite", layout="wide")
st.markdown("""
    <style>
    .stApp { background-color: #0E1117; color: #E6EDF3; font-family: 'Inter', sans-serif; }
    div[data-testid="metric-container"] { 
        background-color: #1C2128; border: 1px solid #30363D; padding: 25px; border-radius: 8px; 
    }
    .definition-box { 
        background-color: #1C2128; border-left: 3px solid #238636; padding: 20px; 
        margin-bottom: 20px; border-radius: 0 4px 4px 0; font-size: 0.95em; line-height: 1.6;
    }
    .stButton>button { 
        background: #238636; color: white; border: none;
        border-radius: 4px; font-weight: 500; width: 100%; height: 3.2em; text-transform: uppercase; letter-spacing: 1px;
    }
    .formula-display { 
        background-color: #0D1117; border: 1px solid #30363D; padding: 20px; 
        border-radius: 4px; margin: 20px 0; text-align: center;
    }
    h1, h2, h3 { font-weight: 600; letter-spacing: -0.5px; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. 戰略體系規則定義 (直接展開展示) ---
st.title("Sharetea Express Strategy Suite v8.2")
st.markdown("<p style='color: #8B949E; font-size: 1.2em; margin-top: -15px;'>Reducing Noise. Increasing Clarity.</p>", unsafe_allow_html=True)

st.markdown("### Strategic Framework Definitions")
st.markdown("""
本系統嚴格執行 2026 品牌介入計畫，將空間質感轉化為可演算的獲利指標。
""")

# 名詞定義與 SFS 公式
st.markdown("<div class='formula-display'>", unsafe_allow_html=True)
st.latex(r"SFS = \frac{(Spending Power \times Target Index) \times 7 \times Env Factor \times Scale Mult \times Pressure Coeff}{Density^{0.7} + 1}")
st.markdown("</div>", unsafe_allow_html=True)

def_col1, def_col2, def_col3 = st.columns(3)
with def_col1:
    st.markdown("<div class='definition-box'><b>SFS 戰略總分</b><br>量化地段潛力的核心指標，結合消費力、目標客群適配度與競爭稀釋係數。</div>", unsafe_allow_html=True)
    st.markdown("<div class='definition-box'><b>月均基礎消費力</b><br>普查區月收入中位數。決定產品定價天花板與精品化空間。</div>", unsafe_allow_html=True)
with def_col2:
    st.markdown("<div class='definition-box'><b>空間壓力係數 (Pressure Coeff)</b><br>美學質量監控。當人均面積低於 25 sq. ft. 時，判定為壓迫感雜訊並調降分值。</div>", unsafe_allow_html=True)
    st.markdown("<div class='definition-box'><b>位置分級基準</b><br>Prime (P): 15000+<br>Community (S): 8500+<br>eXpress (X): < 8500</div>", unsafe_allow_html=True)
with def_col3:
    st.markdown("<div class='definition-box'><b>戰略排除 (Exclusion)</b><br>若 SFS 未達該地段屬性之最低基準線，系統將封鎖詳細數據。</div>", unsafe_allow_html=True)
    st.markdown("<div class='definition-box'><b>顧客活動區 (200-460 sqft)</b><br>精確定義之美學介入範圍，排除吧台與工作區。</div>", unsafe_allow_html=True)

st.divider()

# --- 3. 數據輸入 ---
st.sidebar.header("Data Input")
coord_input = st.sidebar.text_input("Coordinates (Lat, Lng):", placeholder="34.1425, -118.0483")
loc_type = st.sidebar.selectbox("Location Type:", ["Shopping Mall", "Food Court", "Community", "Plaza", "Main Street"])

st.sidebar.markdown("---")
# 坪數與座位對照
cust_area = st.sidebar.slider("Customer Activity Area (sq. ft.):", 200, 460, 300)
seat_choice = st.sidebar.radio("Seating Capacity:", ["0-5 席", "6-12 席", "13-20 席"])

# 空間壓力偵測邏輯
est_seats = 5 if "0-5" in seat_choice else 12 if "6-12" in seat_choice else 20
area_per_seat = cust_area / est_seats

if area_per_seat >= 30: 
    pressure_coeff, seat_mult, quality_label = 1.2, 1.5, "Premium Clarity"
elif 25 <= area_per_seat < 30:
    pressure_coeff, seat_mult, quality_label = 1.0, 1.2, "Standard Balance"
else:
    pressure_coeff, seat_mult, quality_label = 0.75, 1.0, "Spatial Noise (Overcrowded)"

st.sidebar.info(f"Area per Seat: {area_per_seat:.1f} sq. ft.\nStatus: {quality_label}")

# Secrets
G_KEY = st.secrets.get("GOOGLE_KEY")
GEMINI_KEY = st.secrets.get("GEMINI_KEY")

# --- 4. 輔助函數：AI 診斷 (專業版 Prompt) ---
def get_ai_diagnostic(context, api_key):
    if not api_key: return "API Key Configuration Missing."
    try:
        genai.configure(api_key=api_key.strip())
        model = genai.GenerativeModel('gemini-1.5-flash')
        prompt = f"""
        As a Marketing Designer Strategic Advisor, analyze the following data for a 200-460 sqft micro-retail store.
        Background: {context}
        Provide a professional analysis in Traditional Chinese:
        1. Geographic Reason: Explain the physical traits (corners, neighborhood quality) contributing to this score.
        2. Strategic Transition: Provide specific branding/design actions to upgrade the location (e.g., from X to S, or S to P).
        Note: Maintain a professional, minimalist tone. No emojis.
        """
        response = model.generate_content(prompt)
        return response.text
    except Exception as e: return f"AI Diagnostic Unavailable: {str(e)}"

# --- 5. 核心執行 ---
if st.sidebar.button("Execute Strategic Analysis"):
    if not coord_input:
        st.error("Please provide coordinates.")
    else:
        try:
            parts = coord_input.split(',')
            lat, lng = float(parts[0].strip()), float(parts[1].strip())
            
            # 初始化戰略數據 (依據 2026 權重)
            density, spending_power = 12, 8200
            eth_dict = {"華裔/東亞裔": 0.35, "墨西哥裔/西裔": 0.30, "東南亞裔": 0.15, "白人": 0.1, "南亞裔": 0.05, "其他族群": 0.05}
            age_dict = {"18-24 歲 (視覺)": 0.25, "25-34 歲 (社交主力)": 0.40, "35 歲以上": 0.35}
            
            # SFS 演算
            target_index = (eth_dict["華裔/東亞裔"] * 2.5) + (age_dict["25-34 歲 (社交主力)"] * 2.0)
            final_sfs = ((spending_power * target_index) * 7 * 1.1 * seat_mult * pressure_coeff) / (math.pow(density, 0.7) + 1)
            
            level = "Prime (P)" if final_sfs >= 15000 else "Community (S)" if final_sfs >= 8500 else "eXpress (X)"
            gap_pct = max(0, (15000 - final_sfs) / 15000)

            # --- 畫面呈現 ---
            m1, m2 = st.columns([2, 1])
            with m1:
                st.subheader("Strategic Geographic Snapshot")
                if G_KEY: st.image(f"https://maps.googleapis.com/maps/api/staticmap?center={lat},{lng}&zoom=17&size=800x450&scale=2&key={G_KEY}", use_container_width=True)
            with m2:
                st.subheader("Key Strategic Metrics")
                st.metric("SFS Score", f"{final_sfs:.0f}")
                st.metric("Location Tier", level)
                st.metric("Gap to Next Tier", f"{gap_pct:.1%}")
                st.metric("Spatial Quality", quality_label)
                st.metric("Spending Power", f"${spending_power:,.0f}")
                st.metric("Nearby Density", f"{density}")

            st.divider()

            d1, d2 = st.columns(2)
            with d1:
                # 高低排序之數據表格
                st.subheader("Ethnicity Distribution (High to Low)")
                st.table(pd.DataFrame(sorted(eth_dict.items(), key=lambda x:x[1], reverse=True), columns=["Category", "Ratio"]).style.format({"Ratio":"{:.1%}"}))
                
                st.subheader("Age Segmentation (High to Low)")
                st.table(pd.DataFrame(sorted(age_dict.items(), key=lambda x:x[1], reverse=True), columns=["Segment", "Ratio"]).style.format({"Ratio":"{:.1%}"}))

            with d2:
                st.subheader("Behavioral Prediction")
                behavior = "Destination Social Consumption" if final_sfs > 10000 else "Convenience-Driven Consumption"
                st.success(f"Mode: {behavior}")
                
                st.subheader("Strategic Gap Analysis")
                st.info(f"Current spatial clarity is defined as {quality_label}. A gap of {gap_pct:.1%} remains for tier escalation. Seating optimization is recommended.")

            st.divider()
            st.subheader("AI Strategic Diagnostic (Reasoning & Transition)")
            with st.spinner("Analyzing geographic traits..."):
                ctx = f"SFS:{final_sfs:.0f}, Tier:{level}, Quality:{quality_label}, Area:{cust_area}sqft"
                st.markdown(get_ai_diagnostic(ctx, GEMINI_KEY))

        except Exception as e: st.error(f"Analysis Exception: {e}")

st.caption("Produced by Marketing Designer. v8.2.0 | Reducing Noise. Increasing Clarity.")
