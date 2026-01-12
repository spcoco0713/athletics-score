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

# --- CSSで余白を調整 (コンパクト化 & ラジオボタン調整 & フッター非表示) ---
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
        /* ラジオボタンの余白を詰める */
        .stRadio {
            margin-top: -10px;
        }
        .st-emotion-cache-1y4p8pa {
            padding: 1rem 0.5rem;
        }
        
        /* フッター (Built with Streamlit) を非表示にする */
        footer {
            visibility: hidden;
        }
        /* 右上のハンバーガーメニューも消したい場合は以下を追加 */
        /* #MainMenu {visibility: hidden;} */
    </style>
""", unsafe_allow_html=True)

# ==========================================
# ★ 多言語設定 (Translation Resources)
# ==========================================
TEXT_RES = {
    "日本語": {
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
        "approx_label": "採点表の近似値: {} ({}点)",
        "affiliate_header": "🛒 記録向上のための厳選アイテム",
        "affiliate_caption": "※{}選手におすすめのギア",
        "affiliate_common_header": "🥤 全アスリートにおすすめ",
        "link_button": "Amazonで見る ↗",
        "error_no_file": "現在、{} のデータファイル (CSV) が見つかりません。",
        "error_wait": "※管理者がデータをアップロードするまでお待ちください。",
        "error_system": "システムエラー: データファイルが見つかりません。",
        # 入力ラベル
        "label_m": "メートル (m)", "label_cm": "センチ (cm)",
        "label_h": "時間", "label_min": "分", "label_sec": "秒", "label_cs": "1/100秒",
        "label_pts": "得点"
    },
    "English": {
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
        "approx_label": "Nearest table value: {} ({} pts)",
        "affiliate_header": "🛒 Recommended Gear",
        "affiliate_caption": "※Gear for {} athletes",
        "affiliate_common_header": "🥤 For All Athletes",
        "link_button": "View on Amazon (Japan) ↗",
        "error_no_file": "Data file (CSV) for {} not found.",
        "error_wait": "Please wait for the administrator to upload data.",
        "error_system": "System Error: Data file not found.",
        # Input Labels
        "label_m": "Meters (m)", "label_cm": "Centimeters (cm)",
        "label_h": "Hours", "label_min": "Minutes", "label_sec": "Seconds", "label_cs": "1/100 sec",
        "label_pts": "Points"
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
# ★ アフィリエイト設定エリア
# ==========================================
AMAZON_TAG = "athleticsscor-22" 

def get_amazon_link(keyword):
    base_url = "https://www.amazon.co.jp/s"
    return f"{base_url}?k={keyword}&tag={AMAZON_TAG}"

def show_simple_card(icon, title, description, search_keyword, lang_code):
    with st.container(border=True):
        c1, c2 = st.columns([1, 4])
        with c1:
            st.markdown(f"<div style='font-size: 30px; text-align: center; margin-top: 5px;'>{icon}</div>", unsafe_allow_html=True)
        with c2:
            st.markdown(f"**{title}**")
            st.caption(description)
        st.link_button(
            label=get_text("link_button", lang_code), 
            url=get_amazon_link(search_keyword),
            use_container_width=True
        )

def show_affiliate_links(category_name, lang_code):
    st.divider()
    st.subheader(get_text("affiliate_header", lang_code))
    st.caption(get_text("affiliate_caption", lang_code).format(category_name))

    col1, col2 = st.columns(2)
    
    if category_name in CATEGORIES_EN:
        idx = CATEGORIES_EN.index(category_name)
        cat_check = CATEGORIES_JP[idx]
    else:
        cat_check = category_name

    is_jp = (lang_code == "日本語")
    
    def item(jp_t, jp_d, jp_k, en_t, en_d, en_k):
        if is_jp: return (jp_t, jp_d, jp_k)
        return (en_t, en_d, en_k)

    if cat_check == "短距離・ハードル・リレー":
        t1, d1, k1 = item("短距離スパイク", "100m〜400m向け。反発力重視。", "陸上スパイク 短距離", "Sprint Spikes", "For 100m-400m. High responsiveness.", "Track and Field Sprint Spikes")
        t2, d2, k2 = item("ストップウォッチ", "指導者・マネージャーの必需品。", "セイコー ストップウォッチ 陸上", "Stopwatch", "Essential for coaches.", "Seiko Stopwatch Track")
        with col1: show_simple_card("👟", t1, d1, k1, lang_code)
        with col2: show_simple_card("⏱️", t2, d2, k2, lang_code)

    elif cat_check in ["中長距離・障害", "ロード・競歩", "競歩（トラック）"]:
        t1, d1, k1 = item("ランニングシューズ", "練習からレースまで。厚底・薄底。", "ランニングシューズ 厚底", "Running Shoes", "For training and racing.", "Running Shoes Carbon Plate")
        t2, d2, k2 = item("GPSウォッチ", "Garminなど。ペース管理に。", "ガーミン ランニングウォッチ", "GPS Watch", "Pace management with Garmin.", "Garmin Running Watch")
        with col1: show_simple_card("👟", t1, d1, k1, lang_code)
        with col2: show_simple_card("⌚", t2, d2, k2, lang_code)
            
    elif cat_check == "跳躍":
        t1, d1, k1 = item("跳躍用スパイク", "走幅跳・高跳・三段跳・棒高跳。", "陸上スパイク 跳躍", "Jumping Spikes", "Long/High/Triple Jump & Pole Vault.", "Track Spikes Jump")
        t2, d2, k2 = item("テーピング", "足首や膝の保護、怪我予防に。", "キネシオロジーテープ 50mm", "Kinesiology Tape", "Injury prevention and support.", "Kinesiology Tape")
        with col1: show_simple_card("🦘", t1, d1, k1, lang_code)
        with col2: show_simple_card("🩹", t2, d2, k2, lang_code)

    elif cat_check == "投てき":
        t1, d1, k1 = item("投てきシューズ", "回転用・グライド用。", "陸上 投てきシューズ", "Throwing Shoes", "For rotation and glide techniques.", "Track Throwing Shoes")
        t2, d2, k2 = item("トレーニングギア", "ベルトやリストラップなど。", "トレーニングベルト", "Training Gear", "Belts and wrist wraps.", "Weightlifting Belt")
        with col1: show_simple_card("💪", t1, d1, k1, lang_code)
        with col2: show_simple_card("🏋️", t2, d2, k2, lang_code)

    else: 
        t1, d1, k1 = item("陸上スパイク", "全種目対応モデルや練習用。", "陸上スパイク", "Track Spikes", "All-round models for practice.", "Track and Field Spikes")
        t2, d2, k2 = item("リカバリー", "プロテインやフォームローラー。", "ホエイプロテイン", "Recovery", "Protein and foam rollers.", "Whey Protein")
        with col1: show_simple_card("👟", t1, d1, k1, lang_code)
        with col2: show_simple_card("🔋", t2, d2, k2, lang_code)

    st.markdown("") 
    st.markdown(f"##### {get_text('affiliate_common_header', lang_code)}")
    c1, c2, c3 = st.columns(3)
    
    i1 = item("プロテイン", "体づくりに", "ザバス プロテイン", "Protein", "For body building", "Whey Protein")
    i2 = item("ケア用品", "筋膜リリース", "フォームローラー", "Foam Roller", "Myofascial release", "Foam Roller")
    i3 = item("アミノ酸", "BCAAなど", "アミノバイタル", "Amino Acids", "BCAA for endurance", "Amino Vital")
    
    with c1: show_simple_card("🥛", i1[0], i1[1], i1[2], lang_code)
    with c2: show_simple_card("🌀", i2[0], i2[1], i2[2], lang_code)
    with c3: show_simple_card("⚡", i3[0], i3[1], i3[2], lang_code)


# --- 種目名の日英翻訳辞書 (日本語表示用) ---
EVENT_TRANSLATION_JP = {
    # --- 短距離 ---
    "50m": "50m", "55m": "55m", "60m": "60m",
    "100m": "100m", "100y": "100ヤード",
    "200m": "200m", "300m": "300m", "400m": "400m",
    "500m": "500m", "600m": "600m",
    # --- ショートトラック ---
    "50m sh": "50m (ST)", "55m sh": "55m (ST)", "60m sh": "60m (ST)",
    "200m sh": "200m (ST)", "300m sh": "300m (ST)", "400m sh": "400m (ST)",
    "300y sh": "300ヤード (ST)", "440y sh": "440ヤード (ST)",
    # --- ハードル ---
    "50mH": "50mハードル", "55mH": "55mハードル", "60mH": "60mハードル",
    "100mH": "100mハードル", "110mH": "110mハードル", 
    "200mH": "200mハードル", "300mH": "300mハードル", "400mH": "400mハードル",
    "50mH sh": "50mハードル (ST)", "55mH sh": "55mハードル (ST)", "60mH sh": "60mハードル (ST)",
    # --- 中長距離 ---
    "800m": "800m", "1000m": "1000m", "1500m": "1500m",
    "Mile": "1マイル", "2000m": "2000m", "3000m": "3000m", 
    "2 Miles": "2マイル", "5000m": "5000m", "10000m": "10000m",
    # --- ショートトラック中長距離 ---
    "800m sh": "800m (ST)", "1000m sh": "1000m (ST)", "1500m sh": "1500m (ST)",
    "Mile sh": "1マイル (ST)", "3000m sh": "3000m (ST)", "2 Miles sh": "2マイル (ST)",
    "5000m sh": "5000m (ST)",
    # --- 障害 ---
    "2000m SC": "2000m障害", "3000m SC": "3000m障害",
    # --- ロード・マラソン ---
    "5 km": "5kmロード", "10 km": "10kmロード", "15 km": "15kmロード",
    "10 Miles": "10マイルロード", "20 km": "20kmロード", "25 km": "25kmロード",
    "30 km": "30kmロード", "35 km": "35kmロード", "50 km": "50kmロード", "100 km": "100kmロード",
    "HM": "ハーフマラソン", "Marathon": "マラソン", "Road Relay": "ロードリレー",
    # --- 競歩 ---
    "3000mW": "3000m競歩", "5000mW": "5000m競歩", "10000mW": "10000m競歩", "10,000mW": "10000m競歩",
    "15,000mW": "15000m競歩", "20,000mW": "20000m競歩", "30,000mW": "30000m競歩", "35,000mW": "35000m競歩", "50,000mW": "50000m競歩",
    "3km W": "3km競歩", "5km W": "5km競歩", "10km W": "10km競歩", "15km W": "15km競歩", "20km W": "20km競歩", "25km W": "25km競歩",
    "30km W": "30km競歩", "35km W": "35km競歩", "50km W": "50km競歩", "MarW": "マラソン競歩", "HMW": "ハーフマラソン競歩",
    # --- 跳躍 ---
    "HJ": "走高跳", "PV": "棒高跳", "LJ": "走幅跳", "TJ": "三段跳",
    "Standing LJ": "立幅跳", "Standing HJ": "立高跳", "Standing TJ": "立三段跳",
    # --- 投てき ---
    "SP": "砲丸投", "DT": "円盤投", "HT": "ハンマー投", "JT": "やり投",
    "Wt": "重量投", "Wt sh": "重量投 (ST)",
    # --- 混成 ---
    "Dec.": "十種競技", "Hept.": "七種競技", "Pent.": "五種競技",
    "Hept. sh": "七種競技 (ST)", "Pent. sh": "五種競技 (ST)",
    # --- リレー ---
    "4x100m": "4x100mリレー", "4x200m": "4x200mリレー", "4x400m": "4x400mリレー",
    "4x800m": "4x800mリレー", "4x1500m": "4x1500mリレー",
    "4x200m sh": "4x200mリレー (ST)", "4x400m sh": "4x400mリレー (ST)",
    "4x400mix": "男女混合4x400mリレー", "4x400mix sh": "男女混合4x400mリレー (ST)",
    "Distance Medley Relay": "メドレーリレー", "Sprint Medley Relay": "スプリントメドレーリレー"
}

# --- 種目名の日英翻訳辞書 (英語表示用: 略称を展開) ---
EVENT_TRANSLATION_EN = {
    "HJ": "High Jump", "PV": "Pole Vault", "LJ": "Long Jump", "TJ": "Triple Jump",
    "SP": "Shot Put", "DT": "Discus Throw", "HT": "Hammer Throw", "JT": "Javelin Throw",
    "Dec.": "Decathlon", "Hept.": "Heptathlon", "Pent.": "Pentathlon",
    "HM": "Half Marathon", "HMW": "Half Marathon Race Walk", "Marathon": "Marathon", "MarW": "Marathon Race Walk",
    "3000m SC": "3000m Steeplechase", "2000m SC": "2000m Steeplechase",
    "110mH": "110m Hurdles", "100mH": "100m Hurdles", "400mH": "400m Hurdles",
    "50mH": "50m Hurdles", "60mH": "60m Hurdles",
    "3000mW": "3000m Race Walk", "5000mW": "5000m Race Walk", "10000mW": "10000m Race Walk", "10,000mW": "10000m Race Walk",
    "20,000mW": "20000m Race Walk", "30,000mW": "30000m Race Walk", "35,000mW": "35000m Race Walk", "50,000mW": "50000m Race Walk",
    "10km W": "10km Race Walk", "20km W": "20km Race Walk", "35km W": "35km Race Walk", "50km W": "50km Race Walk",
    "Wt": "Weight Throw"
}

# ==========================================
# ★ 種目の並び順 (SORT ORDER)
# ==========================================
CUSTOM_SORT_ORDER = [
    # --- Sprints ---
    "100m", "200m", "400m", "300m", "500m", "600m", "50m", "55m", "60m", "100y",
    # --- Hurdles ---
    "110mH", "100mH", "400mH", "300mH", "50mH", "55mH", "60mH",
    # --- Middle/Long ---
    "800m", "1500m", "3000m", "5000m", "10000m", "Mile", "2000m", "2 Miles", "3000m SC", "2000m SC",
    # --- Jumps ---
    "HJ", "PV", "LJ", "TJ", "Standing LJ", "Standing HJ", "Standing TJ",
    # --- Throws ---
    "SP", "DT", "HT", "JT", "Wt",
    # --- Combined ---
    "Dec.", "Hept.", "Pent.",
    # --- Road Running (Runs) ---
    "Marathon", "HM", "100 km", "50 km", "35 km", "30 km", "25 km", "20 km", "10 Miles", "15 km", "10 km", "5 km", "Road Relay",
    # --- Road Walking (Walks) ---
    "20km W", "35km W", "50km W", "10km W", "5km W", "3km W", "MarW", "HMW",
    # --- Track Walking ---
    "5000mW", "10000mW", "10,000mW", "20,000mW", "30,000mW", "35,000mW", "50,000mW", "3000mW", "15,000mW",
    # --- Relays ---
    "4x100m", "4x400m", "4x400mix", "4x200m", "4x800m", "4x1500m", "Distance Medley Relay", "Sprint Medley Relay"
]

def get_display_name(raw_name, lang_code):
    """言語設定に基づいて表示名を決定する"""
    base_name = raw_name.replace(" sh", " (ST)")
    if lang_code == "日本語":
        return EVENT_TRANSLATION_JP.get(raw_name, base_name)
    else:
        if raw_name in EVENT_TRANSLATION_EN:
            return EVENT_TRANSLATION_EN[raw_name]
        return base_name

def classify_event(event_name_jp):
    name = event_name_jp
    if "種競技" in name: return "混成競技"
    if "跳" in name and "競歩" not in name: return "跳躍"
    if "投" in name: return "投てき"
    if "m競歩" in name and "km" not in name and "マラソン" not in name and "ハーフ" not in name: return "競歩（トラック）"
    if "ロード" in name or "マラソン" in name or "km競歩" in name: return "ロード（長距離・競歩）"
    middle_long_keywords = ["800m", "1000m", "1500m", "2000m", "3000m", "5000m", "10000m", "マイル", "障害"]
    if any(k in name for k in middle_long_keywords): return "中長距離・障害"
    return "短距離・ハードル・リレー"

def classify_event_en(event_name_en):
    name = event_name_en.lower()
    if "dec" in name or "hept" in name or "pent" in name: return "Combined Events"
    if ("hj" in name or "pv" in name or "lj" in name or "tj" in name) and "standing" not in name: return "Jumps"
    if "standing" in name: return "Jumps"
    if "sp" in name or "dt" in name or "ht" in name or "jt" in name or "wt" in name: return "Throws"
    if "mw" in name and "km" not in name: return "Race Walking (Track)"
    if "marathon" in name or "hm" in name or "km" in name or "road" in name or "miles" in name: return "Road Running & Walking"
    if any(k in name for k in ["800m", "1000m", "1500m", "2000m", "3000m", "5000m", "10000m", "mile", "sc", "steeple"]): return "Middle/Long Distance"
    return "Sprints, Hurdles & Relays"

# --- データの読み込みロジック (男女対応) ---
@st.cache_data
def load_data(gender_prefix):
    # ファイル名パターン: M_ALL_*.csv または W_ALL_*.csv
    file_pattern = f"{gender_prefix}_ALL_*.csv"
    csv_files = glob.glob(file_pattern)
    
    if not csv_files:
        return None, None
    
    # 最新ファイルを自動選択
    latest_file = sorted(csv_files)[-1]
    
    try:
        df = pd.read_csv(latest_file)
        # ポイント列を探す
        points_col = [c for c in df.columns if c.lower() in ["points", "pts", "score"]][0]
        return df, points_col
    except Exception:
        return None, None

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

def get_event_type(event_name):
    name = event_name.lower().strip()
    field_keywords = ['hj', 'pv', 'lj', 'tj', 'sp', 'dt', 'ht', 'jt', 'shot', 'disc', 'jave', 'hamm', 'pole', 'jump', 'throw', 'standing', 'wt']
    if any(k in name for k in field_keywords) and not "dec" in name and not "hept" in name and not "pent" in name: return "field"
    if "dec" in name or "hept" in name or "pent" in name: return "score"
    is_walk = 'walk' in name or 'km w' in name or 'marw' in name or 'hmw' in name or name.endswith('w') or '000mw' in name
    if is_walk:
        # 長時間扱いにする種目
        if any(k in name for k in ['3000', '5000', '10000', '10,000', '3km', '5km', '10km']): return "time_ms"
        else: return "time_hms"
    long_dist_keywords = ['marathon', 'hm', 'hour', '15 km', '20 km', '25 km', '30 km', '35 km', '50 km', '100 km', 'miles']
    if name == 'hm': return "time_hms"
    if any(k in name for k in long_dist_keywords): return "time_hms"
    middle_keywords = ['800m', '1000m', '1500m', '2000m', '3000m', '5000m', '10000m', 'mile', 'sc', 'steeple', '4x', 'relay']
    if any(k in name for k in middle_keywords): return "time_ms"
    if '5 km' in name or '10 km' in name: return "time_ms"
    return "time_s"

# --- メイン画面 (タイトルは固定・日英併記) ---
st.title("World Athletics Scoring Calculator / スコア検索ツール")
st.caption("Calculate points based on World Athletics Scoring Tables. / 世界陸連採点表に基づくスコア検索")

# --- 設定エリア (メイン画面上部・サイドバーなし) ---
setting_cols = st.columns(2)

with setting_cols[0]:
    # 言語選択 (初期値 English)
    lang_choice = st.radio("Language / 言語", ["English", "日本語"], horizontal=True)

with setting_cols[1]:
    # 性別選択
    gender_label = get_text("select_gender", lang_choice)
    # 選択肢の表示も言語によって変える (例: Men -> 男子 (Men))
    # ※get_textは翻訳辞書から取得する
    gender_opts = [get_text("men", lang_choice), get_text("women", lang_choice)]
    gender_choice = st.radio(gender_label, gender_opts, horizontal=True)
    
    # 選択肢の文字列に "Men" または "男子" が含まれていれば男子データ
    if "Men" in gender_choice or "男子" in gender_choice:
        gender_prefix = "M"
    else:
        gender_prefix = "W"

df, points_col = load_data(gender_prefix)

if df is not None:
    raw_event_list = [c for c in df.columns if c != points_col]
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

    for cat in categorized_events:
        categorized_events[cat].sort()
        top_keys = [
            "100m", "200m", "400m", "100mH", "110mH", "400mH", 
            "800m", "1500m", "5000m", "10000m", "3000m SC",
            "HJ", "PV", "LJ", "TJ", "SP", "DT", "HT", "JT",
            "Dec.", "Hept.", "Marathon", "HM",
            "5000mW", "10000mW", "20km W", "35km W", "50km W"
        ]
        priority_items = []
        other_items = []
        for disp_name in categorized_events[cat]:
            original_key = all_events_map[disp_name]
            if original_key in top_keys:
                priority_items.append(disp_name)
            else:
                other_items.append(disp_name)
        
        # 2. ソート順ヘルパー関数 (カテゴリ内)
        def get_sort_index(d_name):
            orig_key = all_events_map[d_name]
            clean_key = orig_key.replace(" sh", "")
            if clean_key in CUSTOM_SORT_ORDER:
                return CUSTOM_SORT_ORDER.index(clean_key)
            return 9999

        # 3. それぞれソート
        priority_items.sort(key=get_sort_index)
        other_items.sort(key=get_sort_index)
        
        # 4. 結合
        categorized_events[cat] = priority_items + other_items

    selected_category = st.radio(get_text("select_category", lang_choice), current_categories, horizontal=True)
    events_in_cat = categorized_events[selected_category]
    
    if not events_in_cat:
        st.warning(get_text("no_category_data", lang_choice))
        selected_label = None
    else:
        selected_label = st.selectbox(get_text("select_event", lang_choice), events_in_cat)

    if selected_label:
        selected_event_key = all_events_map[selected_label]
        mode = get_event_type(selected_event_key)
        user_val = 0.0
        input_display_str = ""
        
        with st.container():
            st.markdown("---")
            st.subheader(get_text("input_header", lang_choice).format(selected_label))
            cols = st.columns(4)
            
            if mode == "field":
                m = cols[0].number_input(get_text("label_m", lang_choice), min_value=0, value=0)
                cm = cols[1].number_input(get_text("label_cm", lang_choice), min_value=0, max_value=99, value=0, step=1)
                user_val = float(m) + float(cm) / 100.0
                input_display_str = f"{m}m {cm}cm"
            elif mode == "time_hms":
                h = cols[0].number_input(get_text("label_h", lang_choice), min_value=0, value=0)
                m = cols[1].number_input(get_text("label_min", lang_choice), min_value=0, max_value=59, value=0)
                s = cols[2].number_input(get_text("label_sec", lang_choice), min_value=0, max_value=59, value=0)
                cs = cols[3].number_input(get_text("label_cs", lang_choice), min_value=0, max_value=99, value=0)
                user_val = h*3600 + m*60 + s + (cs/100.0)
                input_display_str = f"{h}:{m:02}:{s:02}.{cs:02}"
            elif mode == "time_ms":
                m = cols[0].number_input(get_text("label_min", lang_choice), min_value=0, value=0)
                s = cols[1].number_input(get_text("label_sec", lang_choice), min_value=0, max_value=59, value=0)
                cs = cols[2].number_input(get_text("label_cs", lang_choice), min_value=0, max_value=99, value=0)
                user_val = m*60 + s + (cs/100.0)
                input_display_str = f"{m}:{s:02}.{cs:02}"
            elif mode == "score":
                pts_in = cols[0].number_input(get_text("label_pts", lang_choice), min_value=0, value=0)
                user_val = float(pts_in)
                input_display_str = f"{pts_in}"
            else:
                s = cols[0].number_input(get_text("label_sec", lang_choice), min_value=0, value=0)
                cs = cols[1].number_input(get_text("label_cs", lang_choice), min_value=0, max_value=99, value=0)
                user_val = float(s) + (cs/100.0)
                input_display_str = f"{s}.{cs:02}"

        if st.button(get_text("calc_button", lang_choice), type="primary"):
            if user_val <= 0:
                st.warning(get_text("warning_input", lang_choice))
            else:
                temp_df = df[[points_col, selected_event_key]].copy()
                temp_df = temp_df[temp_df[selected_event_key] != "-"]
                temp_df = temp_df.dropna(subset=[selected_event_key])
                temp_df['val'] = temp_df[selected_event_key].apply(parse_record_from_csv)
                temp_df = temp_df.dropna(subset=['val'])
                
                if temp_df.empty:
                    st.error("Data not found.")
                else:
                    temp_df['diff'] = (temp_df['val'] - user_val).abs()
                    best_match = temp_df.loc[temp_df['diff'].idxmin()]
                    score = int(best_match[points_col])
                    table_record = best_match[selected_event_key]
                    
                    st.divider()
                    st.subheader(get_text("result_header", lang_choice).format(score))
                    st.write(get_text("input_label", lang_choice).format(input_display_str))
                    st.caption(get_text("approx_label", lang_choice).format(table_record, score))
                    
                    show_affiliate_links(selected_category, lang_choice)

else:
    st.info(get_text("error_no_file", lang_choice).format(gender_choice))
    st.caption(get_text("error_wait", lang_choice))
