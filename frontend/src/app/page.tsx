"use client";

import { useState } from "react";

// テーマ定義
const THEMES = [
  {
    key: "hot_pursuit",
    name: "ホット追従型",
    icon: "🔥",
    description: "直近の流れに乗る",
    color: "from-red-500/20 to-orange-500/20",
    border: "border-red-500/30",
    badge: "bg-red-500/20 text-red-300",
  },
  {
    key: "cold_rebound",
    name: "コールド反発型",
    icon: "❄️",
    description: "出遅れの揺り戻し",
    color: "from-blue-500/20 to-cyan-500/20",
    border: "border-blue-500/30",
    badge: "bg-blue-500/20 text-blue-300",
  },
  {
    key: "balanced",
    name: "バランス重視型",
    icon: "⚖️",
    description: "安定志向の王道",
    color: "from-emerald-500/20 to-teal-500/20",
    border: "border-emerald-500/30",
    badge: "bg-emerald-500/20 text-emerald-300",
  },
  {
    key: "center_cluster",
    name: "中央値集中型",
    icon: "🎯",
    description: "最頻帯を狙い撃ち",
    color: "from-purple-500/20 to-pink-500/20",
    border: "border-purple-500/30",
    badge: "bg-purple-500/20 text-purple-300",
  },
  {
    key: "wildcard",
    name: "ワイルドカード型",
    icon: "🃏",
    description: "揺らぎ最大の攻め",
    color: "from-amber-500/20 to-yellow-500/20",
    border: "border-amber-500/30",
    badge: "bg-amber-500/20 text-amber-300",
  },
];

interface Prediction {
  numbers: number[];
  total: number;
  odd_even: { odd: number; even: number };
  high_low: { low: number; high: number };
  score: number;
  reasons: string[];
}

interface ThemeResult {
  theme: { key: string; name: string; icon: string; description: string };
  top10: { number: number; score: number }[];
  predictions: Prediction[];
}

// デモデータ（Phase 1: APIが繋がるまで）
function generateDemoData(themeKey: string): ThemeResult {
  const theme = THEMES.find((t) => t.key === themeKey)!;
  const rng = () => Math.floor(Math.random() * 43) + 1;

  const predictions: Prediction[] = [];
  for (let i = 0; i < 3; i++) {
    const nums = new Set<number>();
    while (nums.size < 6) nums.add(rng());
    const sorted = [...nums].sort((a, b) => a - b);
    const odd = sorted.filter((n) => n % 2 === 1).length;
    const low = sorted.filter((n) => n <= 21).length;
    predictions.push({
      numbers: sorted,
      total: sorted.reduce((a, b) => a + b, 0),
      odd_even: { odd, even: 6 - odd },
      high_low: { low, high: 6 - low },
      score: Math.round((Math.random() * 30 + 30) * 10) / 10,
      reasons: ["直近ホット番号を含む", "奇偶バランス良好", "合計値が最適帯"],
    });
  }

  return {
    theme: {
      key: themeKey,
      name: theme.name,
      icon: theme.icon,
      description: theme.description,
    },
    top10: Array.from({ length: 10 }, (_, i) => ({
      number: rng(),
      score: Math.round((10 - i + Math.random() * 2) * 100) / 100,
    })),
    predictions,
  };
}

// 番号ボール
function NumberBall({ num, size = "lg" }: { num: number; size?: "sm" | "lg" }) {
  const sizeClass = size === "lg" ? "w-14 h-14 text-2xl" : "w-9 h-9 text-sm";
  let bgColor = "from-slate-500 to-slate-600";
  if (num <= 9) bgColor = "from-yellow-500 to-amber-600";
  else if (num <= 19) bgColor = "from-blue-500 to-indigo-600";
  else if (num <= 29) bgColor = "from-emerald-500 to-green-600";
  else if (num <= 39) bgColor = "from-red-500 to-rose-600";
  else bgColor = "from-purple-500 to-violet-600";

  return (
    <div
      className={`${sizeClass} rounded-full bg-gradient-to-br ${bgColor} flex items-center justify-center font-bold text-white shadow-lg`}
    >
      {num}
    </div>
  );
}

export default function Home() {
  const [selectedTheme, setSelectedTheme] = useState<string | null>(null);
  const [result, setResult] = useState<ThemeResult | null>(null);
  const [loading, setLoading] = useState(false);

  const handlePredict = async (themeKey: string) => {
    setSelectedTheme(themeKey);
    setLoading(true);

    // Phase 1: デモデータ。API接続後は以下に差し替え:
    // const res = await fetch(`/api/predict`, {
    //   method: "POST",
    //   headers: { "Content-Type": "application/json" },
    //   body: JSON.stringify({ mode: themeKey, count: 3 }),
    // });
    // const data = await res.json();

    await new Promise((r) => setTimeout(r, 800));
    const data = generateDemoData(themeKey);
    setResult(data);
    setLoading(false);
  };

  return (
    <main className="min-h-screen">
      {/* ヘッダー */}
      <header className="pt-12 pb-8 text-center">
        <h1 className="text-4xl font-bold tracking-tight mb-2">
          <span className="text-transparent bg-clip-text bg-gradient-to-r from-indigo-400 to-purple-400">
            Loto6 Analyzer
          </span>
        </h1>
        <p className="text-gray-400 text-sm">
          過去2000回超のデータから、統計に基づく予測番号を生成
        </p>
      </header>

      {/* テーマ選択 */}
      <section className="max-w-4xl mx-auto px-4 pb-8">
        <h2 className="text-sm uppercase tracking-widest text-gray-500 mb-4 text-center">
          テーマを選んで予測
        </h2>
        <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-3">
          {THEMES.map((theme) => (
            <button
              key={theme.key}
              onClick={() => handlePredict(theme.key)}
              className={`
                relative p-4 rounded-xl border transition-all duration-200
                bg-gradient-to-br ${theme.color} ${theme.border}
                hover:scale-105 hover:shadow-lg hover:shadow-indigo-500/10
                ${selectedTheme === theme.key ? "ring-2 ring-indigo-400 scale-105" : ""}
              `}
            >
              <div className="text-3xl mb-2">{theme.icon}</div>
              <div className="text-sm font-semibold">{theme.name}</div>
              <div className="text-xs text-gray-400 mt-1">
                {theme.description}
              </div>
            </button>
          ))}
        </div>
      </section>

      {/* ローディング */}
      {loading && (
        <div className="text-center py-16">
          <div className="inline-block w-8 h-8 border-2 border-indigo-400 border-t-transparent rounded-full animate-spin" />
          <p className="text-gray-400 mt-4 text-sm">分析中...</p>
        </div>
      )}

      {/* 結果表示 */}
      {result && !loading && (
        <section className="max-w-4xl mx-auto px-4 pb-16">
          <div className="text-center mb-8">
            <span className="text-4xl">{result.theme.icon}</span>
            <h3 className="text-xl font-bold mt-2">{result.theme.name}</h3>
            <p className="text-gray-400 text-sm">{result.theme.description}</p>
          </div>

          <div className="space-y-6">
            {result.predictions.map((pred, i) => {
              const themeStyle = THEMES.find(
                (t) => t.key === result.theme.key
              )!;
              return (
                <div
                  key={i}
                  className={`rounded-2xl border ${themeStyle.border} p-6 bg-[#1a1a2e]/80 backdrop-blur`}
                >
                  <div className="flex items-center justify-between mb-4">
                    <span
                      className={`text-xs px-2 py-1 rounded-full ${themeStyle.badge}`}
                    >
                      セット {i + 1}
                    </span>
                    <span className="text-xs text-gray-500">
                      スコア: {pred.score}
                    </span>
                  </div>

                  <div className="flex justify-center gap-3 mb-5">
                    {pred.numbers.map((num) => (
                      <NumberBall key={num} num={num} />
                    ))}
                  </div>

                  <div className="flex justify-center gap-6 text-xs text-gray-400 mb-4">
                    <span>
                      合計:{" "}
                      <span className="text-gray-200 font-mono">
                        {pred.total}
                      </span>
                    </span>
                    <span>
                      奇偶:{" "}
                      <span className="text-gray-200 font-mono">
                        {pred.odd_even.odd}:{pred.odd_even.even}
                      </span>
                    </span>
                    <span>
                      高低:{" "}
                      <span className="text-gray-200 font-mono">
                        {pred.high_low.low}:{pred.high_low.high}
                      </span>
                    </span>
                  </div>

                  <div className="flex flex-wrap justify-center gap-2">
                    {pred.reasons.map((reason, j) => (
                      <span
                        key={j}
                        className="text-xs px-2 py-1 rounded-md bg-white/5 text-gray-300"
                      >
                        {reason}
                      </span>
                    ))}
                  </div>
                </div>
              );
            })}
          </div>

          <p className="text-center text-xs text-gray-600 mt-8">
            統計分析に基づく参考情報です。ロト6は完全なランダム抽選であり、
            過去のデータから未来を予測することは理論上不可能です。
          </p>
        </section>
      )}

      {!result && !loading && (
        <div className="text-center py-16">
          <p className="text-gray-600 text-sm">
            上のテーマを選んで予測を開始
          </p>
        </div>
      )}
    </main>
  );
}
