# Flavia AI 料理アシスタント - 核心要件定義

## アプリの本質的な目的
**個人の好みと制約を学習する AI 料理パートナー**
- ユーザーの嗜好、調理環境を理解
- 実用的で現実的なレシピ・献立生成

## 必要最小限の機能

### 1. 核心機能（必須）
```
[入力] ユーザーリクエスト（「今日の夕食何作ろう？」「鶏肉と季節の野菜を使った料理」
入力側にテンプレを用意させましょう。それに応じた入力を人間がするように。）
[処理] 個人データ + AI → パーソナライズドレシピ
[出力] 具体的なレシピ + 材料リスト + 献立
```


### 3. UI（シンプル）
```
[チャット画面] リクエスト入力 + レスピ表示。見やすく。
[週間献立] 指定日数分の献立、夕飯のみ。
[学習状況] RAGを参照。
```

## 不要・過剰な機能

### 削除候補
- 複雑なキャッシュシステム（シンプルな辞書で十分）
- 過度なエラーハンドリング（基本的なtry-catchで十分）
- 多層のRAGシステム（個人データファイル直読みで十分）
- 特売情報連携（コア機能ではない）
- 複雑なコンテキストビルダー（プロンプトテンプレートで十分）
- 評価システム
- 学習機能

### 簡素化すべき箇所
- 複数のモニタリング → ログ出力のみ
- 高度な例外処理 → 基本的なエラー表示

## 理想的なファイル構成

```
src/flavia/
├── core/
│   ├── agent.py           # メインAIエージェント（Claude API呼び出し）
│   └── data_manager.py    # 個人データ管理（読み書き）
├── ui/
│   └── simple_app.py      # UI（自由チャット）
└── data/
    └── personal_data.json # 統合個人データ
```

## コア処理フロー（簡素版）

```python
def generate_recipe(user_request: str) -> dict:
    # 1. 個人データ読み込み
    personal_data = load_personal_data()
    個人データ、UIから入力されたプロンプトを整理。
    
    # 2. プロンプト作成
    prompt = create_prompt(user_request, personal_data)
    
    # 3. Claude API 呼び出し
    response = call_claude_api(prompt)
    
    # 4. JSON レスポンス解析
    recipe = parse_json_response(response)
    
    return recipe
```

## 学習システム（簡素版）

```python
def record_feedback(recipe_name: str, rating: int):
    # 1. フィードバック記録
    feedback = {"recipe": recipe_name, "rating": rating, "date": now()}
    
    # 2. 個人データ更新
    update_preferences(feedback)
    
    # 3. ファイル保存
    save_personal_data()
```

## 結論
現在のコードは機能が過剰で複雑すぎます。
**シンプルな AI チャット + 学習機能** に絞り込むべきです。

目標：現在の 3000行 → 500-800行 に削減

## 開発指針
- **シンプル第一**: 複雑な機能は追加しない
- **個人データ中心**: personal_data.json を軸とした設計
- **自由チャット**: テンプレートではなく自然言語入力
- **JSON応答**: Claude APIからの確実なJSON取得
- **最小限エラー処理**: 基本的なtry-catch のみ
- **学習機能なし**: 静的な個人データのみ使用