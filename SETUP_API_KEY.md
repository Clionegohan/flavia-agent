# Claude API Key セットアップ手順

## 🔑 API Key取得方法

1. **Anthropic Console にアクセス**
   - https://console.anthropic.com/ にアクセス
   - アカウント作成またはログイン

2. **API Key を生成**
   - 「API Keys」セクションに移動
   - 「Create Key」をクリック
   - Key名を設定して生成

3. **API Key をコピー**
   - 生成されたKeyをコピー（一度しか表示されません）

## ⚙️ 設定方法

### 方法1: .envファイル使用（推奨）

```bash
# プロジェクトルートに .env ファイルを作成
cp .env.example .env

# .env ファイルを編集してAPI Keyを設定
ANTHROPIC_API_KEY=sk-ant-api03-xxxxxxxxxxxxxxxxxxxx
```

### 方法2: 環境変数で直接設定

```bash
# 一時的な設定（セッション終了まで）
export ANTHROPIC_API_KEY="sk-ant-api03-xxxxxxxxxxxxxxxxxxxx"

# 永続的な設定（~/.bashrc or ~/.zshrcに追加）
echo 'export ANTHROPIC_API_KEY="sk-ant-api03-xxxxxxxxxxxxxxxxxxxx"' >> ~/.bashrc
```

### 方法3: アプリ起動時に設定

```bash
# アプリ起動時に環境変数として設定
ANTHROPIC_API_KEY="sk-ant-api03-xxxxxxxxxxxxxxxxxxxx" python run_app.py
```

## 🚀 確認方法

```bash
# API Key設定確認
echo $ANTHROPIC_API_KEY

# アプリでの動作確認
python run_app.py
```

## ⚠️ セキュリティ注意事項

- API Keyは秘密情報です。他人と共有しないでください
- .envファイルは.gitignoreに含まれており、Gitにコミットされません
- 本番環境では環境変数による設定を推奨します

## 💡 API Key未設定時の動作

- API Keyが設定されていない場合、アプリはフォールバック応答を返します
- 基本的な機能は動作しますが、AI生成の品質は制限されます
- 実際のClaude AIを使用するにはAPI Keyの設定が必要です

## 💰 料金について

- Claude APIは使用量に応じた従量課金制です
- 詳細は https://www.anthropic.com/pricing をご確認ください
- 開発・テスト目的では比較的低コストで利用できます