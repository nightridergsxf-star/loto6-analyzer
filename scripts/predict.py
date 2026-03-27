"""ロト6 予測生成モジュール"""
import numpy as np
from datetime import datetime
from scoring import THEMES, compute_raw_scores, apply_theme, score_combination


def generate_predictions(draws: list[dict], freq_data: dict, hot_cold_data: dict,
                         interval_data: dict, pair_data: dict, sum_data: dict,
                         theme_key: str = "balanced", n_sets: int = 5,
                         seed: int = None) -> dict:
    """指定テーマで予測番号セットを生成

    Returns:
        {
            "theme": {"key": str, "name": str, "icon": str, "description": str},
            "top10": [{"number": int, "score": float}, ...],
            "predictions": [
                {
                    "numbers": [int, ...],
                    "total": int,
                    "odd_even": {"odd": int, "even": int},
                    "high_low": {"low": int, "high": int},
                    "score": float,
                    "combo_score": float,
                    "reasons": [str, ...],
                }
            ]
        }
    """
    if seed is None:
        seed = int(datetime.now().timestamp())
    np.random.seed(seed)

    theme = THEMES[theme_key]
    sum_mean = sum_data["mean"]
    sum_std = sum_data["std"]

    # 生スコア計算
    raw_scores = compute_raw_scores(draws, freq_data, hot_cold_data, interval_data, pair_data)

    # テーマ重み適用
    scores = apply_theme(raw_scores, theme_key)

    # ランキング
    ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    top10 = [{"number": int(n), "score": round(s, 2)} for n, s in ranked[:10]]

    # ソフトマックスで確率変換
    score_arr = np.array([scores[n] for n in range(1, 44)])
    temperature = theme["temperature"]
    sum_weight = theme["sum_weight"]

    exp_scores = np.exp((score_arr - score_arr.max()) / temperature)
    probs = exp_scores / exp_scores.sum()

    # ルーレット選択
    is_contrarian = theme.get("contrarian", False)
    sets = []
    attempts = 0
    while len(sets) < n_sets * 4 and attempts < 20000:
        attempts += 1
        chosen = sorted([int(x) for x in np.random.choice(range(1, 44), size=6, replace=False, p=probs)])
        s = sum(chosen)
        if s < 40 or s > 220:
            continue
        combo = score_combination(chosen, scores, sum_mean, sum_std, contrarian=is_contrarian)
        num_score = sum(scores[n] for n in chosen)
        total_score = num_score + combo * sum_weight
        sets.append((chosen, round(total_score, 2), round(combo, 2)))

    # 上位を採用
    sets.sort(key=lambda x: x[1], reverse=True)
    best = sets[:n_sets]

    # 理由を生成
    hot_nums = {item["number"] for item in hot_cold_data["hot"][:5]}
    overdue_nums = {item["number"] for item in interval_data.get("overdue_top5", [])}
    last_nums = set(draws[-1]["numbers"])

    predictions = []
    for nums, total_s, combo_s in best:
        reasons = []
        hot_in = [n for n in nums if n in hot_nums]
        cold_in = [n for n in nums if n in overdue_nums]
        carry_in = [n for n in nums if n in last_nums]

        if hot_in:
            reasons.append(f"{','.join(map(str, hot_in))}は直近ホット")
        if cold_in:
            reasons.append(f"{','.join(map(str, cold_in))}は出遅れ反発")
        if carry_in:
            reasons.append(f"{','.join(map(str, carry_in))}は前回引っ張り")

        odd = sum(1 for n in nums if n % 2 == 1)
        even = 6 - odd
        low = sum(1 for n in nums if n <= 21)
        high = 6 - low
        s = sum(nums)

        if abs(odd - even) <= 1:
            reasons.append(f"奇偶バランス{odd}:{even}")

        optimal = sum_data["optimal_range"]
        if optimal["low"] <= s <= optimal["high"]:
            reasons.append("合計値が最適帯")

        # 逆張りモード固有の理由
        if is_contrarian:
            high_zone = [n for n in nums if n >= 32]
            if high_zone:
                reasons.append(f"{','.join(map(str, high_zone))}は誕生日圏外")
            sorted_nums = sorted(nums)
            has_consec = any(sorted_nums[i+1] - sorted_nums[i] == 1 for i in range(len(sorted_nums)-1))
            if not has_consec:
                reasons.append("連番なし（人が選ぶパターンを回避）")
            round_nums = {5, 10, 15, 20, 25, 30, 35, 40}
            if not any(n in round_nums for n in nums):
                reasons.append("キリ番なし")

        predictions.append({
            "numbers": nums,
            "total": s,
            "odd_even": {"odd": odd, "even": even},
            "high_low": {"low": low, "high": high},
            "score": total_s,
            "combo_score": combo_s,
            "reasons": reasons,
        })

    return {
        "theme": {
            "key": theme_key,
            "name": theme["name"],
            "icon": theme["icon"],
            "description": theme["description"],
        },
        "top10": top10,
        "predictions": predictions,
    }


def generate_all_themes(draws: list[dict], freq_data: dict, hot_cold_data: dict,
                        interval_data: dict, pair_data: dict, sum_data: dict,
                        n_sets: int = 5) -> list[dict]:
    """全テーマで予測を生成"""
    results = []
    for theme_key in THEMES:
        result = generate_predictions(
            draws, freq_data, hot_cold_data, interval_data, pair_data, sum_data,
            theme_key=theme_key, n_sets=n_sets
        )
        results.append(result)
    return results


def generate_quick(draws: list[dict], freq_data: dict, hot_cold_data: dict,
                   interval_data: dict, pair_data: dict, sum_data: dict) -> list[dict]:
    """各テーマからベスト1セットずつ"""
    results = []
    for theme_key in THEMES:
        result = generate_predictions(
            draws, freq_data, hot_cold_data, interval_data, pair_data, sum_data,
            theme_key=theme_key, n_sets=1
        )
        if result["predictions"]:
            results.append({
                "theme": result["theme"],
                "numbers": result["predictions"][0]["numbers"],
                "total": result["predictions"][0]["total"],
                "reasons": result["predictions"][0]["reasons"],
            })
    return results
