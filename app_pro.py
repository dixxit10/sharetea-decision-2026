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
    </style>
""", unsafe_allow_html=True)

# --- 1. 安全驗證邏輯 ---
def check_password():
    # 容錯讀取密碼
    try:
        pwd = st.secrets["general"]["APP_PASSWORD"]
    except:
        pwd = "sharetea2026" 

    def password_entered():
        if st.session_state["password"] == pwd:
            st.session_state["password_correct"] = True
            del st.session_state["password"]
        else:
            st.session_state["password_correct"] = False

    if "password_correct" not in st.session_state:
        st.markdown("### 🔐 Sharetea 系統門禁")
        st.text_input("Security Access Code", type="password", on_change=password_entered, key="password")
        st.button("開啟戰略引擎", on_click=password_entered)
        return False
    elif not st.session_state["password_correct"]:
        st.markdown("### 🔐 Sharetea 系統門禁")
        st.text_input("Security Access Code", type="password", on_change=password_entered, key="password")
        st.button("開啟戰略引擎", on_click=password_entered)
        st.error("😕 密碼錯誤")
        return False
    else:
        return True

if check_password():
    # --- 2. 讀取 API Keys ---
    try:
        G_KEY = st.secrets["api_keys"]["GOOGLE_KEY"]
        GEMINI_KEY = st.secrets["api_keys"]["GEMINI_KEY"]
        C_KEY = st.secrets["api_keys"]["CENSUS_KEY"]
    except KeyError:
        st.error("⚠️ Secrets 設定不完整，請檢查 Streamlit 後台設定。")
        st.stop()

    # --- 3. 側邊欄輸入 ---
    st.sidebar.header("📐 物理空間與座標")
    
    location_input = st.sidebar.text_input(
        "目標位置 (地址 或 Lat,Lng):", 
        value="18558 Gale Ave, City of Industry, CA",
        help="輸入完整地址自動解析，或輸入 '緯度,經度'"
    )
    
    st.sidebar.markdown("---")
    st.sidebar.markdown("#### 空間參數")
    cust_area = st.sidebar.slider("顧客活動空間 (sq. ft.):", 100, 600, 300)
    seat_choice = st.sidebar.radio("預計座位數:", ["0-5 席", "6-12 席", "13-20 席", "21 席以上"], index=1)
    
    # 計算人均空間
    est_seats = 5 if "0-5" in seat_choice else 12 if "6-12" in seat_choice else 20 if "13-20" in seat_choice else 30
    area_per_seat = cust_area / est_seats if est_seats > 0 else 0
    
    # 空間壓力判定
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
    
    st.sidebar.markdown(f"人均空間: **{area_per_seat:.1f} sq. ft.**")
    st.sidebar.markdown(f"判定: <span style='color:{q_color}; font-weight:bold;'>{quality_status}</span>", unsafe_allow_html=True)
    st.sidebar.caption(f"壓力補償係數: {pressure_coeff}x")

    # --- 4. 核心工具函式 ---
    
    def resolve_location(input_str):
        """解析地址或座標"""
        try:
            # 嘗試解析座標
            if "," in input_str and any(c.isdigit() for c in input_str):
                try:
                    parts = input_str.split(',')
                    if len(parts) >= 2:
                        lat = float(parts[0].strip())
                        lng = float(parts[1].strip())
                        return lat, lng, f"座標: {lat}, {lng}"
                except ValueError:
                    pass 

            # 解析地址
            url = f"https://maps.googleapis.com/maps/api/geocode/json?address={input_str}&key={G_KEY}"
            resp = requests.get(url, timeout=10).json()
            if resp['status'] == 'OK':
                loc = resp['results'][0]['geometry']['location']
                fmt_addr = resp['results'][0]['formatted_address']
                return loc['lat'], loc['lng'], fmt_addr
            return None, None, None
        except Exception:
            return None, None, None

    def get_census_data(lat, lng):
        """獲取人口數據 (含 Fallback)"""
        try:
            # FCC API
            geo_url = f"https://geo.fcc.gov/api/census/area?lat={lat}&lon={lng}&format=json"
            fips_resp = requests.get(geo_url, timeout=5).json()
            
            if not fips_resp.get('results'):
                raise Exception("Outside US")

            fips = fips_resp['results'][0]['block_fips']
            
            # Census API
            vars = "B19013_001E,B01001_001E,B03002_006E,B03002_012E,B03002_004E,B01001_007E,B01001_011E"
            url = f"https://api.census.gov/data/2022/acs/acs5?get={vars}&for=tract:{fips[5:11]}&in=state:{fips[:2]}%20county:{fips[2:5]}&key={C_KEY}"
            
            r = requests.get(url, timeout=5)
            if r.status_code != 200: raise Exception("Census Error")
            d = r.json()[1]
            
            def safe_int(val):
                try: return int(val)
                except: return 0

            pop = safe_int(d[1])
            if pop == 0: pop = 1
            
            income = safe_int(d[0])
            if income == 0: income = 50000 
            
            eth = {
                "東亞裔": round(safe_int(d[2])/pop, 3), 
                "西裔": round(safe_int(d[3])/pop, 3),
                "非裔": round(safe_int(d[4])/pop, 3)
            }
            age = {
                "18-24": round(safe_int(d[5])/pop, 3), 
                "25-34": round(safe_int(d[6])/pop, 3)
            }
            return income/12, pop, eth, age, "Official Census Data"
        except:
            return 5000, 2000, {"東亞裔": 0.35, "西裔": 0.25, "非裔": 0.1}, {"18-24": 0.2, "25-34": 0.3}, "Estimated (Simulation)"

    def get_density(lat, lng):
        try:
            url = f"https://maps.googleapis.com/maps/api/place/nearbysearch/json?location={lat},{lng}&radius=1000&keyword=bubble tea&key={G_KEY}"
            res = requests.get(url, timeout=5).json()
            return len(res.get('results', []))
        except: return 5

    # --- 5. 主畫面標題 ---
    st.title("📚 Sharetea 2026 戰略指標體系")
    st.latex(r"SFS = \frac{(Income \times TargetIndex) \times 7 \times PressureCoeff}{Density^{0.7} + 1}")
    
    c1, c2, c3 = st.columns(3)
    c1.markdown("<div class='definition-box'><b>SFS 戰略總分</b><br>量化地段獲利天花板指標。整合消費力、族群權重與空間壓力補償。</div>", unsafe_allow_html=True)
    c2.markdown("<div class='definition-box'><b>空間體感質量</b><br>基於人均面積判定：過載、標準、清晰。直接決定品牌體驗的物理上限。</div>", unsafe_allow_html=True)
    c3.markdown("<div class='definition-box'><b>位置分級基準</b><br>M: 15k+ / C: 8.5k+ / X: < 8.5k。SFS 達標但空間過載者將強制轉向 X 型態。</div>", unsafe_allow_html=True)

    # --- 6. 執行邏輯 (平面化結構 - 防止 SyntaxError) ---
    if st.sidebar.button("啟動戰略分析 Execute", type="primary"):
        
        # 1. 驗證輸入
        if not location_input:
            st.error("❌ 請輸入地址或座標")
            st.stop() # 停止執行，避免巢狀縮排

        # 2. 解析位置
        with st.spinner("🛰️ 正在解析地址..."):
            lat, lng, address_found = resolve_location(location_input)
        
        if lat is None:
            st.error(f"❌ 無法解析位置：'{location_input}'")
            st.stop()
            
        st.success(f"📍 已鎖定目標：{address_found}")
        
        # 3. 獲取數據
        with st.spinner("📊 同步衛星數據中..."):
            income, pop, eth, age, data_source = get_census_data(lat, lng)
            density = get_density(lat, lng)
        
        # 4. SFS 運算
        target_index = (eth.get("東亞裔", 0) * 3.0) + (age.get("25-34", 0) * 2.5)
        if target_index < 1.0: target_index = 1.1
        
        final_sfs = ((income * target_index) * 7 * pressure_coeff) / (math.pow(density + 1, 0.7))
        
        # 5. 分級判定
        if cust_area < 250:
            level = "高效普及 (eXpress-X)"
            limit_msg = f"⚠️ 空間狹窄 ({cust_area} sqft)：物理條件限制品牌體驗，建議以此區域之 X 店型營運。"
        else:
            if final_sfs >= 15000: level = "品牌指標 (Model-M)"
            elif final_sfs >= 8500: level = "社區標準 (Community-C)"
            else: level = "高效普及 (eXpress-X)"
            limit_msg = f"✅ 空間條件適宜：{quality_status}"

        # 6. 顯示指標
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("SFS 戰略總分", f"{int(final_sfs):,}")
        m2.metric("位置分級", level)
        m3.metric("空間係數", f"{pressure_coeff}x")
        m4.metric("周邊競業", f"{density} 家")
        
        if "⚠️" in limit_msg: st.warning(limit_msg)
        else: st.success(limit_msg)
        
        if data_source != "Official Census Data":
            st.caption(f"ℹ️ 注意：{data_source} (此區域可能位於美國境外或 API 資料庫未覆蓋)")

        st.divider()

        # --- 7. 地圖與 AI 解析 ---
        col_map, col_ai = st.columns([1, 1])
        
        # 準備數據包
        strategic_packet = {
            "地址": address_found,
            "SFS總分": round(final_sfs),
            "位置分級": level,
            "體感質量": quality_status,
            "月收入(中位)": f"${income:,.0f}",
            "族裔結構": eth,
            "年齡組成": age,
            "人均面積": f"{area_per_seat:.1f} sqft",
            "競爭密度": f"{density} 家/km"
        }

        # 任務 Prompt
        if "Model (M)" in level:
            dynamic_task = f"任務 (Model-M)：物理質量 {quality_status}。評估如何利用空間感撐起品牌溢價？如何處理地圖中周邊的雜訊？"
        elif "Community (C)" in level:
            dynamic_task = f"任務 (Community-C)：體感質量 {quality_status}。評估空間是否足以支持長期停留與社交回購？針對族群 {eth} 建議行銷策略。"
        else:
            dynamic_task = f"任務 (eXpress-X)：空間判定 {quality_status}。如何利用極簡模組掩蓋擁擠感並提升轉換率？在繁忙街道中提升識別度。"

        # 顯示地圖
        with col_map:
            try:
                map_url = f"https://maps.googleapis.com/maps/api/staticmap?center={lat},{lng}&zoom=18&size=640x640&scale=2&maptype=roadmap&markers=color:red%7C{lat},{lng}&key={G_KEY}"
                map_response = requests.get(map_url, timeout=10)
                map_bytes = BytesIO(map_response.content)
                st.image(map_bytes, caption=f"📍 戰略座標快照: {address_found}", use_container_width=True)
                st.json(strategic_packet)
            except Exception as e:
                st.error(f"地圖載入失敗: {e}")
                map_bytes = None

        # 執行 AI 分析
        with col_ai:
            st.subheader("🤖 Gemini 3 Flash 全維度解析")
            
            if map_bytes:
                genai.configure(api_key=GEMINI_KEY)
                
                # 自動模型切換
                try:
                    model = genai.GenerativeModel('gemini-3-flash-preview') 
                except:
                    model = genai.GenerativeModel('gemini-1.5-flash')
                    st.toast("⚠️ Preview 模型連線不穩，已自動切換至 Gemini 1.5 Flash")

                prompt = f"""
                角色：Sharetea 2026 戰略專家。
                【數據包】：{strategic_packet}
                
                請結合「數據包」與傳入的「衛星地圖快照」進行診斷：
                1. **視覺地段分析**：觀察地圖中的街道寬度、建築密度、路口動線，判斷該區的人流屬性。
                2. **戰略執行建議**：{dynamic_task}
                3. **結論**：針對【營運】、【行銷】、【設計】三個維度，給予精準指令。
                """
                
                with st.spinner("AI 正在視覺分析地圖紋理..."):
                    try:
                        map_bytes.seek(0)
                        ai_image = Image.open(map_bytes)
                        response = model.generate_content([prompt, ai_image])
                        st.markdown(response.text)
                    except Exception as e_ai:
                        st.error(f"AI 生成失敗: {e_ai}")
            else:
                st.warning("無法載入地圖，AI 視覺分析暫停。")
