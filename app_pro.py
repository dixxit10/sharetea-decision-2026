import streamlit as st
import pandas as pd
import math
import requests
import google.generativeai as genai
from io import BytesIO

# --- 1. UI & CSS 配置 ---
st.set_page_config(page_title="Sharetea Express 2026 全方位評估", layout="wide")
st.markdown("""
    <style>
    .stApp { background-color: #0E1117; color: #E6EDF3; font-family: 'Inter', sans-serif; }
    
    /* 卡片高度與間距 */
    .definition-box { 
        background-color: #1C2128; 
        border-left: 3px solid #238636; 
        padding: 20px; 
        margin-bottom: 20px; 
        border-radius: 0 4px 4px 0; 
        font-size: 0.92em; 
        line-height: 1.6;
        min-height: 160px;
        display: flex;
        flex-direction: column;
    }
    
    div[data-testid="metric-container"] { 
        background-color: #1C2128; border: 1px solid #30363D; padding: 25px; border-radius: 8px; 
    }
    
    .stButton>button { 
        background: #238636; color: white; border: none;
        border-radius: 4px; font-weight: 500; width: 100%; height: 3.5em; text-transform: uppercase; letter-spacing: 1px;
    }
    
    .formula-display { 
        background-color: #0D1117; border: 1px solid #30363D; padding: 25px; 
        border-radius: 4px; margin: 25px 0; text-align: center;
    }
    
    h1, h2, h3 { font-weight: 600; letter-spacing: -0.5px; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. 規則定義 ---
st.title("📚 名詞定義 v8.3")
st.markdown("<p style='color: #8B949E; font-size: 1.2em; margin-top: -15px;'>Reducing Noise. Increasing Clarity.</p>", unsafe_allow_html=True)

st.markdown("### Strategic Framework Definitions")

# 名詞定義與 SFS 公式
st.markdown("<div class='formula-display'>", unsafe_allow_html=True)
st.latex(r"SFS = \frac{(Spending Power \times Target Index) \times 7 \times Env Factor \times Scale Mult \times Pressure Coeff}{Density^{0.7} + 1}")
st.markdown("</div>", unsafe_allow_html=True)

def_col1, def_col2, def_col3 = st.columns(3)
with def_col1:
    st.markdown("<div class='definition-box'><b>SFS 戰略總分</b><br>量化地段潛力的核心指標，結合消費力、目標客群適配度與競爭稀釋係數。</div>", unsafe_allow_html=True)
    st.markdown("<div class='definition-box'><b>月均基礎消費力</b><br>根據CENSUS普查區月收入中位數。決定產品定價天花板與精品化空間。</div>", unsafe_allow_html=True)
with def_col2:
    st.markdown("<div class='definition-box'><b>空間壓力係數 (Pressure Coeff)</b><br>依照ADA建議指數當人均面積低於 25 sq. ft. 時，判定為壓迫感雜訊並調降分值。</div>", unsafe_allow_html=True)
    st.markdown("<div class='definition-box'><b>位置分級基準</b><br>熱區指標 (P): 15000+<br>社區標準 (C): 8500+<br>高效普及 (X): < 8500</div>", unsafe_allow_html=True)
with def_col3:
    st.markdown("<div class='definition-box'><b>戰略排除 (Exclusion)</b><br>若 SFS 未達該地段屬性之最低基準線，系統將封鎖詳細數據，確保精準開發。</div>", unsafe_allow_html=True)
    st.markdown("<div class='definition-box'><b>顧客活動區 (200-460 sqft)</b><br>精確定義之美學介入範圍，排除吧台與工作區。</div>", unsafe_allow_html=True)

st.divider()

# --- 3. 數據 ---
st.sidebar.header("查詢資料輸入(僅限美國區域)")
coord_input = st.sidebar.text_input("📍座標輸入 (緯度, 經度):", placeholder="34.1425, -118.0483")
loc_type = st.sidebar.selectbox("地點型態:", ["Shopping Mall", "Food Court", "Community", "Plaza", "Main Street"])

st.sidebar.markdown("---")
# 坪數與座位對照
cust_area = st.sidebar.slider("顧客活動空間 (sq. ft.):", 200, 460, 300)
seat_choice = st.sidebar.radio("座位數:", ["0-5 席", "6-12 席", "13-20 席"])

# 空間壓力偵測邏輯
est_seats = 5 if "0-5" in seat_choice else 12 if "6-12" in seat_choice else 20
area_per_seat = cust_area / est_seats

if area_per_seat >= 30: 
    pressure_coeff, seat_mult, quality_label = 1.2, 1.5, "✨ 極致清晰"
elif 25 <= area_per_seat < 30:
    pressure_coeff, seat_mult, quality_label = 1.0, 1.2, "✅ 標準質感"
else:
    # 當人均面積低於 25 sqft (即 460 呎放 20 席) 產生壓迫感
    pressure_coeff, seat_mult, quality_label = 0.75, 1.0, "⚠️ 體驗過載"

st.sidebar.info(f"Inferred Density: {area_per_seat:.1f} sq. ft./seat\nStatus: {quality_label}")

# Secrets
G_KEY = st.secrets.get("GOOGLE_KEY")
GEMINI_KEY = st.secrets.get("GEMINI_KEY")
CENSUS_KEY = st.secrets.get("CENSUS_KEY")

# --- 伺服器端圖片獲取函數 ---
def get_map_image_secure(lat, lng, key):
    url = f"https://maps.googleapis.com/maps/api/staticmap?center={lat},{lng}&zoom=17&size=800x450&scale=2&key={key}"
    response = requests.get(url)
    if response.status_code == 200:
        return BytesIO(response.content)
    return None

# --- 4. AI 診斷 ---
def get_ai_diagnostic(context, api_key):
    if not api_key: return "API Key Configuration Missing."
    try:
        genai.configure(api_key=api_key.strip())
        model = genai.GenerativeModel('gemini-3-flash-preview')
        prompt = f"""
        以行銷、戰略、設計角度，針對坪數與座位席進行專業分析。
        背景數據：{context}
        請提供中文專業分析：
        1.【評分地理成因】：分析地圖地理特徵（路幅、鄰里質感）如何導致目前的 SFS 評分。
        2.【轉型執行建議】：若要針對當前空間質量({quality_label})進行轉型，應如何具體執行和介入？
        """
        response = model.generate_content(prompt)
        return response.text
    except Exception as e: return f"AI Diagnostic Unavailable: {str(e)}"

# --- 5. 核心 ---
if st.sidebar.button("Execute Strategic Analysis"):
    if not coord_input:
        st.error("Please provide coordinates.")
    else:
        try:
            parts = coord_input.split(',')
            lat, lng = float(parts[0].strip()), float(parts[1].strip())
            
            # 初始化數據 (包含華裔、西裔、社交主力等項目)
            density, spending_power = 12, 8200
            eth_dict = {"華裔/東亞裔": 0.35, "墨西哥裔/西裔": 0.30, "東南亞裔": 0.15, "白人": 0.1, "南亞裔": 0.05, "其他": 0.05}
            age_dict = {"18-24 歲 (視覺)": 0.25, "25-34 歲 (社交主力)": 0.40, "35 歲以上": 0.35}
            
            # SFS 演算
            target_index = (eth_dict["華裔/東亞裔"] * 2.5) + (age_dict["25-34 歲 (社交主力)"] * 2.0)
            final_sfs = ((spending_power * target_index) * 7 * 1.1 * seat_mult * pressure_coeff) / (math.pow(density, 0.7) + 1)
            
            level = "熱區指標 (P)" if final_sfs >= 15000 else "社區標準 (C)" if final_sfs >= 8500 else "高效普及 (X)"
            gap_pct = max(0, (15000 - final_sfs) / 15000)

            # --- 畫面呈現 ---
            m1, m2 = st.columns([2, 1])
            with m1:
                st.subheader("Strategic Geographic Snapshot")
                
                map_bytes = get_map_image_secure(lat, lng, G_KEY)
                if map_bytes: 
                    st.image(map_bytes, use_container_width=True, caption="📍 Retina Density Scan (Internal Server Auth)")
            with m2:
                st.subheader("Key Strategic Metrics")
                st.metric("SFS 分數", f"{final_sfs:.0f}")
                st.metric("位置型態", level)
                st.metric("型態差距", f"{gap_pct:.1%}")
                st.metric("Spatial Quality", quality_label)
                st.metric("月消費力", f"${spending_power:,.0f}")
                st.metric("周邊競業", f"{density}")")

            st.divider()

            d1, d2 = st.columns(2)
            with d1:
                # 族裔與年齡
                st.subheader("👥 族群分析")
                st.table(pd.DataFrame(sorted(eth_dict.items(), key=lambda x:x[1], reverse=True), columns=["Category", "Ratio"]).style.format({"Ratio":"{:.1%}"}))
                
                st.subheader("🎂 年齡組成")
                st.table(pd.DataFrame(sorted(age_dict.items(), key=lambda x:x[1], reverse=True), columns=["Segment", "Ratio"]).style.format({"Ratio":"{:.1%}"}))

            with d2:
                st.subheader("行為與差距評估")
                behavior = "目的型社交消費" if final_sfs > 10000 else "便利驅動消費"
                st.success(f"Mode: {behavior}")
                st.info(f"Current human scale is {area_per_seat:.1f} sq. ft. A gap of {gap_pct:.1%} remains to reach Prime status.")
                st.warning("Strategic Advice: Optimize modular furniture layouts to enhance clarity.")

            st.divider()
            st.subheader("Gemini AI 分析")
            with st.spinner("Analyzing geographic traits..."):
                ctx = f"SFS:{final_sfs:.0f}, Tier:{level}, Area:{cust_area}sqft, Seats:{seat_choice}"
                st.markdown(get_ai_diagnostic(ctx, GEMINI_KEY))

        except Exception as e: st.error(f"Analysis Exception: {e}")

st.caption("Produced by Marketing Designer. v8.3.0 | Reducing Noise. Increasing Clarity.")
