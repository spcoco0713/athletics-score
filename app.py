import streamlit as st
import pandas as pd
import glob
import os

# --- ページ設定 ---
st.set_page_config(
    page_title="IAAFスコア計算ツール",
    page_icon="🏃",
    layout="centered"
)

# --- 種目名の日英翻訳辞書 ---
# CSVのヘッダー(英語)を日本語表記に変換するためのマッピング
EVENT_TRANSLATION = {
    # 短距離
    "100m": "100m", "200m": "200m", "300m": "300m", "400m": "400m",
    "50m": "50m", "55m": "55m", "60m": "60m",
    # ハードル
    "110mH": "110mハードル", "400mH": "400mハードル", 
    "50mH": "50mハードル", "55mH": "55mハードル", "60mH": "60mハードル",
    # 中長距離
    "600m": "600m", "800m": "800m", "1000m": "1000m",
    "1500m": "1500m", "Mile": "マイル", "2000m": "2000m",
    "3000m": "3000m", "5000m": "5000m", "10000m": "10000m",
    "2000m SC": "2000m障害", "3000m SC": "3000m障害",
    # ロード
    "5 km": "5kmロード", "10 km": "10kmロード", "15 km": "15kmロード",
    "20 km": "20kmロード", "25 km": "25kmロード", "30 km": "30kmロード",
    "35 km": "35kmロード", "50 km": "50kmロード", "100 km": "100kmロード",
    "HM": "ハーフマラソン", "Marathon": "マラソン",
    # 競歩
    "3000mW": "3000m競歩", "5000mW": "5000m競歩", "10,000mW": "10000m競歩",
    "20,000mW": "20000m競歩", "30,000mW": "30000m競歩", "35,000mW": "35000m競歩", "50,000mW": "50000m競歩",
    "10km W": "10km競歩", "15km W": "15km競歩", "20km W": "20km競歩", 
    "30km W": "30km競歩", "35km W": "35km競歩", "50km W": "50km競歩",
    "MarW": "マラソン競歩",
    # フィールド
    "HJ": "走高跳", "PV": "棒高跳", "LJ": "走幅跳", "TJ": "三段跳",
    "SP": "砲丸投", "DT": "円盤投", "HT": "ハンマー投", "JT": "やり投",
    # 混成
    "Dec.": "十種競技", "Hept.": "七種競技", "Pent.": "五種競技",
    # リレー
    "4x100m": "4x100mリレー", "4x200m": "4x200mリレー", "4x400m": "4x400mリレー"
}

# --- データの読み込みロジック ---
@st.cache_data
def load_data():
    csv_files = glob.glob("M_ALL_*.csv")
    
    if not csv_files:
        return None, None
    
    # 一番新しい日付のファイルを自動選択
    latest_file = sorted(csv_files)[-1]
    
    try:
        df = pd.read_csv(latest_file)
        points_col = [c for c in df.columns if c.lower() in ["points", "pts", "score"]][0]
        return df, points_col
    except Exception:
        return None, None

df, points_col = load_data()

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
    # 判定には元の英語名を使う
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

# --- メイン画面 ---
st.title("IAAFスコア計算ツール")
st.caption("World Athletics Scoring Tables (旧IAAF採点表) に基づくスコア検索")

if df is not None:
    # 列名(英語)を取得
    raw_event_list = [c for c in df.columns if c != points_col]
    
    # 表示用リストを作成（日本語があるものは日本語に、なければ英語のまま）
    # { "日本語名": "元の英語名", ... } という辞書を作る
    display_map = {}
    for eng_name in raw_event_list:
        # 辞書にあれば日本語、なければ英語そのまま
        jp_name = EVENT_TRANSLATION.get(eng_name, eng_name)
        
        # 室内(sh)などは補足をつける
        if " sh" in eng_name:
            jp_name += " (室内)"
        
        display_map[jp_name] = eng_name

    # セレクトボックスには日本語リストを表示
    selected_label = st.selectbox("種目を選択してください", list(display_map.keys()))
    
    # 計算には元の英語名を使う
    selected_event_key = display_map[selected_label]
    
    # 入力フォームの切り替え
    mode = get_event_type(selected_event_key)
    user_val = 0.0
    input_display_str = ""
    
    with st.container():
        st.subheader("記録の入力")
        cols = st.columns(4)
        
        if mode == "field":
            # フィールド (m, cm) - cmは整数入力
            m = cols[0].number_input("メートル (m)", min_value=0, value=0)
            cm = cols[1].number_input("センチ (cm)", min_value=0, max_value=99, value=0, step=1)
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

    # 計算ボタン
    if st.button("スコアを計算する", type="primary"):
        if user_val <= 0:
            st.warning("0より大きい数値を入力してください。")
        else:
            # --- 計算ロジック ---
            temp_df = df[[points_col, selected_event_key]].copy()
            temp_df = temp_df[temp_df[selected_event_key] != "-"]
            temp_df = temp_df.dropna(subset=[selected_event_key])
            
            # 数値化
            temp_df['val'] = temp_df[selected_event_key].apply(parse_record_from_csv)
            temp_df = temp_df.dropna(subset=['val'])
            
            if temp_df.empty:
                st.error("データが見つかりませんでした。")
            else:
                # 近似値検索
                temp_df['diff'] = (temp_df['val'] - user_val).abs()
                best_match = temp_df.loc[temp_df['diff'].idxmin()]
                
                score = int(best_match[points_col])
                table_record = best_match[selected_event_key]
                
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
    st.error("システムエラー: データファイルが見つかりません。管理者に連絡してください。")
