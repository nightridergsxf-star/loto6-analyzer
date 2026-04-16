"""ロト6 / ロト7 データ取得・整形モジュール"""
import pandas as pd
import subprocess
import os

from game_config import GameConfig


def download_csv(output_dir: str, cfg: GameConfig) -> str:
    """最新CSVをダウンロードしてUTF-8変換。CSVパスを返す"""
    sjis_path = os.path.join(output_dir, cfg.csv_sjis_filename)
    csv_path = os.path.join(output_dir, cfg.csv_filename)
    subprocess.run(
        ["curl", "-s", "-o", sjis_path, cfg.csv_url],
        timeout=30
    )
    with open(csv_path, "w") as f:
        subprocess.run(
            ["iconv", "-f", "SHIFT_JIS", "-t", "UTF-8", sjis_path],
            stdout=f, timeout=10
        )
    return csv_path


def load_draws(csv_path: str, cfg: GameConfig) -> list[dict]:
    """CSVを読み込み、抽選データのリストを返す

    Returns: list of dicts like:
        {
            "draw": 1,
            "date": "2000-10-05",
            "numbers": [2, 8, 10, 13, 27, 30],
            "bonus": 39,              # 互換: bonuses[0]
            "bonuses": [39],          # Loto7 は 2個
        }
    """
    df = pd.read_csv(csv_path)
    draws = []
    for _, row in df.iterrows():
        bonuses = [int(row[c]) for c in cfg.bonus_columns]
        draws.append({
            "draw": int(row["開催回"]),
            "date": pd.to_datetime(row["日付"]).strftime("%Y-%m-%d"),
            "numbers": [int(row[c]) for c in cfg.number_columns],
            "bonus": bonuses[0],
            "bonuses": bonuses,
        })
    return draws


def get_latest_draws(output_dir: str, cfg: GameConfig) -> list[dict]:
    """ダウンロード→読み込みを一括で行う"""
    csv_path = download_csv(output_dir, cfg)
    return load_draws(csv_path, cfg)
