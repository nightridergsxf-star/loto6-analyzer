#!/usr/bin/env python3
"""
ロト6 データ生成スクリプト
分析結果と予測をJSON化して data/ に出力する
Cloudflare Workers / Pages から読み込む前処理用
"""
import json
import os
import sys
from datetime import datetime

# scriptsディレクトリをパスに追加
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from data_source import get_latest_draws
from analysis import run_all, frequency, hot_cold, intervals, pair_correlation, sum_analysis
from predict import generate_all_themes, generate_quick


def main():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_dir = os.path.dirname(script_dir)
    data_dir = os.path.join(project_dir, "data")
    os.makedirs(data_dir, exist_ok=True)

    # 1. データ取得
    print("📥 データ取得中...")
    draws = get_latest_draws(project_dir)
    print(f"✅ {len(draws)}回分のデータを取得")

    # 2. 全分析実行
    print("📊 分析実行中...")
    analysis = run_all(draws)

    # 3. 予測生成
    print("🎯 予測生成中...")
    freq_data = analysis["frequency"]
    hot_cold_data = analysis["hot_cold"]
    interval_data = analysis["intervals"]
    pair_data = analysis["pair_correlation"]
    sum_data = analysis["sum"]

    all_predictions = generate_all_themes(
        draws, freq_data, hot_cold_data, interval_data, pair_data, sum_data,
        n_sets=5
    )
    quick_predictions = generate_quick(
        draws, freq_data, hot_cold_data, interval_data, pair_data, sum_data
    )

    # 4. メタ情報
    latest = draws[-1]
    meta = {
        "generated_at": datetime.now().isoformat(),
        "total_draws": len(draws),
        "latest_draw": {
            "number": latest["draw"],
            "date": latest["date"],
            "numbers": latest["numbers"],
            "bonus": latest["bonus"],
        },
        "date_range": {
            "from": draws[0]["date"],
            "to": latest["date"],
        },
    }

    # 5. JSON出力
    # 直近の抽選データ（フロント表示用、直近100回分）
    recent_draws = [
        {"draw": d["draw"], "date": d["date"], "numbers": d["numbers"], "bonus": d["bonus"]}
        for d in draws[-100:]
    ]

    outputs = {
        "meta.json": meta,
        "analysis.json": analysis,
        "predictions.json": {
            "meta": meta,
            "themes": all_predictions,
        },
        "quick.json": {
            "meta": meta,
            "predictions": quick_predictions,
        },
        "recent_draws.json": {
            "meta": meta,
            "draws": recent_draws,
        },
    }

    # pair_counts は巨大なので analysis.json からは除外
    if "pair_correlation" in outputs["analysis.json"]:
        outputs["analysis.json"]["pair_correlation"].pop("pair_counts", None)

    for filename, data in outputs.items():
        path = os.path.join(data_dir, filename)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        size = os.path.getsize(path)
        print(f"  💾 {filename} ({size:,} bytes)")

    print(f"\n✅ 完了！{len(outputs)}ファイルを {data_dir} に出力しました")


if __name__ == "__main__":
    main()
