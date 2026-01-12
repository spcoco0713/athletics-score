import streamlit as st
import pandas as pd
import glob
import os

# --- ページ設定 ---
st.set_page_config(
    page_title="World Athletics Scoring Calculator",
    page_icon="🏃",
    layout="centered"
)

# --- CSSで余白を調整 ---
st.markdown("""
    <style>
        .block-container {
            padding-top: 2rem;
            padding-bottom: 1rem;
            padding-left: 1rem;
            padding-right: 1rem;
        }
        h1 {
            font-size: 1.6rem !important;
            margin-bottom: 0.5rem !important;
        }
        .stRadio {
            margin-top: -10px;
        }
        .stTable {
            font-size: 0.95rem;
        }
        footer {
            visibility: hidden;
        }
    </style>
""", unsafe_allow_html=True)

# ==========================================
# ★ 多言語設定
# ==========================================
TEXT_RES = {
    "日本語": {
        "caption": "世界陸連採点表 (Scoring Tables) に基づくスコア検索",
        "select_gender": "性別 (Gender)",
        "men": "男子 (Men)",
        "women": "女子 (Women)",
        "select_category": "カテゴリを選択",
        "no_category_data": "このカテゴリの種目データがありません。",
        "select_event": "種目を選択",
        "input_header": "{} の記録入力",
        "calc_button": "スコアを検索する",
        "warning_input": "0より大きい数値を入力してください。",
        "result_header": "推定スコア: :blue[{} 点]",
        "input_label": "入力記録: {}",
        "approx_label": "該当するスコア: {}点 (記録: {})",
        "affiliate_header": "🛒 記録向上のための厳選アイテム",
        "affiliate_caption": "※{}選手におすすめのギア",
        "affiliate_common_header": "🥤 全アスリートにおすすめ",
        "link_button": "Amazonで見る ↗",
        "error_no_file": "現在、{} のデータファイル (CSV) が見つかりません。",
        "error_wait": "※管理者がデータをアップロードするまでお待ちください。",
        "label_m": "メートル (m)", "label_cm": "センチ (cm)",
        "label_h": "時間", "label_min": "分", "label_sec": "秒", "label_cs": "1/100秒",
        "label_pts": "得点",
        "nearby_scores": "📊 前後のスコア (該当種目の記録順)",
        "comparison_header": "🔄 同スコアの他種目記録 (主要種目)",
        "comp_sprints": "短距離",
        "comp_middle": "中長距離",
        "comp_jumps": "跳躍",
        "comp_throws": "投てき",
        "comp_road": "ロード・競歩",
        "unit_s": "秒", "unit_m": "m", "unit_pts": "点"
    },
    "English": {
        "caption": "Calculate points based on World Athletics Scoring Tables.",
        "select_gender": "Gender",
        "men": "Men",
        "women": "Women",
        "select_category": "Select Category",
        "no_category_data": "No data available for this category.",
        "select_event": "Select Event",
        "input_header": "Input Result for {}",
        "calc_button": "Calculate Points",
        "warning_input": "Please enter a value greater than 0.",
        "result_header": "Estimated Score: :blue[{} pts]",
        "input_label": "Input: {}",
        "approx_label": "Score found: {} pts (Record: {})",
        "affiliate_header": "🛒 Recommended Gear",
        "affiliate_caption": "※Gear for {} athletes",
        "affiliate_common_header": "🥤 For All Athletes",
        "link_button": "View on Amazon (Japan) ↗",
        "error_no_file": "Data file (CSV) for {} not found.",
        "error_wait": "Please wait for the administrator to upload data.",
        "label_m": "Meters (m)", "label_cm": "Centimeters (cm)",
        "label_h": "Hours", "label_min": "Minutes", "label_sec": "Seconds", "label_cs": "1/100 sec",
        "label_pts": "Points",
        "nearby_scores": "📊 Nearby Records",
        "comparison_header": "🔄 Equivalent Performance (Olympic Events)",
        "comp_sprints": "Sprints",
        "comp_middle": "Middle/Long",
        "comp_jumps": "Jumps",
        "comp_throws": "Throws",
        "comp_road": "Road / Race Walk",
        "unit_s": "s", "unit_m": "m", "unit_pts": "pts"
    }
}

CATEGORIES_JP = [
    "短距離・ハードル・リレー", "中長距離・障害", "跳躍", "投てき",
    "競歩（トラック）", "ロード（長距離・競歩）", "混成競技"
]
CATEGORIES_EN = [
    "Sprints, Hurdles & Relays", "Middle/Long Distance", "Jumps", "Throws",
    "Race Walking (Track)", "Road Running & Walking", "Combined Events"
]

def get_text(key, lang_code):
    return TEXT_RES[lang_code][key]

# ==========================================
# ★ アフィリエイト設定
# ==========================================
AMAZON_TAG = "athleticsscor-22" 

def get_amazon_link(keyword):
    return f"https://www.amazon.co.jp/s?k={keyword}&tag={AMAZON_TAG}"

def show_simple_card(icon, title, description, search_keyword, lang_code):
    with st.container(border=True):
        c1, c2 = st.columns([1, 4])
        with c1: st.markdown(f"<div style='font-size: 30px; text-align: center;'>{icon}</div>", unsafe_allow_html=True)
        with c2:
            st.markdown(f"**{title}**")
            st.caption(description)
        st.link_button(get_text("link_button", lang_code), get_amazon_link(search_keyword), use_container_width=True)

def show_affiliate_links(category_name, lang_code):
    st.divider()
    st.subheader(get_text("affiliate_header", lang_code))
    st.caption(get_text("affiliate_caption", lang_code).format(category_name))
    col1, col2 = st.columns(2)
    
    # カテゴリ名のマッピング調整
    if category_name in CATEGORIES_EN:
        idx = CATEGORIES_EN.index(category_name)
        cat_check = CATEGORIES_JP[idx]
    else:
        cat_check = category_name

    is_jp = (lang_code == "日本語")
    def item(jp_t, jp_d, jp_k, en_t, en_d, en_k): return (jp_t, jp_d, jp_k) if is_jp else (en_t, en_d, en_k)

    if cat_check == "短距離・ハードル・リレー":
        i1 = item("短距離スパイク", "100m〜400m向け", "陸上スパイク 短距離", "Sprint Spikes", "For Sprints", "Track Sprint Spikes")
        i2 = item("ストップウォッチ", "計測の必需品", "セイコー ストップウォッチ", "Stopwatch", "Essential tool", "Seiko Stopwatch")
    elif cat_check in ["中長距離・障害", "ロード（長距離・競歩）", "競歩（トラック）"]:
        i1 = item("ランニングシューズ", "練習・レース用", "ランニングシューズ 厚底", "Running Shoes", "For Racing", "Running Shoes Carbon")
        i2 = item("GPSウォッチ", "ペース管理に", "ガーミン ランニングウォッチ", "GPS Watch", "Pace Control", "Garmin Watch")
    elif cat_check == "跳躍":
        i1 = item("跳躍スパイク", "幅跳・高跳・棒高・三段用", "陸上スパイク 跳躍", "Jumping Spikes", "For Jumps", "Athletics Jump Spikes")
        i2 = item("テーピング", "怪我予防と保護", "キネシオロジーテープ", "Kinesiology Tape", "Injury prevention", "Kinesiology Tape")
    elif cat_check == "投てき":
        i1 = item("投てきシューズ", "回転・グライド対応", "投てきシューズ", "Throwing Shoes", "For Throws", "Athletics Throwing Shoes")
        i2 = item("トレーニングギア", "ベルトやラップ", "トレーニングベルト", "Training Gear", "Belts", "Weightlifting Belt")
    else:
        i1 = item("陸上スパイク", "記録更新の必需品", "陸上スパイク", "Athletics Spikes", "Essential for PB", "Track and Field Spikes")
        i2 = item("スポーツリカバリー", "練習後のケアに", "フォームローラー", "Recovery Gear", "Care", "Foam Roller")
    
    with col1: show_simple_card("👟", i1[0], i1[1], i1[2], lang_code)
    with col2: show_simple_card("🩹", i2[0], i2[1], i2[2], lang_code)

# ==========================================
# ★ 種目処理ロジック & 辞書
# ==========================================
EVENT_TRANSLATION_JP = {
    "50m": "50m", "60m": "60m", "100m": "100m", "200m": "200m", "400m": "400m",
    "800m": "800m", "1500m": "1500m", "3000m": "3000m", "5000m": "5000m", "10000m": "10000m",
    "110mH": "110mH", "100mH": "100mH", "400mH": "400mH", "3000m SC": "3000m障害",
    "HJ": "走高跳", "PV": "棒高跳", "LJ": "走幅跳", "TJ": "三段跳",
    "SP": "砲丸投", "DT": "円盤投", "HT": "ハンマー投", "JT": "やり投",
    "Dec.": "十種競技", "Hept.": "七種競技", "Pent.": "五種競技",
    "Marathon": "マラソン", "HM": "ハーフマラソン", "20km W": "20km競歩", "35km W": "35km競歩", "50km W": "50km競歩"
}
# 並び順指定
CUSTOM_SORT_ORDER = [
    "100m", "200m", "400m", "800m", "1500m", "5000m", "10000m",
    "110mH", "100mH", "400mH", "3000m SC",
    "HJ", "PV", "LJ", "TJ", "SP", "DT", "HT", "JT",
    "Dec.", "Hept.", "Pent.", "Marathon", "HM", "20km W"
]
OLYMPIC_EVENTS_FOR_COMPARE = [
    "100m", "200m", "400m", "800m", "1500m", "5000m", "10000m",
    "110mH", "100mH", "400mH", "3000m SC",
    "HJ", "PV", "LJ", "TJ", "SP", "DT", "HT", "JT", "Marathon", "20km W"
]

def get_display_name(raw_name, lang_code):
    base_name = raw_name.replace(" sh", " (ST)")
    if lang_code == "日本語":
        return EVENT_TRANSLATION_JP.get(raw_name, base_name)
    return base_name

def classify_event(event_name_jp):
    name = event_name_jp
    if "種競技" in name: return "混成競技"
    if "跳" in name and "競歩" not in name: return "跳躍"
    if "投" in name: return "投てき"
    if "m競歩" in name and "km" not in name and "マラソン" not in name: return "競歩（トラック）"
    if "ロード" in name or "マラソン" in name or "km競歩" in name: return "ロード（長距離・競歩）"
    if any(k in name for k in ["800m", "1000m", "1500m", "2000m", "3000m", "5000m", "10000m", "マイル", "障害"]): return "中長距離・障害"
    return "短距離・ハードル・リレー"

def classify_event_en(event_name_en):
    name = event_name_en.lower()
    if "dec" in name or "hept" in name or "pent" in name: return "Combined Events"
    if any(k in name for k in ["hj", "pv", "lj", "tj", "standing"]) and "standing" not in name: return "Jumps"
    if any(k in name for k in ["sp", "dt", "ht", "jt", "wt"]): return "Throws"
    if "mw" in name and "km" not in name: return "Race Walking (Track)"
    if any(k in name for k in ["marathon", "hm", "km", "road", "miles"]): return "Road Running & Walking"
    if any(k in name for k in ["800m", "1500m", "3000m", "5000m", "10000m", "mile", "sc"]): return "Middle/Long Distance"
    return "Sprints, Hurdles & Relays"

def get_event_type(event_name):
    name = event_name.lower().strip()
    if any(k in name for k in ['hj', 'pv', 'lj', 'tj', 'sp', 'dt', 'ht', 'jt', 'shot', 'disc', 'jave', 'hamm', 'jump', 'throw', 'wt']) and "dec" not in name: return "field"
    if "dec" in name or "hept" in name or "pts" in name: return "score"
    if any(k in name for k in ['marathon', 'km w', 'marw', 'hmw', '15 km', '20 km', '25 km', '30 km', '35 km', '50 km', '100 km']): return "time_hms"
    if any(k in name for k in ['800m', '1000m', '1500m', '2000m', '3000m', '5000m', '10000m', 'mile', 'sc', '4x']): return "time_ms"
    return "time_s"

def parse_record_from_csv(record_str):
    if pd.isna(record_str) or str(record_str).strip() in ["-", ""]: return None
    s = str(record_str).strip()
    try:
        if ":" in s:
            parts = s.split(":")
            if len(parts) == 3: return float(parts[0])*3600 + float(parts[1])*60 + float(parts[2])
            elif len(parts) == 2: return float(parts[0])*60 + float(parts[1])
        return float(s)
    except: return None

def format_display_record(val, mode, lang_code):
    if pd.isna(val) or val == "-" or val == "": return "-"
    u_s = get_text("unit_s", lang_code)
    u_m = get_text("unit_m", lang_code)
    if mode == "time_s":
        try: return f"{float(val):.2f}{u_s}"
        except: return f"{val}{u_s}"
    elif mode == "field": return f"{val}{u_m}"
    return str(val)

# --- データの読み込み ---
@st.cache_data
def load_data(gender_prefix):
    file_pattern = f"{gender_prefix}_ALL_*.csv"
    csv_files = sorted(glob.glob(file_pattern))
    if not csv_files: return None, None
    try:
        df = pd.read_csv(csv_files[-1], dtype=str)
        p_col = [c for c in df.columns if c.lower() in ["points", "pts", "score"]][0]
        df["Points_Num"] = pd.to_numeric(df[p_col].str.replace(',', ''), errors='coerce').fillna(0).astype(int)
        return df, p_col
    except: return None, None

# ==========================================
# ★ メインアプリ
# ==========================================
st.title("World Athletics Scoring Calculator / スコア検索ツール")
st.caption("Calculate points based on World Athletics Scoring Tables. / 世界陸連採点表に基づくスコア検索")

cols = st.columns(2)
with cols[0]: lang_choice = st.radio("Language / 言語", ["English", "日本語"], horizontal=True)
with cols[1]:
    gender_choice = st.radio(get_text("select_gender", lang_choice), [get_text("men", lang_choice), get_text("women", lang_choice)], horizontal=True)
    gender_prefix = "M" if ("Men" in gender_choice or "男子" in gender_choice) else "W"

df, points_col = load_data(gender_prefix)

if df is not None:
    raw_event_list = [c for c in df.columns if c not in [points_col, "Points_Num"]]
    
    # ----------------------------------------------------
    # ★ 種目カテゴリ分け & ソートロジック (復活)
    # ----------------------------------------------------
    all_events_map = {}
    if lang_choice == "日本語":
        categorized_events = {cat: [] for cat in CATEGORIES_JP}
        for eng_name in raw_event_list:
            disp_name = get_display_name(eng_name, "日本語")
            all_events_map[disp_name] = eng_name
            cat = classify_event(disp_name)
            if cat in categorized_events: categorized_events[cat].append(disp_name)
            else: categorized_events["短距離・ハードル・リレー"].append(disp_name)
        current_categories = CATEGORIES_JP
    else:
        categorized_events = {cat: [] for cat in CATEGORIES_EN}
        for eng_name in raw_event_list:
            disp_name = get_display_name(eng_name, "English")
            all_events_map[disp_name] = eng_name
            cat = classify_event_en(eng_name)
            if cat in categorized_events: categorized_events[cat].append(disp_name)
            else: categorized_events["Sprints, Hurdles & Relays"].append(disp_name)
        current_categories = CATEGORIES_EN

    # カテゴリ内ソート
    for cat in categorized_events:
        categorized_events[cat].sort()
        # 主要種目を先頭に
        priority = []
        others = []
        for d_name in categorized_events[cat]:
            orig = all_events_map[d_name]
            clean = orig.replace(" sh", "")
            if clean in CUSTOM_SORT_ORDER: priority.append(d_name)
            else: others.append(d_name)
        priority.sort(key=lambda x: CUSTOM_SORT_ORDER.index(all_events_map[x].replace(" sh", "")))
        categorized_events[cat] = priority + others

    # UI描画
    selected_category = st.radio(get_text("select_category", lang_choice), current_categories, horizontal=True)
    events_in_cat = categorized_events[selected_category]
    
    if not events_in_cat:
        st.warning(get_text("no_category_data", lang_choice))
        selected_label = None
    else:
        selected_label = st.selectbox(get_text("select_event", lang_choice), events_in_cat)
    
    if selected_label:
        selected_event_raw = all_events_map[selected_label]
        mode = get_event_type(selected_event_raw)
        
        st.markdown("---")
        st.subheader(get_text("input_header", lang_choice).format(selected_label))
        
        in_cols = st.columns(4)
        user_val = 0.0
        disp_input = ""
        
        # 入力フォーム
        if mode == "field":
            m = in_cols[0].number_input(get_text("label_m", lang_choice), min_value=0, value=0)
            cm = in_cols[1].number_input(get_text("label_cm", lang_choice), min_value=0, max_value=99, value=0)
            user_val = m + (cm / 100.0)
            disp_input = f"{m}m {cm}cm"
        elif mode == "time_hms":
            h = in_cols[0].number_input(get_text("label_h", lang_choice), 0)
            m = in_cols[1].number_input(get_text("label_min", lang_choice), 0, 59)
            s = in_cols[2].number_input(get_text("label_sec", lang_choice), 0, 59)
            cs = in_cols[3].number_input(get_text("label_cs", lang_choice), 0, 99)
            user_val = h*3600 + m*60 + s + cs/100.0
            disp_input = f"{h}:{m:02}:{s:02}.{cs:02}"
        elif mode == "time_ms":
            m = in_cols[0].number_input(get_text("label_min", lang_choice), 0)
            s = in_cols[1].number_input(get_text("label_sec", lang_choice), 0, 59)
            cs = in_cols[2].number_input(get_text("label_cs", lang_choice), 0, 99)
            user_val = m*60 + s + cs/100.0
            disp_input = f"{m}:{s:02}.{cs:02}"
        else:
            s = in_cols[0].number_input(get_text("label_sec", lang_choice), 0)
            cs = in_cols[1].number_input(get_text("label_cs", lang_choice), 0, 99)
            user_val = s + cs/100.0
            disp_input = f"{s}.{cs:02}s"

        if st.button(get_text("calc_button", lang_choice), type="primary"):
            if user_val <= 0:
                st.warning(get_text("warning_input", lang_choice))
            else:
                # ---------------------------------------------------------
                # ★ 検索 & 前後スコア取得ロジック (強化版)
                # ---------------------------------------------------------
                # 1. 選択種目の有効なデータのみを抽出した clean_df を作成
                #    インデックスをリセットすることで、スライス(iloc)による前後取得を容易にする
                clean_df = df[df[selected_event_raw].str.strip() != "-"].copy()
                clean_df['val'] = clean_df[selected_event_raw].apply(parse_record_from_csv)
                clean_df = clean_df.dropna(subset=['val']).sort_values("Points_Num", ascending=False).reset_index(drop=True)
                
                if clean_df.empty:
                    st.error("No valid data for this event.")
                else:
                    # スコア検索 (近似値)
                    if mode == "field":
                        # フィールド: 入力値以下の最大記録
                        candidates = clean_df[clean_df['val'] <= user_val]
                        best_match_idx = candidates.index[0] if not candidates.empty else clean_df.index[-1]
                    else:
                        # トラック: 入力値以上の最小記録（遅い方）
                        candidates = clean_df[clean_df['val'] >= user_val]
                        best_match_idx = candidates.index[0] if not candidates.empty else clean_df.index[-1]
                    
                    match_row = clean_df.iloc[best_match_idx]
                    score = int(match_row["Points_Num"])
                    table_rec = match_row[selected_event_raw]

                    st.divider()
                    st.subheader(get_text("result_header", lang_choice).format(score))
                    st.write(get_text("input_label", lang_choice).format(disp_input))
                    st.caption(get_text("approx_label", lang_choice).format(score, format_display_record(table_rec, mode, lang_choice)))

                    # === 1. 前後3つの記録表示 (clean_dfからインデックスで取得) ===
                    st.markdown(f"**{get_text('nearby_scores', lang_choice)}**")
                    
                    # 前後3行の範囲を計算
                    start_idx = max(0, best_match_idx - 3)
                    end_idx = min(len(clean_df), best_match_idx + 4) # sliceは末尾を含まないので+4
                    
                    nearby_rows = clean_df.iloc[start_idx:end_idx]
                    
                    nearby_list = []
                    for i, r in nearby_rows.iterrows():
                        p = int(r["Points_Num"])
                        # 該当行にマークをつける
                        prefix = "👉 " if i == best_match_idx else ""
                        nearby_list.append({
                            "Score": f"{prefix}{p}", 
                            "Record": format_display_record(r[selected_event_raw], mode, lang_choice)
                        })
                    
                    st.table(pd.DataFrame(nearby_list).set_index("Score"))

                    # ---------------------------------------------------------
                    # ★ 2. 同スコア比較 (主要種目リスト復活)
                    # ---------------------------------------------------------
                    st.markdown(f"**{get_text('comparison_header', lang_choice)}** ({score} pts)")
                    
                    # 元のデータ(df)全体から、特定したスコアの行を取得
                    orig_score_row = df[df["Points_Num"] == score]
                    
                    if not orig_score_row.empty:
                        rd = orig_score_row.iloc[0]
                        c1, c2 = st.columns(2)
                        
                        sprints = ["100m", "200m", "400m", "110mH", "100mH", "400mH"]
                        middle = ["800m", "1500m", "5000m", "10000m", "3000m SC"]
                        jumps = ["HJ", "PV", "LJ", "TJ"]
                        throws = ["SP", "DT", "HT", "JT"]
                        road = ["Marathon", "20km W"] 
                        
                        def show_comp(col, title, ev_list):
                            with col:
                                st.caption(f"▼ {title}")
                                for e in ev_list:
                                    if e in df.columns and pd.notna(rd[e]) and rd[e] != "-":
                                        d_name = get_display_name(e, lang_choice)
                                        e_mode = get_event_type(e)
                                        val_disp = format_display_record(rd[e], e_mode, lang_choice)
                                        st.markdown(f"- **{d_name}**: {val_disp}")

                        show_comp(c1, get_text("comp_sprints", lang_choice), sprints)
                        show_comp(c1, get_text("comp_middle", lang_choice), middle)
                        show_comp(c2, get_text("comp_jumps", lang_choice), jumps)
                        show_comp(c2, get_text("comp_throws", lang_choice), throws)
                        show_comp(c1, get_text("comp_road", lang_choice), road)
                    
                    show_affiliate_links(selected_category, lang_choice)
else:
    st.error("Data file not found.")
