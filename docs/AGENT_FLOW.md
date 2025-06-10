# 🔄 Flavia プロンプトアシスタント フロー

## シンプルなプロンプトアシスタントの処理フロー

```mermaid
graph TD
    %% ユーザー入力
    UserInput([牛肉とトマトを使った料理が食べたい]) --> UI[Streamlit UI]
    UI --> SetDays[日数指定: 1〜7日]
    
    %% プロンプト構築
    SetDays --> LoadPersonal[個人情報読み込み<br/>・嗜好・制約・常備品<br/>・過去の履歴]
    LoadPersonal --> CombinePrompt[プロンプト結合<br/>ユーザーリクエスト + 個人情報]
    
    %% Claude AI呼び出し
    CombinePrompt --> BuildPrompt[精巧なプロンプト構築<br/>・詳細レシピ指示<br/>・買い物リスト形式指定<br/>・多様性ガイドライン]
    BuildPrompt --> ClaudeAPI[Claude API送信]
    
    %% 結果処理
    ClaudeAPI --> AIResponse[Claude応答<br/>JSON形式で返却<br/>・N日分献立<br/>・詳細レシピ<br/>・ソート済み買い物リスト]
    AIResponse --> ParseJSON[JSON解析]
    ParseJSON --> DisplayUI[UI表示<br/>・献立カード<br/>・レシピ詳細<br/>・買い物リスト]
    
    %% 簡潔なスタイル
    classDef input fill:#e1f5fe,stroke:#01579b,stroke-width:2px;
    classDef process fill:#f3e5f5,stroke:#4a148c,stroke-width:2px;
    classDef ai fill:#fff3e0,stroke:#e65100,stroke-width:2px;
    classDef output fill:#e8f5e8,stroke:#1b5e20,stroke-width:2px;
    
    class UserInput,UI,SetDays input;
    class LoadPersonal,CombinePrompt,BuildPrompt,ParseJSON process;
    class ClaudeAPI,AIResponse ai;
    class DisplayUI output;
```

## プロンプトアシスタントの実際の動作フロー

```mermaid
sequenceDiagram
    participant User as ユーザー
    participant UI as Streamlit UI
    participant Assistant as プロンプトアシスタント
    participant PersonalData as 個人データ
    participant Claude as Claude API
    
    %% ユーザー入力
    User->>UI: 「牛肉とトマトを使った料理が食べたい」
    UI->>UI: 日数選択（1〜7日）
    
    %% プロンプト構築フェーズ
    UI->>Assistant: generate(request, days)
    Assistant->>PersonalData: 個人情報取得
    PersonalData-->>Assistant: 嗜好・制約・常備品・履歴
    
    Assistant->>Assistant: プロンプト結合<br/>ユーザーリクエスト + 個人情報
    Assistant->>Assistant: 精巧なプロンプト構築<br/>詳細レシピ指示・買い物リスト形式
    
    %% Claude AI呼び出しフェーズ  
    Assistant->>Claude: 構築済みプロンプト送信
    Note over Claude: プロンプトに従って<br/>N日分献立・詳細レシピ・<br/>ソート済み買い物リスト生成
    Claude-->>Assistant: JSON形式レスポンス
    
    %% 結果表示フェーズ
    Assistant->>Assistant: JSON解析・形式整理
    Assistant-->>UI: 献立データ返却
    UI-->>User: 結果表示<br/>・献立カード<br/>・詳細レシピ<br/>・買い物リスト
```

## システムアーキテクチャ

```mermaid
classDiagram
    class FlaviaPromptAssistant {
        +generate(request, days)
        +generate_recipe() [互換用]
        +generate_weekly_plan() [互換用]
        -_create_prompt(request, context, days)
        -_call_claude_api(prompt)
        -_parse_json_response(response)
        -_format_output(data, request, days)
    }
    
    class PersonalDataManager {
        +create_context_for_ai()
        +get_pantry_items()
        +load_preferences()
        +load_constraints()
    }
    
    class StreamlitUI {
        +handle_user_input()
        +display_results()
        +handle_discord_integration()
    }
    
    FlaviaPromptAssistant --> PersonalDataManager : uses
    StreamlitUI --> FlaviaPromptAssistant : uses
    
    note for FlaviaPromptAssistant "精巧なプロンプトエンジニアリング\nによる料理アシスタント"
    note for PersonalDataManager "個人化のための\nデータ管理"
    note for StreamlitUI "シンプルなWebUI"
```

## 実際の処理内容

1. **入力受付**: 「牛肉とトマトを使った料理が食べたい」+ 日数選択
2. **個人情報結合**: ユーザーの嗜好・制約・常備品情報を読み込み
3. **プロンプト構築**: 精巧な指示文を作成（詳細レシピ・買い物リスト形式等）
4. **Claude API呼び出し**: 構築したプロンプトをClaude AIに送信
5. **結果解析**: JSON形式の応答を解析・整形
6. **UI表示**: 献立・レシピ・買い物リストを表示

**本質**: AIエージェントではなく、**個人化されたプロンプトエンジニアリングシステム**