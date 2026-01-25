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
    
    /* 驗證標籤 */
    .source-tag-success {
        background-color: #1c3323;
        border: 1px solid #238636;
        color: #3fb950;
        padding: 4px 8px;
        border-radius: 4px;
        font-size: 0.8em;
    }
    .source-tag-warning {
        background-color: #3d2c12;
        border: 1px solid #9e6a03;
        color: #d29922;
        padding: 4px 8px;
        border-radius: 4px;
        font-size: 0.8em;
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
    
    # --- 2. 讀取 Keys ---
    def get_api_key(key_name):
        try: return st.secrets["api_keys"][key_name]
        except: return None

    G_KEY = get_api_key("GOOGLE_KEY")
    GEMINI_KEY = get_api_key("GEMINI_KEY")
    C_KEY = get_api_key("CENSUS_KEY")

    # --- 3. 側邊欄輸入區 ---
    st.sidebar.header("📐 戰略參數輸入")
    
    location_input = st.sidebar.text_input(
        "目標位置 (地址 或 Lat,Lng):", 
        value="18558 Gale Ave, City of Industry, CA",
        help="輸入地址自動解析"
    )

    # 3.2 地段基因
    # st.sidebar.markdown("#### 地段基因 (Macro)")
    # env_type = st.sidebar.selectbox(
    #     "選擇地段類型:",
    #     ["Shopping Mall", "Community", "Plaza", "Main Street", "Transit Hub", "Food Court", "Office"]
    # )
    # env_mapping = {
    #     "Shopping Mall": 1.2, "Community": 1.0, "Plaza": 1.0, 
    #     "Main Street": 0.8, "Transit Hub": 0.8, "Food Court": 0.8, "Office": 0.8
    # }
    # env_weight = env_mapping[env_type]
    
    # 3.3 物理空間
    # st.sidebar.markdown("#### 物理空間 (Design Ref)")
    # cust_area = st.sidebar.slider("顧客活動空間 (sq. ft.):", 100, 600, 300)
    # seat_choice = st.sidebar.radio("預計座位數:", ["0-5 席", "6-12 席", "13-20 席", "21 席以上"], index=1)
    
    # est_seats = 5 if "0-5" in seat_choice else 12 if "6-12" in seat_choice else 20 if "13-20" in seat_choice else 30
    # area_per_seat = cust_area / est_seats if est_seats > 0 else 0
    
    # if area_per_seat >= 35:
    #     quality_status = "✨ 極致清晰 (Visual Clarity)"
    #     q_color = "#00FF41"
    # elif area_per_seat >= 25:
    #     quality_status = "✅ 標準質感 (Standard)"
    #     q_color = "#3399FF"
    # elif area_per_seat >= 15:
    #     quality_status = "⚠️ 體驗過載 (Overload)"
    #     q_color = "#FFAA00"
    # else:
    #     quality_status = "🚨 嚴重雜訊 (Noise)"
    #     q_color = "#FF3333"
    
    # st.sidebar.markdown(f"設計參考: <span style='color:{q_color}; font-weight:bold;'>{quality_status}</span>", unsafe_allow_html=True)
    # st.sidebar.caption(f"地段權重: {env_weight}x")

    st.sidebar.markdown("---")
    execute_btn = st.sidebar.button("啟動戰略分析 Execute", type="primary")

    # --- 4. 核心工具函式 ---
    
    @st.cache_data(ttl=3600) 
    def resolve_location_cached(input_str):
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

    @st.cache_data(ttl=3600)
    def get_census_data_cached(lat, lng):
        # 預設數據包含新標籤
        default_data = {
            'income': 50000,
            'eth': {'亞裔/華裔': 30.0, '西裔': 30.0, '白人': 20.0, '其他': 20.0},
            'age': {'18-24': 15.0, '25-34': 25.0, '35-45': 20.0, '其他': 40.0},
            'source': "Estimated (API Unavailable)"
        }
        if not C_KEY: return default_data
        
        try:
            geo_url = f"https://geo.fcc.gov/api/census/area?lat={lat}&lon={lng}&format=json"
            fips_resp = requests.get(geo_url, timeout=5).json()
            if not fips_resp.get('results'): return default_data
            fips = fips_resp['results'][0]['block_fips']
            
            vars = "B19013_001E,B01001_001E,B03002_006E,B03002_012E,B03002_004E,B03002_003E,B01001_007E,B01001_011E"
            url = f"https://api.census.gov/data/2022/acs/acs5?get={vars}&for=tract:{fips[5:11]}&in=state:{fips[:2]}%20county:{fips[2:5]}&key={C_KEY}"
            
            r = requests.get(url, timeout=5)
            if r.status_code != 200: return default_data
            d = r.json()[1]
            
            def safe_val(v): return int(v) if v else 0
            pop = safe_val(d[1]) or 1
            
            return {
                'income': safe_val(d[0]) / 12 if safe_val(d[0]) > 0 else 4500,
                'eth': {
                    '亞裔/華裔': round((safe_val(d[2])/pop)*100, 1),
                    '西裔': round((safe_val(d[3])/pop)*100, 1),
                    '白人': round((safe_val(d[5])/pop)*100, 1), 
                    '其他': round(((pop - safe_val(d[2]) - safe_val(d[3]) - safe_val(d[5]))/pop)*100, 1)
                },
                'age': {
                    '18-24': round((safe_val(d[6])/pop)*100, 1),
                    '25-34': round((safe_val(d[7])/pop)*100, 1),
                    '35-45': round(((pop - safe_val(d[6]) - safe_val(d[7]))/pop)*30, 1),
                    '其他': round(((pop - safe_val(d[6]) - safe_val(d[7]))/pop)*70, 1)
                },
                'source': "Official Census Data"
            }
        except:
            return default_data

    @st.cache_data(ttl=3600)
    def get_density_cached(lat, lng):
        if not G_KEY: return 5
        try:
            url = f"https://maps.googleapis.com/maps/api/place/nearbysearch/json?location={lat},{lng}&radius=1000&keyword=bubble tea&key={G_KEY}"
            res = requests.get(url, timeout=5).json()
            return len(res.get('results', []))
        except: return 5

    # --- 5. 主介面 ---
    st.title("📚 Sharetea 2026 戰略指標體系")
    # st.latex(r"SFS = \frac{(Income \times TargetIndex \times EnvWeight) \times 7}{Density^{0.7} + 1}")
    
    # 定義說明
    # c1, c2, c3 = st.columns(3)
    # c1.markdown("<div class='definition-box'><b>SFS 戰略總分</b><br>核心：亞裔/西裔/白人(2.5x)。25-34歲(2.5x) / 18-24(2.3x) / 35-45(2.0x)。</div>", unsafe_allow_html=True)
    # c2.markdown("<div class='definition-box'><b>空間體感質量 (參考)</b><br>設計師參考指標。基於人均面積判定：過載/標準/清晰。</div>", unsafe_allow_html=True)
    # c3.markdown("<div class='definition-box'><b>位置分級基準</b><br>M: 15k+ / C: 8.5k+ / X: < 8.5k。</div>", unsafe_allow_html=True)

    # --- 6. 執行邏輯 ---
    if execute_btn:
        if not location_input:
            st.error("❌ 請輸入位置")
        else:
            with st.spinner("🛰️ 戰略數據運算與衛星掃描中..."):
                lat, lng, address_found = resolve_location_cached(location_input)
                if lat:
                    census_res = get_census_data_cached(lat, lng)
                    density = get_density_cached(lat, lng)
                    
                    st.session_state['locked_data'] = {
                        'lat': lat, 'lng': lng,
                        'address': address_found,
                        'census': census_res,
                        'density': density
                    }
                else:
                    st.error("無法解析該地址")

    if 'locked_data' in st.session_state:
        data = st.session_state['locked_data']
        census_res = data['census']
        density = data['density']
        income = census_res['income']
        eth = census_res['eth']
        age = census_res['age']
        
        # [關鍵修正]：自動快取清理與相容性檢查
        # 如果舊快取中沒有 '亞裔/華裔' 或 '白人'，代表資料過期，強制重置
        if '亞裔/華裔' not in eth or '白人' not in eth:
            st.warning("⚠️ 系統更新：偵測到舊版快取資料，正在自動重置...請再次點擊 [啟動戰略分析 Execute]。")
            del st.session_state['locked_data']
            st.stop() # 停止執行，等待用戶重新點擊

        # 驗證標籤
        if "Official" in census_res['source']:
            st.markdown(f"""<div class="source-tag-success">🟢 數據驗證通過：{census_res['source']}</div>""", unsafe_allow_html=True)
        else:
            st.markdown(f"""<div class="source-tag-warning">🟡 數據驗證警告：{census_res['source']}</div>""", unsafe_allow_html=True)
        
        # 1. 族裔加權 (Race)
        # 核心 (2.5x): 亞裔/華裔 + 西裔 + 白人
        # 基準 (1.0x): 其他
        race_core_sum = eth['亞裔/華裔'] + eth['西裔'] + eth['白人']
        race_base_sum = eth['其他']
        eth_score_weighted = (race_core_sum * 2.5 + race_base_sum * 1.0) / 100
        
        # 2. 年齡加權 (Age)
        # 25-34 (2.5x), 18-24 (2.3x), 35-45 (2.0x), 其他 (1.0x)
        age_score_weighted = (
            age['25-34'] * 2.5 + 
            age['18-24'] * 2.3 + 
            age['35-45'] * 2.0 + 
            age['其他'] * 1.0
        ) / 100
        
        # 綜合 Target Index
        # target_index = (eth_score_weighted + age_score_weighted) / 2
        # if target_index < 1.0: target_index = 1.0
        
        # SFS 公式
        # final_sfs = ((income * target_index * env_weight) * 7) / (math.pow(density + 1, 0.7))
        
        # 分級
        # if final_sfs >= 15000: level = "品牌指標 (Model-M)"
        # elif final_sfs >= 8500: level = "社區標準 (Community-C)"
        # else: level = "高效普及 (eXpress-X)"

        # 儀表板
        # m1, m2, m3, m4, m5 = st.columns(5)
        m3, m5 = st.columns(5)
        # m1.metric("SFS 戰略總分", f"{int(final_sfs):,}", delta="地段潛力")
        # m2.metric("位置分級", level, delta_color="off")
        m3.metric("月消費力", f"${int(income):,}")
        # m4.metric("地段基因", f"{env_type} ({env_weight}x)")
        m5.metric("周邊競業", f"{density} 家")
        
        st.caption(f"📍 分析標的：{data['address']}")
        # st.caption(f"📊 Target Index: {target_index:.2f}x (核心族群加權)")
        st.divider()
        
        # 圖表區
        col_charts1, col_charts2 = st.columns(3)
        # col_charts1, col_charts2, col_charts3 = st.columns(3)
        with col_charts1:
            st.markdown("**📊 族群組成 (Ethnic %)**")
            st.bar_chart(pd.DataFrame(eth.items(), columns=["族裔", "比例"]).set_index("族裔"), color="#00FF41")
        with col_charts2:
            st.markdown("**📊 年齡結構 (Age %)**")
            st.bar_chart(pd.DataFrame(age.items(), columns=["年齡層", "比例"]).set_index("年齡層"), color="#3399FF")
        # with col_charts3:
        #     st.markdown("**📐 空間設計診斷 (Design Ref)**")
        #     st.metric("人均面積", f"{area_per_seat:.1f} sqft")
        #     progress_val = min(area_per_seat / 40.0, 1.0)
        #     st.progress(progress_val)
        #     st.caption(f"體感質量: {quality_status}")
        #     if area_per_seat < 15:
        #         st.markdown("<span style='color:red'>⚠️ 空間嚴重過載</span>", unsafe_allow_html=True)
        #     elif area_per_seat > 30:
        #         st.markdown("<span style='color:#00FF41'>✅ 空間充裕</span>", unsafe_allow_html=True)

        st.divider()

        # 地圖與 AI
        if execute_btn: 
            packet = {
                "地址": data['address'],
                # "SFS": int(final_sfs),
                # "分級": level,
                # "地段": env_type,
                "月收": f"${income:,.0f}",
                "密度": density,
                "族裔": eth,
                # "空間診斷": f"人均 {area_per_seat} sqft ({quality_status})"
            }
            
            map_bytes = None
            if G_KEY:
                map_url = f"https://maps.googleapis.com/maps/api/staticmap?center={data['lat']},{data['lng']}&zoom=18&size=640x640&scale=2&maptype=roadmap&markers=color:red%7C{data['lat']},{data['lng']}&key={G_KEY}"
                try:
                    img_data = requests.get(map_url).content
                    map_bytes = BytesIO(img_data)
                    st.session_state['locked_map'] = map_bytes
                except: pass
            
            ai_text = "AI 分析連線失敗"
            if map_bytes and GEMINI_KEY:
                genai.configure(api_key=GEMINI_KEY)
                try: model = genai.GenerativeModel('gemini-3-flash-preview')
                except: model = genai.GenerativeModel('gemini-1.5-flash')
                
                prompt = f"""
                角色：Sharetea 2026 戰略專家。
                數據包：{packet}
                任務：
                1. **地段視覺驗證**：用戶設定此地為 [{env_type}]，請觀察衛星圖確認建築密度與道路特徵是否吻合？
                2. **戰略執行**：針對 SFS {int(final_sfs)} 分 (由大環境決定) 及族裔結構，給出商業定位建議。
                3. **空間設計**：針對人均 {area_per_seat} sqft 的空間 (設計限制條件)，給出裝修與動線建議。
                """
                try:
                    map_bytes.seek(0)
                    res = model.generate_content([prompt, Image.open(map_bytes)])
                    ai_text = res.text
                    st.session_state['locked_ai_text'] = ai_text
                except: pass
        
        col_map, col_ai = st.columns([1, 1])
        with col_map:
            if 'locked_map' in st.session_state:
                st.image(st.session_state['locked_map'], caption="📍 戰略座標快照", use_container_width=True)
        with col_ai:
            st.subheader("🤖 Gemini 3 戰略解析")
            if 'locked_ai_text' in st.session_state:
                st.markdown(st.session_state['locked_ai_text'])







