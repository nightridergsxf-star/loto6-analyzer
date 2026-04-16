"use client";

import { useState, useEffect } from "react";

const DATA_BASE_URL =
  "https://raw.githubusercontent.com/nightridergsxf-star/loto6-analyzer/main/data";

type Game = "loto6" | "loto7";

const GAMES: { key: Game; label: string; accent: string }[] = [
  { key: "loto6", label: "ロト6", accent: "from-indigo-400 to-purple-400" },
  { key: "loto7", label: "ロト7", accent: "from-amber-400 to-rose-400" },
];

function readGameFromURL(): Game {
  if (typeof window === "undefined") return "loto6";
  const q = new URLSearchParams(window.location.search).get("game");
  return q === "loto7" ? "loto7" : "loto6";
}

// テーマ定義
const THEMES = [
  {
    key: "hot_pursuit",
    name: "ホット追従型",
    icon: "🔥",
    description: "直近の流れに乗る",
    vibe: "勢いに乗る構成",
    color: "from-red-500/20 to-orange-500/20",
    border: "border-red-500/30",
    badge: "bg-red-500/20 text-red-300",
  },
  {
    key: "cold_rebound",
    name: "コールド反発型",
    icon: "❄️",
    description: "出遅れの揺り戻し",
    vibe: "静かに待った構成",
    color: "from-blue-500/20 to-cyan-500/20",
    border: "border-blue-500/30",
    badge: "bg-blue-500/20 text-blue-300",
  },
  {
    key: "balanced",
    name: "バランス重視型",
    icon: "⚖️",
    description: "安定志向の王道",
    vibe: "安定した構成",
    color: "from-emerald-500/20 to-teal-500/20",
    border: "border-emerald-500/30",
    badge: "bg-emerald-500/20 text-emerald-300",
  },
  {
    key: "center_cluster",
    name: "中央値集中型",
    icon: "🎯",
    description: "最頻帯を狙い撃ち",
    vibe: "統計の中心を突く構成",
    color: "from-purple-500/20 to-pink-500/20",
    border: "border-purple-500/30",
    badge: "bg-purple-500/20 text-purple-300",
  },
  {
    key: "wildcard",
    name: "ワイルドカード型",
    icon: "🃏",
    description: "揺らぎ最大の攻め",
    vibe: "直感に委ねた構成",
    color: "from-amber-500/20 to-yellow-500/20",
    border: "border-amber-500/30",
    badge: "bg-amber-500/20 text-amber-300",
  },
  {
    key: "contrarian",
    name: "逆張り型",
    icon: "🪞",
    description: "設計側の視点で読む",
    vibe: "あえて外した構成",
    color: "from-gray-500/20 to-slate-500/20",
    border: "border-gray-400/30",
    badge: "bg-gray-500/20 text-gray-300",
  },
];

const GRADE_LABELS: Record<string, { label: string; color: string }> = {
  perfect: { label: "完全一致", color: "text-yellow-300" },
  excellent: { label: "4個以上", color: "text-emerald-300" },
  good: { label: "3個一致", color: "text-blue-300" },
  close: { label: "惜しい", color: "text-purple-300" },
  miss: { label: "外れ", color: "text-gray-500" },
};

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
  game?: Game;
  display_name?: string;
  max_number?: number;
  pick_count?: number;
  bonus_count?: number;
  generated_at: string;
  total_draws: number;
  latest_draw: {
    number: number;
    date: string;
    numbers: number[];
    bonus: number;
    bonuses?: number[];
  };
}

interface PredictionsData {
  meta: Meta;
  themes: ThemeResult[];
}

interface HistoryResult {
  matched_numbers: number[];
  match_count: number;
  odd_even_match: boolean;
  high_low_match: boolean;
  sum_range_match: boolean;
  grade: string;
}

interface HistoryEntry {
  target_draw: number;
  based_on_date: string;
  checked: boolean;
  actual: number[] | null;
  themes: Record<string, { numbers: number[]; total: number; reasons: string[] }>;
  results?: Record<string, HistoryResult>;
}

interface HistoryData {
  meta: Meta;
  summary: {
    total_checked: number;
    theme_stats: Record<string, {
      avg_match: number;
      best_match: number;
      grades: Record<string, number>;
      total: number;
    }>;
    recent: HistoryEntry[];
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

function GameToggle({ game, onChange }: { game: Game; onChange: (g: Game) => void }) {
  return (
    <div className="flex justify-center mb-4">
      <div className="inline-flex rounded-xl border border-gray-700/60 bg-white/5 p-1">
        {GAMES.map((g) => (
          <button
            key={g.key}
            onClick={() => onChange(g.key)}
            className={`px-4 py-1.5 text-sm font-semibold rounded-lg transition-all ${
              game === g.key
                ? `text-white bg-gradient-to-r ${g.accent} shadow`
                : "text-gray-400 hover:text-gray-200"
            }`}
          >
            {g.label}
          </button>
        ))}
      </div>
    </div>
  );
}

export default function Home() {
  const [game, setGame] = useState<Game>("loto6");
  const [data, setData] = useState<PredictionsData | null>(null);
  const [historyData, setHistoryData] = useState<HistoryData | null>(null);
  const [selectedTheme, setSelectedTheme] = useState<string | null>(null);
  const [result, setResult] = useState<ThemeResult | null>(null);
  const [myPick, setMyPick] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // 初回マウント: URL から game を復元
  useEffect(() => {
    setGame(readGameFromURL());
  }, []);

  // ゲーム変更時: URL クエリを同期しつつデータ再取得
  useEffect(() => {
    if (typeof window !== "undefined") {
      const params = new URLSearchParams(window.location.search);
      if (game === "loto6") params.delete("game");
      else params.set("game", game);
      const qs = params.toString();
      const newUrl = window.location.pathname + (qs ? `?${qs}` : "");
      window.history.replaceState({}, "", newUrl);
    }

    setLoading(true);
    setError(null);
    setResult(null);
    setSelectedTheme(null);
    setMyPick(null);

    const base = `${DATA_BASE_URL}/${game}`;
    Promise.all([
      fetch(`${base}/predictions.json`).then((r) => r.ok ? r.json() : Promise.reject(r.status)),
      fetch(`${base}/history.json`).then((r) => r.ok ? r.json() : null).catch(() => null),
    ])
      .then(([predictions, history]) => {
        setData(predictions);
        setHistoryData(history);
        setLoading(false);
      })
      .catch((err) => {
        setError(`データ取得に失敗しました: ${err}`);
        setLoading(false);
      });
  }, [game]);

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
  const gameLabel = GAMES.find((g) => g.key === game)?.label ?? "ロト6";
  const gameAccent = GAMES.find((g) => g.key === game)?.accent ?? "from-indigo-400 to-purple-400";

  return (
    <main className="min-h-screen">
      {/* ヘッダー */}
      <header className="pt-12 pb-4 text-center">
        <GameToggle game={game} onChange={setGame} />
        <h1 className="text-4xl font-bold tracking-tight mb-2">
          <span className={`text-transparent bg-clip-text bg-gradient-to-r ${gameAccent}`}>
            {gameLabel} Analyzer
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
            {(meta.latest_draw.bonuses ?? [meta.latest_draw.bonus]).join(", ")}
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
            {/* テーマの一言コメント */}
            {(() => {
              const t = THEMES.find(t => t.key === result.theme.key);
              const vibe = result.theme.key === "contrarian"
                ? "人間の選択バイアスを逆手に取った構成"
                : t?.vibe;
              return vibe ? (
                <p className="text-gray-500 text-xs mt-2 italic">&quot;{vibe}&quot;</p>
              ) : null;
            })()}
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

              // 逆張り度の計算（ゲーム別閾値）
              const contrarianHigh = game === "loto7" ? 28 : 32;
              const maxRound = game === "loto7" ? 35 : 40;
              const roundNums = new Set<number>();
              for (let r = 5; r <= maxRound; r += 5) roundNums.add(r);
              const contrarianLevel = result.theme.key === "contrarian"
                ? (() => {
                    const highZone = pred.numbers.filter(n => n >= contrarianHigh).length;
                    const sorted = [...pred.numbers].sort((a, b) => a - b);
                    const hasConsec = sorted.some((n, i) => i < sorted.length - 1 && sorted[i + 1] - n === 1);
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
            統計分析に基づく参考情報です。{gameLabel}は完全なランダム抽選であり、
            過去のデータから未来を予測することは理論上不可能です。
          </p>
        </section>
      )}

      {/* 未選択時: どっちに賭ける？ + 履歴 */}
      {!result && data && (
        <div className="max-w-4xl mx-auto px-4 pb-16">
          {/* どっちに賭ける？ */}
          {(() => {
            const balanced = data.themes.find(t => t.theme.key === "balanced");
            const contrarian = data.themes.find(t => t.theme.key === "contrarian");
            if (!balanced?.predictions[0] || !contrarian?.predictions[0]) return null;
            const b = balanced.predictions[0];
            const c = contrarian.predictions[0];

            return (
              <div className="mb-12">
                <h2 className="text-sm uppercase tracking-widest text-gray-500 mb-6 text-center">
                  今回、どっちに賭ける？
                </h2>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  {/* バランス側 */}
                  <button
                    onClick={() => { setMyPick("balanced"); handlePredict("balanced"); }}
                    className={`p-6 rounded-2xl border transition-all duration-200
                      ${myPick === "balanced" ? "border-emerald-400 ring-2 ring-emerald-400/50" : "border-emerald-500/30"}
                      bg-gradient-to-br from-emerald-500/10 to-teal-500/10 hover:scale-[1.02]`}
                  >
                    <div className="text-2xl mb-2">⚖️</div>
                    <div className="text-sm font-semibold text-emerald-300 mb-3">バランス重視型</div>
                    <div className="flex justify-center gap-2 mb-3">
                      {b.numbers.map(n => <NumberBall key={n} num={n} size="sm" />)}
                    </div>
                    <p className="text-xs text-gray-400 italic">&quot;安定した構成&quot;</p>
                  </button>

                  {/* 逆張り側 */}
                  <button
                    onClick={() => { setMyPick("contrarian"); handlePredict("contrarian"); }}
                    className={`p-6 rounded-2xl border transition-all duration-200
                      ${myPick === "contrarian" ? "border-gray-300 ring-2 ring-gray-400/50" : "border-gray-500/30"}
                      bg-gradient-to-br from-gray-500/10 to-slate-500/10 hover:scale-[1.02]`}
                  >
                    <div className="text-2xl mb-2">🪞</div>
                    <div className="text-sm font-semibold text-gray-300 mb-3">逆張り型</div>
                    <div className="flex justify-center gap-2 mb-3">
                      {c.numbers.map(n => <NumberBall key={n} num={n} size="sm" />)}
                    </div>
                    <p className="text-xs text-gray-400 italic">&quot;あえて外した構成&quot;</p>
                  </button>
                </div>
              </div>
            );
          })()}

          {/* 履歴セクション */}
          {historyData && historyData.summary.total_checked > 0 && (
            <div>
              <h2 className="text-sm uppercase tracking-widest text-gray-500 mb-6 text-center">
                過去の的中履歴
              </h2>

              {/* テーマ別成績 */}
              <div className="grid grid-cols-2 sm:grid-cols-3 gap-3 mb-8">
                {Object.entries(historyData.summary.theme_stats).map(([key, stats]) => {
                  const theme = THEMES.find(t => t.key === key);
                  if (!theme) return null;
                  return (
                    <div key={key} className="p-3 rounded-xl border border-gray-700/50 bg-white/3 text-center">
                      <span className="text-lg">{theme.icon}</span>
                      <p className="text-xs text-gray-400 mt-1">{theme.name}</p>
                      <p className="text-lg font-bold text-gray-200 mt-1">
                        平均 {stats.avg_match} 個
                      </p>
                      <p className="text-xs text-gray-500">
                        最高 {stats.best_match}個 / {stats.total}回
                      </p>
                    </div>
                  );
                })}
              </div>

              {/* 直近の結果 */}
              <div className="space-y-3">
                {historyData.summary.recent.map((entry, i) => (
                  <div key={i} className="p-4 rounded-xl border border-gray-700/50 bg-white/3">
                    <div className="flex items-center justify-between mb-2">
                      <span className="text-xs text-gray-500">
                        第{entry.target_draw}回（{entry.based_on_date}時点の予測）
                      </span>
                    </div>
                    {entry.actual && (
                      <div className="flex items-center gap-2 mb-3">
                        <span className="text-xs text-gray-500">実際:</span>
                        <div className="flex gap-1">
                          {entry.actual.map(n => <NumberBall key={n} num={n} size="sm" />)}
                        </div>
                      </div>
                    )}
                    <div className="grid grid-cols-2 sm:grid-cols-3 gap-2">
                      {entry.results && Object.entries(entry.results).map(([themeKey, result]) => {
                        const theme = THEMES.find(t => t.key === themeKey);
                        const grade = GRADE_LABELS[result.grade];
                        if (!theme) return null;
                        return (
                          <div key={themeKey} className="flex items-center gap-2 text-xs">
                            <span>{theme.icon}</span>
                            <span className={grade?.color || "text-gray-400"}>
                              {result.match_count}/{meta?.pick_count ?? (game === "loto7" ? 7 : 6)}
                              {result.odd_even_match && " 奇偶○"}
                              {result.sum_range_match && " 合計○"}
                            </span>
                          </div>
                        );
                      })}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* 履歴がまだない場合 */}
          {(!historyData || historyData.summary.total_checked === 0) && (
            <p className="text-center text-gray-600 text-xs mt-8">
              履歴はデータ更新後に蓄積されます
            </p>
          )}
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
          <p>{gameLabel} Analyzer v1.1</p>
        </div>
      </footer>
    </main>
  );
}
