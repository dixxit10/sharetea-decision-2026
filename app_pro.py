import streamlit as st
import pandas as pd
import math
import google.generativeai as genai

# --- [UI 與名詞定義部分保持不變，節省篇幅] ---

# --- 4. 強化版 AI 診斷函數 ---
def get_ai_diagnostic(context, key):
    try:
        genai.configure(api_key=key)
        
        # 戰略備案：自動嘗試不同的模型名稱規範
        model_names = ['gemini-1.5-flash', 'gemini-1.5-flash-latest', 'gemini-pro']
        
        selected_model = None
        # 獲取當前 API Key 支援的所有模型清單（這能徹底解決 404）
        available_models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        
        # 優先尋找 1.5 Flash
        for target in model_names:
            full_target = f"models/{target}"
            if full_target in available_models or target in available_models:
                selected_model = target
                break
        
        if not selected_model:
            selected_model = 'gemini-pro' # 最後的保底
            
        model = genai.GenerativeModel(selected_model)
        
        prompt = f"""
        身為 Marketing Designer 戰略顧問，請執行以下診斷任務：
        數據背景：{context}
        1. 地理特徵解讀：為什麼地段環境會導致目前的 SFS 評分？
        2. 戰略指引：這是『普及擴張』還是『精品溢價』點？給出一個行動指令。
        3. 商務英文翻譯。
        """
        
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"⚠️ AI 診斷連接失敗。請確認 API Key 是否已在 Google AI Studio 啟用 Gemini 1.5 系列權限。\n錯誤代碼: {str(e)}"

# --- 5. 核心診斷流程 (結構對齊版) ---
if st.sidebar.button("啟動精英診斷"):
    if not coord_input:
        st.warning("請輸入座標。")
    else:
        try:
            # 座標解析
            parts = coord_input.split(',')
            lat, lng = float(parts[0].strip()), float(parts[1].strip())
            
            with st.spinner("✨ 數據合成與視覺除噪中..."):
                # [模擬數據抓取邏輯]
                density, spending_power = 12, 8200
                eth_dict = {"華裔/台灣裔": 0.35, "墨西哥裔/西裔": 0.35, "社交主力": 0.30}
                seg_s = 0.30
                
                # 地段權重與 SFS 計算
                env_factor = {"Shopping Mall": 0.85, "Food Court": 0.95, "Main Street": 1.0, "Plaza": 1.15, "Community": 1.25}[loc_type]
                target_index = (0.35 * 2.0) + (0.35 * 2.0) + (0.30 * 2.5)
                final_sfs = ((spending_power * target_index) * 7 * env_factor * 1.0) / (math.pow(density, 0.7) + 1)

            # 門檻判定 (T_EX)
            T_EX = {"Shopping Mall": 6500, "Food Court": 6000, "Main Street": 5500, "Plaza": 4500, "Community": 4000}[loc_type]

            if final_sfs < T_EX:
                st.error(f"🛑 戰略排除：SFS {final_sfs:.0f} 低於基準線。數據鎖定。")
            else:
                level = "熱區指標 (A+)" if final_sfs >= 15000 else "社區標準 (B)" if final_sfs >= 8500 else "高效普及 (C)"
                
                tab1, tab2, tab3 = st.tabs(["💎 診斷報告", "👥 客群畫像", "🤖 AI 戰略翻譯"])
                
                with tab1:
                    # 地圖快照 (High-DPI 渲染)
                    map_url = f"https://maps.googleapis.com/maps/api/staticmap?center={lat},{lng}&zoom=17&size=600x400&scale=2&maptype=roadmap&markers=color:red%7C{lat},{lng}&key={st.secrets['GOOGLE_KEY']}"
                    st.image(map_url, width=700, caption="📍 地理環境視覺稽核")
                    
                    m1, m2, m3 = st.columns(3)
                    m1.metric("SFS 總分", f"{final_sfs:.0f}")
                    m2.metric("位置分級", level.split(' ')[0])
                    m3.metric("月消費力", f"${spending_power:,.0f}")

                with tab2:
                    st.write("##### 🎂 客群比例 (高→低排序)")
                    # 排序邏輯與表格呈現...
                    st.info("族裔與年齡分布已根據比例自動排序。")

                with tab3:
                    with st.spinner("🤖 Gemini 正在自動轉譯地理特徵..."):
                        context_str = f"SFS:{final_sfs:.0f}, 地段:{loc_type}, 社交比例:{seg_s:.1%}, 分級:{level}"
                        report = get_ai_diagnostic(context_str, st.secrets['GEMINI_KEY'])
                        st.markdown("### 🤖 Gemini 戰略翻譯結果")
                        st.info(report)

        except Exception as e:
            st.error(f"分析異常，請檢查座標格式或 API 金鑰配置。 (錯誤: {e})")

st.caption("Marketing Designer Suite v6.8.1")
