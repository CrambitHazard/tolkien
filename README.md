# Tolkien

An AI-powered interactive storytelling agent that generates three distinct chapter continuations, allowing users to choose canonical paths while expanding unchosen options into tragic alternate timelines. Designed for integration with Obsidian vaults for rich story visualization and graph-based exploration.

## 🎯 Overview

This system maintains story continuity through structured metadata summaries, enabling long-form narrative generation without losing track of characters, relationships, and plot threads. The chosen canonical path continues the main story, while rejected options are expanded into complete tragic endings that can be referenced as dreams, visions, or alternate possibilities in future chapters.

## ✨ Features

- **Three-Option Generation**: Creates distinct narrative paths with unique conflicts and outcomes
- **Metadata-Driven Continuity**: Preserves story consistency through structured chapter summaries
- **Tragic Timeline Expansion**: Transforms unchosen options into complete alternate endings
- **Obsidian Integration**: YAML frontmatter, tags, and wikilinks for graph visualization
- **Dual Interface**: Both CLI and web UI for different workflows
- **Export Capabilities**: Generate canonical storyline or full branching narrative
- **Offline Fallback**: Continues working with stub content when LLM is unavailable

## 📁 Project Structure

```
tolkien/
├── chapters/                    # Story content (Obsidian vault compatible)
│   ├── canonical/              # Main storyline chapters (0001.md, 0002.md, ...)
│   ├── choices/                # Generated options before selection
│   │   └── 0001/              # Chapter index folders
│   │       ├── A.md           # Option drafts
│   │       ├── B.md
│   │       └── C.md
│   └── pruned/                 # Tragic alternate timelines
│       └── 0001/              # Chapter index folders
│           ├── A.md           # Expanded tragic endings
│           └── B.md
├── .agent/
│   └── metadata/              # JSON metadata mirrors for context
├── app.py                     # Flask web interface
├── cli.py                     # Command-line interface
├── generator.py               # Three-option generation logic
├── finalizer.py               # Canonical selection and tragic expansion
├── summarizer.py              # Metadata extraction from chapters
├── fs_io.py                   # File system operations
├── llm_client.py              # OpenRouter API client
└── tests/                     # Test suite
```

## 🚀 Quick Start

### Prerequisites

- Python 3.10+
- OpenRouter API key (optional - system works offline with stubs)

### Installation

1. **Clone and setup**:
   ```bash
   git clone <repository-url>
   cd tolkien
   pip install -r requirements.txt
   ```

2. **Configure environment** (optional):
   ```bash
   cp .env.example .env
   # Edit .env with your API key
   ```

3. **Initialize directories**:
   ```bash
   python cli.py generate --n 0
   ```

### Basic Usage

#### CLI Workflow

1. **Generate three chapter options**:
   ```bash
   python cli.py generate --n 5
   ```

2. **Choose canonical option**:
   ```bash
   python cli.py choose --option A --n 5
   ```

3. **View story history**:
   ```bash
   python cli.py history
   ```

4. **Export storyline**:
   ```bash
   python cli.py export --mode canonical
   ```

#### Web Interface

1. **Start the Flask app**:
   ```bash
   python app.py
   ```

2. **Open browser**: Navigate to `http://localhost:5000`

3. **Generate and select**: Use the web form to create options and make choices

## 🔧 Configuration

### Environment Variables

Create a `.env` file with:

```env
# OpenRouter API (optional)
OPENROUTER_API_KEY=your_api_key_here
OPENROUTER_BASE_URL=https://openrouter.ai/api/v1
MODEL=deepseek/deepseek-chat-v3.1:free

# Directory customization (optional)
CHAPTERS_ROOT=chapters
METADATA_ROOT=.agent/metadata
```

### Model Configuration

The system uses `deepseek/deepseek-chat-v3.1:free` by default but supports any OpenRouter-compatible model. Adjust the `MODEL` environment variable or modify `llm_client.py` for different providers.

## 📖 How It Works

### Generation Process

1. **Context Loading**: Reads metadata from the last N canonical chapters and pruned branches
2. **Prompt Construction**: Builds generation prompts with continuity facts and thematic hints
3. **Three-Option Creation**: LLM generates distinct narrative paths (A, B, C)
4. **File Storage**: Saves options as Markdown with YAML frontmatter

### Selection and Finalization

1. **User Choice**: Select option A, B, or C via CLI or web interface
2. **Canonical Storage**: Chosen option becomes the next canonical chapter
3. **Tragic Expansion**: Unchosen options are expanded into complete tragic endings
4. **Metadata Generation**: All chapters get structured summaries for future context

### Metadata Schema

Each chapter generates structured metadata:

```json
{
  "agent_id": "unique_identifier",
  "title": "Chapter Title",
  "synopsis": "Brief chapter summary",
  "characters": ["Character names mentioned"],
  "relationships": ["Key relationship changes"],
  "main_plot_points": ["Major events and decisions"],
  "alternate_possibilities": ["Potential future directions"],
  "possible_plotholes": ["Continuity concerns to address"],
  "themes": ["Thematic elements"],
  "timeline_events": ["Chronological markers"],
  "tags": ["categorical labels"]
}
```

## 🎮 Advanced Usage

### Context Management

- **--n parameter**: Controls how many recent chapters provide context
- **Canonical vs Pruned**: System distinguishes between main timeline and alternate branches
- **Metadata-Only Context**: Uses summaries rather than full text to manage token limits

### Obsidian Integration

- **Graph View**: Visualize story branches and connections
- **Wikilinks**: Automatic linking between chapters and characters
- **Tags**: `#canonical`, `#tragic`, `#choice` for filtering
- **Frontmatter**: Rich metadata in YAML format

### Export Options

```bash
# Canonical storyline only
python cli.py export --mode canonical

# Full branching narrative (future feature)
python cli.py export --mode all
```

## 🧪 Testing

Run the test suite:

```bash
python -m pytest tests/ -v
```

Test coverage focuses on:
- File system operations (`test_fs_io.py`)
- Metadata generation and parsing
- CLI command validation
- Offline fallback behavior

## 🔍 Troubleshooting

### Common Issues

**No API Key**: System works offline with stub content. Set `OPENROUTER_API_KEY` for full functionality.

**Missing Directories**: Run any CLI command to auto-create required folder structure.

**Parsing Errors**: LLM output parsing is robust with fallbacks, but check `generator.py` if options aren't properly separated.

**Continuity Breaks**: Increase `--n` parameter to provide more context, or manually edit metadata files.

### Offline Mode

Without an API key, the system generates placeholder content:
- Stub chapter drafts with consistent structure
- Basic metadata extraction using heuristics
- Full file system operations and organization

## 🛠 Development

### Architecture

- **Modular Design**: Each component handles a specific responsibility
- **Metadata-Driven**: Continuity managed through structured summaries
- **LLM-Agnostic**: Easy to swap different AI providers
- **File-Based Storage**: No database dependencies, Obsidian-compatible

### Key Components

- `generator.py`: Handles three-option creation with distinct narrative beats
- `finalizer.py`: Manages canonical selection and tragic expansion
- `summarizer.py`: Extracts structured metadata from chapter text
- `fs_io.py`: File system operations with proper directory management
- `llm_client.py`: OpenRouter API integration with fallback handling

### Extending the System

- **New LLM Providers**: Modify `llm_client.py` or create new client classes
- **Additional Metadata**: Extend schema in `summarizer.py`
- **Export Formats**: Add new modes in CLI export command
- **UI Enhancements**: Expand Flask templates in `app.py`

## 📄 License

This project follows standard open-source practices. See individual file headers for specific licensing information.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Ensure all tests pass
5. Submit a pull request

---

**Note**: This system is designed for creative writing and storytelling. The AI-generated content should be reviewed and edited as part of your creative process.
