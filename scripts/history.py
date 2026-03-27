"""ロト6 予測履歴・的中チェックモジュール"""
import json
import os
from datetime import datetime


def load_history(history_path: str) -> list[dict]:
    """履歴JSONを読み込む"""
    if os.path.exists(history_path):
        with open(history_path, "r", encoding="utf-8") as f:
            return json.load(f)
    return []


def save_history(history_path: str, history: list[dict]):
    """履歴JSONを保存"""
    with open(history_path, "w", encoding="utf-8") as f:
        json.dump(history, f, ensure_ascii=False, indent=2)


def check_match(prediction_numbers: list[int], actual_numbers: list[int]) -> dict:
    """予測と実際の結果を比較

    Returns:
        {
            "matched_numbers": [int, ...],
            "match_count": int,
            "odd_even_match": bool,
            "high_low_match": bool,
            "sum_range_match": bool,
            "grade": str,  # "perfect", "excellent", "good", "close", "miss"
        }
    """
    pred_set = set(prediction_numbers)
    actual_set = set(actual_numbers)
    matched = sorted(pred_set & actual_set)
    match_count = len(matched)

    # 奇偶一致
    pred_odd = sum(1 for n in prediction_numbers if n % 2 == 1)
    actual_odd = sum(1 for n in actual_numbers if n % 2 == 1)
    odd_even_match = pred_odd == actual_odd

    # 高低一致
    pred_low = sum(1 for n in prediction_numbers if n <= 21)
    actual_low = sum(1 for n in actual_numbers if n <= 21)
    high_low_match = pred_low == actual_low

    # 合計値帯一致（±15以内）
    pred_sum = sum(prediction_numbers)
    actual_sum = sum(actual_numbers)
    sum_range_match = abs(pred_sum - actual_sum) <= 15

    # グレード判定
    if match_count == 6:
        grade = "perfect"
    elif match_count >= 4:
        grade = "excellent"
    elif match_count >= 3:
        grade = "good"
    elif match_count >= 2 or (match_count >= 1 and odd_even_match and sum_range_match):
        grade = "close"
    else:
        grade = "miss"

    return {
        "matched_numbers": matched,
        "match_count": match_count,
        "odd_even_match": odd_even_match,
        "high_low_match": high_low_match,
        "sum_range_match": sum_range_match,
        "grade": grade,
    }


def save_predictions_to_history(history_path: str, predictions_data: dict,
                                 meta: dict) -> dict:
    """今回の予測を履歴に追加する

    Args:
        history_path: 履歴JSONのパス
        predictions_data: generate_all_themes()の結果
        meta: メタ情報

    Returns: 追加した履歴エントリ
    """
    history = load_history(history_path)

    # 最新の抽選回号で既に保存済みか確認
    target_draw = meta["latest_draw"]["number"] + 1  # 次回抽選用の予測
    existing = [h for h in history if h.get("target_draw") == target_draw]
    if existing:
        return existing[0]  # 既に保存済み

    # 各テーマのベスト1を保存
    entry = {
        "generated_at": meta["generated_at"],
        "target_draw": target_draw,
        "based_on_draw": meta["latest_draw"]["number"],
        "based_on_date": meta["latest_draw"]["date"],
        "themes": {},
        "checked": False,
        "actual": None,
    }

    for theme in predictions_data:
        theme_key = theme["theme"]["key"]
        if theme["predictions"]:
            best = theme["predictions"][0]
            entry["themes"][theme_key] = {
                "numbers": best["numbers"],
                "total": best["total"],
                "score": best["score"],
                "reasons": best["reasons"],
            }

    history.append(entry)

    # 直近50件だけ保持
    history = history[-50:]
    save_history(history_path, history)

    return entry


def check_history_against_results(history_path: str, draws: list[dict]) -> list[dict]:
    """未チェックの履歴を実際の結果と照合する

    Args:
        history_path: 履歴JSONのパス
        draws: 全抽選データ

    Returns: 更新された履歴
    """
    history = load_history(history_path)
    draw_map = {d["draw"]: d["numbers"] for d in draws}
    updated = False

    for entry in history:
        if entry["checked"]:
            continue

        target = entry["target_draw"]
        if target not in draw_map:
            continue  # まだ抽選されていない

        actual = draw_map[target]
        entry["actual"] = actual
        entry["checked"] = True
        entry["results"] = {}

        for theme_key, pred in entry["themes"].items():
            result = check_match(pred["numbers"], actual)
            entry["results"][theme_key] = result

        updated = True

    if updated:
        save_history(history_path, history)

    return history


def get_history_summary(history: list[dict]) -> dict:
    """履歴の集計サマリーを生成

    Returns:
        {
            "total_checked": int,
            "theme_stats": {
                "balanced": {"avg_match": float, "best_match": int, "grades": {...}},
                ...
            },
            "recent": [最新5件の履歴],
        }
    """
    checked = [h for h in history if h.get("checked")]

    theme_stats = {}
    for entry in checked:
        for theme_key, result in entry.get("results", {}).items():
            if theme_key not in theme_stats:
                theme_stats[theme_key] = {
                    "matches": [],
                    "grades": {"perfect": 0, "excellent": 0, "good": 0, "close": 0, "miss": 0},
                    "odd_even_matches": 0,
                    "sum_range_matches": 0,
                    "total": 0,
                }
            stats = theme_stats[theme_key]
            stats["matches"].append(result["match_count"])
            stats["grades"][result["grade"]] += 1
            stats["total"] += 1
            if result["odd_even_match"]:
                stats["odd_even_matches"] += 1
            if result["sum_range_match"]:
                stats["sum_range_matches"] += 1

    # 平均と最高を計算
    for key, stats in theme_stats.items():
        if stats["matches"]:
            stats["avg_match"] = round(sum(stats["matches"]) / len(stats["matches"]), 2)
            stats["best_match"] = max(stats["matches"])
        else:
            stats["avg_match"] = 0
            stats["best_match"] = 0
        del stats["matches"]  # 詳細リストは不要

    return {
        "total_checked": len(checked),
        "theme_stats": theme_stats,
        "recent": checked[-5:][::-1],  # 最新5件を新しい順に
    }
