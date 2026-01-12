# ==========================================
# Google Colab専用 男子データ診断・修復スクリプト
# (M_ALL_FINAL.csv の表記揺れ・マイクロ秒などをクリーニング)
# ==========================================
import pandas as pd
from google.colab import files
import io
import re
import datetime
import pytz

print("1. クリーニングしたい男子データ(M_ALL_FINAL.csvなど)をアップロードしてください...")
uploaded = files.upload()

if not uploaded:
    print("ファイルが選択されませんでした。")
else:
    filename = next(iter(uploaded))
    print(f"\n読み込み中: {filename}")

    try:
        # CSVを文字列として読み込み（勝手な変換を防ぐため）
        df = pd.read_csv(io.BytesIO(uploaded[filename]), dtype=str)
        print(f"データサイズ: {df.shape[0]}行 × {df.shape[1]}列")

        # 診断レポート用カウンタ
        report = {
            "microsecond_fixed": 0, # .000000 を削除した数
            "date_fixed": 0,        # 1900-01-01 を削除した数
            "serial_fixed": 0,      # シリアル値を復元した数
            "format_fixed": 0       # 03:04:05 -> 3:04:05 に直した数
        }

        # --- クリーニングロジック ---
        def clean_value(val):
            if pd.isna(val) or val.strip() == "" or val == "-":
                return "-"
            
            original_val = val
            val = val.strip()

            # 1. 日付形式 (1900-01-01) の削除
            if "1900" in val:
                val = re.sub(r'\d{4}-\d{2}-\d{2}\s+', '', val)
                if val != original_val:
                    report["date_fixed"] += 1

            # 2. マイクロ秒 (.xxxxxx) の削除
            # 例: 03:34:32.960000 -> 03:34:32.96
            if re.search(r'\.\d{6}$', val):
                # 秒ジャスト(.000000)なら消す、それ以外は1/100秒(2桁)にする
                if re.search(r'\.000000$', val):
                    val = re.sub(r'\.000000$', '', val)
                else:
                    val = re.sub(r'(\.\d{2})\d{4}$', r'\1', val)
                
                if val != original_val:
                    report["microsecond_fixed"] += 1

            # 3. シリアル値 (0.xxxx) の復元
            # Excelで [h]:mm:ss になっていると 1.0未満の小数になる
            try:
                if re.match(r'^0\.\d+$', val):
                    f_val = float(val)
                    # 24時間以内(0.0 ~ 1.0) の場合のみ変換
                    if 0.00001 < f_val < 0.999:
                        total_seconds = int(round(f_val * 24 * 3600))
                        h = total_seconds // 3600
                        m = (total_seconds % 3600) // 60
                        s = total_seconds % 60
                        
                        report["serial_fixed"] += 1
                        if h > 0:
                            return f"{h}:{m:02}:{s:02}"
                        else:
                            return f"{m}:{s:02}"
            except:
                pass

            # 4. 頭のゼロを取る (03:45:00 -> 3:45:00)
            # 見た目をスッキリさせるため
            if re.match(r'^0\d:', val):
                val = re.sub(r'^0', '', val)
                if val != original_val:
                    report["format_fixed"] += 1

            return val

        # --- 全列適用 ---
        print("\n診断と修復を実行中...")
        cols = df.columns
        # Points列を探す (Points, Pts, Scoreなど)
        points_col = [c for c in cols if c.lower() in ["points", "pts", "score"]][0]

        for col in cols:
            if col == points_col: continue
            df[col] = df[col].apply(clean_value)

        # Points列を数値化してソート
        df[points_col] = pd.to_numeric(df[points_col], errors='coerce')
        df = df.dropna(subset=[points_col])
        df[points_col] = df[points_col].astype(int)
        df = df.sort_values(by=points_col, ascending=False)

        # --- 保存ファイル名 ---
        jst = pytz.timezone('Asia/Tokyo')
        now = datetime.datetime.now(jst)
        timestamp_str = now.strftime('%Y%m%d')
        # M_ALL_YYYYMMDD.csv
        output_filename = f"M_ALL_{timestamp_str}.csv"

        # --- レポート表示 ---
        print("\n" + "="*40)
        print(" 【診断レポート】")
        print("="*40)
        print(f"・マイクロ秒(.000000)を削除 : {report['microsecond_fixed']} 箇所")
        print(f"・日付(1900-..)を削除     : {report['date_fixed']} 箇所")
        print(f"・シリアル値を時間に復元   : {report['serial_fixed']} 箇所")
        print(f"・時刻フォーマット整形     : {report['format_fixed']} 箇所")
        print("-" * 40)
        print(f"✅ 保存ファイル名 : {output_filename}")
        print("="*40)

        # 保存とダウンロード
        df.to_csv(output_filename, index=False, encoding='utf-8-sig')
        files.download(output_filename)

    except Exception as e:
        print(f"\nエラーが発生しました: {e}")
