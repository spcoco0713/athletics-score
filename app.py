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
    "50m sh": "50m (ST)", "55m sh": "55m (ST)", "60m sh": "60m (ST)",
    "200m sh": "200m (ST)", "300m sh": "300m (ST)", "400m sh": "400m (ST)",
    
    # ハードル
    "50mH": "50mハードル", "55mH": "55mハードル", "60mH": "60mハードル",
    "110mH": "110mハードル", "400mH": "400mハードル", "300mH": "300mハードル",
    "50mH sh": "50mハードル (ST)", "55mH sh": "55mハードル (ST)", "60mH sh": "60mハードル (ST)",

    # 中長距離
    "800m": "800m", "1000m": "1000m", "1500m": "1500m",
    "Mile": "1マイル", "2000m": "2000m", "3000m": "3000m", 
    "2 Miles": "2マイル", "5000m": "5000m", "10000m": "10000m",
    "800m sh": "800m (ST)", "1000m sh": "1000m (ST)", "1500m sh": "1500m (ST)",
    "Mile sh": "1マイル (ST)", "3000m sh": "3000m (ST)", "2 Miles sh": "2マイル (ST)",
    "5000m sh": "5000m (ST)",

    # 障害
    "2000m SC": "2000m障害", "3000m SC": "3000m障害",

    # ロード・マラソン
    "5 km": "5kmロード", "10 km": "10kmロード", "15 km": "15kmロード",
    "10 Miles": "10マイルロード", "20 km": "20kmロード",
    "HM": "ハーフマラソン", "25 km": "25kmロード", "30 km": "30kmロード",
    "Marathon": "マラソン", "35 km": "35kmロード", "50 km": "50kmロード", "100 km": "100kmロード",
    "Road Relay": "ロードリレー",

    # 競歩
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
    "Hept. sh": "七種競技 (ST)", "Pent. sh": "五種競技 (ST)",

    # リレー
    "4x100m": "4x100mリレー", "4x200m": "4x200mリレー", "4x400m": "4x400mリレー",
    "4x200m sh": "4x200mリレー (ST)", "4x400m sh": "4x400mリレー (ST)",
    "4x400mix": "男女混合4x400mリレー", "4x400mix sh": "男女混合4x400mリレー (ST)",
    "Distance Medley Relay": "メドレーリレー"
}

# --- カテゴリ定義 ---
def classify_event(event_name_jp):
    """日本語の種目名をカテゴリに分類する"""
    name = event_name_jp
    
    # 1. 混成
    if "種競技" in name:
        return "混成競技"
    
    # 2. 跳躍
    if "跳" in name:
        return "跳躍"
        
    # 3. 投てき
    if "投" in name:
        return "投てき"
        
    # 4. ロード・競歩
    if "競歩" in name or "マラソン" in name or "ロード" in name:
        return "ロード・競歩"
        
    # 5. 中長距離 (800m以上, 障害含む)
    # ※マイル(約1600m)も含む
    middle_long_keywords = ["800m", "1000m", "1500m", "2000m", "3000m", "5000m", "10000m", "マイル", "障害"]
    if any(k in name for k in middle_long_keywords):
        return "中長距離・障害"
        
    # 6. 短距離・ハードル・リレー (それ以外)
    return "短距離・ハードル・リレー"

# カテゴリの並び順
CATEGORY_ORDER = [
    "短距離・ハードル・リレー",
    "中長距離・障害",
    "跳躍",
    "投てき",
    "ロード・競歩",
    "混成競技"
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
    
    # 1. 種目リストの整理と分類
    # { "日本語名": "英語キー" }
    all_events_map = {}
    # カテゴリごとにリスト化 { "短距離": ["100m", "200m"...], "跳躍": [...] }
    categorized_events = {cat: [] for cat in CATEGORY_ORDER}
    
    for eng_name in raw_event_list:
        jp_name = EVENT_TRANSLATION.get(eng_name, eng_name)
        all_events_map[jp_name] = eng_name
        
        # カテゴリ分類
        cat = classify_event(jp_name)
        if cat in categorized_events:
            categorized_events[cat].append(jp_name)
        else:
            # 万が一分類漏れがあれば短距離へ
            categorized_events["短距離・ハードル・リレー"].append(jp_name)

    # 各カテゴリ内で種目名をソート
    for cat in categorized_events:
        # 主要種目(100mなど)が上に来るように工夫してもいいが、
        # ここではシンプルに名前順でソート、ただし主要なものが先頭に来るように文字長などで工夫もできるが
        # ひとまずリスト順（CSV順）または名前順
        categorized_events[cat].sort()
        
        # 主要種目を先頭に持ってくるロジック (簡易版)
        # 例えば "100m" があればリストの先頭へ移動させる
        top_priority = ["100m", "200m", "400m", "110mハードル", "400mハードル", 
                        "800m", "1500m", "5000m", "10000m",
                        "走高跳", "棒高跳", "走幅跳", "三段跳",
                        "砲丸投", "円盤投", "ハンマー投", "やり投",
                        "十種競技", "マラソン", "ハーフマラソン"]
        
        # 優先種目を抽出して並べ替え
        priority_items = [e for e in categorized_events[cat] if e in top_priority]
        other_items = [e for e in categorized_events[cat] if e not in top_priority]
        
        # 優先リストの順序を守りつつ結合
        sorted_priority = sorted(priority_items, key=lambda x: top_priority.index(x) if x in top_priority else 999)
        categorized_events[cat] = sorted_priority + other_items

    # 2. UI配置
    
    # カテゴリ選択 (ラジオボタンで横並び)
    selected_category = st.radio("カテゴリを選択してください", CATEGORY_ORDER, horizontal=True)
    
    # そのカテゴリ内の種目リストを取得
    events_in_cat = categorized_events[selected_category]
    
    if not events_in_cat:
        st.warning("このカテゴリの種目データがありません。")
        selected_label = None
    else:
        # 種目選択
        selected_label = st.selectbox("種目を選択", events_in_cat)

    if selected_label:
        selected_event_key = all_events_map[selected_label]
        mode = get_event_type(selected_event_key)
        user_val = 0.0
        input_display_str = ""
        
        with st.container():
            st.markdown("---")
            st.subheader(f"{selected_label} の記録入力")
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
