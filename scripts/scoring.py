"""ロト6 / ロト7 スコア計算モジュール"""
import numpy as np
from collections import defaultdict, Counter

from game_config import GameConfig


THEMES = {
    "hot_pursuit": {
        "name": "ホット追従型",
        "icon": "🔥",
        "description": "直近の流れに乗る。勢いのある番号を重視",
        "weights": {"frequency": 0.10, "hot": 0.45, "overdue": 0.10, "carryover": 0.15, "pair": 0.10, "decay": 0.10},
        "temperature": 1.0,
        "sum_weight": 1.0,
    },
    "cold_rebound": {
        "name": "コールド反発型",
        "icon": "❄️",
        "description": "出遅れ番号の揺り戻しを狙う。そろそろ来る番号を重視",
        "weights": {"frequency": 0.15, "hot": 0.05, "overdue": 0.45, "carryover": 0.05, "pair": 0.15, "decay": 0.15},
        "temperature": 1.0,
        "sum_weight": 1.0,
    },
    "balanced": {
        "name": "バランス重視型",
        "icon": "⚖️",
        "description": "全要素を均等に評価。安定志向の王道スタイル",
        "weights": {"frequency": 0.17, "hot": 0.17, "overdue": 0.17, "carryover": 0.17, "pair": 0.16, "decay": 0.16},
        "temperature": 0.8,
        "sum_weight": 1.0,
    },
    "center_cluster": {
        "name": "中央値集中型",
        "icon": "🎯",
        "description": "合計値を最頻帯に寄せる。最も出やすいゾーンを狙い撃ち",
        "weights": {"frequency": 0.25, "hot": 0.20, "overdue": 0.10, "carryover": 0.10, "pair": 0.20, "decay": 0.15},
        "temperature": 1.0,
        "sum_weight": 2.0,
    },
    "wildcard": {
        "name": "ワイルドカード型",
        "icon": "🃏",
        "description": "揺らぎ最大。直感的な偏りを許容する攻めの構成",
        "weights": {"frequency": 0.05, "hot": 0.30, "overdue": 0.30, "carryover": 0.10, "pair": 0.05, "decay": 0.20},
        "temperature": 1.5,
        "sum_weight": 1.0,
    },
    "contrarian": {
        "name": "逆張り型",
        "icon": "🪞",
        "description": "設計側の視点。当たりそうで当たらない領域を読む",
        "weights": {"frequency": 0.20, "hot": 0.15, "overdue": 0.10, "carryover": -0.10, "pair": -0.20, "decay": 0.15},
        "temperature": 1.2,
        "sum_weight": 1.0,
        "contrarian": True,
    },
}


def _freq_num_lookup(freq_numbers: dict, n: int):
    """JSON 経由で int キーが str 化されるケースに対応"""
    if n in freq_numbers:
        return freq_numbers[n]
    return freq_numbers[str(n)]


def compute_raw_scores(draws: list[dict], freq_data: dict, hot_cold_data: dict,
                       interval_data: dict, pair_data: dict, cfg: GameConfig) -> dict:
    """各番号の生スコア（要素別）を計算する"""
    total_draws = len(draws)

    k = 0.003
    latest_draw = draws[-1]["draw"]
    decay_scores = {}
    for n in cfg.number_range:
        decay_sum = 0.0
        for d in draws:
            if n in d["numbers"]:
                age = latest_draw - d["draw"]
                decay_sum += float(np.exp(-k * age))
        decay_scores[n] = decay_sum

    max_decay = max(decay_scores.values()) if decay_scores else 1.0

    pair_score_map = defaultdict(float)
    pair_expected = pair_data["pair_expected"]
    for key, count in pair_data["pair_counts"].items():
        a, b = [int(x) for x in key.split(",")]
        bonus = count / pair_expected - 1
        if bonus > 0:
            pair_score_map[a] += bonus
            pair_score_map[b] += bonus
    max_pair = max(pair_score_map.values()) if pair_score_map else 1.0

    recent_freq = hot_cold_data["freq"]
    intervals = interval_data["intervals"]
    current = interval_data["current"]
    last_nums = set(draws[-1]["numbers"])

    expected_rate = cfg.pick_count / cfg.max_number
    recent_expected = 30 * cfg.pick_count / cfg.max_number

    raw = {}
    for n in cfg.number_range:
        scores = {}

        count = _freq_num_lookup(freq_data["numbers"], n)["count"]
        overall_rate = count / total_draws
        scores["frequency"] = round((overall_rate / expected_rate - 1) * 10, 4)

        recent_count = recent_freq.get(n, recent_freq.get(str(n), 0))
        scores["hot"] = round((recent_count / max(recent_expected, 0.1) - 1) * 15, 4)

        int_list = intervals.get(n, intervals.get(str(n), []))
        if int_list:
            avg_interval = float(np.mean(int_list))
            cur = current.get(n, current.get(str(n), 0))
            ratio = cur / avg_interval if avg_interval > 0 else 0
            scores["overdue"] = round(min((ratio - 1) * 10, 20) if ratio > 1.0 else (ratio - 1) * 3, 4)
        else:
            scores["overdue"] = 0.0

        scores["carryover"] = 5.0 if n in last_nums else 0.0
        scores["pair"] = round((pair_score_map.get(n, 0) / max_pair) * 10, 4)
        scores["decay"] = round((decay_scores[n] / max_decay) * 10, 4)

        raw[n] = scores

    return raw


def apply_theme(raw_scores: dict, theme_key: str, cfg: GameConfig) -> dict:
    """テーマの重みを適用して最終スコアを計算"""
    theme = THEMES[theme_key]
    weights = theme["weights"]
    final = {}

    for n in cfg.number_range:
        total = 0.0
        for key, w in weights.items():
            total += raw_scores[n][key] * w
        final[n] = round(total, 4)

    return final


def score_combination(chosen: list[int], scores: dict, sum_mean: float, sum_std: float,
                      cfg: GameConfig, contrarian: bool = False) -> float:
    """組み合わせのソフトスコアを計算"""
    total = sum(chosen)
    combo = 0.0

    z = abs(total - sum_mean) / sum_std if sum_std > 0 else 0
    combo += max(0, 10 - z * 5)

    # 奇偶: 理想比率は pick_count/2 周辺
    half = cfg.pick_count / 2
    odd = sum(1 for n in chosen if n % 2 == 1)
    combo += max(0, 6 - abs(odd - half) * 2)

    # 高低: 理想比率は pick_count/2 周辺
    low = sum(1 for n in chosen if n <= cfg.low_high_split)
    combo += max(0, 6 - abs(low - half) * 2)

    # 十の位の分散 (config の decade_buckets 数に応じて)
    decades = set()
    for n in chosen:
        for i, (name, lo, hi) in enumerate(cfg.decade_buckets):
            if lo <= n <= hi:
                decades.add(i)
                break
    combo += len(decades) * 1.5

    if contrarian:
        combo += _contrarian_bonus(chosen, cfg)

    return round(combo, 2)


def _contrarian_bonus(chosen: list[int], cfg: GameConfig) -> float:
    """逆張り専用の組み合わせボーナス

    設計側ロジック:
    - 誕生日ゾーンに偏りすぎを避ける → contrarian_high 以上を含むと加点
    - 人が選びがちなキリのいい数字を避ける
    - 連番ペアを避ける
    """
    bonus = 0.0

    high_zone = sum(1 for n in chosen if n >= cfg.contrarian_high)
    bonus += high_zone * 2.0

    round_count = sum(1 for n in chosen if n in cfg.round_numbers)
    bonus -= round_count * 1.5

    sorted_nums = sorted(chosen)
    consec = sum(1 for i in range(len(sorted_nums)-1) if sorted_nums[i+1] - sorted_nums[i] == 1)
    bonus -= consec * 3.0

    tails = [n % 10 for n in chosen]
    tail_counts = Counter(tails)
    for t, c in tail_counts.items():
        if c >= 2:
            bonus += c * 1.0

    return bonus
