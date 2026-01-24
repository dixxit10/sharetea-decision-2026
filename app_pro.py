# --- 第五階段：分級邏輯與差距運算 (10% 門檻精算) ---
            # 定義戰略門檻
            THRESHOLD_A_PLUS = 15000
            THRESHOLD_B = 8500
            THRESHOLD_C = 4500

            # 初始分級
            if final_sfs >= THRESHOLD_A_PLUS: 
                grade, color, next_t = "Grade A+ (旗艦標竿)", "gold", None
            elif final_sfs >= THRESHOLD_B:
                grade, color, next_t = "Grade B (優質標準)", "orange", THRESHOLD_A_PLUS
            elif final_sfs >= THRESHOLD_C:
                grade, color, next_t = "Grade C (普及成長)", "blue", THRESHOLD_B
            else:
                grade, color, next_t = "Grade F (戰略排除)", "red", THRESHOLD_C

            # 差距分析邏輯 (僅標示 10% 內差距)
            gap_info = ""
            if grade.startswith("Grade B"):
                # 向上距離 A+ 的差距
                up_gap = (THRESHOLD_A_PLUS - final_sfs) / THRESHOLD_A_PLUS
                # 向下距離 C 的差距 (跨過 B 的底線)
                down_gap = (final_sfs - THRESHOLD_B) / THRESHOLD_B
                
                if up_gap <= 0.10:
                    gap_info = f"📈 **潛力躍升**：距離 A+ 旗艦標竿僅差 {up_gap:.1%}，建議透過優化能見度分值突破門檻。"
                elif down_gap <= 0.10:
                    gap_info = f"⚠️ **降級風險**：距離 C 普及成長僅差 {down_gap:.1%}，需嚴格監控營運效率。"
                else:
                    gap_info = "📍 **戰略穩定**：指標數據穩健，建議維持當前 Grade B 戰略位置。"
            
            elif grade.startswith("Grade C"):
                up_gap = (THRESHOLD_B - final_sfs) / THRESHOLD_B
                if up_gap <= 0.10:
                    gap_info = f"📈 **潛力躍升**：距離 B 優質標準僅差 {up_gap:.1%}。"
                else:
                    gap_info = "📍 **戰略穩定**：建議維持當前 Grade C 戰略位置。"
            else:
                gap_info = "📍 **戰略確診**：明確維持該戰略位置。"

            # --- 第六階段：消費行為與消費力分析 ---
            # 根據主導族群與年齡推論消費行為
            behavior = "社交美學導向 (Social & Aesthetics)" if age_26_35_r > 0.20 else "品質忠誠導向 (Quality & Loyalty)"
            if hispanic_r > asian_r:
                spending_style = "偏好鮮果系列與高視覺衝擊產品。"
            else:
                spending_style = "偏好純茶系列與低糖/機能性配方。"

            # --- 🚀 輸出報告 ---
            st.subheader("📊 診斷中心即時報告")
            m1, m2, m3, m4 = st.columns(4)
            m1.metric("SFS 戰略總分", f"{final_sfs:.0f}")
            m2.metric("當前戰略位置", grade)
            m3.metric("月均基礎消費力", f"${spending_power:,.0f}")
            m4.metric("周邊競業數", f"{density} 家")
            
            st.divider()
            
            # 戰略差距與消費行為分析
            col_l, col_r = st.columns(2)
            with col_l:
                st.markdown(f"### 🎯 戰略差距分析\n{gap_info}")
                st.write("\n")
                st.markdown(f"### 🛍️ 消費行為預判\n* **核心行為**：{behavior}\n* **消費風格**：{spending_style}")
            
            with col_r:
                st.markdown("### 👥 人口與年齡組成")
                # 顯示細分年齡組成
                age_data = pd.DataFrame({
                    "年齡層": ["18-24歲 (Gen-Z)", "25-34歲 (社交主力)", "35歲以上"],
                    "比例": [f"{gen_z_r:.1%}", f"{young_social_r:.1%}", f"{(1-gen_z_r-young_social_r):.1%}"]
                })
                st.table(age_data)
