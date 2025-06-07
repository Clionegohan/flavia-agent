# 🍽️ Flavia Personal Agent - 個人専用AI献立エージェント仕様書

## プロジェクト概要

### 目的
**あなた専用の食事パートナー** - 個人の食の嗜好、健康状態、生活パターンを深く理解し、継続的に学習しながら最適な献立を提案するパーソナライズドAIエージェント

### ビジョン
「一人ひとりに寄り添い、共に成長する食事のベストパートナー」

### 新コンセプト
- **Single User Focus**: マルチユーザー対応より、1人への深い理解を重視
- **RAG-based Personalization**: テキストファイルベースの嗜好管理
- **Continuous Learning**: 日々の反応から学習し、関係性を深化
- **Intimate Assistant**: システムではなく、パートナーとしての体験

## 核心機能要件

### 1. 個人データ管理 (RAG Foundation)

#### 1.1 個人嗜好データベース
**保存場所**: `data/personal/` (テキストファイル群)

**構成ファイル**:
```
data/personal/
├── profile.txt           # 基本プロフィール
├── preferences.txt       # 食の好み・苦手
├── health_goals.txt      # 健康目標・制約
├── cooking_skills.txt    # 料理スキル・設備
├── seasonal_notes.txt    # 季節ごとの傾向
├── meal_history.txt      # 食事履歴・評価
├── learning_log.txt      # エージェントの学習記録
└── context_memory.txt    # 対話コンテキスト記憶
```

#### 1.2 動的嗜好学習
- 献立への評価・感想の収集
- 選択パターンの分析
- 嗜好ファイルの自動更新提案
- 季節・体調変化への対応

### 2. RAG統合エージェント

#### 2.1 コンテキスト構築
- 個人データファイルからの関連情報抽出
- 現在の状況（季節、体調、気分）考慮
- 過去の献立履歴との照合
- 個人化されたプロンプト生成

#### 2.2 パーソナライズド献立生成
- 個人の嗜好を深く反映した提案
- 健康目標との整合性チェック
- 調理スキル・時間に応じた難易度調整
- 「今日の気分」に対応した柔軟な提案

### 3. 学習・進化システム

#### 3.1 フィードバック学習
- 献立への5段階評価
- 「美味しかった」「時間かかりすぎ」等の自由コメント
- 食材の好き嫌い変化の検出
- 調理スキル向上の認識

#### 3.2 パターン認識
- 季節による嗜好変化
- 体調・ストレス状態での食事傾向
- 成功レシピの共通要素分析
- 避けるべき組み合わせの学習

### 4. 対話型インターフェース

#### 4.1 チャット的な相談機能
```
「今日は疲れてるから、簡単で栄養のあるもの作りたいな」
→ Flavia: "お疲れ様！いつもの豚肉の生姜焼きはどう？ 
         野菜も一緒に炒めれば15分で完成よ 🍳"
```

#### 4.2 継続的関係性
- 過去の会話の記憶
- 成長・変化への気づき
- 祝日・記念日の特別提案
- 体調不良時の気遣い

## 技術アーキテクチャ

### 新ディレクトリ構造
```
src/flavia_agent/
├── agent/
│   ├── flavia.py              # メインエージェント
│   └── personality.py         # 個人化・対話ロジック
├── rag/                       # NEW: RAG機能
│   ├── __init__.py
│   ├── file_reader.py         # 個人データファイル読取
│   ├── context_builder.py     # コンテキスト構築
│   ├── preference_parser.py   # 嗜好データ解析
│   └── learning_updater.py    # 学習・ファイル更新
├── data/
│   ├── models/                # Pydanticモデル
│   ├── personal/              # NEW: 個人データ
│   │   ├── profile.txt
│   │   ├── preferences.txt
│   │   ├── health_goals.txt
│   │   ├── cooking_skills.txt
│   │   ├── seasonal_notes.txt
│   │   ├── meal_history.txt
│   │   ├── learning_log.txt
│   │   └── context_memory.txt
│   └── storage/               # NEW: セッション・履歴
│       ├── meal_sessions/     # 献立セッション記録
│       ├── evaluations/       # 評価データ
│       └── analytics/         # 分析結果
├── ui/
│   ├── streamlit_app.py       # 現在のUI
│   └── chat_interface.py      # NEW: チャット型UI
└── utils/
    ├── logging.py
    └── file_utils.py          # NEW: ファイル操作
```

### RAG データフロー
```
1. ユーザー入力「今日は何作ろうかな？」
   ↓
2. RAG Context Builder
   - profile.txt: 基本情報読取
   - preferences.txt: 好み分析
   - meal_history.txt: 最近の傾向
   - seasonal_notes.txt: 季節考慮
   ↓
3. Personalized Prompt Generation
   「30代、中辛好み、最近鍋料理続き、
    今日は軽めが良さそう、15分以内希望」
   ↓
4. AI Agent (OpenAI/Anthropic)
   個人化されたコンテキスト付きで献立生成
   ↓
5. Learning System
   - 提案への反応記録
   - 嗜好ファイル更新提案
   - パターン学習
```

## フェーズ別実装計画

### Phase 1: RAG Foundation (2-3週間)
**目標**: 個人データの読み書きとAI統合

1. **個人データファイル管理**
   - テキストファイルテンプレート作成
   - 読み書き機能実装
   - データ構造の定義

2. **RAG統合基盤**
   - ファイル読取エンジン
   - コンテキスト構築ロジック
   - プロンプト個人化機能

3. **基本学習機能**
   - 献立評価の記録
   - 簡単な嗜好更新

### Phase 2: Personal Intelligence (3-4週間)
**目標**: 賢い個人化エージェント

4. **高度な学習システム**
   - パターン認識・分析
   - 自動嗜好更新提案
   - 季節・体調考慮

5. **対話的エージェント**
   - チャット型インターフェース
   - 継続的会話記憶
   - 気分・状況への対応

### Phase 3: Advanced Partnership (将来)
**目標**: 真のパートナー体験

6. **予測・提案機能**
   - 体調・気分の察知
   - プロアクティブな提案
   - 健康状態との連携

7. **深化した関係性**
   - 長期的な成長追跡
   - 人生イベントへの対応
   - 感情的なサポート

## データモデル設計

### 個人プロフィール
```python
@dataclass
class PersonalProfile:
    name: str
    age_range: str
    activity_level: str
    allergies: List[str]
    health_conditions: List[str]
    created_at: datetime
    last_updated: datetime
```

### 嗜好データ
```python
@dataclass
class FoodPreferences:
    loved_foods: List[str]
    disliked_foods: List[str]
    preferred_cuisines: List[str]
    spice_tolerance: str
    texture_preferences: Dict[str, str]
    confidence_scores: Dict[str, float]  # 学習による確信度
```

### 学習記録
```python
@dataclass
class LearningEntry:
    timestamp: datetime
    meal_id: str
    user_feedback: str
    rating: int
    detected_patterns: List[str]
    preference_updates: Dict[str, Any]
```

## 成功指標 (Personal KPI)

### エージェント品質
- **的中率**: 提案献立の満足度 90%以上
- **学習効果**: 月次での嗜好理解向上
- **継続使用**: 週3回以上の相談頻度

### パーソナライゼーション
- **個人化度**: 汎用提案との差異
- **記憶精度**: 過去の会話・選択の記憶
- **成長認識**: スキル・嗜好変化への適応

### ユーザー体験
- **親密感**:「パートナー」としての信頼度
- **利便性**: 相談から献立決定までの時間短縮
- **楽しさ**: 食事・料理への意欲向上

## セキュリティ・プライバシー

### データ保護
- **ローカル保存**: 個人データは全てローカル
- **暗号化**: 機密性の高い健康情報
- **アクセス制御**: ファイルレベルでの保護

### 学習制限
- **明示的同意**: 嗜好更新は提案→承認制
- **データ主権**: いつでも削除・修正可能
- **透明性**: 学習内容の可視化

---

**バージョン**: 2.0 (Personal Agent Edition)
**最終更新**: 2024年12月  
**承認者**: Flavia Personal Agent開発チーム