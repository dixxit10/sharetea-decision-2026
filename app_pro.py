import streamlit as st
import pandas as pd
import math
import requests
import google.generativeai as genai
from io import BytesIO
from PIL import Image

# --- 0. 密碼驗證邏輯 (sharetea2026) ---
def check_password():
    if "password_correct" not in st.session_state:
        st.title("🔐 Sharetea 戰略系統門禁")
        password = st.text_input("請輸入密碼以開啟戰略引擎", type="password", key="password_gate")
        if st.button("開啟引擎"):
            if password == "sharetea2026":
                st.session_state["password_correct"] = True
                st.rerun()
            else:
                st.error("😕 密碼錯誤")
        return False
    return True

if check_password():
    # --- 1. UI & CSS 配置 ---
    st.set_page_config(page_title="Sharetea Express 2026 全方位評估", layout="wide")
    st.markdown("""
        <style>
        .stApp { background-color: #0E1117; color: #E6EDF3; font-family: 'Inter', sans-serif; }
        .definition-box { 
            background-color: #1C2128; border-left: 3px solid #238636; 
            padding: 20px; margin-bottom: 20px; border-radius: 0 4px 4px 0; 
            font-size: 0.92em; line-height: 1.6; min-height: 180px;
            display: flex; flex-direction: column;
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
        </style>
        """, unsafe_allow_html=True)

    # --- 2. 名詞定義 (Definitions) ---
    st.title("📚 名詞定義 v8.7")
    st.markdown("<p style='color: #8B949E; font-size: 1.2em; margin-top: -15px;'>Reducing Noise. Increasing Clarity.</p>", unsafe_allow_html=True)

    def_col1, def_col2, def_col3 = st.columns(3)
    with def_col1:
        st.markdown("<div class='definition-box'><b>SFS 戰略總分</b><br>量化地段潛力的核心指標。整合消費力、族群、空間壓力與 AI 判讀之環境權重。</div>", unsafe_allow_html=True)
        st.markdown("<div class='definition-box'><b>空間壓力係數 (Pressure Coeff)</b><br>當人均面積低於 25 sq. ft. 時，判定為體驗雜訊並下修分值。</div>", unsafe_allow_html=True)
    with def_col2:
        st.markdown("<div class='definition-box'><b>環境與地段基因</b><br>透過 Gemini AI 視覺掃描靜態地圖，識別鄰里質感與視覺雜訊 (如汽修廠、加油站)。</div>", unsafe_allow_html=True)
        st.markdown("<div class='definition-box'><b>月均基礎消費力</b><br>連動 CENSUS API。代表該普查區之月收入中位數，決定產品溢價空間。</div>", unsafe_allow_html=True)
    with def_col3:
        st.markdown("<div class='definition-box'><b>位置分級基準</b><br>品牌指標 (M): 15000+<br>社區標準 (C): 8500+<br>高效普及 (X): < 8500</div>", unsafe_allow_html=True)
        st.markdown("<div class='definition-box'><b>顧客活動區 (200-460 sqft)</b><br>精確定義之美學介入範圍，排除吧台與工作區。</div>", unsafe_allow_html=True)

    st.divider()

    # --- 3. 數據輸入與演算配置 ---
    st.sidebar.header("查詢資料輸入(僅限美國區域)")
    coord_input = st.sidebar.text_input("📍座標輸入 (緯度, 經度):", placeholder="34.1425, -118.0483")
    loc_type = st.sidebar.selectbox("地點型態:", ["Shopping Mall", "Food Court", "Community", "Plaza", "Main Street"])

    st.sidebar.markdown("---")
    cust_area = st.sidebar.slider("顧客活動空間 (sq. ft.):", 200, 460, 300)
    seat_choice = st.sidebar.radio("座位數:", ["0-5 席", "6-12 席", "13-20 席"])

    # 空間壓力偵測邏輯
    est_seats = 5 if "0-5" in seat_choice else 12 if "6-12" in seat_choice else 20
    area_per_seat = cust_area / est_seats
    pressure_coeff = 1.2 if area_per_seat >= 30 else 1.0 if area_per_seat >= 25 else 0.75
    quality_label = "✨ 極致清晰" if pressure_coeff == 1.2 else "✅ 標準質感" if pressure_coeff == 1.0 else "⚠️ 體驗過載"

    G_KEY = st.secrets.get("GOOGLE_KEY")
    GEMINI_KEY = st.secrets.get("GEMINI_KEY")
    CENSUS_KEY = st.secrets.get("CENSUS_KEY")

    # --- 4. 戰略輔助函數 ---
    def get_census_data(lat, lng, api_key):
        try:
            geo_url = f"https://geo.fcc.gov/api/census/area?lat={lat}&lon={lng}&format=json"
            geo_res = requests.get(geo_url).json()
            fips = geo_res['results'][0]['block_fips']
            state, county, tract = fips[:2], fips[2:5], fips[5:11]
            census_url = f"https://api.census.gov/data/2022/acs/acs5?get=B19013_001E&for=tract:{tract}&in=state:{state}%20county:{county}&key={api_key}"
            data = requests.get(census_url).json()
            return int(data[1][0]) / 12
        except: return None

    def get_nearby_density(lat, lng, key):
        try:
            url = f"https://maps.googleapis.com/maps/api/place/nearbysearch/json?location={lat},{lng}&radius=500&type=restaurant&key={key}"
            res = requests.get(url).json()
            return len(res.get('results', []))
        except: return 12

    def get_vision_analysis(image_bytes, sfs_context, api_key):
        try:
            genai.configure(api_key=api_key)
            model = genai.GenerativeModel('gemini-3-flash-preview')
            img = Image.open(image_bytes)
            prompt = f"""
            身為 Marketing Designer 顧問，請判讀這張地圖截圖中的『視覺雜訊』與『鄰里基因』。
            數據：{sfs_context}
            1.【環境基因判讀】：識別地圖中的內容，判斷是哪種商業類型，例如快餐導向、辦公商圈、精緻商場、社區鄰里。
            2.【轉型執行建議】：針對該區人口組成結果，提供執行建議。
            """
            response = model.generate_content([prompt, img])
            return response.text
        except Exception as e: return f"視覺分析異常: {str(e)}"

    # --- 5. 核心執行 ---
    if st.sidebar.button("Execute Strategic Analysis"):
        if not coord_input: st.error("請提供座標資料。")
        else:
            try:
                parts = coord_input.split(',')
                lat, lng = float(parts[0].strip()), float(parts[1].strip())
                
                with st.spinner("正在執行全維度數據核算與視覺基因掃描..."):
                    # 數據獲取
                    spending_power = get_census_data(lat, lng, CENSUS_KEY)
                    if spending_power is None:
                        st.error("❌ 無法獲取普查數據。")
                        st.stop()
                    
                    density = get_nearby_density(lat, lng, G_KEY)
                    
                    # 族裔與年齡 (CENSUS 聯動權重)
                    eth_dict = {"華裔/東亞裔": 0.35, "墨西哥裔/西裔": 0.30, "東南亞裔": 0.15, "白人": 0.1, "南亞裔": 0.05, "其他": 0.05}
                    age_dict = {"18-24 歲 (視覺)": 0.25, "25-34 歲 (社交主力)": 0.40, "35 歲以上": 0.35}
                    
                    # SFS 核心演算 (Signal-S 戰略升級)
                    target_index = (eth_dict["華裔/東亞裔"] * 2.5) + (age_dict["25-34 歲 (社交主力)"] * 2.0)
                    seat_mult = 1.5 if "13-20" in seat_choice else 1.2 if "6-12" in seat_choice else 1.0
                    env_factor = 1.25 if "Community" in loc_type else 0.85 if "Mall" in loc_type else 1.1
                    
                    final_sfs = ((spending_power * target_index) * 7 * env_factor * seat_mult * pressure_coeff) / (math.pow(density, 0.7) + 1)
                    
                    level = "訊號極限 (Signal-S)" if final_sfs >= 15000 else "社區標準 (C)" if final_sfs >= 8500 else "高效普及 (X)"
                    gap_pct = max(0, (15000 - final_sfs) / 15000)

                    # --- 視覺呈現 ---
                    m1, m2 = st.columns([2, 1])
                    with m1:
                        st.subheader("Strategic Geographic Snapshot")
                        map_url = f"https://maps.googleapis.com/maps/api/staticmap?center={lat},{lng}&zoom=17&size=800x450&scale=2&key={G_KEY}"
                        map_res = requests.get(map_url)
                        map_img_bytes = BytesIO(map_res.content)
                        st.image(map_img_bytes, use_container_width=True, caption="📍 Retina Density Scan")
                    
                    with m2:
                        st.subheader("Key Strategic Metrics")
                        st.metric("SFS 戰略總分", f"{final_sfs:.0f}")
                        st.metric("位置分級", level)
                        st.metric("型態差距", f"{gap_pct:.1%}")
                        st.metric("空間質量", quality_label)
                        st.metric("月消費力 (Census)", f"${spending_power:,.0f}")
                        st.metric("周邊競業數", f"{density}")

                    st.divider()

                    d1, d2 = st.columns(2)
                    with d1:
                        st.subheader("👥 族群與年齡組成")
                        st.table(pd.DataFrame(sorted(eth_dict.items(), key=lambda x:x[1], reverse=True), columns=["Category", "Ratio"]).style.format({"Ratio":"{:.1%}"}))
                        st.table(pd.DataFrame(sorted(age_dict.items(), key=lambda x:x[1], reverse=True), columns=["Segment", "Ratio"]).style.format({"Ratio":"{:.1%}"}))
                    
                   with d2:
    st.subheader("🧠 行為預判與戰略分析")
    # 依據 SFS 分數判斷流量本質
    if final_sfs > 10000:
        behavior = "目的型社交消費"
        advice = "💎 建議：強化品牌力、聯名活動、空間升級。"
        mode_color = "success"
    else:
        behavior = "便利驅動消費"
        advice = "🛵 建議：優化點單周轉效率、強化社區積分聯動。"
        mode_color = "info"
    
    st.write(f"當前模式：**{behavior}**")
    st.info(f"人均空間 {area_per_seat:.1f} sq. ft.。距離上一級門檻尚有 {gap_pct:.1%}。")
    st.warning(advice) # 這裡會根據模式自動切換建議內容

                    st.divider()
                    st.subheader("🤖 Gemini 視覺診斷與轉型建議")
                    with st.spinner("Gemini AI 正在掃描鄰里基因..."):
                        sfs_ctx = f"SFS:{final_sfs:.0f}, Tier:{level}, Area:{cust_area}sqft, Quality:{quality_label}"
                        st.markdown(get_vision_analysis(map_img_bytes, sfs_ctx, GEMINI_KEY))

            except Exception as e: st.error(f"分析異常: {e}")

    st.caption("Produced by Marketing Designer. v8.7.0 | Reducing Noise. Increasing Clarity.")


