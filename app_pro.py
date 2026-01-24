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
        st.title("🔐 Sharetea 系統門禁")
        password = st.text_input("請輸入密碼以開啟引擎", type="password", key="password_gate")
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
    st.title("📚 名詞定義 v8.8.8")
    st.markdown("<p style='color: #8B949E; font-size: 1.2em; margin-top: -15px;'>Reducing Noise. Increasing Clarity.</p>", unsafe_allow_html=True)

    st.markdown("<div class='formula-display'>", unsafe_allow_html=True)
    st.latex(r"SFS = \frac{(Spending Power \times Target Index) \times 7 \times Env Factor \times Scale Mult \times Pressure Coeff}{Density^{0.7} + 1}")
    st.markdown("</div>", unsafe_allow_html=True)

    def_col1, def_col2, def_col3 = st.columns(3)
    with def_col1:
        st.markdown("<div class='definition-box'><b>SFS 戰略總分</b><br>量化地段潛力的核心指標。整合動態消費力、即時族群權重、空間壓力與 AI 視覺診斷。</div>", unsafe_allow_html=True)
        st.markdown("<div class='definition-box'><b>空間壓力係數 (Pressure Coeff)</b><br>根據 ADA 標準，當人均面積低於 25 sq. ft. 時，判定為體驗雜訊並下修分值。</div>", unsafe_allow_html=True)
    with def_col2:
        st.markdown("<div class='definition-box'><b>環境與地段基因</b><br>透過 Gemini 視覺掃描靜態地圖，識別鄰里質感與視覺雜訊 (如汽修廠、加油站)。</div>", unsafe_allow_html=True)
        st.markdown("<div class='definition-box'><b>月均基礎消費力</b><br>實時連動 CENSUS API。代表普查區月收入中位數，決定產品溢價空間。</div>", unsafe_allow_html=True)
    with def_col3:
        st.markdown("<div class='definition-box'><b>位置分級基準</b><br>訊號極限 (Signal-S): 15000+<br>社區標準 (C): 8500+<br>高效普及 (X): < 8500</div>", unsafe_allow_html=True)
        st.markdown("<div class='definition-box'><b>顧客活動區 (200-460 sqft)</b><br>精確定義顧客使用範圍，排除工作區、吧台後方雜訊。</div>", unsafe_allow_html=True)

    st.divider()

    # --- 3. 配置與輔助函數 ---
    G_KEY = st.secrets.get("GOOGLE_KEY")
    GEMINI_KEY = st.secrets.get("GEMINI_KEY")
    CENSUS_KEY = st.secrets.get("CENSUS_KEY")

    def get_census_full_profile(lat, lng, api_key):
        try:
            # 1. 取得 FIPS 碼
            geo_url = f"https://geo.fcc.gov/api/census/area?lat={lat}&lon={lng}&format=json"
            geo_res = requests.get(geo_url).json()
            fips = geo_res['results'][0]['block_fips']
            state, county, tract = fips[:2], fips[2:5], fips[5:11]
            
            # 2. 聯動 Census API (精確抓取族裔 B03002 與 詳細年齡 B01001)
            # 包含：華裔/東亞、東南亞、西裔、南亞、白人
            vars = "B19013_001E,B01001_001E,B03002_006E,B03002_004E,B03002_003E,B03002_012E,B03002_005E," + \
                   "B01001_007E,B01001_008E,B01001_009E,B01001_010E,B01001_031E,B01001_032E,B01001_033E,B01001_034E," + \
                   "B01001_011E,B01001_012E,B01001_035E,B01001_036E"
            
            census_url = f"https://api.census.gov/data/2022/acs/acs5?get={vars}&for=tract:{tract}&in=state:{state}%20county:{county}&key={api_key}"
            res = requests.get(census_url).json()
            d = res[1]
            
            total_pop = int(d[1])
            income = int(d[0]) / 12
            
            eth = {
                "華裔/東亞裔": int(d[2]) / total_pop if total_pop > 0 else 0,
                "墨西哥裔/西裔": int(d[3]) / total_pop if total_pop > 0 else 0,
                "白人": int(d[4]) / total_pop if total_pop > 0 else 0,
                "東南亞裔": int(d[5]) / total_pop if total_pop > 0 else 0,
                "南亞裔": int(d[6]) / total_pop if total_pop > 0 else 0
            }
            
            age_18_24 = sum(int(x) for x in d[7:15])
            age_25_34 = sum(int(x) for x in d[15:19])
            
            age_profile = {
                "18-24 歲 (視覺打卡)": age_18_24 / total_pop if total_pop > 0 else 0,
                "25-34 歲 (社交主力)": age_25_34 / total_pop if total_pop > 0 else 0,
                "35 歲以上 (穩定客群)": (total_pop - age_18_24 - age_25_34) / total_pop if total_pop > 0 else 0
            }
            
            return income, eth, age_profile
        except: return None, None, None

    def get_nearby_density(lat, lng, key):
        try:
            url = f"https://maps.googleapis.com/maps/api/place/nearbysearch/json?location={lat},{lng}&radius=800&type=restaurant&key={key}"
            res = requests.get(url).json()
            return len(res.get('results', []))
        except: return 0

    def get_vision_analysis(image_bytes, sfs_context, api_key):
        try:
            genai.configure(api_key=api_key)
            model = genai.GenerativeModel('gemini-1.5-flash')
            img = Image.open(image_bytes)
            prompt = f"""
            依照營運、行銷、設計角度，請判讀地圖截圖中的『視覺雜訊』與『鄰里基因』。
            數據場景：{sfs_context}
            核心任務：識別地圖上的店家機能型態。判斷此區是快餐導向、辦公鄰里、還是質感社交型態。
            1.【位置分級基準】：分析當前 SFS 分級是否與視覺環境有落差？原因為何 (例如汽修廠與加油站的雜訊干擾)？
            2.【執行方向】：針對詳細人口組成，提供簡易執行建議：
               - 營運：動線效率與產品組合。
               - 行銷：聯名對接與族群觸達。
               - 設計：視覺屏蔽與氛圍降噪。
            """
            response = model.generate_content([prompt, img])
            return response.text
        except: return "視覺診斷暫時不可用。"

    # --- 4. 側邊欄輸入 ---
    st.sidebar.header("查詢資料輸入(美國區域)")
    coord_input = st.sidebar.text_input("📍座標輸入 (緯度, 經度):", placeholder="34.1425, -118.0483")
    loc_type = st.sidebar.selectbox("地點型態:", ["Plaza", "Shopping Mall", "Main Street", "Community"])

    st.sidebar.markdown("---")
    cust_area = st.sidebar.slider("顧客活動空間 (sq. ft.):", 200, 460, 300)
    seat_choice = st.sidebar.radio("座位數:", ["0-5 席", "6-12 席", "13-20 席"])

    est_seats = 5 if "0-5" in seat_choice else 12 if "6-12" in seat_choice else 20
    area_per_seat = cust_area / est_seats
    pressure_coeff = 1.2 if area_per_seat >= 30 else 1.0 if area_per_seat >= 25 else 0.75
    quality_label = "✨ 極致清晰" if pressure_coeff == 1.2 else "✅ 標準質感" if pressure_coeff == 1.0 else "⚠️ 體驗過載"

    # --- 5. 核心執行 ---
    if st.sidebar.button("Execute Strategic Analysis"):
        if not coord_input or "," not in coord_input: st.error("請提供正確座標 (緯度, 經度)。")
        else:
            try:
                parts = coord_input.split(',')
                lat, lng = float(parts[0].strip()), float(parts[1].strip())
                
                with st.spinner("正在執行全維度數據核算與視覺基因掃描...請稍後"):
                    # 1. 動態連線數據
                    spending_power, dynamic_eth, dynamic_age = get_census_full_profile(lat, lng, CENSUS_KEY)
                    if spending_power is None:
                        st.error("❌ 無法獲取該地段普查數據。請確認座標在美國境內且經度為負數。")
                        st.stop()
                    
                    real_density = get_nearby_density(lat, lng, G_KEY)
                    
                    # 2. 戰略演算
                    target_index = (dynamic_eth.get("華裔/東亞裔", 0) * 2.5) + (dynamic_age.get("25-34 歲 (社交主力)", 0) * 3.0)
                    seat_mult = 1.5 if "13-20" in seat_choice else 1.2 if "6-12" in seat_choice else 1.0
                    env_factor = 1.25 if "Community" in loc_type else 1.1
                    
                    final_sfs = ((spending_power * target_index) * 7 * env_factor * seat_mult * pressure_coeff) / (math.pow(real_density + 1, 0.7))
                    level = "訊號極限 (Signal-S)" if final_sfs >= 15000 else "社區標準 (C)" if final_sfs >= 8500 else "高效普及 (X)"
                    gap_pct = max(0, (15000 - final_sfs) / 15000)

                    # --- 渲染結果 ---
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
                        st.metric("型態差距 (Gap)", f"{gap_pct:.1%}")
                        st.metric("月消費力 (Census)", f"${spending_power:,.0f}")
                        st.metric("周邊競業數", f"{real_density}")

                    st.divider()
                    d1, d2 = st.columns(2)
                    with d1:
                        st.subheader("👥 實時族群組成 (Census API)")
                        st.table(pd.DataFrame(sorted(dynamic_eth.items(), key=lambda x:x[1], reverse=True), columns=["族裔", "比例"]).style.format({"比例":"{:.1%}"}))
                        st.subheader("🎂 詳細年齡組成")
                        st.table(pd.DataFrame(dynamic_age.items(), columns=["年齡段", "比例"]).style.format({"比例":"{:.1%}"}))
                    
                    with d2:
                        st.subheader("🧠 行為預判與戰略分析")
                        behavior = "目的型社交消費" if final_sfs > 10000 else "便利驅動消費"
                        if dynamic_age.get("25-34 歲 (社交主力)", 0) > 0.3:
                            advice = "💎 核心建議：高社交主力區。重點在於『視覺降噪』與屏蔽外部機能雜訊，建立品牌綠洲。"
                        elif dynamic_age.get("18-24 歲 (視覺打卡)", 0) > 0.3:
                            advice = "📸 核心建議：打卡熱門區。強化 Miffy 聯名視覺張力與外部招牌清晰度。"
                        else:
                            advice = "🛵 核心建議：穩定客群區。優化動線效率與標準化機能家具配置。"
                        
                        st.write(f"當前模式：**{behavior}**")
                        st.info(f"人均空間 {area_per_seat:.1f} sq. ft.。")
                        st.warning(advice)

                    st.divider()
                    st.subheader("🤖 Gemini 視覺診斷與轉型建議")
                    with st.spinner("AI 正在分析地圖質感..."):
                        sfs_ctx = f"SFS:{final_sfs:.0f}, Tier:{level}, Density:{real_density}, Age_Peak: 25-34"
                        st.markdown(get_vision_analysis(map_img_bytes, sfs_ctx, GEMINI_KEY))

            except Exception as e: st.error(f"分析異常: {e}")

    st.caption("Produced by Marketing Designer. v8.8.8 | Reducing Noise. Increasing Clarity.")
