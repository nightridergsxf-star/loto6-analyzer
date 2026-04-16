# Lottery Analyzer (Loto6 / Loto7)

## プロジェクト概要
ロト6 / ロト7 の過去全データを統計分析し、テーマ別のおすすめ番号を生成する Web サービス。
CLI 版（ロト6 のみ、レガシー互換）と Web 版（ロト6/ロト7 切替、Cloudflare Pages + Workers）を提供。

## アーキテクチャ
```
scripts/          Python - データ取得・分析・前処理（JSON生成、両ゲーム対応）
  game_config.py  GameConfig dataclass（LOTO6 / LOTO7 定義）
  data_source.py  CSV取得・整形（config 受け取り）
  analysis.py     全13種の統計分析（config で範囲・pick数を切替）
  scoring.py      テーマ別スコア計算 + 逆張り (contrarian) ボーナス
  predict.py      予測番号生成
  history.py      予測履歴・的中チェック
  generate.py     JSON出力スクリプト (--game loto6|loto7|all)

data/
  loto6/{meta,analysis,predictions,quick,recent_draws,history}.json
  loto7/{meta,analysis,predictions,quick,recent_draws,history}.json

worker/           Cloudflare Worker（API, ?game=loto6|loto7 対応）
  src/index.ts

frontend/         Next.js 16 (App Router, Cloudflare Pages)
  src/app/page.tsx  ゲームトグル (URL クエリ ?game=... で状態保持)

loto6.csv / loto7.csv    ダウンロード済み生データ
loto6_analyzer.py        既存 CLI（ロト6 専用、互換維持のため凍結）
```

## GameConfig で切替している主なパラメータ
- 番号範囲: ロト6=1-43 / ロト7=1-37
- pick数: 6 / 7
- ボーナス数: 1 / 2
- 高低分割: 21 / 18
- 逆張り「誕生日圏外」閾値: 32+ / 28+
- CSV URL & カラム名

## よく使うコマンド
```bash
# CLI 版（ロト6 のみ）
python3 loto6_analyzer.py

# JSON 生成（両ゲーム）
python3 scripts/generate.py
python3 scripts/generate.py --game loto7   # 片方だけ

# フロント開発
cd frontend && npm run dev

# Worker 開発
cd worker && npx wrangler dev

# API 呼び出し例
curl "https://.../api/predict?game=loto7"
```

## デプロイ
- フロント: Cloudflare Pages（GitHub 連携）
- API: Cloudflare Workers
- データ更新: GitHub Actions（月・木・金 20:30 JST、`scripts/generate.py` で両ゲームを一括生成）
