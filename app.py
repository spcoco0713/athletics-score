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

# ==========================================
# ★ アフィリエイト設定エリア
# ==========================================
# あなたのアソシエイトID (トラッキングID)
AMAZON_TAG = "athleticsscor-22" 

def get_amazon_link(keyword):
    """キーワード検索結果へのアフィリエイトリンクを生成する"""
    base_url = "https://www.amazon.co.jp/s"
    return f"{base_url}?k={keyword}&tag={AMAZON_TAG}"

def show_affiliate_links(category_name):
    """カテゴリに応じたおすすめ商品を表示する"""
    st.divider()
    st.markdown("### 🛒 競技力向上のための厳選アイテム")
    st.caption(f"※{category_name}選手におすすめのギアをAmazonで探せます")

    col1, col2 = st.columns(2)

    # --- カテゴリ別のおすすめ商品定義 ---
    if category_name == "短距離・ハードル・リレー":
        with col1:
            st.info("👟 **短距離スパイク**")
            st.markdown(f"100m〜400m向けの最新モデル。\n\n[Amazonで探す ➤]({get_amazon_link('陸上スパイク 短距離')})")
        with col2:
            st.info("⏱ **ストップウォッチ**")
            st.markdown(f"指導者・マネージャーの必需品。\n\n[Amazonで探す ➤]({get_amazon_link('セイコー ストップウォッチ 陸上')})")

    elif category_name in ["中長距離・障害", "ロード・競歩", "競歩（トラック）"]:
        with col1:
            st.info("👟 **ランニングシューズ**")
            st.markdown(f"厚底から薄底まで。\n\n[Amazonで探す ➤]({get_amazon_link('ランニングシューズ 厚底')})")
        with col2:
            st.info("⌚ **GPSウォッチ**")
            st.markdown(f"Garminなどペース管理に。\n\n[Amazonで探す ➤]({get_amazon_link('ガーミン ランニングウォッチ')})")
            
    elif category_name == "跳躍":
        with col1:
            st.info("👟 **跳躍用スパイク**")
            st.markdown(f"走幅跳・高跳・三段跳・棒高跳。\n\n[Amazonで探す ➤]({get_amazon_link('陸上スパイク 跳躍')})")
        with col2:
            st.info("🩹 **テーピング・サポーター**")
            st.markdown(f"足首や膝の保護に。\n\n[Amazonで探す ➤]({get_amazon_link('キネシオロジーテープ 50mm')})")

    elif category_name == "投てき":
        with col1:
            st.info("👟 **投てきシューズ**")
            st.markdown(f"回転用・グライド用。\n\n[Amazonで探す ➤]({get_amazon_link('陸上 投てきシューズ')})")
        with col2:
            st.info("💪 **ウエイトトレーニング**")
            st.markdown(f"ベルトやリストラップなど。\n\n[Amazonで探す ➤]({get_amazon_link('トレーニングベルト')})")

    else: # 混成などその他
        with col1:
            st.info("👟 **陸上スパイク**")
            st.markdown(f"全種目対応モデルなど。\n\n[Amazonで探す ➤]({get_amazon_link('陸上スパイク')})")
        with col2:
            st.info("🥤 **プロテイン・サプリ**")
            st.markdown(f"リカバリーと体づくりに。\n\n[Amazonで探す ➤]({get_amazon_link('ホエイプロテイン')})")

    # --- 全員におすすめ (下段) ---
    st.markdown("") # 余白
    with st.expander("🥤 全アスリートにおすすめ (プロテイン・ケア用品)"):
        c1, c2, c3 = st.columns(3)
        with c1:
            st.markdown(f"**プロテイン**\n\n[Amazonを見る]({get_amazon_link('ザバス プロテイン')})")
        with c2:
            st.markdown(f"**フォームローラー**\n\n[Amazonを見る]({get_amazon_link('フォームローラー 筋膜リリース')})")
        with c3:
            st.markdown(f"**アミノ酸 (BCAA)**\n\n[Amazonを見る]({get_amazon_link('アミノバイタル')})")


# --- 以下、既存のロジック ---

# --- 種目名の日英翻訳辞書 (完全版: Wとshの徹底排除) ---
EVENT_TRANSLATION = {
    # --- 短距離 ---
    "50m": "50m", "55m": "55m", "60m": "60m",
    "100m": "100m", "100y": "100ヤード",
    "200m": "200m", "300m": "300m", "400m": "400m",
    "500m": "500m", "600m": "600m",
    
    # --- ショートトラック短距離 (sh -> ST) ---
    "50m sh": "50m (ST)", "55m sh": "55m (ST)", "60m sh": "60m (ST)",
    "200m sh": "200m (ST)", "300m sh": "300m (ST)", "400m sh": "400m (ST)",
    "300y sh": "300ヤード (ST)", "440y sh": "440ヤード (ST)",
    
    # --- ハードル ---
    "50mH": "50mハードル", "55mH": "55mハードル", "60mH": "60mハードル",
    "100mH": "100mハードル", # 女子用
    "110mH": "110mハードル", 
    "200mH": "200mハードル", "300mH": "300mハードル", "400mH": "400mハードル",
    
    # --- ショートトラックハードル ---
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
    "HM": "ハーフマラソン", "Marathon": "マラソン", 
    "Road Relay": "ロードリレー",

    # --- 競歩 (トラック) mW ---
    "3000mW": "3000m競歩", "5000mW": "5000m競歩", "10000mW": "10000m競歩", "10,000mW": "10000m競歩",
    "15,000mW": "15000m競歩", "20,000mW": "20000m競歩", 
    "30,000mW": "30000m競歩", "35,000mW": "35000m競歩", "50,000mW": "50000m競歩",
    
    # --- 競歩 (ロード) W / MarW / HMW ---
    "3km W": "3km競歩", "5km W": "5km競歩", "10km W": "10km競歩", 
    "15km W": "15km競歩", "20km W": "20km競歩", "25km W": "25km競歩",
    "30km W": "30km競歩", "35km W": "35km競歩", "50km W": "50km競歩",
    "MarW": "マラソン競歩", "HMW": "ハーフマラソン競歩",

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
    "Distance Medley Relay": "メドレーリレー",
    "Sprint Medley Relay": "スプリントメドレーリレー"
}

# --- カテゴリ定義 ---
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

CATEGORY_ORDER = [
    "短距離・ハードル・リレー",
    "中長距離・障害",
    "跳躍",
    "投てき",
    "競歩（トラック）",
    "ロード（長距離・競歩）",
    "混成競技"
]

@st.cache_data
def load_data():
    csv_files = glob.glob("M_ALL_*.csv")
    if not csv_files: return None, None
    latest_file = sorted(csv_files)[-1]
    try:
        df = pd.read_csv(latest_file)
        points_col = [c for c in df.columns if c.lower() in ["points", "pts", "score"]][0]
        return df, points_col
    except Exception: return None, None

df, points_col = load_data()

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
        if any(k in name for k in ['3000', '5000', '10000', '10,000', '3km', '5km', '10km']): return "time_ms"
        else: return "time_hms"
    long_dist_keywords = ['marathon', 'hm', 'hour', '15 km', '20 km', '25 km', '30 km', '35 km', '50 km', '100 km', 'miles']
    if name == 'hm': return "time_hms"
    if any(k in name for k in long_dist_keywords): return "time_hms"
    middle_keywords = ['800m', '1000m', '1500m', '2000m', '3000m', '5000m', '10000m', 'mile', 'sc', 'steeple', '4x', 'relay']
    if any(k in name for k in middle_keywords): return "time_ms"
    if '5 km' in name or '10 km' in name: return "time_ms"
    return "time_s"

# --- メイン画面 ---
st.title("IAAFスコア計算ツール")
st.caption("World Athletics Scoring Tables (旧IAAF採点表) に基づくスコア検索")

if df is not None:
    raw_event_list = [c for c in df.columns if c != points_col]
    all_events_map = {}
    categorized_events = {cat: [] for cat in CATEGORY_ORDER}
    for eng_name in raw_event_list:
        jp_name = EVENT_TRANSLATION.get(eng_name, eng_name)
        all_events_map[jp_name] = eng_name
        cat = classify_event(jp_name)
        if cat in categorized_events: categorized_events[cat].append(jp_name)
        else: categorized_events["短距離・ハードル・リレー"].append(jp_name)

    for cat in categorized_events:
        categorized_events[cat].sort()
        top_priority = ["100m", "200m", "400m", "110mハードル", "400mハードル", 
                        "800m", "1500m", "5000m", "10000m",
                        "走高跳", "棒高跳", "走幅跳", "三段跳",
                        "砲丸投", "円盤投", "ハンマー投", "やり投",
                        "十種競技", "マラソン", "ハーフマラソン",
                        "5000m競歩", "10000m競歩", "20km競歩", "35km競歩", "50km競歩"]
        priority_items = [e for e in categorized_events[cat] if e in top_priority]
        other_items = [e for e in categorized_events[cat] if e not in top_priority]
        sorted_priority = sorted(priority_items, key=lambda x: top_priority.index(x) if x in top_priority else 999)
        categorized_events[cat] = sorted_priority + other_items

    selected_category = st.radio("カテゴリを選択してください", CATEGORY_ORDER, horizontal=True)
    events_in_cat = categorized_events[selected_category]
    
    if not events_in_cat:
        st.warning("このカテゴリの種目データがありません。")
        selected_label = None
    else:
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
            else:
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
                    
                    # ★ 収益化エリア（カテゴリごとに変化）
                    show_affiliate_links(selected_category)

else:
    st.error("システムエラー: データファイルが見つかりません。管理者に連絡してください。")
