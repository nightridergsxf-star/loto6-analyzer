#!/usr/bin/env python3
"""
ロト6 全盛り分析 & 予測ツール
過去データを多角的に分析し、統計に基づいたおすすめ番号を生成する
"""

import pandas as pd
import numpy as np
from collections import Counter, defaultdict
from itertools import combinations
import subprocess
import sys
import os
import argparse
from datetime import datetime

# ============================================================
# データ読み込み
# ============================================================

def load_data(csv_path="loto6.csv"):
    """CSVからロト6データを読み込む"""
    df = pd.read_csv(csv_path)
    num_cols = [f"第{i}数字" for i in range(1, 7)]
    df["numbers"] = df[num_cols].values.tolist()
    df["bonus"] = df["BONUS数字"]
    df["date"] = pd.to_datetime(df["日付"])
    df["draw"] = df["開催回"]
    return df


# ============================================================
# 1. 基本分析：出現回数・出現率
# ============================================================

def analyze_frequency(df):
    """各番号の出現回数と出現率"""
    all_nums = []
    for nums in df["numbers"]:
        all_nums.extend(nums)

    total_draws = len(df)
    freq = Counter(all_nums)

    print("=" * 60)
    print("【1】各番号の出現回数・出現率")
    print("=" * 60)
    print(f"総抽選回数: {total_draws}回\n")

    # 理論上の出現回数 (各回6個/43個)
    expected = total_draws * 6 / 43
    print(f"理論上の期待出現回数: {expected:.1f}回\n")

    print(f"{'番号':>4} {'出現回数':>8} {'出現率':>8} {'偏差':>8}  グラフ")
    print("-" * 60)

    max_freq = max(freq.values())
    for n in range(1, 44):
        count = freq.get(n, 0)
        rate = count / total_draws * 100
        deviation = count - expected
        bar = "█" * int(count / max_freq * 30)
        dev_str = f"+{deviation:.0f}" if deviation >= 0 else f"{deviation:.0f}"
        print(f"  {n:2d}   {count:5d}    {rate:5.1f}%   {dev_str:>5}  {bar}")

    # TOP 10 / WORST 10
    sorted_freq = sorted(freq.items(), key=lambda x: x[1], reverse=True)
    print(f"\n🔥 出現回数 TOP 10: {', '.join(f'{n}({c}回)' for n, c in sorted_freq[:10])}")
    print(f"❄️  出現回数 WORST 10: {', '.join(f'{n}({c}回)' for n, c in sorted_freq[-10:])}")

    return freq


def analyze_bonus(df):
    """ボーナス数字の出現傾向"""
    bonus_freq = Counter(df["bonus"])
    total = len(df)

    print("\n" + "=" * 60)
    print("【2】ボーナス数字の出現傾向")
    print("=" * 60)

    sorted_bonus = sorted(bonus_freq.items(), key=lambda x: x[1], reverse=True)
    print(f"\nTOP 10: {', '.join(f'{n}({c}回)' for n, c in sorted_bonus[:10])}")
    print(f"WORST 10: {', '.join(f'{n}({c}回)' for n, c in sorted_bonus[-10:])}")

    return bonus_freq


# ============================================================
# 2. パターン分析
# ============================================================

def analyze_consecutive(df):
    """連番ペアの出現率"""
    print("\n" + "=" * 60)
    print("【3】連番ペアの出現分析")
    print("=" * 60)

    consec_counts = Counter()
    draws_with_consec = 0
    consec_per_draw = []

    for nums in df["numbers"]:
        sorted_nums = sorted(nums)
        count = 0
        for i in range(len(sorted_nums) - 1):
            if sorted_nums[i + 1] - sorted_nums[i] == 1:
                pair = (sorted_nums[i], sorted_nums[i + 1])
                consec_counts[pair] += 1
                count += 1
        consec_per_draw.append(count)
        if count > 0:
            draws_with_consec += 1

    total = len(df)
    print(f"\n連番を含む抽選の割合: {draws_with_consec}/{total} ({draws_with_consec/total*100:.1f}%)")
    print(f"平均連番ペア数/回: {np.mean(consec_per_draw):.2f}")

    # 連番ペア数の分布
    consec_dist = Counter(consec_per_draw)
    print("\n連番ペア数の分布:")
    for k in sorted(consec_dist.keys()):
        pct = consec_dist[k] / total * 100
        print(f"  {k}組: {consec_dist[k]}回 ({pct:.1f}%)")


def analyze_odd_even(df):
    """奇数・偶数の比率分析"""
    print("\n" + "=" * 60)
    print("【4】奇数・偶数バランス")
    print("=" * 60)

    patterns = Counter()
    for nums in df["numbers"]:
        odd = sum(1 for n in nums if n % 2 == 1)
        even = 6 - odd
        patterns[(odd, even)] += 1

    total = len(df)
    print(f"\n{'奇数:偶数':>10} {'回数':>6} {'割合':>7}")
    print("-" * 30)
    for key in sorted(patterns.keys()):
        odd, even = key
        pct = patterns[key] / total * 100
        print(f"  {odd}:{even}       {patterns[key]:5d}   {pct:5.1f}%")

    return patterns


def analyze_high_low(df):
    """高低バランス（1-21:低, 22-43:高）"""
    print("\n" + "=" * 60)
    print("【5】高低バランス（低1-21 / 高22-43）")
    print("=" * 60)

    patterns = Counter()
    for nums in df["numbers"]:
        low = sum(1 for n in nums if n <= 21)
        high = 6 - low
        patterns[(low, high)] += 1

    total = len(df)
    print(f"\n{'低:高':>10} {'回数':>6} {'割合':>7}")
    print("-" * 30)
    for key in sorted(patterns.keys()):
        low, high = key
        pct = patterns[key] / total * 100
        print(f"  {low}:{high}       {patterns[key]:5d}   {pct:5.1f}%")

    return patterns


def analyze_decade(df):
    """十の位の分布"""
    print("\n" + "=" * 60)
    print("【6】十の位グループの分布")
    print("=" * 60)

    groups = {
        "1-9": (1, 9),
        "10-19": (10, 19),
        "20-29": (20, 29),
        "30-39": (30, 39),
        "40-43": (40, 43),
    }

    group_counts = defaultdict(int)
    total_nums = 0

    for nums in df["numbers"]:
        for n in nums:
            total_nums += 1
            for name, (lo, hi) in groups.items():
                if lo <= n <= hi:
                    group_counts[name] += 1
                    break

    print(f"\n{'グループ':>8} {'出現数':>7} {'割合':>7} {'期待値':>7}")
    print("-" * 40)
    for name, (lo, hi) in groups.items():
        count = group_counts[name]
        pct = count / total_nums * 100
        expected_pct = (hi - lo + 1) / 43 * 100
        print(f"  {name:>6}  {count:6d}   {pct:5.1f}%   {expected_pct:5.1f}%")


def analyze_tail(df):
    """末尾数字の分布"""
    print("\n" + "=" * 60)
    print("【7】末尾数字の分布")
    print("=" * 60)

    tail_counts = Counter()
    total_nums = 0

    for nums in df["numbers"]:
        for n in nums:
            tail_counts[n % 10] += 1
            total_nums += 1

    print(f"\n{'末尾':>4} {'出現数':>7} {'割合':>7}")
    print("-" * 25)
    for t in range(10):
        count = tail_counts[t]
        pct = count / total_nums * 100
        print(f"   {t}   {count:6d}   {pct:5.1f}%")


# ============================================================
# 3. 時系列分析
# ============================================================

def analyze_hot_cold(df, recent_n=30):
    """直近N回のホット/コールドナンバー"""
    print("\n" + "=" * 60)
    print(f"【8】ホット & コールドナンバー（直近{recent_n}回）")
    print("=" * 60)

    recent = df.tail(recent_n)
    recent_nums = []
    for nums in recent["numbers"]:
        recent_nums.extend(nums)

    recent_freq = Counter(recent_nums)
    expected = recent_n * 6 / 43

    # ホットナンバー
    hot = sorted(recent_freq.items(), key=lambda x: x[1], reverse=True)[:10]
    print(f"\n🔥 ホットナンバー（直近{recent_n}回でよく出る）:")
    for n, c in hot:
        print(f"   {n:2d}: {c}回 (期待値{expected:.1f}回の{c/expected:.1f}倍)")

    # コールドナンバー
    all_numbers = set(range(1, 44))
    appeared = set(recent_freq.keys())
    not_appeared = all_numbers - appeared

    cold_list = [(n, recent_freq.get(n, 0)) for n in range(1, 44)]
    cold = sorted(cold_list, key=lambda x: x[1])[:10]
    print(f"\n❄️  コールドナンバー（直近{recent_n}回で出にくい）:")
    for n, c in cold:
        print(f"   {n:2d}: {c}回")

    if not_appeared:
        print(f"\n⚠️  直近{recent_n}回で一度も出ていない番号: {sorted(not_appeared)}")

    return recent_freq


def analyze_interval(df):
    """各番号の出現間隔（インターバル）"""
    print("\n" + "=" * 60)
    print("【9】出現間隔（インターバル）分析")
    print("=" * 60)

    last_seen = {}
    intervals = defaultdict(list)

    for idx, row in df.iterrows():
        draw = row["draw"]
        for n in row["numbers"]:
            if n in last_seen:
                interval = draw - last_seen[n]
                intervals[n].append(interval)
            last_seen[n] = draw

    # 現在のインターバル（最後に出てからの回数）
    latest_draw = df["draw"].max()
    current_interval = {}
    for n in range(1, 44):
        if n in last_seen:
            current_interval[n] = latest_draw - last_seen[n]
        else:
            current_interval[n] = latest_draw

    print(f"\n{'番号':>4} {'平均間隔':>8} {'最大間隔':>8} {'現在の間隔':>10} {'状態':>6}")
    print("-" * 50)

    overdue = []
    for n in range(1, 44):
        if intervals[n]:
            avg = np.mean(intervals[n])
            max_int = max(intervals[n])
            cur = current_interval[n]
            status = "⚡出遅れ" if cur > avg * 1.5 else "　通常"
            if cur > avg * 1.5:
                overdue.append((n, cur, avg))
            print(f"  {n:2d}    {avg:5.1f}     {max_int:4d}       {cur:4d}    {status}")

    if overdue:
        overdue.sort(key=lambda x: x[1] / x[2], reverse=True)
        print(f"\n⚡ 出遅れ番号 TOP5:")
        for n, cur, avg in overdue[:5]:
            print(f"   {n:2d}: 現在{cur}回空き (平均{avg:.1f}回の{cur/avg:.1f}倍)")

    return intervals, current_interval


def analyze_carryover(df):
    """前回からの引っ張り分析"""
    print("\n" + "=" * 60)
    print("【10】前回引っ張り分析（前回の番号が次回も出る確率）")
    print("=" * 60)

    carryover_counts = []
    for i in range(1, len(df)):
        prev = set(df.iloc[i - 1]["numbers"])
        curr = set(df.iloc[i]["numbers"])
        overlap = len(prev & curr)
        carryover_counts.append(overlap)

    dist = Counter(carryover_counts)
    total = len(carryover_counts)

    print(f"\n{'引っ張り数':>10} {'回数':>6} {'割合':>7}")
    print("-" * 30)
    for k in sorted(dist.keys()):
        pct = dist[k] / total * 100
        print(f"    {k}個      {dist[k]:5d}   {pct:5.1f}%")

    avg = np.mean(carryover_counts)
    print(f"\n平均引っ張り数: {avg:.2f}個/回")

    return carryover_counts


# ============================================================
# 4. 高度な分析
# ============================================================

def analyze_sum(df):
    """当選番号の合計値分析"""
    print("\n" + "=" * 60)
    print("【11】当選番号の合計値分析")
    print("=" * 60)

    sums = [sum(nums) for nums in df["numbers"]]

    print(f"\n平均合計値: {np.mean(sums):.1f}")
    print(f"中央値: {np.median(sums):.1f}")
    print(f"標準偏差: {np.std(sums):.1f}")
    print(f"最小: {min(sums)} / 最大: {max(sums)}")

    # 分布をヒストグラム的に表示
    bins = [(50, 80), (81, 100), (101, 120), (121, 140), (141, 160), (161, 180), (181, 210)]
    print(f"\n{'範囲':>10} {'回数':>6} {'割合':>7}  グラフ")
    print("-" * 50)
    total = len(sums)
    for lo, hi in bins:
        count = sum(1 for s in sums if lo <= s <= hi)
        pct = count / total * 100
        bar = "█" * int(pct)
        print(f"  {lo:3d}-{hi:3d}   {count:5d}   {pct:5.1f}%  {bar}")

    return sums


def analyze_monthly(df):
    """月別の傾向"""
    print("\n" + "=" * 60)
    print("【12】月別出現傾向")
    print("=" * 60)

    df_copy = df.copy()
    df_copy["month"] = df_copy["date"].dt.month

    monthly_freq = defaultdict(lambda: Counter())
    for _, row in df_copy.iterrows():
        month = row["month"]
        for n in row["numbers"]:
            monthly_freq[month][n] += 1

    # 各月のTOP5
    print()
    for m in range(1, 13):
        top5 = monthly_freq[m].most_common(5)
        nums_str = ", ".join(f"{n}({c})" for n, c in top5)
        print(f"  {m:2d}月 TOP5: {nums_str}")


# ============================================================
# 4.5 ペア相関分析
# ============================================================

def analyze_pair_correlation(df):
    """よく一緒に出る番号ペアを分析"""
    print("\n" + "=" * 60)
    print("【13】ペア相関分析（よく一緒に出る番号）")
    print("=" * 60)

    pair_counts = Counter()
    for nums in df["numbers"]:
        for pair in combinations(sorted(nums), 2):
            pair_counts[pair] += 1

    total = len(df)
    # 期待値: C(41,4)/C(43,6) * total ≈ total * 6/43 * 5/42
    expected = total * (6 * 5) / (43 * 42)

    top20 = pair_counts.most_common(20)
    print(f"\n期待出現回数: {expected:.1f}回\n")
    print(f"{'ペア':>8} {'出現回数':>8} {'期待値比':>8}")
    print("-" * 30)
    for (a, b), c in top20:
        ratio = c / expected
        print(f"  ({a:2d},{b:2d})    {c:4d}     {ratio:.2f}倍")

    return pair_counts, expected


# ============================================================
# 5. 予測ロジック（テーマ別スコアリング方式 v2）
# ============================================================

# テーマ定義: 各テーマごとにスコアの重みと性格を変える
THEMES = {
    "hot_pursuit": {
        "name": "ホット追従型",
        "icon": "🔥",
        "description": "直近の流れに乗る。勢いのある番号を重視",
        "weights": {
            "frequency": 0.10,
            "hot": 0.45,
            "overdue": 0.10,
            "carryover": 0.15,
            "pair": 0.10,
            "decay": 0.10,
        },
    },
    "cold_rebound": {
        "name": "コールド反発型",
        "icon": "❄️",
        "description": "出遅れ番号の揺り戻しを狙う。そろそろ来る番号を重視",
        "weights": {
            "frequency": 0.15,
            "hot": 0.05,
            "overdue": 0.45,
            "carryover": 0.05,
            "pair": 0.15,
            "decay": 0.15,
        },
    },
    "balanced": {
        "name": "バランス重視型",
        "icon": "⚖️",
        "description": "全要素を均等に評価。安定志向の王道スタイル",
        "weights": {
            "frequency": 0.17,
            "hot": 0.17,
            "overdue": 0.17,
            "carryover": 0.17,
            "pair": 0.16,
            "decay": 0.16,
        },
    },
    "center_cluster": {
        "name": "中央値集中型",
        "icon": "🎯",
        "description": "合計値を最頻帯に寄せる。最も出やすいゾーンを狙い撃ち",
        "weights": {
            "frequency": 0.25,
            "hot": 0.20,
            "overdue": 0.10,
            "carryover": 0.10,
            "pair": 0.20,
            "decay": 0.15,
        },
    },
    "wildcard": {
        "name": "ワイルドカード型",
        "icon": "🃏",
        "description": "揺らぎ最大。直感的な偏りを許容する攻めの構成",
        "weights": {
            "frequency": 0.05,
            "hot": 0.30,
            "overdue": 0.30,
            "carryover": 0.10,
            "pair": 0.05,
            "decay": 0.20,
        },
    },
}


def compute_raw_scores(df, freq, recent_freq, intervals, current_interval, pair_counts, pair_expected):
    """各番号の生スコア（要素別）を計算する"""
    total_draws = len(df)
    raw = {}

    # --- 時間減衰つき出現頻度 ---
    decay_scores = {}
    k = 0.003  # 減衰係数
    latest_draw = df["draw"].max()
    for n in range(1, 44):
        decay_sum = 0.0
        for _, row in df.iterrows():
            if n in row["numbers"]:
                age = latest_draw - row["draw"]
                decay_sum += np.exp(-k * age)
        decay_scores[n] = decay_sum

    # 正規化用
    max_decay = max(decay_scores.values()) if decay_scores else 1
    max_freq = max(freq.values()) if freq else 1

    # ペアスコア: 各番号が強いペアをどれだけ持ってるか
    pair_score_map = defaultdict(float)
    for (a, b), count in pair_counts.items():
        bonus = count / pair_expected - 1  # 期待値比 - 1
        if bonus > 0:
            pair_score_map[a] += bonus
            pair_score_map[b] += bonus
    max_pair = max(pair_score_map.values()) if pair_score_map else 1

    for n in range(1, 44):
        scores = {}

        # 1) 全期間出現率
        overall_rate = freq.get(n, 0) / total_draws
        expected_rate = 6 / 43
        scores["frequency"] = (overall_rate / expected_rate - 1) * 10

        # 2) 直近ホット度
        recent_count = recent_freq.get(n, 0)
        recent_expected = 30 * 6 / 43
        scores["hot"] = (recent_count / max(recent_expected, 0.1) - 1) * 15

        # 3) 出遅れスコア（ソフト化: 段階的にスコア上昇）
        if intervals[n]:
            avg_interval = np.mean(intervals[n])
            cur_interval = current_interval[n]
            ratio = cur_interval / avg_interval
            if ratio > 1.0:
                scores["overdue"] = min((ratio - 1) * 10, 20)
            else:
                scores["overdue"] = (ratio - 1) * 3  # 出たばかりは軽くマイナス
        else:
            scores["overdue"] = 0.0

        # 4) 前回引っ張り
        last_nums = set(df.iloc[-1]["numbers"])
        scores["carryover"] = 5.0 if n in last_nums else 0.0

        # 5) ペア相関スコア
        scores["pair"] = (pair_score_map.get(n, 0) / max_pair) * 10

        # 6) 時間減衰スコア
        scores["decay"] = (decay_scores[n] / max_decay) * 10

        raw[n] = scores

    return raw


def apply_theme_weights(raw_scores, theme_key):
    """テーマの重みを適用して最終スコアを計算"""
    theme = THEMES[theme_key]
    weights = theme["weights"]
    final = {}
    details = {}

    for n in range(1, 44):
        total = 0.0
        det = []
        for key, w in weights.items():
            val = raw_scores[n][key] * w
            total += val
            det.append(f"{key}:{val:+.1f}")
        final[n] = total
        details[n] = det

    return final, details


def score_combination(chosen, scores, df):
    """組み合わせ自体のソフトスコアを計算（フィルタではなくスコア化）"""
    all_sums = [sum(nums) for nums in df["numbers"]]
    sum_mean = np.mean(all_sums)
    sum_std = np.std(all_sums)

    total = sum(chosen)
    combo_score = 0.0

    # 合計値スコア: 理想値からの距離で減点（ソフト）
    z = abs(total - sum_mean) / sum_std
    combo_score += max(0, 10 - z * 5)  # 1σ以内なら+5以上

    # 奇偶バランススコア
    odd = sum(1 for n in chosen if n % 2 == 1)
    balance_penalty = abs(odd - 3)  # 3:3が最良
    combo_score += max(0, 6 - balance_penalty * 2)

    # 高低バランススコア
    low = sum(1 for n in chosen if n <= 21)
    hl_penalty = abs(low - 3)
    combo_score += max(0, 6 - hl_penalty * 2)

    # 十の位の分散スコア（散らばってるほうが良い）
    decades = set()
    for n in chosen:
        if n <= 9:
            decades.add(0)
        elif n <= 19:
            decades.add(1)
        elif n <= 29:
            decades.add(2)
        elif n <= 39:
            decades.add(3)
        else:
            decades.add(4)
    combo_score += len(decades) * 1.5  # 多くのグループに散らばるほど加点

    return combo_score


def predict_numbers(df, freq, recent_freq, intervals, current_interval,
                    pair_counts, pair_expected, n_sets=5):
    """テーマ別にスコアリングし、確率抽選でおすすめ番号を生成"""
    print("\n" + "=" * 60)
    print("🎯 予測番号の生成（v2: テーマ別スコアリング）")
    print("=" * 60)

    # 生スコア計算（全テーマ共通）
    raw_scores = compute_raw_scores(
        df, freq, recent_freq, intervals, current_interval,
        pair_counts, pair_expected
    )

    np.random.seed(int(datetime.now().timestamp()))

    for theme_key, theme in THEMES.items():
        print(f"\n{'─' * 60}")
        print(f"  {theme['icon']} テーマ: {theme['name']}")
        print(f"  {theme['description']}")
        print(f"{'─' * 60}")

        # テーマ重み適用
        scores, details = apply_theme_weights(raw_scores, theme_key)

        # スコアランキング TOP10
        ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        print(f"\n  📊 スコア TOP 10:")
        for rank, (n, s) in enumerate(ranked[:10], 1):
            print(f"     {rank:2d}. [{n:2d}] {s:+6.2f}")

        # --- ルーレット選択（確率抽選） ---
        # スコアをソフトマックスで確率に変換
        score_arr = np.array([scores[n] for n in range(1, 44)])
        # 温度パラメータ: ワイルドカードは高温（揺らぎ大）、バランスは低温（安定）
        temperature = 1.5 if theme_key == "wildcard" else (0.8 if theme_key == "balanced" else 1.0)
        # 中央値集中型は合計値フィットを強く評価
        sum_weight = 2.0 if theme_key == "center_cluster" else 1.0

        exp_scores = np.exp((score_arr - score_arr.max()) / temperature)
        probs = exp_scores / exp_scores.sum()

        sets = []
        attempts = 0
        while len(sets) < n_sets and attempts < 20000:
            attempts += 1
            chosen = list(np.random.choice(range(1, 44), size=6, replace=False, p=probs))
            chosen.sort()
            chosen = [int(x) for x in chosen]

            # ソフトスコアで評価（ハードフィルタなし）
            combo = score_combination(chosen, scores, df)
            num_score = sum(scores[n] for n in chosen)
            total_score = num_score + combo * sum_weight

            # 最低品質ライン（極端な組み合わせだけ弾く）
            s = sum(chosen)
            if s < 40 or s > 220:
                continue

            sets.append((chosen, total_score, combo))

        # 総合スコア上位を採用
        sets.sort(key=lambda x: x[1], reverse=True)
        best = sets[:n_sets]

        print(f"\n  🎰 選出番号:")
        for i, (nums, total_s, combo_s) in enumerate(best, 1):
            s = sum(nums)
            odd = sum(1 for n in nums if n % 2 == 1)
            even = 6 - odd
            low = sum(1 for n in nums if n <= 21)
            high = 6 - low
            print(f"\n     セット{i}: {nums}")
            print(f"       合計:{s} / 奇偶={odd}:{even} / 高低={low}:{high} / "
                  f"総合スコア:{total_s:+.1f} (組合せ補正:{combo_s:+.1f})")

    # 最終サマリー
    all_sums = [sum(nums) for nums in df["numbers"]]
    sum_mean = np.mean(all_sums)
    sum_std = np.std(all_sums)

    print(f"\n{'=' * 60}")
    print("📝 分析サマリー")
    print(f"{'=' * 60}")
    print(f"  - 合計値の最適範囲: {sum_mean - sum_std:.0f}〜{sum_mean + sum_std:.0f}")
    print(f"  - 各テーマから{n_sets}セットずつ、計{n_sets * len(THEMES)}セット生成")
    print(f"  - スコアは確率抽選（ルーレット選択）で生成")
    print(f"  - 組み合わせ品質もソフトスコアで評価（ハードフィルタなし）")


# ============================================================
# データ更新・読み込み
# ============================================================

def update_and_load():
    """最新データをダウンロードして読み込む"""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    csv_path = os.path.join(script_dir, "loto6.csv")

    print("📥 最新データをダウンロード中...")
    try:
        sjis_path = os.path.join(script_dir, "loto6_sjis.csv")
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
        print("✅ データ更新完了")
    except Exception as e:
        print(f"⚠️  データ更新失敗（既存データを使用）: {e}")

    df = load_data(csv_path)
    print(f"📊 全{len(df)}回分 ({df['date'].min().strftime('%Y/%m/%d')}〜{df['date'].max().strftime('%Y/%m/%d')})")
    print()
    return df


def run_all_analysis(df):
    """全分析を実行して結果を返す"""
    freq = analyze_frequency(df)
    bonus_freq = analyze_bonus(df)
    analyze_consecutive(df)
    analyze_odd_even(df)
    analyze_high_low(df)
    analyze_decade(df)
    analyze_tail(df)
    recent_freq = analyze_hot_cold(df, recent_n=30)
    intervals, current_interval = analyze_interval(df)
    analyze_carryover(df)
    analyze_sum(df)
    analyze_monthly(df)
    pair_counts, pair_expected = analyze_pair_correlation(df)
    return freq, recent_freq, intervals, current_interval, pair_counts, pair_expected


ANALYSIS_MENU = {
    "1": ("出現回数・出現率", lambda df: analyze_frequency(df)),
    "2": ("ボーナス数字", lambda df: analyze_bonus(df)),
    "3": ("連番ペア", lambda df: analyze_consecutive(df)),
    "4": ("奇数・偶数バランス", lambda df: analyze_odd_even(df)),
    "5": ("高低バランス", lambda df: analyze_high_low(df)),
    "6": ("十の位グループ", lambda df: analyze_decade(df)),
    "7": ("末尾数字", lambda df: analyze_tail(df)),
    "8": ("ホット/コールド", lambda df: analyze_hot_cold(df, recent_n=30)),
    "9": ("出現間隔", lambda df: analyze_interval(df)),
    "10": ("前回引っ張り", lambda df: analyze_carryover(df)),
    "11": ("合計値分析", lambda df: analyze_sum(df)),
    "12": ("月別傾向", lambda df: analyze_monthly(df)),
    "13": ("ペア相関", lambda df: analyze_pair_correlation(df)),
}

THEME_KEYS = list(THEMES.keys())


def print_disclaimer():
    print("\n⚠️  注意: 統計分析に基づく参考情報です。ロト6は完全なランダム抽選です。")


# ============================================================
# 対話モード
# ============================================================

def interactive_mode():
    """対話型メニューで操作"""
    df = update_and_load()

    # キャッシュ（予測用の分析結果）
    cache = {}

    def ensure_cache():
        if not cache:
            print("\n⏳ 予測に必要な分析を実行中...\n")
            freq = analyze_frequency.__wrapped__(df) if hasattr(analyze_frequency, '__wrapped__') else _quiet_analyze(df)
            cache.update(_build_cache(df))

    while True:
        print("\n" + "━" * 50)
        print("  🎱 ロト6 アナライザー")
        print("━" * 50)
        print()
        print("  [1] 📊 全分析を表示")
        print("  [2] 📊 分析を選んで表示")
        print("  [3] 🎯 予測番号を生成（全テーマ）")
        print("  [4] 🎯 テーマを選んで予測")
        print("  [5] ⚡ クイック予測（番号だけ表示）")
        print("  [6] 🔄 データ更新")
        print("  [q] 終了")
        print()

        choice = input("  👉 選択: ").strip().lower()

        if choice == "1":
            run_all_analysis(df)

        elif choice == "2":
            print("\n  分析メニュー:")
            for key, (name, _) in ANALYSIS_MENU.items():
                print(f"    [{key:>2}] {name}")
            print(f"    [ a] 全部")
            print()
            sel = input("  番号を選択（カンマ区切りで複数可）: ").strip().lower()
            if sel == "a":
                run_all_analysis(df)
            else:
                for s in sel.split(","):
                    s = s.strip()
                    if s in ANALYSIS_MENU:
                        ANALYSIS_MENU[s][1](df)
                    else:
                        print(f"  ⚠️  '{s}' は無効な選択です")

        elif choice == "3":
            c = _build_cache(df)
            predict_numbers(df, c["freq"], c["recent_freq"], c["intervals"],
                          c["current_interval"], c["pair_counts"],
                          c["pair_expected"], n_sets=5)
            print_disclaimer()

        elif choice == "4":
            print("\n  テーマ:")
            for i, key in enumerate(THEME_KEYS):
                t = THEMES[key]
                print(f"    [{i+1}] {t['icon']} {t['name']} — {t['description']}")
            print()
            sel = input("  テーマ番号: ").strip()
            try:
                idx = int(sel) - 1
                if 0 <= idx < len(THEME_KEYS):
                    c = _build_cache(df)
                    _predict_single_theme(df, c, THEME_KEYS[idx], n_sets=5)
                    print_disclaimer()
                else:
                    print("  ⚠️  無効な番号です")
            except ValueError:
                print("  ⚠️  数字を入力してください")

        elif choice == "5":
            c = _build_cache(df)
            _quick_predict(df, c)

        elif choice == "6":
            df = update_and_load()

        elif choice == "q":
            print("\n  👋 またね！当たるといいね！\n")
            break

        else:
            print("  ⚠️  1-6 または q を入力してください")


def _build_cache(df):
    """予測に必要な分析結果をまとめて計算（表示なし）"""
    import io
    from contextlib import redirect_stdout

    with redirect_stdout(io.StringIO()):
        freq = analyze_frequency(df)
        recent_freq = analyze_hot_cold(df, recent_n=30)
        intervals, current_interval = analyze_interval(df)
        pair_counts, pair_expected = analyze_pair_correlation(df)

    return {
        "freq": freq,
        "recent_freq": recent_freq,
        "intervals": intervals,
        "current_interval": current_interval,
        "pair_counts": pair_counts,
        "pair_expected": pair_expected,
    }


def _predict_single_theme(df, cache, theme_key, n_sets=5):
    """単一テーマで予測を実行"""
    raw_scores = compute_raw_scores(
        df, cache["freq"], cache["recent_freq"],
        cache["intervals"], cache["current_interval"],
        cache["pair_counts"], cache["pair_expected"]
    )
    np.random.seed(int(datetime.now().timestamp()))

    theme = THEMES[theme_key]
    scores, details = apply_theme_weights(raw_scores, theme_key)

    print(f"\n{'─' * 50}")
    print(f"  {theme['icon']} テーマ: {theme['name']}")
    print(f"  {theme['description']}")
    print(f"{'─' * 50}")

    ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    print(f"\n  📊 スコア TOP 10:")
    for rank, (n, s) in enumerate(ranked[:10], 1):
        print(f"     {rank:2d}. [{n:2d}] {s:+6.2f}")

    score_arr = np.array([scores[n] for n in range(1, 44)])
    temperature = 1.5 if theme_key == "wildcard" else (0.8 if theme_key == "balanced" else 1.0)
    sum_weight = 2.0 if theme_key == "center_cluster" else 1.0

    exp_scores = np.exp((score_arr - score_arr.max()) / temperature)
    probs = exp_scores / exp_scores.sum()

    sets = []
    attempts = 0
    while len(sets) < n_sets and attempts < 20000:
        attempts += 1
        chosen = sorted([int(x) for x in np.random.choice(range(1, 44), size=6, replace=False, p=probs)])
        combo = score_combination(chosen, scores, df)
        num_score = sum(scores[n] for n in chosen)
        total_score = num_score + combo * sum_weight
        s = sum(chosen)
        if s < 40 or s > 220:
            continue
        sets.append((chosen, total_score, combo))

    sets.sort(key=lambda x: x[1], reverse=True)
    best = sets[:n_sets]

    print(f"\n  🎰 選出番号:")
    for i, (nums, total_s, combo_s) in enumerate(best, 1):
        s = sum(nums)
        odd = sum(1 for n in nums if n % 2 == 1)
        even = 6 - odd
        low = sum(1 for n in nums if n <= 21)
        high = 6 - low
        print(f"\n     セット{i}: {nums}")
        print(f"       合計:{s} / 奇偶={odd}:{even} / 高低={low}:{high} / "
              f"スコア:{total_s:+.1f}")


def _quick_predict(df, cache):
    """番号だけサクッと表示"""
    raw_scores = compute_raw_scores(
        df, cache["freq"], cache["recent_freq"],
        cache["intervals"], cache["current_interval"],
        cache["pair_counts"], cache["pair_expected"]
    )
    np.random.seed(int(datetime.now().timestamp()))

    print(f"\n{'━' * 50}")
    print("  ⚡ クイック予測")
    print(f"{'━' * 50}")

    for theme_key, theme in THEMES.items():
        scores, _ = apply_theme_weights(raw_scores, theme_key)
        score_arr = np.array([scores[n] for n in range(1, 44)])
        temperature = 1.5 if theme_key == "wildcard" else (0.8 if theme_key == "balanced" else 1.0)
        sum_weight = 2.0 if theme_key == "center_cluster" else 1.0

        exp_scores = np.exp((score_arr - score_arr.max()) / temperature)
        probs = exp_scores / exp_scores.sum()

        best = None
        best_score = -999
        for _ in range(5000):
            chosen = sorted([int(x) for x in np.random.choice(range(1, 44), size=6, replace=False, p=probs)])
            s = sum(chosen)
            if s < 40 or s > 220:
                continue
            combo = score_combination(chosen, scores, df)
            total_score = sum(scores[n] for n in chosen) + combo * sum_weight
            if total_score > best_score:
                best_score = total_score
                best = chosen

        if best:
            print(f"\n  {theme['icon']} {theme['name']:　<10}  →  {best}  (合計:{sum(best)})")

    print_disclaimer()


# ============================================================
# コマンドラインインターフェース
# ============================================================

def main():
    parser = argparse.ArgumentParser(
        description="🎱 ロト6 全盛り分析 & 予測ツール",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用例:
  python3 loto6_analyzer.py              対話モード
  python3 loto6_analyzer.py --quick      番号だけサクッと表示
  python3 loto6_analyzer.py --all        全分析＋全テーマ予測
  python3 loto6_analyzer.py --theme hot  ホット追従型で予測
  python3 loto6_analyzer.py --analyze    全分析のみ（予測なし）
        """
    )
    parser.add_argument("--quick", action="store_true",
                        help="クイック予測（番号だけ表示）")
    parser.add_argument("--all", action="store_true",
                        help="全分析＋全テーマ予測を一括実行")
    parser.add_argument("--analyze", action="store_true",
                        help="全分析のみ（予測なし）")
    parser.add_argument("--theme", choices=["hot", "cold", "balance", "center", "wild"],
                        help="指定テーマで予測")
    parser.add_argument("--sets", type=int, default=5,
                        help="生成セット数（デフォルト: 5）")

    args = parser.parse_args()

    theme_map = {
        "hot": "hot_pursuit",
        "cold": "cold_rebound",
        "balance": "balanced",
        "center": "center_cluster",
        "wild": "wildcard",
    }

    # 引数なし → 対話モード
    if not (args.quick or args.all or args.analyze or args.theme):
        interactive_mode()
        return

    # 引数あり → ワンショット実行
    df = update_and_load()

    if args.analyze:
        run_all_analysis(df)

    elif args.all:
        freq, recent_freq, intervals, current_interval, pair_counts, pair_expected = run_all_analysis(df)
        predict_numbers(df, freq, recent_freq, intervals, current_interval,
                       pair_counts, pair_expected, n_sets=args.sets)
        print_disclaimer()

    elif args.quick:
        cache = _build_cache(df)
        _quick_predict(df, cache)

    elif args.theme:
        cache = _build_cache(df)
        _predict_single_theme(df, cache, theme_map[args.theme], n_sets=args.sets)
        print_disclaimer()


if __name__ == "__main__":
    main()
