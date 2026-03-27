"use client";

import { useState, useEffect } from "react";

// Phase 1: GitHub raw URLから直接読む
// Phase 2: Cloudflare Worker API に差し替え
const DATA_URL =
  "https://raw.githubusercontent.com/nightridergsxf-star/loto6-analyzer/main/data";

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
  {
    key: "contrarian",
    name: "逆張り型",
    icon: "🪞",
    description: "設計側の視点で読む",
    color: "from-gray-500/20 to-slate-500/20",
    border: "border-gray-400/30",
    badge: "bg-gray-500/20 text-gray-300",
  },
];

interface Prediction {
  numbers: number[];
  total: number;
  odd_even: { odd: number; even: number };
  high_low: { low: number; high: number };
  score: number;
  combo_score: number;
  reasons: string[];
}

interface ThemeResult {
  theme: { key: string; name: string; icon: string; description: string };
  top10: { number: number; score: number }[];
  predictions: Prediction[];
}

interface Meta {
  generated_at: string;
  total_draws: number;
  latest_draw: {
    number: number;
    date: string;
    numbers: number[];
    bonus: number;
  };
}

interface PredictionsData {
  meta: Meta;
  themes: ThemeResult[];
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
  const [data, setData] = useState<PredictionsData | null>(null);
  const [selectedTheme, setSelectedTheme] = useState<string | null>(null);
  const [result, setResult] = useState<ThemeResult | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // 初回読み込み: predictions.json を取得
  useEffect(() => {
    fetch(`${DATA_URL}/predictions.json`)
      .then((res) => {
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        return res.json();
      })
      .then((json: PredictionsData) => {
        setData(json);
        setLoading(false);
      })
      .catch((err) => {
        setError(`データ取得に失敗しました: ${err.message}`);
        setLoading(false);
      });
  }, []);

  const handlePredict = (themeKey: string) => {
    if (!data) return;
    setSelectedTheme(themeKey);
    const theme = data.themes.find((t) => t.theme.key === themeKey);
    setResult(theme || null);
  };

  // 初回ローディング
  if (loading) {
    return (
      <main className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <div className="inline-block w-10 h-10 border-2 border-indigo-400 border-t-transparent rounded-full animate-spin" />
          <p className="text-gray-400 mt-4">データを読み込み中...</p>
        </div>
      </main>
    );
  }

  // エラー
  if (error) {
    return (
      <main className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <p className="text-red-400 mb-2">{error}</p>
          <button
            onClick={() => window.location.reload()}
            className="text-sm text-indigo-400 underline"
          >
            再読み込み
          </button>
        </div>
      </main>
    );
  }

  const meta = data?.meta;

  return (
    <main className="min-h-screen">
      {/* ヘッダー */}
      <header className="pt-12 pb-4 text-center">
        <h1 className="text-4xl font-bold tracking-tight mb-2">
          <span className="text-transparent bg-clip-text bg-gradient-to-r from-indigo-400 to-purple-400">
            Loto6 Analyzer
          </span>
        </h1>
        <p className="text-gray-400 text-sm">
          過去{meta?.total_draws?.toLocaleString()}回のデータから、統計に基づく予測番号を生成
        </p>
      </header>

      {/* メタ情報 */}
      {meta && (
        <div className="flex justify-center gap-6 text-xs text-gray-500 pb-6">
          <span>
            最新: 第{meta.latest_draw.number}回（{meta.latest_draw.date}）
          </span>
          <span>
            当選番号: {meta.latest_draw.numbers.join(", ")} +{" "}
            {meta.latest_draw.bonus}
          </span>
        </div>
      )}

      {/* テーマ選択 */}
      <section className="max-w-4xl mx-auto px-4 pb-8">
        <h2 className="text-sm uppercase tracking-widest text-gray-500 mb-4 text-center">
          テーマを選んで予測
        </h2>
        <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3">
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

      {/* 結果表示 */}
      {result && (
        <section className="max-w-4xl mx-auto px-4 pb-16">
          <div className="text-center mb-8">
            <span className="text-4xl">{result.theme.icon}</span>
            <h3 className="text-xl font-bold mt-2">{result.theme.name}</h3>
            <p className="text-gray-400 text-sm">{result.theme.description}</p>
            {/* 逆張りモード: 思想サマリー */}
            {result.theme.key === "contrarian" && (
              <p className="text-gray-500 text-xs mt-2 italic">
                &quot;人間の選択バイアスを逆手に取った構成&quot;
              </p>
            )}
          </div>

          {/* 逆張りモード: バランス型との比較 */}
          {result.theme.key === "contrarian" && data && (() => {
            const balanced = data.themes.find(t => t.theme.key === "balanced");
            if (!balanced) return null;
            const balancedNums = new Set(balanced.predictions.flatMap(p => p.numbers));
            const contrarianNums = new Set(result.predictions.flatMap(p => p.numbers));
            const onlyContrarian = [...contrarianNums].filter(n => !balancedNums.has(n)).sort((a, b) => a - b);
            const onlyBalanced = [...balancedNums].filter(n => !contrarianNums.has(n)).sort((a, b) => a - b);

            return (
              <div className="mb-8 p-4 rounded-xl border border-gray-700/50 bg-white/3">
                <h4 className="text-xs text-gray-500 uppercase tracking-widest mb-3 text-center">
                  バランス型とのズレ
                </h4>
                <div className="grid grid-cols-2 gap-4">
                  <div className="text-center">
                    <p className="text-xs text-emerald-400 mb-2">⚖️ バランス型だけ</p>
                    <div className="flex justify-center gap-1 flex-wrap">
                      {onlyBalanced.slice(0, 8).map(n => (
                        <NumberBall key={n} num={n} size="sm" />
                      ))}
                    </div>
                  </div>
                  <div className="text-center">
                    <p className="text-xs text-gray-300 mb-2">🪞 逆張り型だけ</p>
                    <div className="flex justify-center gap-1 flex-wrap">
                      {onlyContrarian.slice(0, 8).map(n => (
                        <NumberBall key={n} num={n} size="sm" />
                      ))}
                    </div>
                  </div>
                </div>
              </div>
            );
          })()}

          {/* スコアTOP10 */}
          <div className="flex justify-center gap-2 mb-8 flex-wrap">
            {result.top10.map((item, i) => (
              <div
                key={i}
                className="flex items-center gap-1 bg-white/5 rounded-lg px-2 py-1"
              >
                <NumberBall num={item.number} size="sm" />
                <span className="text-xs text-gray-400 font-mono">
                  {item.score > 0 ? "+" : ""}
                  {item.score}
                </span>
              </div>
            ))}
          </div>

          {/* 予測セット */}
          <div className="space-y-6">
            {result.predictions.map((pred, i) => {
              const themeStyle = THEMES.find(
                (t) => t.key === result.theme.key
              )!;

              // 逆張り度の計算
              const contrarianLevel = result.theme.key === "contrarian"
                ? (() => {
                    const highZone = pred.numbers.filter(n => n >= 32).length;
                    const sorted = [...pred.numbers].sort((a, b) => a - b);
                    const hasConsec = sorted.some((n, i) => i < sorted.length - 1 && sorted[i + 1] - n === 1);
                    const roundNums = new Set([5, 10, 15, 20, 25, 30, 35, 40]);
                    const hasRound = pred.numbers.some(n => roundNums.has(n));
                    const score = highZone * 2 + (hasConsec ? 0 : 2) + (hasRound ? 0 : 1);
                    if (score >= 6) return { label: "強い逆張り", icon: "⚠️", color: "text-red-400" };
                    if (score >= 3) return { label: "中程度", icon: "🔀", color: "text-amber-400" };
                    return { label: "バランス寄り", icon: "🎯", color: "text-emerald-400" };
                  })()
                : null;

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
                    <div className="flex items-center gap-3">
                      {contrarianLevel && (
                        <span className={`text-xs ${contrarianLevel.color}`}>
                          {contrarianLevel.icon} {contrarianLevel.label}
                        </span>
                      )}
                      <span className="text-xs text-gray-500">
                        スコア: {pred.score}
                      </span>
                    </div>
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

                  {pred.reasons.length > 0 && (
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
                  )}
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

      {/* 未選択時 */}
      {!result && (
        <div className="text-center py-16">
          <p className="text-gray-600 text-sm">
            上のテーマを選んで予測を開始
          </p>
        </div>
      )}

      {/* フッター */}
      <footer className="py-6 text-center border-t border-gray-800/50">
        <div className="text-xs text-gray-600 space-y-1">
          {meta && (
            <p>
              データ更新:{" "}
              {new Date(meta.generated_at).toLocaleString("ja-JP")} / 全
              {meta.total_draws.toLocaleString()}回分
            </p>
          )}
          <p>Loto6 Analyzer v1.0</p>
        </div>
      </footer>
    </main>
  );
}
