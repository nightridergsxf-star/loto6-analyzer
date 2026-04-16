#!/usr/bin/env python3
"""
ロト6 / ロト7 データ生成スクリプト
分析結果と予測をJSON化して data/<game>/ に出力する
Cloudflare Workers / Pages から読み込む前処理用

Usage:
    python scripts/generate.py                   # 両ゲーム生成
    python scripts/generate.py --game loto6      # ロト6 のみ
    python scripts/generate.py --game loto7      # ロト7 のみ
"""
import argparse
import json
import os
import sys
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from data_source import get_latest_draws
from analysis import run_all
from predict import generate_all_themes, generate_quick
from history import save_predictions_to_history, check_history_against_results, get_history_summary
from game_config import GAMES, get_config


def run_for_game(cfg, project_dir: str):
    data_dir = os.path.join(project_dir, "data", cfg.name)
    os.makedirs(data_dir, exist_ok=True)

    print(f"\n=== {cfg.display_name} ({cfg.name}) ===")

    print("📥 データ取得中...")
    draws = get_latest_draws(project_dir, cfg)
    print(f"✅ {len(draws)}回分のデータを取得")

    print("📊 分析実行中...")
    analysis = run_all(draws, cfg)

    print("🎯 予測生成中...")
    freq_data = analysis["frequency"]
    hot_cold_data = analysis["hot_cold"]
    interval_data = analysis["intervals"]
    pair_data = analysis["pair_correlation"]
    sum_data = analysis["sum"]

    all_predictions = generate_all_themes(
        draws, freq_data, hot_cold_data, interval_data, pair_data, sum_data,
        cfg, n_sets=5
    )
    quick_predictions = generate_quick(
        draws, freq_data, hot_cold_data, interval_data, pair_data, sum_data, cfg
    )

    latest = draws[-1]
    meta = {
        "game": cfg.name,
        "display_name": cfg.display_name,
        "max_number": cfg.max_number,
        "pick_count": cfg.pick_count,
        "bonus_count": cfg.bonus_count,
        "low_high_split": cfg.low_high_split,
        "generated_at": datetime.now().isoformat(),
        "total_draws": len(draws),
        "latest_draw": {
            "number": latest["draw"],
            "date": latest["date"],
            "numbers": latest["numbers"],
            "bonus": latest["bonus"],
            "bonuses": latest.get("bonuses", [latest["bonus"]]),
        },
        "date_range": {
            "from": draws[0]["date"],
            "to": latest["date"],
        },
    }

    recent_draws = [
        {"draw": d["draw"], "date": d["date"], "numbers": d["numbers"],
         "bonus": d["bonus"], "bonuses": d.get("bonuses", [d["bonus"]])}
        for d in draws[-100:]
    ]

    outputs = {
        "meta.json": meta,
        "analysis.json": analysis,
        "predictions.json": {"meta": meta, "themes": all_predictions},
        "quick.json": {"meta": meta, "predictions": quick_predictions},
        "recent_draws.json": {"meta": meta, "draws": recent_draws},
    }

    print("📜 履歴を更新中...")
    history_path = os.path.join(data_dir, "history.json")
    save_predictions_to_history(history_path, all_predictions, meta)
    history = check_history_against_results(history_path, draws, cfg)
    history_summary = get_history_summary(history)

    outputs["history.json"] = {
        "meta": meta,
        "summary": history_summary,
        "entries": history,
    }

    checked_count = history_summary["total_checked"]
    print(f"  📊 照合済み: {checked_count}件")
    if checked_count > 0:
        for theme_key, stats in history_summary["theme_stats"].items():
            print(f"     {theme_key}: 平均{stats['avg_match']}個一致 / 最高{stats['best_match']}個")

    if "pair_correlation" in outputs["analysis.json"]:
        outputs["analysis.json"]["pair_correlation"].pop("pair_counts", None)

    for filename, data in outputs.items():
        path = os.path.join(data_dir, filename)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        size = os.path.getsize(path)
        print(f"  💾 {cfg.name}/{filename} ({size:,} bytes)")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--game", choices=list(GAMES.keys()) + ["all"], default="all")
    args = parser.parse_args()

    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_dir = os.path.dirname(script_dir)

    targets = list(GAMES.values()) if args.game == "all" else [get_config(args.game)]

    for cfg in targets:
        run_for_game(cfg, project_dir)

    print(f"\n✅ 完了！")


if __name__ == "__main__":
    main()
