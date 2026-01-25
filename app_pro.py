import streamlit as st
import pandas as pd
import math
import requests
import google.generativeai as genai
from io import BytesIO
from PIL import Image

# --- 0. 系統配置與 CSS ---
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
    label { color: #fff !important; }
    .stSpinner > div { border-top-color: #00FF41 !important; }
    
    /* 修正按鈕樣式，確保明顯 */
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

# --- 1. 安全驗證邏輯 (Form 表單版 - 穩定不崩潰) ---
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

# --- 主程式開始 ---
if check_password():
    
    # --- 2. 讀取 API Keys ---
    def get_api_key(key_name):
        try:
            return st.secrets["api_keys"][key_name]
        except:
            return None

    G_KEY = get_api_key("GOOGLE_KEY")
    GEMINI_KEY = get_api_key("GEMINI_KEY")
    C_KEY = get_api_key("CENSUS_KEY")

    if not G_KEY:
        st.warning("⚠️ 警告：未偵測到 Google Maps API Key")

    # --- 3. 側邊欄輸入區 (完整還原) ---
    st.sidebar.header("📐 戰略參數輸入")
    
    # 3.1 地點輸入
    location_input = st.sidebar.text_input(
        "目標位置 (地址 或 Lat,Lng):", 
        value="18558 Gale Ave, City of Industry, CA",
        help="輸入完整地址自動解析，或輸入 '緯度,經度'"
    )
    
    # 3.2 [還原] 地段基因下拉選單
    st.sidebar.markdown("#### 地段基因 (Environment)")
    env_type = st.sidebar.selectbox(
        "選擇地段類型:",
        ["Shopping Mall", "Community", "Plaza", "Main Street", "Transit Hub", "Food Court"]
    )
    
    # 定義地段權重 (Env Weight)
    env_mapping = {
        "Shopping Mall": 1.2,
        "Community": 1.0,
        "Plaza": 1.0,
        "Main Street": 0.8,
        "Transit Hub": 0.8,
        "Food Court": 0.8
    }
    env_weight = env_mapping[env_type]
    
    # 3.3 物理空間參數
    st.sidebar.markdown("#### 物理空間")
    cust_area = st.sidebar.slider("顧客活動空間 (sq. ft.):", 100, 600, 300)
    seat_choice = st.sidebar.radio("預計座位數:", ["0-5 席", "6-12 席", "13-20 席", "21 席以上"], index=1)
    
    # 計算人均空間與壓力係數
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

    # 3.4 [還原] 執行按鈕 (放在側邊欄最下方)
    st.sidebar.markdown("---")
    execute_btn = st.sidebar.button("啟動戰略分析 Execute", type="primary")

    # --- 4. 核心工具函式 ---
    def resolve_location(input_str):
        if not G_KEY: return None, None, "API Key Missing"
        try:
            if "," in input_str and any(c.isdigit() for c in input_str):
                try:
                    parts = input_str.split(',')
                    if len(parts) >= 2:
                        lat = float(parts[0].strip())
                        lng = float(parts[1].strip())
                        return lat, lng, f"座標: {lat}, {lng}"
                except ValueError:
                    pass 
            url = f"https://maps.googleapis.com/maps/api/geocode/json?address={input_str}&key={G_KEY}"
            resp = requests.get(url, timeout=10).json()
            if resp['status'] == 'OK':
                loc = resp['results'][0]['geometry']['location']
                fmt_addr = resp['results'][0]['formatted_address']
                return loc['lat'], loc['lng'], fmt_addr
            return None, None, None
        except: return None, None, None

    def get_census_data(lat, lng):
        if not C_KEY: return 5000, 2000, {}, {}, "Simulated (No Key)"
        try:
            geo_url = f"https://geo.fcc.gov/api/census/area?lat={lat}&lon={lng}&format=json"
            fips_resp = requests.get(geo_url, timeout=5).json()
            if not fips_resp.get('results'): raise Exception("Outside US")
            fips = fips_resp['results'][0]['block_fips']
            
            vars = "B19013_001E,B01001_001E,B03002_006E,B03002_012E,B03002_004E,B01001_007E,B01001_011E"
            url = f"https://api.census.gov/data/2022/acs/acs5?get={vars}&for=tract:{fips[5:11]}&in=state:{fips[:2]}%20county:{fips[2:5]}&key={C_KEY}"
            r = requests.get(url, timeout=5)
            if r.status_code != 200: raise Exception("Census Error")
            d = r.json()[1]
            
            def safe_int(val):
                try: return int(val)
                except: return 0

            pop = safe_int(d[1])
            pop = 1 if pop == 0 else pop
            income = safe_int(d[0])
            income = 50000 if income == 0 else income
            
            eth = {"東亞裔": round(safe_int(d[2])/pop, 3), "西裔": round(safe_int(d[3])/pop, 3), "非裔": round(safe_int(d[4])/pop, 3)}
            age = {"18-24": round(safe_int(d[5])/pop, 3), "25-34": round(safe_int(d[6])/pop, 3)}
            return income/12, pop, eth, age, "Official Census Data"
        except:
            return 5000, 2000, {"東亞裔": 0.35, "西裔": 0.25, "非裔": 0.1}, {"18-24": 0.2, "25-34": 0.3}, "Estimated (Simulation)"

    def get_density(lat, lng):
        if not G_KEY: return 5
        try:
            url = f"https://maps.googleapis.com/maps/api/place/nearbysearch/json?location={lat},{lng}&radius=1000&keyword=bubble tea&key={G_KEY}"
            res = requests.get(url, timeout=5).json()
            return len(res.get('results', []))
        except: return 5

    # --- 5. 主畫面標題 ---
    st.title("📚 Sharetea 2026 戰略指標體系")
    st.latex(r"SFS = \frac{(Income \times TargetIndex \times EnvWeight) \times 7 \times PressureCoeff}{Density^{0.7} + 1}")
    
    c1, c2, c3 = st.columns(3)
    c1.markdown("<div class='definition-box'><b>SFS 戰略總分</b><br>量化地段獲利天花板指標。整合消費力、族群權重、地段基因與空間壓力補償。</div>", unsafe_allow_html=True)
    c2.markdown("<div class='definition-box'><b>空間體感質量</b><br>基於人均面積判定：過載、標準、清晰。直接決定品牌體驗的物理上限。</div>", unsafe_allow_html=True)
    c3.markdown("<div class='definition-box'><b>位置分級基準</b><br>M: 15k+ / C: 8.5k+ / X: < 8.5k。SFS 達標但空間過載者將強制轉向 X 型態。</div>", unsafe_allow_html=True)

    # --- 6. 執行邏輯 (Execute) ---
    if execute_btn:
        if not location_input:
            st.error("❌ 請輸入地址或座標")
        else:
            with st.spinner("🛰️ 正在解析地址並同步衛星數據..."):
                # 1. 解析地址
                lat, lng, address_found = resolve_location(location_input)
                
                if lat is None:
                    st.error(f"❌ 無法解析位置：'{location_input}'。")
                else:
                    st.success(f"📍 已鎖定目標：{address_found}")
                    
                    try:
                        # 2. 獲取數據
                        income, pop, eth, age, data_source = get_census_data(lat, lng)
                        density = get_density(lat, lng)
                        
                        # 3. SFS 運算 (加入 env_weight)
                        target_index = (eth.get("東亞裔", 0) * 3.0) + (age.get("25-34", 0) * 2.5)
                        if target_index < 1.0: target_index = 1.1
                        
                        # [公式更新] 加入 User 選擇的 Env Weight
                        final_sfs = ((income * target_index * env_weight) * 7 * pressure_coeff) / (math.pow(density + 1, 0.7))
                        
                        # 4. 分級判定
                        if cust_area < 250:
                            level = "高效普及 (eXpress-X)"
                            limit_msg = f"⚠️ 空間狹窄 ({cust_area} sqft)：建議以此區域之 X 店型營運。"
                        else:
                            if final_sfs >= 15000: level = "品牌指標 (Model-M)"
                            elif final_sfs >= 8500: level = "社區標準 (Community-C)"
                            else: level = "高效普及 (eXpress-X)"
                            limit_msg = f"✅ 空間條件適宜：{quality_status}"

                        # 5. 顯示指標
                        m1, m2, m3, m4 = st.columns(4)
                        m1.metric("SFS 戰略總分", f"{int(final_sfs):,}")
                        m2.metric("位置分級", level)
                        m3.metric("地段權重", f"{env_weight}x ({env_type})") # 顯示地段選擇
                        m4.metric("周邊競業", f"{density} 家")
                        
                        if "⚠️" in limit_msg: st.warning(limit_msg)
                        else: st.success(limit_msg)
                        
                        st.divider()

                        # --- 7. 地圖與 AI ---
                        col_map, col_ai = st.columns([1, 1])
                        
                        strategic_packet = {
                            "地址": address_found,
                            "SFS總分": round(final_sfs),
                            "位置分級": level,
                            "地段基因": env_type, 
                            "地段權重": env_weight,
                            "體感質量": quality_status,
                            "月收入(中位)": f"${income:,.0f}",
                            "族裔結構": eth,
                            "人均面積": f"{area_per_seat:.1f} sqft",
                            "競爭密度": f"{density} 家/km"
                        }

                        if "Model (M)" in level:
                            dynamic_task = f"任務 (Model-M)：因地段屬性為 {env_type}，物理質量 {quality_status}。評估如何利用空間感撐起品牌溢價？"
                        elif "Community (C)" in level:
                            dynamic_task = f"任務 (Community-C)：地段為 {env_type}。評估空間是否足以支持長期停留與社交回購？針對族群 {eth} 建議行銷策略。"
                        else:
                            dynamic_task = f"任務 (eXpress-X)：地段為 {env_type}。如何利用極簡模組掩蓋擁擠感並提升轉換率？"

                        with col_map:
                            if G_KEY:
                                map_url = f"https://maps.googleapis.com/maps/api/staticmap?center={lat},{lng}&zoom=18&size=640x640&scale=2&maptype=roadmap&markers=color:red%7C{lat},{lng}&key={G_KEY}"
                                map_response = requests.get(map_url, timeout=10)
                                map_bytes = BytesIO(map_response.content)
                                st.image(map_bytes, caption=f"📍 戰略座標快照", use_container_width=True)
                                st.json(strategic_packet)
                            else:
                                st.warning("無地圖 (Missing Key)")
                                map_bytes = None
                        
                        with col_ai:
                            st.subheader("🤖 Gemini 3 Flash 全維度解析")
                            
                            if map_bytes and GEMINI_KEY:
                                genai.configure(api_key=GEMINI_KEY)
                                try:
                                    model = genai.GenerativeModel('gemini-3-flash-preview') 
                                except:
                                    model = genai.GenerativeModel('gemini-1.5-flash')
                                    st.toast("⚠️ Preview 模型連線不穩，已切換至 1.5 Flash")

                                prompt = f"""
                                角色：Sharetea 2026 戰略專家。
                                【數據包】：{strategic_packet}
                                
                                請結合「數據包」與「衛星地圖快照」進行診斷：
                                1. **視覺與地段吻合度**：使用者設定此地為 [{env_type}]，請觀察衛星圖中的建築密度與道路，判斷這是否準確？(例如設定 Mall 但看起來像街邊)
                                2. **戰略執行建議**：{dynamic_task}
                                3. **結論**：針對【營運】、【行銷】、【設計】三個維度，給予精準指令。
                                """
                                
                                with st.spinner("AI 正在視覺分析地圖紋理..."):
                                    map_bytes.seek(0)
                                    ai_image = Image.open(map_bytes)
                                    response = model.generate_content([prompt, ai_image])
                                    st.markdown(response.text)
                            else:
                                st.warning("無法執行 AI 分析")

                    except Exception as e:
                        st.error(f"系統執行錯誤: {str(e)}")
