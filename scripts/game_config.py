"""ゲーム設定モジュール (Loto6 / Loto7 共通化)"""
from dataclasses import dataclass, field


@dataclass(frozen=True)
class GameConfig:
    name: str
    display_name: str
    max_number: int
    pick_count: int
    bonus_count: int
    low_high_split: int
    contrarian_high: int   # 誕生日圏外の下限 (Loto6=32, Loto7=28)
    csv_url: str
    csv_filename: str
    csv_sjis_filename: str
    number_columns: tuple  # ("第1数字", "第2数字", ...)
    bonus_columns: tuple   # ("BONUS数字",) or ("BONUS数字1", "BONUS数字2")

    @property
    def number_range(self) -> range:
        return range(1, self.max_number + 1)

    @property
    def decade_buckets(self) -> list:
        """十の位グループ [(name, low, high), ...]"""
        buckets = []
        lo = 1
        while lo <= self.max_number:
            hi = min(lo + (9 if lo == 1 else 9), self.max_number)
            if lo == 1:
                hi = 9 if 9 <= self.max_number else self.max_number
            name = f"{lo}-{hi}"
            buckets.append((name, lo, hi))
            lo = hi + 1
        return buckets

    @property
    def contrarian_high_threshold(self) -> int:
        return self.contrarian_high

    @property
    def round_numbers(self) -> set:
        """キリのいい数字 (5 刻み, max 以下)"""
        return {n for n in range(5, self.max_number + 1, 5)}

    @property
    def sum_bins(self) -> list:
        """合計値ヒストグラムのビン境界 (動的に生成)"""
        min_sum = sum(range(1, self.pick_count + 1))
        max_sum = sum(range(self.max_number - self.pick_count + 1, self.max_number + 1))
        step = max(10, (max_sum - min_sum) // 7)
        bins = []
        lo = min_sum
        while lo <= max_sum:
            hi = min(lo + step - 1, max_sum)
            bins.append((lo, hi))
            lo = hi + 1
        return bins


LOTO6 = GameConfig(
    name="loto6",
    display_name="ロト6",
    max_number=43,
    pick_count=6,
    bonus_count=1,
    low_high_split=21,
    contrarian_high=32,
    csv_url="https://loto6.thekyo.jp/data/loto6.csv",
    csv_filename="loto6.csv",
    csv_sjis_filename="loto6_sjis.csv",
    number_columns=tuple(f"第{i}数字" for i in range(1, 7)),
    bonus_columns=("BONUS数字",),
)

LOTO7 = GameConfig(
    name="loto7",
    display_name="ロト7",
    max_number=37,
    pick_count=7,
    bonus_count=2,
    low_high_split=18,
    contrarian_high=28,
    csv_url="https://loto7.thekyo.jp/data/loto7.csv",
    csv_filename="loto7.csv",
    csv_sjis_filename="loto7_sjis.csv",
    number_columns=tuple(f"第{i}数字" for i in range(1, 8)),
    bonus_columns=("BONUS数字1", "BONUS数字2"),
)


GAMES = {
    "loto6": LOTO6,
    "loto7": LOTO7,
}


def get_config(name: str) -> GameConfig:
    if name not in GAMES:
        raise ValueError(f"Unknown game: {name}. Available: {list(GAMES.keys())}")
    return GAMES[name]
