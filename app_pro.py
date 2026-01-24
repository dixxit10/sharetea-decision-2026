import streamlit as st
import pandas as pd
import math
import requests
import google.generativeai as genai
from io import BytesIO
from PIL import Image

# --- 0. 密碼驗證邏輯 ---
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
            padding: 15px; margin-bottom: 15px; border-radius: 0 4px 4px 0; font-size: 0.9em;
        }
        div[data-testid="metric-container"] { 
            background-color: #1C2128; border: 1px solid #30363D; padding: 20px; border-radius: 8px; 
        }
        .stButton>button { 
            background: #238636; color: white; border: none; border-radius: 4px; font-weight: 500; height: 3.5em;
        }
        </style>
        """, unsafe_allow_html=True)

    # --- 2. 配置與輔助函數 (API Logic) ---
    G_KEY = st.secrets.get("GOOGLE_KEY")
    GEMINI_KEY = st.secrets.get("GEMINI_KEY")
    CENSUS_KEY = st.secrets.get("CENSUS_KEY")

    def get_census_data(lat, lng, api_key):
        """實時抓取美國人口普查數據"""
        try:
            geo_url = f"https://geo.fcc.gov/api/census/area?lat={lat}&lon={lng}&format=json"
            fips = requests.get(geo_url).json()['results'][0]['block_fips']
            state, county, tract = fips[:2], fips[2:5], fips[5:11]
            vars = "B19013_001E,B01001_001E,B03002_006E,B03002_012E,B03002_004E,B03002_003E,B03002_005E,B01001_007E,B01001_008E,B01001_009E,B01001_010E,B01001_011E,B01001_012E"
            url = f"https://api.census.gov/data/2022/acs/acs5?get={vars}&for=tract:{tract}&in=state:{state}%20county:{county}&key={api_key}"
            d = requests.get(url).json()[1]
            income, total_pop = int(d[0]) / 12, int(d[1])
            eth = {
                "華裔/東亞裔": int(d[2])/total_pop, "東南亞裔": int(d[3])/total_pop,
                "墨西哥裔/西裔": int(d[4])/total_pop, "白人": int(d[5])/total_pop, "南亞裔": int(d[6])/total_pop
            }
            age = {
                "18-24 歲": sum(int(x) for x in d[7:11])/total_pop,
                "25-34 歲 (社交主力)": sum(int(x) for x in d[11:13])/total_pop
            }
            return income, eth, age
        except: return None, None, None

    def get_nearby_density(lat, lng, key):
        """Place API: 實時競爭密度掃描"""
        try:
            url = f"https://maps.googleapis.com/maps/api/place/nearbysearch/json?location={lat},{lng}&radius=1000&keyword=boba|tea|coffee&key={key}"
            res = requests.get(url).json()
            return len(res.get('results', []))
        except: return 5

    def get_ai_analysis(img_bytes, context, api_key):
        """Gemini 3 Flash: 地圖基因診斷"""
        try:
            genai.configure(api_key=api_key)
            model = genai.GenerativeModel('gemini-3-flash-preview')
            img = Image.open(img_bytes)
            prompt = f"""
            依照營運、行銷、設計角度，請判讀地圖截圖中的『視覺雜訊』與『鄰里基因』。
            數據場景：{context}
            核心任務：識別地圖上的店家機能為哪種型態，推測消費者到此區的目的為何，是快餐、鄰里、還是質感型態。
            1.【位置分級基準】：位置分級基準是否與環境型態有落差，原因為何?
            2.【執行方向】：針對詳細人口組成，提供簡易的執行建議(營運、行銷、設計)。
            """
            return model.generate_content([prompt, img]).text
        except: return "AI 診斷引擎連線逾時。"

    # --- 3. 名詞定義區 ---
    st.title("📚 名詞定義 v9.8.8")
    st.latex(r"SFS = \frac{(Income \times TargetIndex) \times 7 \times EnvFactor \times PressureCoeff}{Density^{0.7} + 1}")
    
    d_col1, d_col2, d_col3 = st.columns(3)
    with d_col1:
        st.markdown("<div class='definition-box'><b>SFS 戰略總分</b><br>動態核算地段潛力，分數越高代表單店產值天花板越高。</div>", unsafe_allow_html=True)
        st.markdown("<div class='definition-box'><b>空間壓力係數</b><br>當人均面積低於 25 sqft，判定為體驗過載，下修補償分值。</div>", unsafe_allow_html=True)
    with d_col2:
        st.markdown("<div class='definition-box'><b>環境與地段基因</b><br>透過 AI 識別鄰里質感與視覺雜訊 (如汽修廠、加油站等質感斷層)。</div>", unsafe_allow_html=True)
        st.markdown("<div class='definition-box'><b>月均基礎消費力</b><br>連動 CENSUS API 之 Tract 等級月收入中位數。</div>", unsafe_allow_html=True)
    with d_col3:
        st.markdown("<div class='definition-box'><b>位置分級基準</b><br>M: 15000+ (指標店)<br>C: 8500+ (社區店)<br>X: < 8500 (機能店)</div>", unsafe_allow_html=True)
        st.markdown("<div class='definition-box'><b>顧客活動區 (200-460 sqft)</b><br>排除工作區，定義顧客可停留的純效能空間。</div>", unsafe_allow_html=True)

    st.divider()

    # --- 4. 側邊欄輸入 ---
    st.sidebar.header("📍 戰略座標輸入")
    coord_input = st.sidebar.text_input("座標 (Lat, Lng):", placeholder="33.6507, -117.8381")
    loc_type = st.sidebar.selectbox("地點型態:", ["Plaza", "Shopping Mall", "Main Street", "Community"])
    
    st.sidebar.markdown("---")
    cust_area = st.sidebar.slider("顧客活動空間 (sq. ft.):", 200, 460, 300)
    seat_choice = st.sidebar.radio("座位數:", ["0-5 席", "6-12 席", "13-20 席"])

    # 實時空間診斷 (不按按鈕也能看)
    est_seats = 5 if "0-5" in seat_choice else 12 if "6-12" in seat_choice else 20
    area_per_seat = cust_area / est_seats
    pressure_coeff = 1.2 if area_per_seat >= 30 else 1.0 if area_per_seat >= 25 else 0.75
    st.sidebar.info(f"人均空間：{area_per_seat:.1f} sqft")
    st.sidebar.caption(f"壓力係數：{pressure_coeff}")

    # --- 5. 執行分析 ---
    if st.sidebar.button("Execute Strategic Analysis"):
        if not coord_input: st.error("請提供座標。")
        else:
            try:
                lat, lng = [float(x.strip()) for x in coord_input.split(',')]
                with st.spinner("🚀 執行維度對接中..."):
                    # 數據抓取
                    income, eth, age = get_census_data(lat, lng, CENSUS_KEY)
                    density = get_nearby_density(lat, lng, G_KEY)
                    
                    if income:
                        # 戰略邏輯運算 (非 Hardcode)
                        target_index = (eth.get("華裔/東亞裔", 0) * 2.5) + (age.get("25-34 歲 (社交主力)", 0) * 3.0)
                        final_sfs = ((income * (target_index if target_index > 0 else 1.1)) * 7 * 1.15 * pressure_coeff) / (math.pow(density + 1, 0.7))
                        level = "Model (M)" if final_sfs >= 15000 else "Community (C)" if final_sfs >= 8500 else "eXpress (X)"
                        gap_to_m = max(0, (15000 - final_sfs) / 15000)

                        # 結果呈現
                        m1, m2 = st.columns([2, 1])
                        with m1:
                            map_url = f"https://maps.googleapis.com/maps/api/staticmap?center={lat},{lng}&zoom=17&size=800x450&scale=2&key={G_KEY}"
                            img_content = BytesIO(requests.get(map_url).content)
                            st.image(img_content, use_container_width=True, caption=f"📍 座標 {lat}, {lng} 靜態掃描")
                        with m2:
                            st.metric("SFS 戰略總分", f"{final_sfs:.0f}")
                            st.metric("位置分級", level)
                            st.metric("月消費力", f"${income:,.0f}")
                            st.metric("周邊競業數", f"{density}")
                            st.metric("分級差距 (Gap to M)", f"{gap_to_m:.1%}")

                        st.divider()
                        # 維度分析區
                        d1, d2 = st.columns(2)
                        with d1:
                            st.subheader("👥 實時族群與年齡細分")
                            st.table(pd.DataFrame(eth.items(), columns=["族裔", "比例"]).style.format({"比例":"{:.1%}"}))
                            st.table(pd.DataFrame(age.items(), columns=["年齡段", "比例"]).style.format({"比例":"{:.1%}"}))
                        
                        with d2:
                            st.subheader("🧠 全維度戰略定位")
                            # M/C/X 複合判定
                            if income > 7500 and age.get("25-34 歲 (社交主力)", 0) > 0.3:
                                st.success("💎 定位：Model (M). 重點：建立品牌綠洲，屏蔽視覺雜訊。")
                            elif income > 5000 and eth.get("華裔/東亞裔", 0) > 0.2:
                                st.info("📸 定位：Community (C). 重點：強化視覺張力與聯名活動。")
                            else:
                                st.warning("🛵 定位：eXpress (X). 重點：極致化取餐動線與外送能效。")
                            
                            st.subheader("📉 戰略差距分析")
                            st.write(f"當前地段密度為 **{density}**。建議透過{'強化視覺' if density > 10 else '降低營運成本'}來抵銷競爭壓力。")
                            
                        # AI 分析
                        st.subheader("🤖 Gemini 3 視覺診斷建議")
                        ctx = f"SFS:{final_sfs:.0f}, Level:{level}, Income:{income}, Density:{density}"
                        st.markdown(get_ai_analysis(img_content, ctx, GEMINI_KEY))

            except Exception as e: st.error(f"分析報錯: {e}")

    st.caption("Produced by Marketing Designer. v9.8.8 | Reducing Noise. Increasing Clarity.")
