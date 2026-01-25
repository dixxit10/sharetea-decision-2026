import streamlit as st
import pandas as pd
import math
import requests
import google.generativeai as genai
from io import BytesIO
from PIL import Image

# --- 0. 系統配置 ---
st.set_page_config(page_title="Sharetea Express 2026 戰略診斷", layout="wide")

st.markdown("""
    <style>
    /* 全域背景 */
    .stApp { background-color: #0E0E0E; color: #E0E0E0; }
    
    /* 定義框 */
    .definition-box { 
        background-color: #1A1A1A; 
        border-left: 3px solid #00FF41; 
        padding: 15px; 
        margin-bottom: 10px; 
        border-radius: 4px; 
        font-size: 0.9em; 
    }
    
    /* 指標卡片 */
    div[data-testid="metric-container"] { 
        background-color: #1C1C1C; 
        border: 1px solid #333; 
        padding: 15px; 
        border-radius: 8px; 
        color: #fff; 
    }
    
    /* Loading 動畫 */
    .stSpinner > div { border-top-color: #00FF41 !important; }
    
    /* 執行按鈕 */
    div.stButton > button:first-child {
        background-color: #00FF41;
        color: #000000;
        font-weight: bold;
        border: none;
        width: 100%;
        padding: 0.8rem;
        font-size: 1.1em;
    }
    div.stButton > button:first-child:hover {
        background-color: #00CC33;
    }
    </style>
""", unsafe_allow_html=True)

# --- 1. 安全驗證 (Form 表單穩定版) ---
def check_password():
    if st.session_state.get("password_correct", False):
        return True
    try:
        correct_pwd = st.secrets["general"]["APP_PASSWORD"]
    except:
        correct_pwd = "sharetea2026"

    with st.form("login_form"):
        st.markdown("### 🔐 Sharetea 系統門禁")
        input_pwd = st.text_input("Security Access Code", type="password")
        submit_button = st.form_submit_button("開啟戰略引擎")

    if submit_button:
        if input_pwd == correct_pwd:
            st.session_state["password_correct"] = True
            st.rerun()
        else:
            st.error("😕 密碼錯誤")
    return False

# --- 主程式 ---
if check_password():
    
    # --- 2. 讀取 Keys ---
    def get_api_key(key_name):
        try: return st.secrets["api_keys"][key_name]
        except: return None

    G_KEY = get_api_key("GOOGLE_KEY")
    GEMINI_KEY = get_api_key("GEMINI_KEY")
    C_KEY = get_api_key("CENSUS_KEY")

    # --- 3. 側邊欄輸入區 (精簡版) ---
    st.sidebar.header("📐 戰略參數輸入")
    
    # 3.1 地址輸入
    location_input = st.sidebar.text_input(
        "目標位置 (地址 或 Lat,Lng):", 
        value="18558 Gale Ave, City of Industry, CA",
        help="輸入地址自動解析"
    )

    # 3.2 地段基因選單
    st.sidebar.markdown("#### 地段基因 (Environment)")
    env_type = st.sidebar.selectbox(
        "選擇地段類型:",
        ["Shopping Mall", "Community", "Plaza", "Main Street", "Transit Hub", "Food Court"]
    )
    # 定義權重
    env_mapping = {
        "Shopping Mall": 1.2,
        "Community": 1.0, 
        "Plaza": 1.0,
        "Main Street": 0.8,
        "Transit Hub": 0.8,
        "Food Court": 0.8
    }
    env_weight = env_mapping[env_type]
    
    # 3.3 物理空間
    st.sidebar.markdown("#### 物理空間")
    cust_area = st.sidebar.slider("顧客活動空間 (sq. ft.):", 100, 600, 300)
    seat_choice = st.sidebar.radio("預計座位數:", ["0-5 席", "6-12 席", "13-20 席", "21 席以上"], index=1)
    
    # 計算人均空間 & 壓力係數
    est_seats = 5 if "0-5" in seat_choice else 12 if "6-12" in seat_choice else 20 if "13-20" in seat_choice else 30
    area_per_seat = cust_area / est_seats if est_seats > 0 else 0
    
    if area_per_seat >= 35:
        pressure_coeff = 1.2
        quality_status = "✨ 極致清晰 (Visual Clarity)"
        q_color = "#00FF41"
    elif area_per_seat >= 25:
        pressure_coeff = 1.0
        quality_status = "✅ 標準質感 (Standard)"
        q_color = "#3399FF"
    elif area_per_seat >= 15:
        pressure_coeff = 0.75
        quality_status = "⚠️ 體驗過載 (Overload)"
        q_color = "#FFAA00"
    else:
        pressure_coeff = 0.5
        quality_status = "🚨 嚴重雜訊 (Noise)"
        q_color = "#FF3333"
    
    st.sidebar.markdown(f"判定: <span style='color:{q_color}; font-weight:bold;'>{quality_status}</span>", unsafe_allow_html=True)
    st.sidebar.caption(f"地段權重: {env_weight}x | 壓力補償: {pressure_coeff}x")

    # 3.4 執行按鈕
    st.sidebar.markdown("---")
    execute_btn = st.sidebar.button("啟動戰略分析 Execute", type="primary")

    # --- 4. 核心工具函式 ---
    def resolve_location(input_str):
        if not G_KEY: return None, None, "No API Key"
        try:
            if "," in input_str and any(c.isdigit() for c in input_str):
                try:
                    parts = input_str.split(',')
                    if len(parts) >= 2:
                        return float(parts[0].strip()), float(parts[1].strip()), f"座標: {input_str}"
                except: pass
            
            url = f"https://maps.googleapis.com/maps/api/geocode/json?address={input_str}&key={G_KEY}"
            resp = requests.get(url, timeout=10).json()
            if resp['status'] == 'OK':
                loc = resp['results'][0]['geometry']['location']
                return loc['lat'], loc['lng'], resp['results'][0]['formatted_address']
            return None, None, None
        except: return None, None, None

    def get_census_data(lat, lng):
        """直接回傳 API 數據 (如果失敗則回傳預設值)"""
        # 預設數據 (Fallback)
        default_data = {
            'income': 50000,
            'eth': {'東亞裔': 0.35, '西裔': 0.25, '非裔': 0.1, '其他': 0.3},
            'age': {'18-24': 0.2, '25-34': 0.3, '其他': 0.5},
            'source': "Estimated (API Unavailable)"
        }

        if not C_KEY: return default_data
        
        try:
            # FCC API
            geo_url = f"https://geo.fcc.gov/api/census/area?lat={lat}&lon={lng}&format=json"
            fips_resp = requests.get(geo_url, timeout=5).json()
            if not fips_resp.get('results'): return default_data
            fips = fips_resp['results'][0]['block_fips']
            
            # Census API
            vars = "B19013_001E,B01001_001E,B03002_006E,B03002_012E,B03002_004E,B01001_007E,B01001_011E"
            url = f"https://api.census.gov/data/2022/acs/acs5?get={vars}&for=tract:{fips[5:11]}&in=state:{fips[:2]}%20county:{fips[2:5]}&key={C_KEY}"
            
            r = requests.get(url, timeout=5)
            if r.status_code != 200: return default_data
            d = r.json()[1]
            
            def safe_val(v): return int(v) if v else 0
            pop = safe_val(d[1]) or 1
            
            # 計算真實數據
            return {
                'income': safe_val(d[0]) / 12 if safe_val(d[0]) > 0 else 4500,
                'eth': {
                    '東亞裔': round(safe_val(d[2])/pop, 3),
                    '西裔': round(safe_val(d[3])/pop, 3),
                    '非裔': round(safe_val(d[4])/pop, 3),
                    '其他': round((pop - safe_val(d[2]) - safe_val(d[3]) - safe_val(d[4]))/pop, 3)
                },
                'age': {
                    '18-24': round(safe_val(d[5])/pop, 3),
                    '25-34': round(safe_val(d[6])/pop, 3),
                    '其他': round((pop - safe_val(d[5]) - safe_val(d[6]))/pop, 3)
                },
                'source': "Official Census Data"
            }
        except:
            return default_data

    def get_density(lat, lng):
        if not G_KEY: return 5
        try:
            url = f"https://maps.googleapis.com/maps/api/place/nearbysearch/json?location={lat},{lng}&radius=1000&keyword=bubble tea&key={G_KEY}"
            res = requests.get(url, timeout=5).json()
            return len(res.get('results', []))
        except: return 5

    # --- 5. 主介面 ---
    st.title("📚 Sharetea 2026 戰略指標體系")
    st.latex(r"SFS = \frac{(Income \times TargetIndex \times EnvWeight) \times 7 \times PressureCoeff}{Density^{0.7} + 1}")
    
    # 定義說明
    c1, c2, c3 = st.columns(3)
    c1.markdown("<div class='definition-box'><b>SFS 戰略總分</b><br>整合消費力、族群權重、地段基因與空間壓力。</div>", unsafe_allow_html=True)
    c2.markdown("<div class='definition-box'><b>空間體感質量</b><br>直接決定品牌體驗的物理上限 (過載/標準/清晰)。</div>", unsafe_allow_html=True)
    c3.markdown("<div class='definition-box'><b>位置分級基準</b><br>M: 15k+ / C: 8.5k+ / X: < 8.5k。</div>", unsafe_allow_html=True)

    # --- 6. 執行邏輯 ---
    if execute_btn:
        if not location_input:
            st.error("❌ 請輸入位置")
        else:
            with st.spinner("🛰️ 戰略數據運算與衛星掃描中..."):
                # 1. 解析地址
                lat, lng, address_found = resolve_location(location_input)
                
                if lat:
                    # 2. 獲取數據
                    census_res = get_census_data(lat, lng)
                    density = get_density(lat, lng)
                    
                    income = census_res['income']
                    eth = census_res['eth']
                    age = census_res['age']
                    
                    # 3. SFS 運算
                    age_score = (age['25-34'] * 2.5 + age['18-24'] * 2.3) / 100
                    eth_score = (eth['東亞裔'] * 3.0 + eth['西裔'] * 1.5) / 100 
                    target_index = (eth_score + age_score)
                    if target_index < 1.0: target_index = 1.0
                    
                    final_sfs = ((income * target_index * env_weight) * 7 * pressure_coeff) / (math.pow(density + 1, 0.7))
                    
                    # 4. 判定分級
                    if cust_area < 250:
                        level = "高效普及 (eXpress-X)"
                        limit_msg = f"⚠️ 空間狹窄：建議以此區域之 X 店型營運。"
                    else:
                        if final_sfs >= 15000: level = "品牌指標 (Model-M)"
                        elif final_sfs >= 8500: level = "社區標準 (Community-C)"
                        else: level = "高效普及 (eXpress-X)"
                        limit_msg = f"✅ 空間條件適宜：{quality_status}"

                    # 5. 核心指標卡片
                    m1, m2, m3, m4 = st.columns(4)
                    m1.metric("SFS 戰略總分", f"{int(final_sfs):,}", delta="核心指標")
                    m2.metric("位置分級", level, delta_color="off")
                    m3.metric("月消費力 (Income)", f"${int(income):,}")
                    m4.metric("地段基因", f"{env_type} ({env_weight}x)")
                    
                    if "⚠️" in limit_msg: st.warning(limit_msg)
                    else: st.success(limit_msg)
                    
                    if census_res['source'] != "Official Census Data":
                        st.caption(f"ℹ️ 提示：{census_res['source']}")

                    st.divider()
                    
                    # --- 6. 視覺化圖表區 ---
                    col_charts1, col_charts2, col_charts3 = st.columns(3)
                    
                    with col_charts1:
                        st.markdown("**📊 族裔組成 (Ethnic)**")
                        st.bar_chart(pd.DataFrame(eth.items(), columns=["族裔", "比例"]).set_index("族裔"), color="#00FF41")

                    with col_charts2:
                        st.markdown("**📊 年齡結構 (Age)**")
                        st.bar_chart(pd.DataFrame(age.items(), columns=["年齡層", "比例"]).set_index("年齡層"), color="#3399FF")

                    with col_charts3:
                        st.markdown("**📏 空間壓力 (Pressure)**")
                        st.metric("人均面積", f"{area_per_seat:.1f} sqft")
                        progress_val = min(area_per_seat / 40.0, 1.0)
                        st.progress(progress_val)
                        st.caption(f"競業密度: {density} 家/km")

                    st.divider()

                    # --- 7. 地圖與 AI 視覺分析 ---
                    col_map, col_ai = st.columns([1, 1])
                    
                    packet = {
                        "地址": address_found,
                        "SFS": int(final_sfs),
                        "分級": level,
                        "地段": env_type,
                        "月收": f"${income:,.0f}",
                        "人均面積": f"{area_per_seat} sqft",
                        "密度": density,
                        "族裔": eth
                    }
                    
                    map_bytes = None
                    with col_map:
                        if G_KEY:
                            map_url = f"https://maps.googleapis.com/maps/api/staticmap?center={lat},{lng}&zoom=18&size=640x640&scale=2&maptype=roadmap&markers=color:red%7C{lat},{lng}&key={G_KEY}"
                            try:
                                img_data = requests.get(map_url).content
                                map_bytes = BytesIO(img_data)
                                st.image(map_bytes, caption="📍 戰略座標快照", use_container_width=True)
                                st.json(packet)
                            except: st.error("地圖載入失敗")
                        else: st.warning("無地圖 (Missing Key)")
                            
                    with col_ai:
                        if map_bytes and GEMINI_KEY:
                            st.subheader("🤖 Gemini 3 戰略解析")
                            genai.configure(api_key=GEMINI_KEY)
                            try: model = genai.GenerativeModel('gemini-3-flash-preview')
                            except: model = genai.GenerativeModel('gemini-1.5-flash')
                            
                            prompt = f"""
                            角色：Sharetea 2026 戰略專家。
                            數據包：{packet}
                            任務：
                            1. **地段視覺驗證**：用戶設定此地為 [{env_type}]，請觀察衛星圖中的建築密度、道路寬度與停車場配置，判斷這是否準確？(例如設定 Mall 但看起來像街邊)。
                            2. **戰略執行**：針對此區域的 SFS 分數與族裔結構，給出具體的行銷建議。
                            3. **空間設計**：針對人均 {area_per_seat} sqft 的空間，給出設計上的放大空間感建議。
                            """
                            with st.spinner("AI 正在閱讀地圖紋理..."):
                                map_bytes.seek(0)
                                res = model.generate_content([prompt, Image.open(map_bytes)])
                                st.markdown(res.text)
                        else: st.warning("AI 未啟動 (缺少 Key 或 地圖)")
