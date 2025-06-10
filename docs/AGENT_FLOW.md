# 🔄 Flavia Agent プロセスフロー

## 現在のFlaviaAgentの処理フロー

```mermaid
graph TD
    %% メインフロー
    Start([ユーザーリクエスト]) --> RecipeGen{レシピ生成?}
    RecipeGen -->|Yes| SingleRecipe[単発レシピ生成]
    RecipeGen -->|No| WeeklyPlan[週間献立生成]
    
    %% 単発レシピ生成フロー
    SingleRecipe --> LoadContext1[個人データ読み込み]
    LoadContext1 --> CreatePrompt1[レシピプロンプト生成]
    CreatePrompt1 --> CallAI1[Claude API呼び出し]
    CallAI1 --> ParseJSON1[JSON解析]
    ParseJSON1 --> ReturnRecipe[レシピ返却]
    
    %% 週間献立生成フロー
    WeeklyPlan --> LoadContext2[個人データ読み込み]
    LoadContext2 --> CreatePrompt2[週間献立プロンプト生成]
    CreatePrompt2 --> CallAI2[Claude API呼び出し]
    CallAI2 --> ParseJSON2[JSON解析]
    ParseJSON2 --> GenShoppingList[買い物リスト生成]
    GenShoppingList --> GroupIngredients[食材グループ化]
    GroupIngredients --> ReturnPlan[献立返却]
    
    %% 買い物リスト処理
    GenShoppingList --> CheckPantry{常備品チェック}
    CheckPantry -->|常備品| ExcludePantry[常備品除外]
    CheckPantry -->|購入品| AddToList[リスト追加]
    ExcludePantry --> GroupIngredients
    AddToList --> GroupIngredients
    
    %% エラーハンドリング
    CallAI1 --> Error1{エラー?}
    CallAI2 --> Error2{エラー?}
    Error1 -->|Yes| HandleError1[エラー処理]
    Error2 -->|Yes| HandleError2[エラー処理]
    HandleError1 --> ReturnError1[エラー返却]
    HandleError2 --> ReturnError2[エラー返却]
    
    %% スタイル定義
    classDef process fill:#f9f,stroke:#333,stroke-width:2px;
    classDef decision fill:#bbf,stroke:#333,stroke-width:2px;
    classDef start fill:#9f9,stroke:#333,stroke-width:2px;
    classDef error fill:#f99,stroke:#333,stroke-width:2px;
    
    class Start start;
    class RecipeGen,CheckPantry,Error1,Error2 decision;
    class SingleRecipe,WeeklyPlan,LoadContext1,LoadContext2,CreatePrompt1,CreatePrompt2,CallAI1,CallAI2,ParseJSON1,ParseJSON2,GenShoppingList,GroupIngredients process;
    class HandleError1,HandleError2,ReturnError1,ReturnError2 error;
```

## データフロー詳細

```mermaid
sequenceDiagram
    participant User as ユーザー
    participant UI as UI層
    participant Agent as FlaviaAgent
    participant Data as DataManager
    participant AI as Claude API
    
    %% レシピ生成リクエスト
    User->>UI: レシピリクエスト
    UI->>Agent: generate_recipe()
    
    %% コンテキスト生成
    Agent->>Data: create_context_for_ai()
    Data-->>Agent: 個人データ
    
    %% プロンプト生成とAI呼び出し
    Agent->>Agent: _create_recipe_prompt()
    Agent->>AI: _call_claude_api()
    AI-->>Agent: JSONレスポンス
    
    %% レスポンス処理
    Agent->>Agent: _parse_json_response()
    Agent-->>UI: レシピデータ
    UI-->>User: 結果表示
    
    %% 週間献立の場合
    User->>UI: 週間献立リクエスト
    UI->>Agent: generate_weekly_plan()
    
    %% 買い物リスト生成
    Agent->>Agent: _generate_shopping_list()
    Agent->>Agent: _group_same_ingredients()
    Agent-->>UI: 献立と買い物リスト
    UI-->>User: 結果表示
```

## コンポーネント間の関係

```mermaid
classDiagram
    class FlaviaAgent {
        +generate_recipe()
        +generate_weekly_plan()
        -_create_recipe_prompt()
        -_create_weekly_prompt()
        -_call_claude_api()
        -_parse_json_response()
        -_generate_shopping_list()
        -_group_same_ingredients()
    }
    
    class PersonalDataManager {
        +create_context_for_ai()
        +get_pantry_items()
        +update_preferences()
    }
    
    class StreamlitUI {
        +handle_user_input()
        +display_recipe()
        +display_weekly_plan()
    }
    
    FlaviaAgent --> PersonalDataManager : uses
    StreamlitUI --> FlaviaAgent : uses
```

## エラーハンドリングフロー

```mermaid
graph TD
    %% エラーハンドリングの流れ
    Start([処理開始]) --> TryBlock{try}
    TryBlock --> Process[メイン処理]
    Process --> Success{成功?}
    
    %% 成功パス
    Success -->|Yes| ReturnSuccess[成功レスポンス]
    
    %% エラーパス
    Success -->|No| CatchBlock{catch}
    CatchBlock --> ErrorType{エラー種別}
    
    %% エラー種別による分岐
    ErrorType -->|API Error| APIError[APIエラー処理]
    ErrorType -->|JSON Error| JSONError[JSON解析エラー]
    ErrorType -->|Validation Error| ValidationError[バリデーションエラー]
    ErrorType -->|Other Error| OtherError[その他エラー]
    
    %% エラー処理後の流れ
    APIError --> ErrorResponse[エラーレスポンス]
    JSONError --> ErrorResponse
    ValidationError --> ErrorResponse
    OtherError --> ErrorResponse
    
    %% スタイル定義
    classDef process fill:#f9f,stroke:#333,stroke-width:2px;
    classDef decision fill:#bbf,stroke:#333,stroke-width:2px;
    classDef error fill:#f99,stroke:#333,stroke-width:2px;
    
    class Start process;
    class TryBlock,CatchBlock,Success,ErrorType decision;
    class APIError,JSONError,ValidationError,OtherError error;
```

## 補足説明

1. **メインフロー**
   - ユーザーリクエストに基づいて単発レシピ生成か週間献立生成かを判断
   - それぞれの処理フローで個人データの読み込みとAI API呼び出しを実行
   - 週間献立の場合は買い物リスト生成も含む

2. **データフロー**
   - UI層、Agent層、Data層、AI層の4層で構成
   - 各層間のデータの受け渡しを明確化
   - 非同期処理（async/await）の流れを表現

3. **コンポーネント関係**
   - FlaviaAgentを中心とした依存関係
   - 各クラスの主要メソッドを表示
   - コンポーネント間の関連を明確化

4. **エラーハンドリング**
   - try-catchによるエラー処理の流れ
   - エラー種別による分岐処理
   - エラーレスポンスの生成までを表現 
