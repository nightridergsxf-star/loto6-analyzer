/**
 * ロト6 API - Cloudflare Worker
 *
 * エンドポイント:
 *   GET  /api/health     - ヘルスチェック
 *   GET  /api/predict     - クイック予測（全テーマ×1セット）
 *   POST /api/predict     - テーマ指定予測
 *   GET  /api/analysis    - 分析サマリー
 *   GET  /api/recent      - 直近の抽選結果
 *
 * データは data/ ディレクトリのJSONを読み込む（前処理済み）
 * Phase 2以降でKVやD1に移行予定
 */

export interface Env {
	ENVIRONMENT: string;
}

// CORS ヘッダー
const corsHeaders = {
	"Access-Control-Allow-Origin": "*",
	"Access-Control-Allow-Methods": "GET, POST, OPTIONS",
	"Access-Control-Allow-Headers": "Content-Type",
};

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

// ── データ読み込み（Phase 1: 静的JSONから）──
// Phase 2でKV/D1に移行する想定
// 今は GitHub Pages or R2 に置いた JSON を fetch する

const DATA_BASE_URL = "https://raw.githubusercontent.com/{owner}/{repo}/main/data";

async function fetchData(filename: string): Promise<unknown> {
	// Phase 1: ローカルの data/ から直接 import するか、
	// GitHub raw URL から取得する
	// 開発時は埋め込みJSONを使用
	const url = `${DATA_BASE_URL}/${filename}`;
	const res = await fetch(url);
	if (!res.ok) {
		throw new Error(`Failed to fetch ${filename}: ${res.status}`);
	}
	return res.json();
}

// ── ルーティング ──

export default {
	async fetch(request: Request, env: Env): Promise<Response> {
		const url = new URL(request.url);
		const path = url.pathname;

		// CORS preflight
		if (request.method === "OPTIONS") {
			return new Response(null, { headers: corsHeaders });
		}

		try {
			// Health check
			if (path === "/api/health") {
				return jsonResponse({
					status: "ok",
					environment: env.ENVIRONMENT,
					timestamp: new Date().toISOString(),
				});
			}

			// クイック予測
			if (path === "/api/predict" && request.method === "GET") {
				const data = await fetchData("quick.json");
				return jsonResponse(data);
			}

			// テーマ指定予測
			if (path === "/api/predict" && request.method === "POST") {
				const body = (await request.json()) as { mode?: string; count?: number };
				const mode = body.mode || "balanced";
				const validModes = [
					"hot_pursuit",
					"cold_rebound",
					"balanced",
					"center_cluster",
					"wildcard",
				];
				if (!validModes.includes(mode)) {
					return errorResponse(
						`Invalid mode. Use one of: ${validModes.join(", ")}`
					);
				}

				// Phase 1: 全予測データから該当テーマを返す
				const data = (await fetchData("predictions.json")) as {
					meta: unknown;
					themes: Array<{ theme: { key: string } }>;
				};
				const theme = data.themes.find((t) => t.theme.key === mode);
				if (!theme) {
					return errorResponse("Theme not found", 404);
				}

				return jsonResponse({
					meta: data.meta,
					...theme,
				});
			}

			// 分析サマリー
			if (path === "/api/analysis") {
				const data = await fetchData("analysis.json");
				return jsonResponse(data);
			}

			// 直近の抽選結果
			if (path === "/api/recent") {
				const data = await fetchData("recent_draws.json");
				return jsonResponse(data);
			}

			return errorResponse("Not found", 404);
		} catch (e) {
			const message = e instanceof Error ? e.message : "Internal error";
			return errorResponse(message, 500);
		}
	},
};
