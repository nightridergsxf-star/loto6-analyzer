"""ロト6 / ロト7 分析モジュール（全13種）- 純粋データ返却、表示なし"""
import numpy as np
from collections import Counter, defaultdict
from itertools import combinations

from game_config import GameConfig


def frequency(draws: list[dict], cfg: GameConfig) -> dict:
    """各番号の出現回数・出現率"""
    all_nums = []
    for d in draws:
        all_nums.extend(d["numbers"])

    total = len(draws)
    freq = Counter(all_nums)
    expected = total * cfg.pick_count / cfg.max_number

    numbers = {}
    for n in cfg.number_range:
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


def bonus_frequency(draws: list[dict], cfg: GameConfig) -> dict:
    """ボーナス数字の出現傾向 (Loto7 は 2個分を合算)"""
    all_bonuses = []
    for d in draws:
        all_bonuses.extend(d.get("bonuses", [d["bonus"]]))
    freq = Counter(all_bonuses)
    sorted_freq = sorted(freq.items(), key=lambda x: x[1], reverse=True)
    return {
        "top10": [{"number": n, "count": c} for n, c in sorted_freq[:10]],
        "worst10": [{"number": n, "count": c} for n, c in sorted_freq[-10:]],
    }


def consecutive_pairs(draws: list[dict], cfg: GameConfig) -> dict:
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


def odd_even_balance(draws: list[dict], cfg: GameConfig) -> dict:
    """奇数・偶数の比率"""
    patterns = Counter()
    for d in draws:
        odd = sum(1 for n in d["numbers"] if n % 2 == 1)
        patterns[(odd, cfg.pick_count - odd)] += 1

    total = len(draws)
    return {
        "distribution": [
            {"odd": o, "even": e, "count": patterns[(o, e)], "rate": round(patterns[(o, e)]/total*100, 1)}
            for o, e in sorted(patterns.keys())
        ]
    }


def high_low_balance(draws: list[dict], cfg: GameConfig) -> dict:
    """高低バランス (低1〜split / 高 split+1〜max)"""
    patterns = Counter()
    for d in draws:
        low = sum(1 for n in d["numbers"] if n <= cfg.low_high_split)
        patterns[(low, cfg.pick_count - low)] += 1

    total = len(draws)
    return {
        "distribution": [
            {"low": lo, "high": hi, "count": patterns[(lo, hi)], "rate": round(patterns[(lo, hi)]/total*100, 1)}
            for lo, hi in sorted(patterns.keys())
        ]
    }


def decade_distribution(draws: list[dict], cfg: GameConfig) -> dict:
    """十の位グループの分布"""
    groups = cfg.decade_buckets
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
             "expected_rate": round((hi-lo+1)/cfg.max_number*100, 1)}
            for name, lo, hi in groups
        ]
    }


def tail_distribution(draws: list[dict], cfg: GameConfig) -> dict:
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


def hot_cold(draws: list[dict], cfg: GameConfig, recent_n: int = 30) -> dict:
    """直近N回のホット/コールドナンバー"""
    recent = draws[-recent_n:]
    recent_nums = []
    for d in recent:
        recent_nums.extend(d["numbers"])

    freq = Counter(recent_nums)
    expected = recent_n * cfg.pick_count / cfg.max_number

    all_numbers = set(cfg.number_range)
    appeared = set(freq.keys())
    not_appeared = sorted(all_numbers - appeared)

    hot = sorted(freq.items(), key=lambda x: x[1], reverse=True)[:10]
    cold_list = [(n, freq.get(n, 0)) for n in cfg.number_range]
    cold = sorted(cold_list, key=lambda x: x[1])[:10]

    return {
        "recent_n": recent_n,
        "expected": round(expected, 1),
        "hot": [{"number": n, "count": c, "ratio": round(c/expected, 1)} for n, c in hot],
        "cold": [{"number": n, "count": c} for n, c in cold],
        "not_appeared": not_appeared,
        "freq": {n: freq.get(n, 0) for n in cfg.number_range},
    }


def intervals(draws: list[dict], cfg: GameConfig) -> dict:
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
    for n in cfg.number_range:
        current[n] = latest_draw - last_seen[n] if n in last_seen else latest_draw

    numbers = {}
    overdue = []
    for n in cfg.number_range:
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
        "intervals": {n: interval_data[n] for n in cfg.number_range},
        "current": current,
    }


def carryover(draws: list[dict], cfg: GameConfig) -> dict:
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


def sum_analysis(draws: list[dict], cfg: GameConfig) -> dict:
    """合計値分析"""
    sums = [sum(d["numbers"]) for d in draws]
    mean = float(np.mean(sums))
    std = float(np.std(sums))

    bins = cfg.sum_bins
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


def monthly(draws: list[dict], cfg: GameConfig) -> dict:
    """月別出現傾向"""
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


def pair_correlation(draws: list[dict], cfg: GameConfig) -> dict:
    """ペア相関分析"""
    pair_counts = Counter()
    for d in draws:
        for pair in combinations(sorted(d["numbers"]), 2):
            pair_counts[pair] += 1

    total = len(draws)
    k = cfg.pick_count
    m = cfg.max_number
    expected = total * (k * (k - 1)) / (m * (m - 1))

    top20 = pair_counts.most_common(20)
    return {
        "expected": round(expected, 1),
        "top20": [{"pair": [a, b], "count": c, "ratio": round(c/expected, 2)}
                  for (a, b), c in top20],
        "pair_counts": {f"{a},{b}": c for (a, b), c in pair_counts.items()},
        "pair_expected": expected,
    }


def run_all(draws: list[dict], cfg: GameConfig) -> dict:
    """全分析を実行して結果をまとめて返す"""
    return {
        "frequency": frequency(draws, cfg),
        "bonus": bonus_frequency(draws, cfg),
        "consecutive": consecutive_pairs(draws, cfg),
        "odd_even": odd_even_balance(draws, cfg),
        "high_low": high_low_balance(draws, cfg),
        "decade": decade_distribution(draws, cfg),
        "tail": tail_distribution(draws, cfg),
        "hot_cold": hot_cold(draws, cfg),
        "intervals": intervals(draws, cfg),
        "carryover": carryover(draws, cfg),
        "sum": sum_analysis(draws, cfg),
        "monthly": monthly(draws, cfg),
        "pair_correlation": pair_correlation(draws, cfg),
    }
