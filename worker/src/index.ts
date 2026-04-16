/**
 * ロト6 / ロト7 API - Cloudflare Worker
 *
 * エンドポイント（全て ?game=loto6|loto7 対応、デフォルト loto6）:
 *   GET  /api/health
 *   GET  /api/predict      - クイック予測
 *   POST /api/predict      - テーマ指定予測
 *   GET  /api/analysis     - 分析サマリー
 *   GET  /api/recent       - 直近の抽選結果
 *   GET  /api/history      - 予測履歴と的中集計
 */

export interface Env {
	ENVIRONMENT: string;
}

const corsHeaders = {
	"Access-Control-Allow-Origin": "*",
	"Access-Control-Allow-Methods": "GET, POST, OPTIONS",
	"Access-Control-Allow-Headers": "Content-Type",
};

const VALID_GAMES = ["loto6", "loto7"] as const;
type Game = typeof VALID_GAMES[number];

function jsonResponse(data: unknown, status = 200): Response {
	return new Response(JSON.stringify(data, null, 2), {
		status,
		headers: {
			"Content-Type": "application/json; charset=utf-8",
			...corsHeaders,
		},
	});
}

function errorResponse(message: string, status = 400): Response {
	return jsonResponse({ error: message }, status);
}

const DATA_BASE_URL = "https://raw.githubusercontent.com/nightridergsxf-star/loto6-analyzer/main/data";

function resolveGame(url: URL): Game {
	const raw = (url.searchParams.get("game") || "loto6").toLowerCase();
	if ((VALID_GAMES as readonly string[]).includes(raw)) {
		return raw as Game;
	}
	return "loto6";
}

async function fetchData(game: Game, filename: string): Promise<unknown> {
	const res = await fetch(`${DATA_BASE_URL}/${game}/${filename}`);
	if (!res.ok) {
		throw new Error(`Failed to fetch ${game}/${filename}: ${res.status}`);
	}
	return res.json();
}

export default {
	async fetch(request: Request, env: Env): Promise<Response> {
		const url = new URL(request.url);
		const path = url.pathname;
		const game = resolveGame(url);

		if (request.method === "OPTIONS") {
			return new Response(null, { headers: corsHeaders });
		}

		try {
			if (path === "/api/health") {
				return jsonResponse({
					status: "ok",
					environment: env.ENVIRONMENT,
					game,
					timestamp: new Date().toISOString(),
				});
			}

			if (path === "/api/predict" && request.method === "GET") {
				const data = await fetchData(game, "quick.json");
				return jsonResponse(data);
			}

			if (path === "/api/predict" && request.method === "POST") {
				const body = (await request.json()) as { mode?: string; count?: number };
				const mode = body.mode || "balanced";
				const validModes = [
					"hot_pursuit",
					"cold_rebound",
					"balanced",
					"center_cluster",
					"wildcard",
					"contrarian",
				];
				if (!validModes.includes(mode)) {
					return errorResponse(
						`Invalid mode. Use one of: ${validModes.join(", ")}`
					);
				}

				const data = (await fetchData(game, "predictions.json")) as {
					meta: unknown;
					themes: Array<{ theme: { key: string } }>;
				};
				const theme = data.themes.find((t) => t.theme.key === mode);
				if (!theme) {
					return errorResponse("Theme not found", 404);
				}

				return jsonResponse({ meta: data.meta, ...theme });
			}

			if (path === "/api/analysis") {
				return jsonResponse(await fetchData(game, "analysis.json"));
			}

			if (path === "/api/recent") {
				return jsonResponse(await fetchData(game, "recent_draws.json"));
			}

			if (path === "/api/history") {
				return jsonResponse(await fetchData(game, "history.json"));
			}

			return errorResponse("Not found", 404);
		} catch (e) {
			const message = e instanceof Error ? e.message : "Internal error";
			return errorResponse(message, 500);
		}
	},
};
