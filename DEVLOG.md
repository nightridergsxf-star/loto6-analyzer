# DEVLOG

## 2026-04-17 ロト7 対応（ゲーム切替アーキテクチャ）
### 実施内容
- `scripts/game_config.py` 新設: `GameConfig` dataclass + LOTO6 / LOTO7 インスタンス
  - 番号範囲/pick数/ボーナス数/高低分割/逆張り閾値/CSV URL & カラム を一元管理
- Python 側を全てパラメータ化（`data_source` / `analysis` / `scoring` / `predict` / `history`）
- `scripts/generate.py` を両ゲーム対応 (`--game loto6|loto7|all`)、出力を `data/loto6/` `data/loto7/` に分離
- Worker: 全エンドポイントに `?game=loto6|loto7` パラメータ追加（デフォルト loto6）
- Frontend: ヘッダーにロト6/ロト7 トグル、URL クエリ `?game=...` で状態保持、`bonuses` 複数対応
- GitHub Actions: cron に金曜 (ロト7 抽選日) 追加、`loto7.csv` も commit
- `loto6_analyzer.py` (旧 CLI) は触らず凍結
- 旧 `data/*.json`（root 直下）は削除、全て `data/{loto6,loto7}/` 配下へ

### 成果
- ロト6: 2094回分 / ロト7: 672回分 のデータ生成確認
- `cd frontend && npm run build` 成功

### 課題・備考
- Loto7 の予測履歴は初回投入のみ。次回以降の抽選で照合が回るかを観察
- contrarian ボーナスの Loto7 向けチューニング（閾値=28, ラウンド数=35以下）はざっくり設定。運用しつつ調整余地あり

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
