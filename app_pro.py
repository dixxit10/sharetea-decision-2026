import streamlit as st
import pandas as pd
import numpy as np
import requests
import time

# -----------------------------------------------------------------------------
# 1. Page Configuration & Strategic Visuals
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="Sharetea Express 2026 SFS System (Live API)",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
    <style>
    /* 戰略黑主題 */
    .stApp { background-color: #0E0E0E; color: #E0E0E0; }
    h1, h2, h3 { color: #FFFFFF !important; font-family: 'Helvetica Neue', sans-serif; font-weight: 700; }
    
    /* 戰略綠/紅 */
    .strategic-green { color: #00FF41 !important; font-family: 'Courier New', monospace; font-weight: bold; }
    .strategic-red { color: #FF3333 !important; font-family: 'Courier New', monospace; font-weight: bold; }
    
    /* 數據框 */
    .metric-box {
        background-color: #1A1A1A;
        border-left: 4px solid #00FF41;
        padding: 20px;
        margin-bottom: 15px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.5);
    }
    
    /* AI Console Style */
    .ai-console {
        font-family: 'Courier New', monospace;
        background-color: #000;
        padding: 20px;
        border: 1px solid #333;
        color: #00FF41;
        white-space: pre-wrap;
    }

    /* 按鈕樣式 */
    div.stButton > button:first-child {
        background-color: #00FF41;
        color: #000000;
        font-weight: 800;
        border: none;
        width: 100%;
        padding: 0.8rem;
    }
    div.stButton > button:first-child:hover {
        background-color: #00CC33;
    }
    </style>
""", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# 2. REAL API INTEGRATION LAYER (The Dynamic Core)
# -----------------------------------------------------------------------------

def get_google_data(address, api_key):
    """
    呼叫 Google Maps API 獲取：
    1. 經緯度 (Geocoding)
    2. 地段類型 (Place Types -> Env Weight)
    3. 競業密度 (Nearby Search -> Density)
    """
    results = {}
    
    # --- Step 1: Geocoding (地址 -> 座標) ---
    geo_url = f"https://maps.googleapis.com/maps/api/geocode/json?address={address}&key={api_key}"
    try:
        geo_resp = requests.get(geo_url).json()
        if geo_resp['status'] != 'OK':
            st.error(f"Google Maps Error: {geo_resp['status']}")
            return None
        
        location = geo_resp['results'][0]['geometry']['location']
        place_id = geo_resp['results'][0]['place_id']
        lat, lng = location['lat'], location['lng']
        results['coords'] = (lat, lng)
        results['formatted_address'] = geo_resp['results'][0]['formatted_address']

        # --- Step 2: Env Weight (地段基因) ---
        # 透過 Place Details 檢查這個地點是否屬於 Shopping Mall
        details_url = f"https://maps.googleapis.com/maps/api/place/details/json?place_id={place_id}&fields=types&key={api_key}"
        details_resp = requests.get(details_url).json()
        place_types = details_resp.get('result', {}).get('types', [])
        
        if 'shopping_mall' in place_types or 'department_store' in place_types:
            results['env_type'] = "Shopping Mall"
            results['env_weight'] = 1.2
        elif 'transit_station' in place_types:
            results['env_type'] = "Transit Hub"
            results['env_weight'] = 0.8
        else:
            # 預設邏輯：若無明確 Mall 標籤，視為一般街邊或 Plaza
            results['env_type'] = "Street / Plaza"
            results['env_weight'] = 1.0

        # --- Step 3: Density (競業密度) ---
        # 搜尋半徑 1000m 內的 "bubble tea"
        radius = 1000
        keyword = "bubble tea"
        search_url = f"https://maps.googleapis.com/maps/api/place/nearbysearch/json?location={lat},{lng}&radius={radius}&keyword={keyword}&key={api_key}"
        search_resp = requests.get(search_url).json()
        
        # 計算回傳結果數量作為 Density
        # Google API 一頁最多 20 筆，若要更精確需處理 next_page_token，此處簡化為單次請求
        density_count = len(search_resp.get('results', []))
        results['density'] = density_count
        
        return results

    except Exception as e:
        st.error(f"Google API 連線失敗: {e}")
        return None

def get_census_data(lat, lng, api_key):
    """
    呼叫 US Census API 獲取人口數據：
    1. FCC API: 座標 -> FIPS Code (State + County + Tract)
    2. Census ACS API: FIPS -> Demographics
    """
    # --- Step 1: Get FIPS via FCC API (No key needed) ---
    fcc_url = f"https://geo.fcc.gov/api/census/area?lat={lat}&lon={lng}&showall=true&format=json"
    try:
        fcc_resp = requests.get(fcc_url, timeout=5).json()
        if not fcc_resp['results']:
            return None # 座標可能不在美國
            
        fips = fcc_resp['results'][0]['block_fips']
        state_code = fips[:2]
        county_code = fips[2:5]
        tract_code = fips[5:11]
    except:
        return None

    # --- Step 2: Get ACS Data via Census API ---
    # 變數代碼 (ACS 5-Year): 
    # B19013_001E (Median Household Income)
    # B01003_001E (Total Population)
    # B02001_002E (White), B02001_005E (Asian), B03003_003E (Hispanic) - 簡化示範
    
    variables = "B19013_001E,B01003_001E,B02001_005E,B03003_003E,B02001_002E"
    census_url = f"https://api.census.gov/data/2021/acs/acs5?get={variables}&for=tract:{tract_code}&in=state:{state_code}%20county:{county_code}&key={api_key}"
    
    try:
        census_resp = requests.get(census_url, timeout=5)
        if census_resp.status_code == 200:
            data = census_resp.json()
            # data format: [['header1', ...], ['value1', ...]]
            values = data[1]
            
            income = int(values[0]) if values[0] else 50000
            total_pop = int(values[1]) if values[1] else 1
            asian_pop = int(values[2]) if values[2] else 0
            hisp_pop = int(values[3]) if values[3] else 0
            white_pop = int(values[4]) if values[4] else 0
            
            # 簡易計算比例 (真實專案需更嚴謹處理重疊族裔定義)
            race_dist = {
                "Asian": round((asian_pop / total_pop) * 100, 1),
                "Hispanic": round((hisp_pop / total_pop) * 100, 1),
                "White": round((white_pop / total_pop) * 100, 1),
                "Other": round(((total_pop - asian_pop - hisp_pop - white_pop) / total_pop) * 100, 1)
            }
            
            # 這裡簡化年齡分佈抓取，使用固定比例模擬以保持代碼長度可讀性
            # 真實應用需抓取 B01001 系列約 10-20 個變數來計算 18-24, 25-34
            age_dist = {"25-34": 30.0, "18-24": 20.0, "35-45": 20.0, "Other": 30.0} 

            return {
                "monthly_income": round(income / 12),
                "race": race_dist,
                "age": age_dist,
                "source": "Census ACS 2021"
            }
        else:
            st.warning("Census API 回傳錯誤，使用備用數據。")
            return None
    except:
        return None

# -----------------------------------------------------------------------------
# 3. SFS Calculation Logic (The Constitution)
# -----------------------------------------------------------------------------
def calculate_sfs(market_data, census_data, area_sqft, seats_cat):
    
    # Fallback data if API failed
    if not census_data:
        census_data = {
            "monthly_income": 4500, # Default fallback
            "race": {"Asian": 20, "Hispanic": 20, "White": 40, "Other": 20},
            "age": {"25-34": 25, "18-24": 15, "35-45": 20, "Other": 40}
        }
        
    # 1. Target Index
    race = census_data['race']
    age = census_data['age']
    
    race_score = ((race['Asian'] + race['Hispanic'] + race['White']) * 2.5 + race['Other'] * 1.0) / 100
    age_score = ((age['25-34'] * 2.5) + (age['18-24'] * 2.3) + (age['35-45'] * 2.0) + age['Other'] * 1.0) / 100
    target_index = (race_score + age_score) / 2
    
    # 2. Env Weight
    env_weight = market_data['env_weight']
    
    # 3. Pressure Coeff (Physical)
    seat_map = {"0-6 席": 4, "7-12 席": 10, "13-20 席": 17, "20+ 席": 25}
    est_seats = seat_map.get(seats_cat, 10)
    sqft_pp = area_sqft / est_seats if est_seats > 0 else 0
    
    if sqft_pp >= 35:
        p_coeff = 1.2
        p_msg = "Visual Clarity (視覺純淨)"
    elif sqft_pp < 15:
        p_coeff = 0.5
        p_msg = "Overload (嚴重過載)"
    else:
        p_coeff = 1.0
        p_msg = "Balanced (標準平衡)"
        
    # 4. SFS Formula
    income = census_data['monthly_income']
    density = market_data['density']
    
    numerator = (income * target_index * env_weight) * 7 * p_coeff
    denominator = (density ** 0.7) + 1
    sfs = numerator / denominator
    
    return sfs, target_index, p_coeff, p_msg, sqft_pp, census_data

def get_model_decision(sfs):
    if sfs >= 15000: return "Model (M)", "品牌綠洲店"
    elif sfs >= 8500: return "Community (C)", "社區標準店"
    else: return "eXpress (X)", "高效機能店"

# -----------------------------------------------------------------------------
# 4. Main Execution Flow
# -----------------------------------------------------------------------------

# Load Secrets
try:
    GOOGLE_KEY = st.secrets["api_keys"]["GOOGLE_KEY"]
    CENSUS_KEY = st.secrets["api_keys"]["CENSUS_KEY"]
except:
    st.error("⚠️ API Keys Missing. 請在 .streamlit/secrets.toml 設定 GOOGLE_KEY 與 CENSUS_KEY")
    st.stop()

# --- Sidebar Input (Dynamic) ---
st.sidebar.markdown("### ⬅️ Strategic Input")
target_address = st.sidebar.text_input("目標地址 (Address)", "18558 Gale Ave, City of Industry, CA")

st.sidebar.markdown("#### 物理空間")
area_sqft = st.sidebar.number_input("顧客活動空間 (sq. ft.)", 100, 600, 300)
seats_cat = st.sidebar.selectbox("預計座位數", ["0-6 席", "7-12 席", "13-20 席", "20+ 席"], index=1)

run_btn = st.sidebar.button("啟動 API 戰略分析 Execute", type="primary")

if run_btn:
    with st.spinner('🛰️ 正在連線 Google Maps Platform 與 Census Bureau...'):
        
        # 1. Fetch Real Data
        google_data = get_google_data(target_address, GOOGLE_KEY)
        
        if google_data:
            lat, lng = google_data['coords']
            census_data = get_census_data(lat, lng, CENSUS_KEY)
            
            # 2. Calculate SFS
            sfs, target_idx, p_coeff, p_msg, sqft_pp, final_census = calculate_sfs(google_data, census_data, area_sqft, seats_cat)
            model_code, model_name = get_model_decision(sfs)
            
            # --- Dashboard ---
            st.title(f"📍 2026 戰略決策報告")
            st.markdown(f"**分析標的**: `{google_data['formatted_address']}`")
            
            # Section 1: Indicators
            col1, col2, col3 = st.columns(3)
            with col1:
                st.markdown(f"<div class='metric-box'><h3>SFS 總分</h3><span class='strategic-green' style='font-size:42px'>{int(sfs):,}</span></div>", unsafe_allow_html=True)
            with col2:
                st.markdown(f"<div class='metric-box'><h3>店型判定</h3><span style='font-size:36px'>{model_code}</span><br><small>{model_name}</small></div>", unsafe_allow_html=True)
            with col3:
                p_color = "strategic-red" if p_coeff < 1.0 else "strategic-green"
                st.markdown(f"<div class='metric-box'><h3>物理壓力係數</h3><span class='{p_color}' style='font-size:36px'>{p_coeff}x</span><br><small>{p_msg}</small></div>", unsafe_allow_html=True)

            # Section 2: Data Investigation (API Results)
            st.markdown("### 📡 API 數據調查報告 (The Investigation)")
            
            d1, d2 = st.columns(2)
            with d1:
                st.markdown("**市場環境 (Google Maps API)**")
                st.write(f"地段基因: **{google_data['env_type']}** (Weight: {google_data['env_weight']}x)")
                st.write(f"1km 競業密度: **{google_data['density']}** 家 (Bubble Tea)")
                st.write(f"座標: `{lat}, {lng}`")
            
            with d2:
                st.markdown("**區域人口 (Census API)**")
                if final_census.get("source"):
                    st.write(f"預估月收入: **${final_census['monthly_income']:,}**")
                    st.write(f"數據來源: {final_census['source']}")
                    st.caption(f"Target Index: {target_idx:.2f}x (高獲利族群權重)")
                    # Show breakdown
                    df_race = pd.DataFrame([final_census['race']]).T
                    st.dataframe(df_race, use_container_width=True)
                else:
                    st.warning("無法獲取人口普查數據，已使用預設值計算。")

            # Section 3: AI Console
            st.markdown("### 🧠 AI 核心戰略指令")
            
            if "M" in model_code:
                strat = "執行「視覺純淨」策略。該區具備高消費力與強品牌信號，需使用清水模與全封閉設計隔離外部噪音。"
            elif "C" in model_code:
                strat = "執行「生活連結」策略。該區強調鄰里關係，保留落地窗與部分通透性。"
            else:
                strat = "執行「極致能效」策略。高密度競爭區，需專注於出餐速度與識別度，使用高強度磨砂金屬。"
            
            console_text = f"""
[ SYSTEM PROTOCOL 2026.01 - LIVE DATA ]
---------------------------------------
> 偵測到競業密度為 {google_data['density']} 家。
> 地段基因為 {google_data['env_type']}。

[ 戰略建議 ]
{strat}

[ 物理空間診斷 ]
人均面積 {int(sqft_pp)} sqft。
{"⚠️ 警告：空間嚴重不足，需強制執行外帶導向。" if p_coeff == 0.5 else "✅ 空間充裕，可執行完整品牌體驗。"}
---------------------------------------
            """
            st.markdown(f"<div class='ai-console'>{console_text}</div>", unsafe_allow_html=True)
            
        else:
            st.error("無法解析該地址，請檢查輸入。")
