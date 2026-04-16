# DEVLOG

## 2026-04-16 最新データ反映 & history.json 読み書きバグ修正
### 実施内容
- `scripts/generate.py` 実行で最新抽選データを反映（第2085回 → 第2094回、+9回分）
- `history.json` が dict 形式で保存されると次回実行時に `load_history` が list として扱えず `AttributeError` で落ちるバグを修正
  - `scripts/history.py#load_history` を dict/list 両形式対応に
  - `scripts/generate.py` の出力に `entries` キーを追加し履歴リストを保持
- README のデータソース注記を最新回数・日付に更新

### 成果
- 最新抽選: 第2094回 / 2026-04-16 / 本数字 3,4,7,11,24,30 / ボーナス 16
- `data/` 配下6ファイル再生成完了

### 課題・備考
- `checked: 0件` 状態のため、次回以降の実行で予測→照合のサイクルが回るか要観察

## 2026-03-24 (2) Web化・プロジェクト構造化
### 実施内容
- Phase 5まで見据えたプロジェクト構造を設計・実装
- Pythonロジックをモジュール分割
  - `scripts/data_source.py` — データ取得・整形
  - `scripts/analysis.py` — 全13種分析（純粋データ返却、print排除）
  - `scripts/scoring.py` — テーマ別スコア計算
  - `scripts/predict.py` — 予測番号生成
  - `scripts/generate.py` — JSON出力スクリプト
- Cloudflare Worker API 作成 (`worker/src/index.ts`)
  - `GET /api/health`, `GET /api/predict`, `POST /api/predict`, `GET /api/analysis`, `GET /api/recent`
- Next.js フロントエンド作成 (`frontend/`)
  - テーマ選択UI（5テーマのカード）
  - 番号ボール表示（十の位グループで色分け）
  - スコア・奇偶・高低・理由の表示
- GitHub Actions ワークフロー作成
  - 毎週月・木 20:30 JST にデータ自動更新
- `data/` にJSON出力確認済み（5ファイル）

### 成果
- CLI版は既存の `loto6_analyzer.py` で互換維持
- Web版はデモデータで動作確認済み
- JSON生成パイプライン動作確認済み
- Next.js ビルド成功

### 課題・備考
- Worker の DATA_BASE_URL を実際のGitHubリポジトリに差し替える必要あり
- Cloudflare Pages / Workers のデプロイ設定はリポジトリ作成後に実施
- フロントは現在デモデータ、API接続でリアルデータに切替予定
- Phase 2: 予測履歴・的中チェック機能の追加

## 2026-03-24 (1) 初期開発
### 実施内容
- ロト6分析・予測ツール `loto6_analyzer.py` を新規作成
- KYO's LOTO6 サイトからCSVデータの自動取得機能を実装
- 全13種類の統計分析を実装
- 予測ロジック v2 実装（エリゥさんのレビューを反映）
  - テーマ別スコアリング（5テーマ）
  - 6要素スコア + 確率抽選 + ソフトスコア評価
- 対話モード + コマンドラインインターフェース追加

### 成果
- 2085回分の過去データを正常に取得・分析
- 計25セットのおすすめ番号を生成
- 実行時間: 約2.5秒
