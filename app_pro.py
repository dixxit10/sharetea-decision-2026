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
    .stApp { background-color: #0E0E0E; color: #E0E0E0; }
    .definition-box { 
        background-color: #1A1A1A; 
        border-left: 3px solid #00FF41; 
        padding: 15px; 
        margin-bottom: 10px; 
        border-radius: 4px; 
        font-size: 0.9em; 
    }
    div[data-testid="metric-container"] { 
        background-color: #1C1C1C; 
        border: 1px solid #333; 
        padding: 15px; 
        border-radius: 8px; 
        color: #fff; 
    }
    .stSpinner > div { border-top-color: #00FF41 !important; }
    
    /* 按鈕樣式 */
    div.stButton > button:first-child {
        background-color: #00FF41;
        color: #000000;
        font-weight: bold;
        border: none;
        width: 100%;
        padding: 0.6rem;
    }
    div.stButton > button:first-child:hover {
        background-color: #00CC33;
    }
    </style>
""", unsafe_allow_html=True)

# --- 1. 安全驗證 ---
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
    
    # 初始化 Session State
    if 'census_data' not in st.session_state:
        st.session_state['census_data'] = {
            'income': 50000, 
            'asian': 35, 'hispanic': 25, 'black': 10,
            'age_18_24': 20, 'age_25_34': 30
        }
    
    # --- 讀取 Keys ---
    def get_api_key(key_name):
        try: return st.secrets["api_keys"][key_name]
        except: return None

    G_KEY = get_api_key("GOOGLE_KEY")
    GEMINI_KEY = get_api_key("GEMINI_KEY")
    C_KEY = get_api_key("CENSUS_KEY")

    # --- 側邊欄 ---
    st.sidebar.header("📐 戰略參數輸入")
    
    location_input = st.sidebar.text_input(
        "目標位置 (地址 或 Lat,Lng):", 
        value="18558 Gale Ave, City of Industry, CA",
        help="輸入地址自動解析"
    )

    st.sidebar.markdown("#### 地段基因")
    env_type = st.sidebar.selectbox("選擇地段類型:", ["Shopping Mall", "Community", "Plaza", "Main Street", "Transit Hub", "Food Court"])
    env_mapping = {"Shopping Mall": 1.2, "Community": 1.0, "Plaza": 1.0, "Main Street": 0.8, "Transit Hub": 0.8, "Food Court": 0.8}
    env_weight = env_mapping[env_type]
    
    st.sidebar.markdown("#### 物理空間")
    cust_area = st.sidebar.slider("顧客活動空間 (sq. ft.):", 100, 600, 300)
    seat_choice = st.sidebar.radio("預計座位數:", ["0-5 席", "6-12 席", "13-20 席", "21 席以上"], index=1)
    
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

    # --- 專家校準 ---
    st.sidebar.markdown("---")
    with st.sidebar.expander("⚙️ 數據專家校準 (Calibration)", expanded=True):
        st.caption("手動修正 API 數據以符合商業直覺")
        cal_asian = st.slider("東亞裔 %", 0, 100, int(st.session_state['census_data']['asian']), key='slider_asian')
        cal_hispanic = st.slider("西裔 %", 0, 100, int(st.session_state['census_data']['hispanic']), key='slider_hispanic')
        cal_income = st.number_input("預估月收入 ($)", value=int(st.session_state['census_data']['income']), step=500, key='input_income')
        
    execute_btn = st.sidebar.button("啟動戰略分析 Execute", type="primary")

    # --- 工具函式 ---
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

    def fetch_census_api(lat, lng):
        if not C_KEY: return
        try:
            geo_url = f"https://geo.fcc.gov/api/census/area?lat={lat}&lon={lng}&format=json"
            fips_resp = requests.get(geo_url, timeout=5).json()
            if not fips_resp.get('results'): return
            fips = fips_resp['results'][0]['block_fips']
            vars = "B19013_001E,B01001_001E,B03002_006E,B03002_012E,B03002_004E,B01001_007E,B01001_011E"
            url = f"https://api.census.gov/data/2022/acs/acs5?get={vars}&for=tract:{fips[5:11]}&in=state:{fips[:2]}%20county:{fips[2:5]}&key={C_KEY}"
            r = requests.get(url, timeout=5)
            if r.status_code != 200: return
            d = r.json()[1]
            def safe_val(v): return int(v) if v else 0
            pop = safe_val(d[1]) or 1
            st.session_state['census_data'] = {
                'income': safe_val(d[0]) / 12 if safe_val(d[0]) > 0 else 4000,
                'asian': round((safe_val(d[2])/pop)*100),
                'hispanic': round((safe_val(d[3])/pop)*100),
                'black': round((safe_val(d[4])/pop)*100),
                'age_18_24': round((safe_val(d[5])/pop)*100),
                'age_25_34': round((safe_val(d[6])/pop)*100)
            }
            st.rerun()
        except: pass

    def get_density(lat, lng):
        if not G_KEY: return 5
        try:
            url = f"https://maps.googleapis.com/maps/api/place/nearbysearch/json?location={lat},{lng}&radius=1000&keyword=bubble tea&key={G_KEY}"
            res = requests.get(url, timeout=5).json()
            return len(res.get('results', []))
        except: return 5

    # --- 介面 ---
    st.title("📚 Sharetea 2026 戰略指標體系")
    
    if execute_btn:
        if not location_input:
            st.error("❌ 請輸入位置")
        else:
            with st.spinner("🛰️ 戰略數據運算中..."):
                lat, lng, address_found = resolve_location(location_input)
                
                if lat:
                    density = get_density(lat, lng)
                    
                    # 運算邏輯
                    income = cal_income
                    age_score = (st.session_state['census_data']['age_25_34'] * 2.5 + st.session_state['census_data']['age_18_24'] * 2.3) / 100
                    eth_score = (cal_asian * 3.0 + cal_hispanic * 1.5) / 100 
                    target_index = (eth_score + age_score)
                    if target_index < 1.0: target_index = 1.0
                    
                    final_sfs = ((income * target_index * env_weight) * 7 * pressure_coeff) / (math.pow(density + 1, 0.7))
                    
                    if cust_area < 250:
                        level = "高效普及 (eXpress-X)"
                        limit_msg = f"⚠️ 空間狹窄：建議以此區域之 X 店型營運。"
                    else:
                        if final_sfs >= 15000: level = "品牌指標 (Model-M)"
                        elif final_sfs >= 8500: level = "社區標準 (Community-C)"
                        else: level = "高效普及 (eXpress-X)"
                        limit_msg = f"✅ 空間條件適宜：{quality_status}"

                    # --- 1. 核心指標卡片 ---
                    m1, m2, m3, m4 = st.columns(4)
                    m1.metric("SFS 戰略總分", f"{int(final_sfs):,}", delta="核心指標")
                    m2.metric("位置分級", level, delta_color="off")
                    m3.metric("月消費力 (Income)", f"${int(income):,}")
                    m4.metric("周邊競業", f"{density} 家")
                    
                    if "⚠️" in limit_msg: st.warning(limit_msg)
                    else: st.success(limit_msg)
                    
                    st.divider()
                    
                    # --- 2. 視覺化圖表區 (Charts) ---
                    col_charts1, col_charts2, col_charts3 = st.columns(3)
                    
                    # 族裔組成圖表
                    with col_charts1:
                        st.markdown("**📊 族裔組成 (Ethnic)**")
                        # 準備數據
                        eth_data = {
                            "族裔": ["東亞裔", "西裔", "非裔", "其他"],
                            "比例": [cal_asian, cal_hispanic, st.session_state['census_data']['black'], 100 - (cal_asian+cal_hispanic+st.session_state['census_data']['black'])]
                        }
                        df_eth = pd.DataFrame(eth_data)
                        st.bar_chart(df_eth.set_index("族裔"), color="#00FF41") # 戰略綠

                    # 年齡組成圖表
                    with col_charts2:
                        st.markdown("**📊 年齡結構 (Age)**")
                        age_data = {
                            "年齡層": ["18-24", "25-34", "其他"],
                            "比例": [st.session_state['census_data']['age_18_24'], st.session_state['census_data']['age_25_34'], 100 - (st.session_state['census_data']['age_18_24'] + st.session_state['census_data']['age_25_34'])]
                        }
                        df_age = pd.DataFrame(age_data)
                        st.bar_chart(df_age.set_index("年齡層"), color="#3399FF") # 科技藍

                    # 空間與壓力可視化
                    with col_charts3:
                        st.markdown("**📏 空間壓力 (Pressure)**")
                        st.metric("人均面積", f"{area_per_seat:.1f} sqft")
                        # 製作一個進度條來表示擁擠度 (以 35sqft 為滿分基準)
                        progress_val = min(area_per_seat / 40.0, 1.0)
                        st.progress(progress_val)
                        if area_per_seat < 15:
                            st.caption("🔴 嚴重過載 (<15)")
                        elif area_per_seat < 25:
                            st.caption("🟡 體驗密集 (15-25)")
                        else:
                            st.caption("🟢 體驗舒適 (>25)")

                    st.divider()

                    # --- 3. 地圖與 AI ---
                    col_map, col_ai = st.columns([1, 1])
                    
                    packet = {
                        "地址": address_found,
                        "SFS": int(final_sfs),
                        "分級": level,
                        "地段": env_type,
                        "收入": f"${income}",
                        "人均面積": f"{area_per_seat} sqft",
                        "密度": density
                    }
                    
                    with col_map:
                        if G_KEY:
                            map_url = f"https://maps.googleapis.com/maps/api/staticmap?center={lat},{lng}&zoom=18&size=640x640&scale=2&maptype=roadmap&markers=color:red%7C{lat},{lng}&key={G_KEY}"
                            try:
                                img_data = requests.get(map_url).content
                                map_bytes = BytesIO(img_data)
                                st.image(map_bytes, caption="📍 戰略座標", use_container_width=True)
                            except: st.error("地圖載入失敗")
                            
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
                            1. **地段視覺驗證**：用戶設定為[{env_type}]，請看圖確認建築密度與道路是否吻合？
                            2. **營運策略**：針對月收 {income} 與 SFS {int(final_sfs)} 的區域，給出具體營運建議。
                            3. **空間建議**：人均 {area_per_seat} sqft，請給出設計上的放大空間感建議。
                            """
                            with st.spinner("AI 分析中..."):
                                map_bytes.seek(0)
                                res = model.generate_content([prompt, Image.open(map_bytes)])
                                st.markdown(res.text)
                        else: st.warning("AI 未啟動")

    st.sidebar.markdown("---")
    if st.sidebar.button("🔄 重置為 Census API 原始數據"):
        lat, lng, _ = resolve_location(location_input)
        if lat:
            with st.spinner("正在連線 US Census Bureau..."):
                fetch_census_api(lat, lng)
