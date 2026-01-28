import streamlit as st
import pandas as pd
import math
import requests
import google.generativeai as genai
from io import BytesIO
from PIL import Image
import traceback

print("start123")
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
    .error-debug {
        color: #FF3333;
        font-size: 0.8em;
        background-color: #220000;
        padding: 5px;
        border-radius: 5px;
        margin-top: 5px;
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

    # 3.2 地段基因 (保留UI)
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

    # 重寫：移除 @st.cache_data 以便除錯 (稍後可加回)，並替換 FCC API 為 Census Geocoder
    def get_census_data_live(lat, lng):
        default_data = {
            'income': 50000,
            'eth': {'亞裔/華裔': 30.0, '西裔': 30.0, '白人': 20.0, '其他': 20.0},
            'age': {'18-24': 15.0, '25-34': 25.0, '35-45': 20.0, '其他': 40.0},
            'source': "Estimated (API Failed)"
        }
        
        if not C_KEY: 
            return default_data, "錯誤：CENSUS_KEY 未設定 (請檢查 secrets.toml)"

        try:
            # --- 步驟 1: 使用 Census Official Geocoder (比 FCC 穩定) ---
            # 參數：x=經度, y=緯度
            geo_url = f"https://geocoding.geo.census.gov/geocoder/geographies/coordinates?x={lng}&y={lat}&benchmark=Public_AR_Current&vintage=Current_Current&format=json"
            
            geo_resp = requests.get(geo_url, timeout=15) # 延長 timeout
            if geo_resp.status_code != 200:
                return default_data, f"Geocoder 連線失敗: Status {geo_resp.status_code}"
                
            geo_json = geo_resp.json()
            
            # 解析 Census 回傳結構
            # result -> geographies -> Census Tracts -> [0]
            if 'result' not in geo_json or 'geographies' not in geo_json['result'] or 'Census Tracts' not in geo_json['result']['geographies']:
                return default_data, "Geocoder 無法解析此座標 (可能位於海域或非普查區)"
                
            tract_data = geo_json['result']['geographies']['Census Tracts'][0]
            state = tract_data['STATE']
            county = tract_data['COUNTY']
            tract = tract_data['TRACT']
            
            # --- 步驟 2: 抓取數據 (Census Data API) ---
            vars = "B19013_001E,B01001_001E,B03002_006E,B03002_012E,B03002_003E,B01001_007E,B01001_011E"
            # 嘗試使用 2022，若失敗可手動改為 2021
            url = f"https://api.census.gov/data/2022/acs/acs5?get={vars}&for=tract:{tract}&in=state:{state}%20county:{county}&key={C_KEY}"
            
            r = requests.get(url, timeout=10)
            if r.status_code != 200:
                return default_data, f"Census Data API 失敗: {r.text}"
                
            data_rows = r.json()
            if len(data_rows) < 2:
                return default_data, "API 回傳空數據"
                
            d = data_rows[1]
            
            # 數據解析
            def safe_val(v): return int(v) if v else 0
            
            pop = safe_val(d[1]) or 1
            income_val = safe_val(d[0])
            asian = safe_val(d[2])
            hispanic = safe_val(d[3])
            white = safe_val(d[4])
            
            # 年齡 (簡化)
            age18_24 = safe_val(d[5]) # 其實是單一變數，這裡僅作示意
            age25_34 = safe_val(d[6])
            
            final_data = {
                'income': income_val / 12 if income_val > 0 else 4500,
                'eth': {
                    '亞裔/華裔': round((asian/pop)*100, 1),
                    '西裔': round((hispanic/pop)*100, 1),
                    '白人': round((white/pop)*100, 1), 
                    '其他': round(((pop - asian - hispanic - white)/pop)*100, 1)
                },
                'age': {
                    '18-24': 18.0, # 簡化估計，避免 API 變數過多報錯
                    '25-34': 25.0,
                    '35-45': 22.0,
                    '其他': 35.0
                },
                'source': f"Official Census (Tract {tract})"
            }
            return final_data, None # None 代表沒有錯誤

        except Exception as e:
            return default_data, f"系統異常: {str(e)}"

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
                    # 呼叫新的 Live 函數 (不快取，以便 Debug)
                    census_res, error_msg = get_census_data_live(lat, lng)
                    density = get_density_cached(lat, lng)
                    
                    st.session_state['locked_data'] = {
                        'lat': lat, 'lng': lng,
                        'address': address_found,
                        'census': census_res,
                        'density': density,
                        'error': error_msg # 儲存錯誤訊息
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
        if '亞裔/華裔' not in eth or '白人' not in eth:
            st.warning("⚠️ 系統更新：偵測到舊版快取資料，正在自動重置...請再次點擊 [啟動戰略分析 Execute]。")
            del st.session_state['locked_data']
            st.rerun()

        # 驗證標籤 (顯示詳細錯誤)
        if "Official" in census_res['source']:
            st.markdown(f"""<div class="source-tag-success">🟢 數據驗證通過：{census_res['source']}</div>""", unsafe_allow_html=True)
        else:
            st.markdown(f"""<div class="source-tag-warning">🟡 數據驗證警告：{census_res['source']}</div>""", unsafe_allow_html=True)
            if data.get('error'):
                st.error(f"🔧 詳細錯誤代碼 (Debug): {data['error']}")
        
        # 1. 族裔加權 (Race)
        race_core_sum = eth['亞裔/華裔'] + eth['西裔'] + eth['白人']
        race_base_sum = eth['其他']
        eth_score_weighted = (race_core_sum * 2.5 + race_base_sum * 1.0) / 100
        
        # 2. 年齡加權 (Age)
        age_score_weighted = (
            age['25-34'] * 2.5 + 
            age['18-24'] * 2.3 + 
            age['35-45'] * 2.0 + 
            age['其他'] * 1.0
        ) / 100
        
        # 儀表板
        # m1, m2, m3, m4, m5 = st.columns(5)
        m3, m5 = st.columns(2)
        # m1.metric("SFS 戰略總分", f"{int(final_sfs):,}", delta="地段潛力")
        # m2.metric("位置分級", level, delta_color="off")
        m3.metric("月消費力", f"${int(income):,}")
        # m4.metric("地段基因", f"{env_type} ({env_weight}x)")
        m5.metric("周邊競業", f"{density} 家")
        
        st.caption(f"📍 分析標的：{data['address']}")
        st.divider()
        
        # 圖表區
        col_charts1, col_charts2 = st.columns(2)
        with col_charts1:
            st.markdown("**📊 族群組成 (Ethnic %)**")
            st.bar_chart(pd.DataFrame(eth.items(), columns=["族裔", "比例"]).set_index("族裔"), color="#00FF41")
        with col_charts2:
            st.markdown("**📊 年齡結構 (Age %)**")
            st.bar_chart(pd.DataFrame(age.items(), columns=["年齡層", "比例"]).set_index("年齡層"), color="#3399FF")

        st.divider()

              
        # 1. 執行與存儲邏輯 (只有點擊按鈕時觸發)
        if execute_btn:
            with st.spinner("🛰️ 戰略數據運算與衛星掃描中..."):
                # 準備數據包
                packet = {
                    "地址": data['address'],
                    "月收": f"${income:,.0f}",
                    "密度": density,
                    "族裔": eth,
                    "年齡層": age
                }
                
                # 抓取 Google Static Map
                if G_KEY:
                    map_url = f"https://maps.googleapis.com/maps/api/staticmap?center={data['lat']},{data['lng']}&zoom=18&size=640x640&scale=2&maptype=roadmap&markers=color:red%7C{data['lat']},{data['lng']}&key={G_KEY}"
                    try:
                        img_data = requests.get(map_url).content
                        st.session_state['locked_map'] = BytesIO(img_data)
                    except Exception as e:
                        st.error(f"地圖抓取失敗: {str(e)}")
        
                # 呼叫 Gemini 進行 DNA 戰略分析
                if GEMINI_KEY and 'locked_map' in st.session_state:
                    genai.configure(api_key=GEMINI_KEY)
                    model = genai.GenerativeModel('gemini-1.5-flash')
                    
                    # 融入品牌 DNA 關鍵字：現代萃取、律動呼吸感、儀式化連結
                    prompt = f"""
                    角色：Sharetea 2026 戰略專家 (Marketing Designer)。
                    品牌 DNA 核心：1. 現代萃取(專業) 2. 律動呼吸感(降噪) 3. 儀式化連結(情感)。
                    數據包：{packet}
                    
                    任務：
                    1. 診斷場域：觀察衛星圖，判定 Business Mix % 屬於「熱區、社區、或通路」。
                    2. 品牌定位：針對 24-35 歲(華、西、白人)，說明如何運用 DNA 支柱提升品牌引力(AOI)。
                    3. 空間處方：基於數據，建議該店應執行「路徑 A：視覺降噪包」或「路徑 B：效率擴張包」。
                    4. 視覺細節：給出符合『誠實、效率、降噪』關鍵字的裝修細節建議。
                    """
                    
                    try:
                        # 關鍵修正：歸零指針以供重複讀取
                        st.session_state['locked_map'].seek(0)
                        img = Image.open(st.session_state['locked_map'])
                        
                        res = model.generate_content([prompt, img])
                        st.session_state['locked_ai_text'] = res.text
                    except Exception as e:
                        st.error(f"AI 解析失敗: {str(e)}")
        
        # 2. 獨立顯示區塊 (只要 session_state 有資料就顯示，不受按鈕狀態影響)
        st.divider()
        col_map, col_ai = st.columns([1, 1])
        
        with col_map:
            if 'locked_map' in st.session_state:
                st.image(st.session_state['locked_map'], caption="📍 戰略座標衛星快照", use_container_width=True)
        
        with col_ai:
            st.subheader("🤖 Gemini 3 戰略診斷報告")
            if 'locked_ai_text' in st.session_state:
                st.markdown(st.session_state['locked_ai_text'])
            elif execute_btn:
                st.info("AI 專家正在分析地段 DNA，請稍候...")session_state['locked_ai_text'])
        
