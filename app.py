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

# --- 種目名の日英翻訳辞書 (完全版) ---
EVENT_TRANSLATION = {
    # 短距離
    "50m": "50m", "55m": "55m", "60m": "60m",
    "100m": "100m", "200m": "200m", "300m": "300m", "400m": "400m",
    "500m": "500m", "600m": "600m",
    # 室内短距離 (sh = short track/indoor)
    "50m sh": "50m (室内)", "55m sh": "55m (室内)", "60m sh": "60m (室内)",
    "200m sh": "200m (室内)", "300m sh": "300m (室内)", "400m sh": "400m (室内)",
    
    # ハードル
    "50mH": "50mハードル", "55mH": "55mハードル", "60mH": "60mハードル",
    "110mH": "110mハードル", "400mH": "400mハードル", "300mH": "300mハードル",
    # 室内ハードル
    "50mH sh": "50mハードル (室内)", "55mH sh": "55mハードル (室内)", "60mH sh": "60mハードル (室内)",

    # 中長距離
    "800m": "800m", "1000m": "1000m", "1500m": "1500m",
    "Mile": "1マイル", "2000m": "2000m", "3000m": "3000m", 
    "2 Miles": "2マイル", "5000m": "5000m", "10000m": "10000m",
    # 室内中長距離
    "800m sh": "800m (室内)", "1000m sh": "1000m (室内)", "1500m sh": "1500m (室内)",
    "Mile sh": "1マイル (室内)", "3000m sh": "3000m (室内)", "2 Miles sh": "2マイル (室内)",
    "5000m sh": "5000m (室内)",

    # 障害
    "2000m SC": "2000m障害", "3000m SC": "3000m障害",

    # ロード・マラソン
    "5 km": "5kmロード", "10 km": "10kmロード", "15 km": "15kmロード",
    "10 Miles": "10マイルロード", "20 km": "20kmロード",
    "HM": "ハーフマラソン", "25 km": "25kmロード", "30 km": "30kmロード",
    "Marathon": "マラソン", "35 km": "35kmロード", "50 km": "50kmロード", "100 km": "100kmロード",
    "Road Relay": "ロードリレー",

    # 競歩 (トラック/ロード)
    "3000mW": "3000m競歩", "5000mW": "5000m競歩", "10,000mW": "10000m競歩",
    "20,000mW": "20000m競歩", "30,000mW": "30000m競歩", "35,000mW": "35000m競歩", "50,000mW": "50000m競歩",
    "10km W": "10km競歩", "15km W": "15km競歩", "20km W": "20km競歩", 
    "30km W": "30km競歩", "35km W": "35km競歩", "50km W": "50km競歩",
    "MarW": "マラソン競歩", "HMW": "ハーフマラソン競歩",

    # 跳躍
    "HJ": "走高跳", "PV": "棒高跳", "LJ": "走幅跳", "TJ": "三段跳",
    "Standing LJ": "立幅跳",

    # 投てき
    "SP": "砲丸投", "DT": "円盤投", "HT": "ハンマー投", "JT": "やり投",
    "Wt": "重量投",

    # 混成
    "Dec.": "十種競技", "Hept.": "七種競技", "Pent.": "五種競技",
    "Hept. sh": "七種競技 (室内)", "Pent. sh": "五種競技 (室内)",

    # リレー
    "4x100m": "4x100mリレー", "4x200m": "4x200mリレー", "4x400m": "4x400mリレー",
    "4x200m sh": "4x200mリレー (室内)", "4x400m sh": "4x400mリレー (室内)",
    "4x400mix": "男女混合4x400mリレー", "4x400mix sh": "男女混合4x400mリレー (室内)",
    "Distance Medley Relay": "メドレーリレー"
}

# --- 主要種目の表示順リスト（これらを優先的に上に表示） ---
PRIMARY_ORDER = [
    # --- トラック (短距離) ---
    "100m", "200m", "400m",
    # --- トラック (中長距離) ---
    "800m", "1500m", "3000m", "5000m", "10000m",
    # --- トラック (障害・ハードル) ---
    "110mハードル", "400mハードル", "3000m障害",
    # --- 跳躍 ---
    "走高跳", "棒高跳", "走幅跳", "三段跳",
    # --- 投てき ---
    "砲丸投", "円盤投", "ハンマー投", "やり投",
    # --- 混成 ---
    "十種競技", "七種競技 (室内)",
    # --- リレー ---
    "4x100mリレー", "4x400mリレー",
    # --- ロード ---
    "ハーフマラソン", "マラソン",
    # --- 競歩 ---
    "5000m競歩", "10000m競歩", "20km競歩", "35km競歩", "50km競歩"
]

# --- データの読み込みロジック ---
@st.cache_data
def load_data():
    csv_files = glob.glob("M_ALL_*.csv")
    if not csv_files:
        return None, None
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
    name = event_name.lower().strip()
    # A. フィールド
    field_keywords = ['hj', 'pv', 'lj', 'tj', 'sp', 'dt', 'ht', 'jt', 'shot', 'disc', 'jave', 'hamm', 'pole', 'jump', 'throw', 'standing', 'wt']
    if any(k in name for k in field_keywords) and not "dec" in name and not "hept" in name and not "pent" in name:
        return "field"
    # B. 混成
    if "dec" in name or "hept" in name or "pent" in name:
        return "score"
    # C. 長時間
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
    # D. 中長距離
    middle_keywords = ['800m', '1000m', '1500m', '2000m', '3000m', '5000m', '10000m', 'mile', 'sc', 'steeple', '4x', 'relay']
    if any(k in name for k in middle_keywords):
        return "time_ms"
    if '5 km' in name or '10 km' in name:
        return "time_ms"
    # E. 短距離
    return "time_s"

# --- メイン画面 ---
st.title("IAAFスコア計算ツール")
st.caption("World Athletics Scoring Tables (旧IAAF採点表) に基づくスコア検索")

if df is not None:
    raw_event_list = [c for c in df.columns if c != points_col]
    
    # --- 表示用リストの作成と並び替え ---
    
    # 1. 全ての種目を {日本語名: 英語キー} の形にする
    all_events_map = {}
    for eng_name in raw_event_list:
        # 辞書にあれば日本語、なければ英語そのまま
        jp_name = EVENT_TRANSLATION.get(eng_name, eng_name)
        all_events_map[jp_name] = eng_name

    # 2. 並び順を決定する
    # 主要種目リストにあるものはその順序で、それ以外は名前順で後ろに追加
    sorted_labels = []
    
    # まず主要種目を追加
    for primary in PRIMARY_ORDER:
        if primary in all_events_map:
            sorted_labels.append(primary)
            
    # 残りの種目（マイナー、室内など）を追加
    remaining = [k for k in all_events_map.keys() if k not in sorted_labels]
    # 残りは読みやすいように五十音/アルファベット順にしておく
    sorted_labels.extend(sorted(remaining))

    # セレクトボックス作成
    selected_label = st.selectbox("種目を選択してください", sorted_labels)
    
    # 計算には元の英語名を使う
    selected_event_key = all_events_map[selected_label]
    
    # 入力フォームの切り替え
    mode = get_event_type(selected_event_key)
    user_val = 0.0
    input_display_str = ""
    
    with st.container():
        st.subheader("記録の入力")
        cols = st.columns(4)
        
        if mode == "field":
            m = cols[0].number_input("メートル (m)", min_value=0, value=0)
            cm = cols[1].number_input("センチ (cm)", min_value=0, max_value=99, value=0, step=1)
            user_val = float(m) + float(cm) / 100.0
            input_display_str = f"{m}m {cm}cm"
            
        elif mode == "time_hms":
            h = cols[0].number_input("時間", min_value=0, value=0)
            m = cols[1].number_input("分", min_value=0, max_value=59, value=0)
            s = cols[2].number_input("秒", min_value=0, max_value=59, value=0)
            cs = cols[3].number_input("1/100秒", min_value=0, max_value=99, value=0)
            user_val = h*3600 + m*60 + s + (cs/100.0)
            input_display_str = f"{h}:{m:02}:{s:02}.{cs:02}"
            
        elif mode == "time_ms":
            m = cols[0].number_input("分", min_value=0, value=0)
            s = cols[1].number_input("秒", min_value=0, max_value=59, value=0)
            cs = cols[2].number_input("1/100秒", min_value=0, max_value=99, value=0)
            user_val = m*60 + s + (cs/100.0)
            input_display_str = f"{m}:{s:02}.{cs:02}"
            
        elif mode == "score":
            pts_in = cols[0].number_input("得点", min_value=0, value=0)
            user_val = float(pts_in)
            input_display_str = f"{pts_in}点"
            
        else: # time_s
            s = cols[0].number_input("秒", min_value=0, value=0)
            cs = cols[1].number_input("1/100秒", min_value=0, max_value=99, value=0)
            user_val = float(s) + (cs/100.0)
            input_display_str = f"{s}.{cs:02}秒"

    if st.button("スコアを計算する", type="primary"):
        if user_val <= 0:
            st.warning("0より大きい数値を入力してください。")
        else:
            temp_df = df[[points_col, selected_event_key]].copy()
            temp_df = temp_df[temp_df[selected_event_key] != "-"]
            temp_df = temp_df.dropna(subset=[selected_event_key])
            
            temp_df['val'] = temp_df[selected_event_key].apply(parse_record_from_csv)
            temp_df = temp_df.dropna(subset=['val'])
            
            if temp_df.empty:
                st.error("データが見つかりませんでした。")
            else:
                temp_df['diff'] = (temp_df['val'] - user_val).abs()
                best_match = temp_df.loc[temp_df['diff'].idxmin()]
                
                score = int(best_match[points_col])
                table_record = best_match[selected_event_key]
                
                st.divider()
                st.subheader(f"推定スコア: :blue[{score} 点]")
                st.write(f"入力記録: {input_display_str}")
                st.caption(f"採点表の近似値: {table_record} ({score}点)")
                
                st.divider()
                st.markdown("### 👟 記録向上のためのアイテム")
                col1, col2 = st.columns(2)
                with col1:
                    st.info("Amazonリンク (スパイクなど)")
                with col2:
                    st.info("Amazonリンク (サプリメントなど)")
else:
    st.error("システムエラー: データファイルが見つかりません。管理者に連絡してください。")
