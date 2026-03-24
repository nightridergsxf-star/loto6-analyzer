"""ロト6 分析モジュール（全13種）- 純粋データ返却、表示なし"""
import numpy as np
from collections import Counter, defaultdict
from itertools import combinations


def frequency(draws: list[dict]) -> dict:
    """各番号(1-43)の出現回数・出現率"""
    all_nums = []
    for d in draws:
        all_nums.extend(d["numbers"])

    total = len(draws)
    freq = Counter(all_nums)
    expected = total * 6 / 43

    numbers = {}
    for n in range(1, 44):
        count = freq.get(n, 0)
        numbers[n] = {
            "count": count,
            "rate": round(count / total * 100, 2),
            "deviation": round(count - expected, 1),
        }

    sorted_by_count = sorted(freq.items(), key=lambda x: x[1], reverse=True)
    return {
        "total_draws": total,
        "expected": round(expected, 1),
        "numbers": numbers,
        "top10": [{"number": n, "count": c} for n, c in sorted_by_count[:10]],
        "worst10": [{"number": n, "count": c} for n, c in sorted_by_count[-10:]],
    }


def bonus_frequency(draws: list[dict]) -> dict:
    """ボーナス数字の出現傾向"""
    freq = Counter(d["bonus"] for d in draws)
    sorted_freq = sorted(freq.items(), key=lambda x: x[1], reverse=True)
    return {
        "top10": [{"number": n, "count": c} for n, c in sorted_freq[:10]],
        "worst10": [{"number": n, "count": c} for n, c in sorted_freq[-10:]],
    }


def consecutive_pairs(draws: list[dict]) -> dict:
    """連番ペアの出現分析"""
    consec_per_draw = []
    draws_with = 0

    for d in draws:
        nums = sorted(d["numbers"])
        count = sum(1 for i in range(len(nums)-1) if nums[i+1] - nums[i] == 1)
        consec_per_draw.append(count)
        if count > 0:
            draws_with += 1

    total = len(draws)
    dist = Counter(consec_per_draw)
    return {
        "draws_with_consecutive": draws_with,
        "total_draws": total,
        "rate": round(draws_with / total * 100, 1),
        "average_per_draw": round(float(np.mean(consec_per_draw)), 2),
        "distribution": {str(k): {"count": dist[k], "rate": round(dist[k]/total*100, 1)}
                        for k in sorted(dist.keys())},
    }


def odd_even_balance(draws: list[dict]) -> dict:
    """奇数・偶数の比率"""
    patterns = Counter()
    for d in draws:
        odd = sum(1 for n in d["numbers"] if n % 2 == 1)
        patterns[(odd, 6 - odd)] += 1

    total = len(draws)
    return {
        "distribution": [
            {"odd": o, "even": e, "count": patterns[(o, e)], "rate": round(patterns[(o, e)]/total*100, 1)}
            for o, e in sorted(patterns.keys())
        ]
    }


def high_low_balance(draws: list[dict]) -> dict:
    """高低バランス (低1-21 / 高22-43)"""
    patterns = Counter()
    for d in draws:
        low = sum(1 for n in d["numbers"] if n <= 21)
        patterns[(low, 6 - low)] += 1

    total = len(draws)
    return {
        "distribution": [
            {"low": lo, "high": hi, "count": patterns[(lo, hi)], "rate": round(patterns[(lo, hi)]/total*100, 1)}
            for lo, hi in sorted(patterns.keys())
        ]
    }


def decade_distribution(draws: list[dict]) -> dict:
    """十の位グループの分布"""
    groups = [("1-9", 1, 9), ("10-19", 10, 19), ("20-29", 20, 29), ("30-39", 30, 39), ("40-43", 40, 43)]
    counts = defaultdict(int)
    total_nums = 0

    for d in draws:
        for n in d["numbers"]:
            total_nums += 1
            for name, lo, hi in groups:
                if lo <= n <= hi:
                    counts[name] += 1
                    break

    return {
        "groups": [
            {"name": name, "count": counts[name],
             "rate": round(counts[name]/total_nums*100, 1),
             "expected_rate": round((hi-lo+1)/43*100, 1)}
            for name, lo, hi in groups
        ]
    }


def tail_distribution(draws: list[dict]) -> dict:
    """末尾数字の分布"""
    tails = Counter()
    total_nums = 0
    for d in draws:
        for n in d["numbers"]:
            tails[n % 10] += 1
            total_nums += 1

    return {
        "distribution": [
            {"tail": t, "count": tails[t], "rate": round(tails[t]/total_nums*100, 1)}
            for t in range(10)
        ]
    }


def hot_cold(draws: list[dict], recent_n: int = 30) -> dict:
    """直近N回のホット/コールドナンバー"""
    recent = draws[-recent_n:]
    recent_nums = []
    for d in recent:
        recent_nums.extend(d["numbers"])

    freq = Counter(recent_nums)
    expected = recent_n * 6 / 43

    all_numbers = set(range(1, 44))
    appeared = set(freq.keys())
    not_appeared = sorted(all_numbers - appeared)

    hot = sorted(freq.items(), key=lambda x: x[1], reverse=True)[:10]
    cold_list = [(n, freq.get(n, 0)) for n in range(1, 44)]
    cold = sorted(cold_list, key=lambda x: x[1])[:10]

    return {
        "recent_n": recent_n,
        "expected": round(expected, 1),
        "hot": [{"number": n, "count": c, "ratio": round(c/expected, 1)} for n, c in hot],
        "cold": [{"number": n, "count": c} for n, c in cold],
        "not_appeared": not_appeared,
        "freq": {n: freq.get(n, 0) for n in range(1, 44)},
    }


def intervals(draws: list[dict]) -> dict:
    """出現間隔（インターバル）分析"""
    last_seen = {}
    interval_data = defaultdict(list)

    for d in draws:
        draw_num = d["draw"]
        for n in d["numbers"]:
            if n in last_seen:
                interval_data[n].append(draw_num - last_seen[n])
            last_seen[n] = draw_num

    latest_draw = draws[-1]["draw"]
    current = {}
    for n in range(1, 44):
        current[n] = latest_draw - last_seen[n] if n in last_seen else latest_draw

    numbers = {}
    overdue = []
    for n in range(1, 44):
        if interval_data[n]:
            avg = float(np.mean(interval_data[n]))
            max_int = max(interval_data[n])
            cur = current[n]
            is_overdue = cur > avg * 1.5
            numbers[n] = {
                "avg_interval": round(avg, 1),
                "max_interval": max_int,
                "current_interval": cur,
                "overdue": is_overdue,
            }
            if is_overdue:
                overdue.append({"number": n, "current": cur, "avg": round(avg, 1), "ratio": round(cur/avg, 1)})

    overdue.sort(key=lambda x: x["ratio"], reverse=True)

    return {
        "numbers": numbers,
        "overdue_top5": overdue[:5],
        "intervals": {n: interval_data[n] for n in range(1, 44)},
        "current": current,
    }


def carryover(draws: list[dict]) -> dict:
    """前回引っ張り分析"""
    counts = []
    for i in range(1, len(draws)):
        prev = set(draws[i-1]["numbers"])
        curr = set(draws[i]["numbers"])
        counts.append(len(prev & curr))

    dist = Counter(counts)
    total = len(counts)
    return {
        "average": round(float(np.mean(counts)), 2),
        "distribution": [
            {"overlap": k, "count": dist[k], "rate": round(dist[k]/total*100, 1)}
            for k in sorted(dist.keys())
        ],
    }


def sum_analysis(draws: list[dict]) -> dict:
    """合計値分析"""
    sums = [sum(d["numbers"]) for d in draws]
    mean = float(np.mean(sums))
    std = float(np.std(sums))

    bins = [(50, 80), (81, 100), (101, 120), (121, 140), (141, 160), (161, 180), (181, 210)]
    total = len(sums)

    return {
        "mean": round(mean, 1),
        "median": round(float(np.median(sums)), 1),
        "std": round(std, 1),
        "min": min(sums),
        "max": max(sums),
        "optimal_range": {"low": round(mean - std), "high": round(mean + std)},
        "distribution": [
            {"range": f"{lo}-{hi}", "count": sum(1 for s in sums if lo <= s <= hi),
             "rate": round(sum(1 for s in sums if lo <= s <= hi)/total*100, 1)}
            for lo, hi in bins
        ],
    }


def monthly(draws: list[dict]) -> dict:
    """月別出現傾向"""
    from datetime import datetime
    monthly_freq = defaultdict(Counter)
    for d in draws:
        month = int(d["date"].split("-")[1])
        for n in d["numbers"]:
            monthly_freq[month][n] += 1

    result = {}
    for m in range(1, 13):
        top5 = monthly_freq[m].most_common(5)
        result[str(m)] = [{"number": n, "count": c} for n, c in top5]
    return result


def pair_correlation(draws: list[dict]) -> dict:
    """ペア相関分析"""
    pair_counts = Counter()
    for d in draws:
        for pair in combinations(sorted(d["numbers"]), 2):
            pair_counts[pair] += 1

    total = len(draws)
    expected = total * (6 * 5) / (43 * 42)

    top20 = pair_counts.most_common(20)
    return {
        "expected": round(expected, 1),
        "top20": [{"pair": [a, b], "count": c, "ratio": round(c/expected, 2)}
                  for (a, b), c in top20],
        "pair_counts": {f"{a},{b}": c for (a, b), c in pair_counts.items()},
        "pair_expected": expected,
    }


def run_all(draws: list[dict]) -> dict:
    """全分析を実行して結果をまとめて返す"""
    return {
        "frequency": frequency(draws),
        "bonus": bonus_frequency(draws),
        "consecutive": consecutive_pairs(draws),
        "odd_even": odd_even_balance(draws),
        "high_low": high_low_balance(draws),
        "decade": decade_distribution(draws),
        "tail": tail_distribution(draws),
        "hot_cold": hot_cold(draws),
        "intervals": intervals(draws),
        "carryover": carryover(draws),
        "sum": sum_analysis(draws),
        "monthly": monthly(draws),
        "pair_correlation": pair_correlation(draws),
    }
