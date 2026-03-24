"""ロト6 データ取得・整形モジュール"""
import pandas as pd
import subprocess
import os

def download_csv(output_dir: str) -> str:
    """最新CSVをダウンロードしてUTF-8変換。CSVパスを返す"""
    sjis_path = os.path.join(output_dir, "loto6_sjis.csv")
    csv_path = os.path.join(output_dir, "loto6.csv")
    subprocess.run(
        ["curl", "-s", "-o", sjis_path,
         "https://loto6.thekyo.jp/data/loto6.csv"],
        timeout=30
    )
    with open(csv_path, "w") as f:
        subprocess.run(
            ["iconv", "-f", "SHIFT_JIS", "-t", "UTF-8", sjis_path],
            stdout=f, timeout=10
        )
    return csv_path

def load_draws(csv_path: str) -> list[dict]:
    """CSVを読み込み、抽選データのリストを返す

    Returns: list of dicts like:
        {
            "draw": 1,
            "date": "2000-10-05",
            "numbers": [2, 8, 10, 13, 27, 30],
            "bonus": 39,
        }
    """
    df = pd.read_csv(csv_path)
    num_cols = [f"第{i}数字" for i in range(1, 7)]
    draws = []
    for _, row in df.iterrows():
        draws.append({
            "draw": int(row["開催回"]),
            "date": pd.to_datetime(row["日付"]).strftime("%Y-%m-%d"),
            "numbers": [int(row[c]) for c in num_cols],
            "bonus": int(row["BONUS数字"]),
        })
    return draws

def get_latest_draws(output_dir: str) -> list[dict]:
    """ダウンロード→読み込みを一括で行う"""
    csv_path = download_csv(output_dir)
    return load_draws(csv_path)
