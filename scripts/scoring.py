"""ロト6 スコア計算モジュール"""
import numpy as np
from collections import defaultdict


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


def compute_raw_scores(draws: list[dict], freq_data: dict, hot_cold_data: dict,
                       interval_data: dict, pair_data: dict) -> dict:
    """各番号の生スコア（要素別）を計算する

    Args:
        draws: 全抽選データ
        freq_data: frequency()の結果
        hot_cold_data: hot_cold()の結果
        interval_data: intervals()の結果
        pair_data: pair_correlation()の結果

    Returns: {1: {"frequency": float, "hot": float, ...}, 2: {...}, ...}
    """
    total_draws = len(draws)

    # 時間減衰つき出現頻度
    k = 0.003
    latest_draw = draws[-1]["draw"]
    decay_scores = {}
    for n in range(1, 44):
        decay_sum = 0.0
        for d in draws:
            if n in d["numbers"]:
                age = latest_draw - d["draw"]
                decay_sum += float(np.exp(-k * age))
        decay_scores[n] = decay_sum

    max_decay = max(decay_scores.values()) if decay_scores else 1.0

    # ペアスコア
    pair_score_map = defaultdict(float)
    pair_expected = pair_data["pair_expected"]
    for key, count in pair_data["pair_counts"].items():
        a, b = [int(x) for x in key.split(",")]
        bonus = count / pair_expected - 1
        if bonus > 0:
            pair_score_map[a] += bonus
            pair_score_map[b] += bonus
    max_pair = max(pair_score_map.values()) if pair_score_map else 1.0

    # 各番号のスコア
    recent_freq = hot_cold_data["freq"]
    intervals = interval_data["intervals"]
    current = interval_data["current"]
    last_nums = set(draws[-1]["numbers"])

    raw = {}
    for n in range(1, 44):
        scores = {}

        # 1) 全期間出現率
        count = freq_data["numbers"][str(n) if isinstance(list(freq_data["numbers"].keys())[0], str) else n]["count"]
        overall_rate = count / total_draws
        expected_rate = 6 / 43
        scores["frequency"] = round((overall_rate / expected_rate - 1) * 10, 4)

        # 2) 直近ホット度
        recent_count = recent_freq.get(n, recent_freq.get(str(n), 0))
        recent_expected = 30 * 6 / 43
        scores["hot"] = round((recent_count / max(recent_expected, 0.1) - 1) * 15, 4)

        # 3) 出遅れスコア
        n_key = n if n in current else str(n)
        if intervals.get(n, intervals.get(str(n), [])):
            int_list = intervals.get(n, intervals.get(str(n), []))
            avg_interval = float(np.mean(int_list))
            cur = current.get(n, current.get(str(n), 0))
            ratio = cur / avg_interval if avg_interval > 0 else 0
            scores["overdue"] = round(min((ratio - 1) * 10, 20) if ratio > 1.0 else (ratio - 1) * 3, 4)
        else:
            scores["overdue"] = 0.0

        # 4) 前回引っ張り
        scores["carryover"] = 5.0 if n in last_nums else 0.0

        # 5) ペア相関
        scores["pair"] = round((pair_score_map.get(n, 0) / max_pair) * 10, 4)

        # 6) 時間減衰
        scores["decay"] = round((decay_scores[n] / max_decay) * 10, 4)

        raw[n] = scores

    return raw


def apply_theme(raw_scores: dict, theme_key: str) -> dict:
    """テーマの重みを適用して最終スコアを計算

    Returns: {1: float, 2: float, ...}
    """
    theme = THEMES[theme_key]
    weights = theme["weights"]
    final = {}

    for n in range(1, 44):
        total = 0.0
        for key, w in weights.items():
            total += raw_scores[n][key] * w
        final[n] = round(total, 4)

    return final


def score_combination(chosen: list[int], scores: dict, sum_mean: float, sum_std: float,
                      contrarian: bool = False) -> float:
    """組み合わせのソフトスコアを計算"""
    total = sum(chosen)
    combo = 0.0

    # 合計値スコア
    z = abs(total - sum_mean) / sum_std if sum_std > 0 else 0
    combo += max(0, 10 - z * 5)

    # 奇偶バランス
    odd = sum(1 for n in chosen if n % 2 == 1)
    combo += max(0, 6 - abs(odd - 3) * 2)

    # 高低バランス
    low = sum(1 for n in chosen if n <= 21)
    combo += max(0, 6 - abs(low - 3) * 2)

    # 十の位の分散
    decades = set()
    for n in chosen:
        if n <= 9: decades.add(0)
        elif n <= 19: decades.add(1)
        elif n <= 29: decades.add(2)
        elif n <= 39: decades.add(3)
        else: decades.add(4)
    combo += len(decades) * 1.5

    if contrarian:
        combo += _contrarian_bonus(chosen)

    return round(combo, 2)


def _contrarian_bonus(chosen: list[int]) -> float:
    """逆張り専用の組み合わせボーナス

    設計側ロジック:
    - 誕生日ゾーン(1-31)に偏りすぎを避ける → 32-43を含むと加点
    - 人が選びがちなキリのいい数字(10,20,30,40)を避ける
    - 連番ペアを避ける（人は連番を好む）
    - バランスは自然に見せる（崩しすぎない）
    """
    bonus = 0.0

    # 32-43の高域番号を含むほど加点（人は誕生日ゾーン1-31を選びがち）
    high_zone = sum(1 for n in chosen if n >= 32)
    bonus += high_zone * 2.0

    # キリのいい数字を避ける
    round_nums = {5, 10, 15, 20, 25, 30, 35, 40}
    round_count = sum(1 for n in chosen if n in round_nums)
    bonus -= round_count * 1.5

    # 連番ペアを避ける（人は連番を好むので、設計側は連番を出さない）
    sorted_nums = sorted(chosen)
    consec = sum(1 for i in range(len(sorted_nums)-1) if sorted_nums[i+1] - sorted_nums[i] == 1)
    bonus -= consec * 3.0

    # 末尾が同じ数字が複数あると減点（見た目の違和感で人が選ばない）
    tails = [n % 10 for n in chosen]
    from collections import Counter
    tail_counts = Counter(tails)
    for t, c in tail_counts.items():
        if c >= 2:
            bonus += c * 1.0  # 逆に設計側はこれを使う（人が避けるから）

    return bonus
