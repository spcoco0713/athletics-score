import streamlit as st
import pandas as pd
import glob
import os

# --- ページ設定 ---
st.set_page_config(
    page_title="陸上競技スコア計算ツール",
    page_icon="🏃",
    layout="centered"
)

# --- データの読み込みロジック (自動検出版) ---
@st.cache_data
def load_data():
    # 1. "M_ALL_" で始まるCSVファイルをすべて探す
    csv_files = glob.glob("M_ALL_*.csv")
    
    if not csv_files:
        return None, None, "ファイルが見つかりません"
    
    # 2. ファイル名でソートして、一番新しい(最後尾の)ファイルを選ぶ
    # (日付がファイル名に入っていれば、名前順=日付順になります)
    latest_file = sorted(csv_files)[-1]
    
    try:
        df = pd.read_csv(latest_file)
        
        # Points列の特定 (大文字小文字のゆらぎ吸収)
        points_col = [c for c in df.columns if c.lower() in ["points", "pts", "score"]][0]
        
        return df, points_col, latest_file
    except Exception as e:
        return None, None, f"読み込みエラー: {e}"

df, points_col, current_filename = load_data()

# --- ユーティリティ関数 ---
def parse_record_from_csv(record_str):
    if pd.isna(record_str) or str(record_str).strip() in ["-", ""]:
        return None
    s = str(record_str).strip()
    try:
        if ":" in s:
            parts = s.split(":")
            if len(parts) == 3: return float(parts[0])*3600 + float(parts[1])*60 + float(parts[2])
            elif len(parts) == 2: return float(parts[0])*60 + float(parts[1])
        return float(s)
    except:
        return None

def get_event_type(event_name):
    name = event_name.lower().strip()
    
    # A. フィールド
    field_keywords = ['hj', 'pv', 'lj', 'tj', 'sp', 'dt', 'ht', 'jt', 'shot', 'disc', 'jave', 'hamm', 'pole', 'jump', 'throw']
    if any(k in name for k in field_keywords) and not "dec" in name and not "hept" in name:
        return "field"
    
    # B. 混成
    if "dec" in name or "hept" in name:
        return "score"
        
    # C. 長時間 (時:分:秒)
    is_walk = 'walk' in name or 'km w' in name or 'marw' in name or 'hmw' in name or name.endswith('w') or '000mw' in name
    if is_walk:
        if any(k in name for k in ['3000', '5000', '10000', '10,000', '3km', '5km', '10km']):
             return "time_ms"
        else:
             return "time_hms"

    long_dist_keywords = ['marathon', 'hm', 'hour', '15 km', '20 km', '25 km', '30 km', '35 km', '50 km', '100 km', 'miles']
    if name == 'hm': return "time_hms"
    if any(k in name for k in long_dist_keywords):
        return "time_hms"

    # D. 中長距離 (分:秒)
    middle_keywords = ['800m', '1000m', '1500m', '2000m', '3000m', '5000m', '10000m', 'mile', 'sc', 'steeple', '4x']
    if any(k in name for k in middle_keywords):
        return "time_ms"
    if '5 km' in name or '10 km' in name:
        return "time_ms"

    # E. 短距離 (秒)
    return "time_s"

# --- サイドバー (管理者用情報) ---
with st.sidebar:
    st.header("About")
    if current_filename:
        st.success(f"データ読込完了\n\n📄 {current_filename}")
    else:
        st.error("データなし")
    st.markdown("---")
    st.caption("© Athletics Score Lab.")

# --- メイン画面 ---
st.title("🏃‍♂️ 陸上競技スコア計算ツール")
st.caption("世界陸連採点表 (World Athletics Scoring Tables) に基づくスコア検索")

if df is not None:
    event_list = [c for c in df.columns if c != points_col]
    
    # 1. 種目選択
    selected_event = st.selectbox("種目を選択してください", event_list)
    
    # 2. 入力フォームの切り替え
    mode = get_event_type(selected_event)
    user_val = 0.0
    input_display_str = ""
    
    with st.container():
        st.subheader("記録の入力")
        cols = st.columns(4)
        
        if mode == "field":
            # フィールド (m, cm)
            m = cols[0].number_input("メートル (m)", min_value=0, value=0)
            cm = cols[1].number_input("センチ (cm)", min_value=0.0, value=0.0, step=1.0)
            user_val = float(m) + float(cm) / 100.0
            input_display_str = f"{m}m {cm}cm"
            
        elif mode == "time_hms":
            # 長時間 (時, 分, 秒, 1/100)
            h = cols[0].number_input("時間", min_value=0, value=0)
            m = cols[1].number_input("分", min_value=0, max_value=59, value=0)
            s = cols[2].number_input("秒", min_value=0, max_value=59, value=0)
            cs = cols[3].number_input("1/100秒", min_value=0, max_value=99, value=0)
            user_val = h*3600 + m*60 + s + (cs/100.0)
            input_display_str = f"{h}:{m:02}:{s:02}.{cs:02}"
            
        elif mode == "time_ms":
            # 中長距離 (分, 秒, 1/100)
            m = cols[0].number_input("分", min_value=0, value=0)
            s = cols[1].number_input("秒", min_value=0, max_value=59, value=0)
            cs = cols[2].number_input("1/100秒", min_value=0, max_value=99, value=0)
            user_val = m*60 + s + (cs/100.0)
            input_display_str = f"{m}:{s:02}.{cs:02}"
            
        elif mode == "score":
            # 得点入力
            pts_in = cols[0].number_input("得点", min_value=0, value=0)
            user_val = float(pts_in)
            input_display_str = f"{pts_in}点"
            
        else: # time_s
            # 短距離 (秒, 1/100)
            s = cols[0].number_input("秒", min_value=0, value=0)
            cs = cols[1].number_input("1/100秒", min_value=0, max_value=99, value=0)
            user_val = float(s) + (cs/100.0)
            input_display_str = f"{s}.{cs:02}秒"

    # 3. 計算ボタン
    if st.button("スコアを計算する", type="primary"):
        if user_val <= 0:
            st.warning("0より大きい数値を入力してください。")
        else:
            # --- 計算ロジック ---
            temp_df = df[[points_col, selected_event]].copy()
            # 欠損値処理
            temp_df = temp_df[temp_df[selected_event] != "-"]
            temp_df = temp_df.dropna(subset=[selected_event])
            
            # 数値化
            temp_df['val'] = temp_df[selected_event].apply(parse_record_from_csv)
            temp_df = temp_df.dropna(subset=['val'])
            
            if temp_df.empty:
                st.error("データが見つかりませんでした。")
            else:
                # 近似値検索
                temp_df['diff'] = (temp_df['val'] - user_val).abs()
                best_match = temp_df.loc[temp_df['diff'].idxmin()]
                
                score = int(best_match[points_col])
                table_record = best_match[selected_event]
                
                # --- 結果表示 ---
                st.divider()
                st.subheader(f"推定スコア: :blue[{score} 点]")
                st.write(f"入力記録: {input_display_str}")
                st.caption(f"採点表の近似値: {table_record} ({score}点)")
                
                # --- 収益化エリア ---
                st.divider()
                st.markdown("### 👟 記録向上のためのアイテム")
                col1, col2 = st.columns(2)
                with col1:
                    st.info("Amazonリンク (スパイクなど)")
                with col2:
                    st.info("Amazonリンク (サプリメントなど)")

else:
    st.error("CSVファイル (M_ALL_*.csv) が見つかりません。")
