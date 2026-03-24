# Loto6 Analyzer

## プロジェクト概要
ロト6の過去全データを統計分析し、テーマ別のおすすめ番号を生成するWebサービス。
CLI版とWeb版（Cloudflare Pages + Workers）の両方を提供。

## アーキテクチャ
```
scripts/          Python - データ取得・分析・前処理（JSON生成）
  data_source.py  CSV取得・整形
  analysis.py     全13種の統計分析（純粋データ返却）
  scoring.py      テーマ別スコア計算
  predict.py      予測番号生成
  generate.py     JSON出力スクリプト（CI/手動で実行）

data/             生成されたJSON（Worker/Pagesから読み込み）
  meta.json       メタ情報
  analysis.json   分析結果
  predictions.json 全テーマ予測
  quick.json      クイック予測
  recent_draws.json 直近100回の抽選結果

worker/           Cloudflare Worker（API）
  src/index.ts    エンドポイント定義

frontend/         Next.js（Cloudflare Pages）
  src/app/        App Router

loto6_analyzer.py 既存CLIツール（互換維持）
```

## よく使うコマンド
```bash
# CLI版
python3 loto6_analyzer.py
python3 loto6_analyzer.py --quick
python3 loto6_analyzer.py --theme hot

# JSON生成（デプロイ前処理）
python3 scripts/generate.py

# フロント開発
cd frontend && npm run dev

# Worker開発
cd worker && npx wrangler dev
```

## デプロイ
- フロント: Cloudflare Pages（GitHub連携）
- API: Cloudflare Workers
- データ更新: GitHub Actions（毎週月・木 20:30 JST）
