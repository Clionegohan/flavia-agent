# 🍽️ Flavia - AI Meal Planning Agent
*献立×レシピ×買い物エージェント*

Flavia is an intelligent meal planning assistant that suggests personalized recipes based on your budget, dietary preferences, and cooking constraints.

## Features

- 🤖 AI-powered recipe suggestions using OpenAI or Anthropic
- 💰 Budget-conscious meal planning
- 🥗 Dietary restriction support
- 🌍 Multi-cuisine preferences
- ⏱️ Cooking time constraints
- 🖥️ Beautiful Streamlit web interface

## Quick Start

1. **Clone and setup:**
   ```bash
   git clone https://github.com/Clionegohan/flavia-agent.git
   cd flavia-agent
   source .venv/bin/activate
   ```

2. **Configure API keys:**
   ```bash
   cp .env.example .env
   # Edit .env with your API keys
   ```

3. **Run the app:**
   ```bash
   # Option 1: Using script
   ./scripts/run_app.sh
   
   # Option 2: Direct command
   streamlit run src/flavia_agent/ui/streamlit_app.py
   ```

## Project Structure

```
flavia-agent/
├── src/
│   └── flavia_agent/
│       ├── agent/      # AI agent logic
│       ├── data/       # Data models and storage
│       │   ├── models/ # Pydantic models
│       │   └── schemas/# Database schemas (future)
│       └── ui/         # Streamlit interface
├── tests/              # Test files
├── scripts/            # Utility scripts
├── docs/               # Project documentation
├── .env.example        # Environment template
└── pyproject.toml      # Project configuration
```

## Development

```bash
# Install dev dependencies
uv sync --extra dev

# Run tests
pytest

# Format code
black .
ruff check .
```

## Requirements

- Python 3.12+
- OpenAI API key or Anthropic API key
- Optional: AWS credentials for enhanced features
