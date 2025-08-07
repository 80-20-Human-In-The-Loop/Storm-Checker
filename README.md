[WARNING] This isn't deployed or ready for contributions yet. I am very excited for this project, but my priorities are elsewhere for now.

<img width="519" height="506" alt="image" src="https://github.com/user-attachments/assets/4077b7be-49da-4ce2-b60f-3e3465ca79cf" />

> Smart Python type checking that teaches while it helps

**Part of the [80-20 Human in The Loop](https://github.com/80-20-Human-In-The-Loop) ecosystem**

[![PyPI version](https://img.shields.io/pypi/v/storm-checker?label=pip%20install%20storm-checker&color=brightgreen)](https://pypi.org/project/storm-checker/)
[![Python 3.8+](https://img.shields.io/badge/Python-3.8%2B-blue?logo=python&logoColor=white)](https://pypi.org/project/storm-checker/)
[![80-20 Philosophy](https://img.shields.io/badge/Philosophy-80%25%20AI%20%2B%2020%25%20Human-purple)](https://github.com/80-20-Human-In-The-Loop)
[![Teaches While You Code](https://img.shields.io/badge/Learning-Built%20In-orange)](https://github.com/80-20-Human-In-The-Loop/storm-checker)
[![AI Agent Ready](https://img.shields.io/badge/AI%20Agents-JSON%20%2B%20MCP-red)](https://github.com/80-20-Human-In-The-Loop/storm-checker)
[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](https://github.com/80-20-Human-In-The-Loop/storm-checker/blob/main/LICENSE)

## What This Does

Storm Checker helps you fix Python type errors and learn type safety. It works with MyPy to find problems in your code and shows you how to fix them.

**The result**: Code that works better and developers who understand types better.

## 🤝 The 80-20 Human in The Loop Philosophy

We believe the best tools help humans grow while automating tedious work.

**How it works**:
- **80% Automation**: AI handles routine type fixes and pattern recognition
- **20% Human Wisdom**: You make important decisions about code architecture
- **100% Learning**: Everyone improves their understanding of type safety

**Three ways to use Storm Checker**:
1. **Learning Mode** (`--edu`): Teaches you while you work
2. **Professional Mode**: Fast, clean results for experienced developers  
3. **AI Mode** (`--json`): Structured output for AI agents and automation

## ⚡ Quick Start

### Install Storm Checker

```bash
pip install storm-checker
```

### Try it now

```bash
# For beginners - learn while you fix
stormcheck mypy --edu

# For professionals - fast results  
stormcheck mypy

# For AI agents - structured data
stormcheck mypy --json

# Try the interactive tutorial system
stormcheck tutorial hello_world
```

That's it! Storm Checker will analyze your Python files and help you improve them.

## 🎓 For Students and Beginners

**New to Python types?** Storm Checker teaches you step by step.

### Educational Features

- **Learn by Doing**: Fix real errors in your code
- **Clear Explanations**: Understand why each fix matters
- **Achievement System**: Celebrate your progress
- **Safe Practice**: Work on real projects without fear

### Your First Type Error Fix

```bash
# Start learning mode
stormcheck mypy --edu

# Storm Checker will:
# 1. Find type errors in your code
# 2. Explain what each error means
# 3. Show you how to fix it
# 4. Teach you why it matters
```

### Example Learning Session

```python
# Your code:
def calculate_grade(score):
    return score * 100

# Storm Checker teaches:
"This function needs type hints. Here's why types help:
1. Other developers understand your code better
2. Your editor can help you write code faster
3. You catch mistakes before users see them

Try this fix:
def calculate_grade(score: float) -> float:
    return score * 100"
```

### Track Your Progress

```bash
# See how much you've learned
stormcheck mypy --dashboard
```

![Student Progress Dashboard](screenshots/student-dashboard.png)
*See your learning journey with achievements, progress tracking, and next steps*

### Built-in Interactive Tutorials

```bash
# List all available tutorials
stormcheck tutorial --list

# Start with the intro tutorial
stormcheck tutorial hello_world

# Get MyPy-specific tutorials
stormcheck mypy tutorial --list
```

![Interactive Tutorial System](screenshots/tutorial-session.png)
*Learn type safety step-by-step with interactive tutorials and real-time feedback*

## 💼 For Professional Developers

**Need efficient type checking?** Storm Checker respects your time and expertise.

### Professional Features

- **Fast Analysis**: Check large codebases quickly
- **Business Impact**: See which errors affect users most
- **Framework Smart**: Understands Django, FastAPI, Flask patterns
- **CI Integration**: Works with your existing tools

### Efficient Workflows

```bash
# Check your entire project
stormcheck mypy

# Focus on important files
stormcheck mypy -k "models|views"

# Get one focused task (great for AI agents)
stormcheck mypy --random

# Get tutorial recommendations for current errors
stormcheck mypy --tutorial

# See progress over time
stormcheck mypy --dashboard
```

### Example Professional Output

![Professional Analysis Dashboard](screenshots/professional-dashboard.png)
*Clean, actionable results focused on what matters most*

## 🤖 For AI Agents and Automation

**Building automated workflows?** Storm Checker provides structured data for AI systems.

### AI-Friendly Features

- **JSON Output**: Machine-readable results
- **Random Issue Selection**: Get focused tasks
- **Confidence Scores**: Know which fixes are safe to automate
- **MCP Integration**: Works with Claude and other AI systems

### Automation Examples

```bash
# Get structured data
stormcheck mypy --json

# Get one focused issue to fix
stormcheck mypy --random --json
```

![AI Agent JSON Output](screenshots/ai-json-output.png)
*Structured JSON output perfect for AI agents and automation workflows*

### MCP Integration (Coming Soon)

```bash
# Install MCP server
pip install stormcheck-mcp

# Use with Claude or other AI systems
# Full documentation: github.com/80-20-Human-In-The-Loop/stormcheck-mcp
```

## 🚀 Installation and Setup

### Requirements

- Python 3.8 or newer
- MyPy (installed automatically)

### Install Options

```bash
# Standard installation
pip install storm-checker

# With extra features
pip install storm-checker[dev]

# Development version
pip install git+https://github.com/80-20-Human-In-The-Loop/storm-checker.git
```

### Verify Installation

```bash
# Check it works
stormcheck mypy --version

# Test on sample file
echo "def hello(name): return f'Hi {name}'" > test.py
stormcheck mypy test.py --edu
```

![First Run Experience](screenshots/first-run.png)
*Your first Storm Checker analysis - clear, educational, and encouraging*

## 📖 Common Usage Examples

### Daily Development

```bash
# Check your current work
stormcheck mypy

# Focus on specific files
stormcheck mypy -k "billing|payment"

# Get a focused task to work on
stormcheck mypy --random
```

### Learning Sessions

```bash
# Start with educational mode
stormcheck mypy --edu

# Get tutorial recommendations for your errors  
stormcheck mypy --tutorial

# Try the interactive tutorial system
stormcheck tutorial hello_world

# Track your progress
stormcheck mypy --dashboard
```

![Progress Dashboard](screenshots/student-dashboard.png)
*Track your learning journey with progress visualization*

### Working with JSON Output

```bash
# Get structured output for scripts/AI
stormcheck mypy --json

# Combine with other flags
stormcheck mypy --random --json
```

## ⚙️ Configuration

Storm Checker works with your existing MyPy configuration. Set up your `pyproject.toml`:

### Basic Setup

```toml
[build-system]
requires = ["hatchling>=1.13.0"]
build-backend = "hatchling.build"

[project]
name = "your-project"
requires-python = ">=3.8"

# Storm Checker works with your existing MyPy setup
[tool.mypy]
python_version = "3.10"
warn_return_any = true
warn_unused_configs = true
show_error_codes = true
pretty = false

# Common MyPy settings that work well with Storm Checker
strict = true
disallow_untyped_defs = true
disallow_incomplete_defs = true
check_untyped_defs = true
warn_redundant_casts = true
warn_unused_ignores = true
```

### For Existing Projects

If you already have MyPy configured, Storm Checker will use your existing settings. No additional configuration needed!

### Advanced MyPy Options

```toml
[tool.mypy]
# Useful for learning (shows more context)
show_error_context = true
show_column_numbers = true

# Great for educational mode
pretty = true
color_output = true

# Exclude directories Storm Checker should ignore
exclude = [
    "venv/",
    "build/",
    "tests/fixtures/"
]
```

## 🌟 Key Features

### Educational Features
- **Interactive Learning**: Fix errors while learning concepts
- **Achievement System**: Celebrate progress milestones
- **Progress Tracking**: See improvement over time
- **Gentle Guidance**: Explanations that don't overwhelm

### Professional Features
- **Business Impact Analysis**: Focus on errors that matter most
- **Framework Intelligence**: Understands Django, FastAPI, Flask patterns
- **Team Analytics**: Track progress across your development team
- **CI/CD Integration**: Works with existing development workflows

### AI Integration Features
- **Structured Output**: JSON format for automated processing
- **Confidence Scoring**: Know which fixes are safe to automate
- **Random Issue Selection**: Get focused tasks for AI agents
- **MCP Protocol Support**: Integration with Claude and other AI systems

## 🔧 Advanced Usage

### Pattern Matching with Keywords

```bash
# Find files with specific patterns
stormcheck mypy -k "model"

# Multiple patterns (OR logic)
stormcheck mypy -k "model|view|controller"

# Focus on business logic
stormcheck mypy -k "billing|payment|order"
```

### Combining Flags

```bash
# Educational mode with specific files
stormcheck mypy --edu -k "models"

# JSON output for specific pattern
stormcheck mypy --json -k "api"

# Get random issue from filtered files
stormcheck mypy --random -k "views"
```

### Different Output Modes

```bash
# Default: Human-friendly output
stormcheck mypy

# Educational: Learning guidance included
stormcheck mypy --edu

# JSON: Perfect for AI agents and scripts
stormcheck mypy --json

# Progress: See your improvement over time
stormcheck mypy --dashboard
```

## 🌍 Part of a Bigger Vision

Storm Checker is the first tool in the **80-20 Human in The Loop** ecosystem. We're building tools that:

- **Respect Human Intelligence**: Automate the routine, elevate the important
- **Promote Learning**: Every interaction should teach something valuable
- **Enable AI Collaboration**: Humans and AI working together effectively
- **Stay Accessible**: Complex tools that remain simple to use

### Upcoming Tools in the Ecosystem

- **stormcheck-mcp**: AI agent integration for seamless automation
- **More coming soon**: Tools that follow the same human-centered philosophy

### Join Our Community

- **GitHub Organization**: [80-20-Human-In-The-Loop](https://github.com/80-20-Human-In-The-Loop)
- **Philosophy**: Tools that make humans smarter, not replace them
- **First Adopter**: [EduLite Education Platform](https://github.com/ibrahim-sisar/EduLite)

## 🤝 Contributing

We welcome everyone! Whether you're:
- A student learning Python
- A professional developer
- An AI researcher
- Someone who just wants to help

### Quick Contributing Guide

1. **Get the code**: `git clone https://github.com/80-20-Human-In-The-Loop/storm-checker.git`
2. **Set up environment**: `pip install -e .[dev]`
3. **Make changes**: Follow our [Contributing Guide](CONTRIBUTING.md)
4. **Test changes**: `pytest`
5. **Submit**: Create a pull request

### Ways to Help

- **Fix bugs**: Check our [issues](https://github.com/80-20-Human-In-The-Loop/storm-checker/issues)
- **Add features**: Suggest improvements
- **Improve documentation**: Make it clearer for everyone
- **Share feedback**: Tell us how Storm Checker helps you

## 🛡️ Privacy and Ethics

We respect your privacy and believe in ethical AI:

- **No code upload**: Your code stays on your computer
- **Optional telemetry**: Anonymous usage stats to improve the tool (opt-in only)
- **Transparent AI**: Clear explanation of how AI suggestions are generated
- **Human control**: You always make the final decisions

## 📊 Project Structure

```
storm-checker/
├── cli/                    # Command-line interface
│   ├── colors.py          # Beautiful terminal output
│   └── components/        # Progress bars, borders, formatting
├── logic/                 # Core functionality
│   ├── mypy_runner.py     # MyPy integration
│   ├── mypy_error_analyzer.py # Error analysis and categorization
│   └── progress_tracker.py # Learning progress tracking
├── models/                # Data structures
│   └── progress_models.py # Achievement and progress models
├── scripts/               # Entry points
│   ├── stormcheck.py      # Main CLI entry
│   ├── check_mypy.py      # MyPy command handler
│   └── tutorial.py        # Interactive tutorial system
└── tutorials/             # Built-in learning content
    ├── hello_world.py     # Introduction tutorial
    └── type_annotations_basics.py # Core concepts
```

## ❓ Common Questions

### "How is this different from MyPy?"

MyPy finds type errors. Storm Checker helps you understand and fix them while learning type safety concepts.

### "Is this good for beginners?"

Yes! Use `--edu` mode for explanations and guidance. The tool adapts to your skill level.

### "Can AI agents use this?"

Absolutely! Use `--json` flag for structured output. MCP integration coming soon.

### "Does it work with my framework?"

Storm Checker understands Django, FastAPI, and Flask patterns. It also works with any Python project.

### "Is my code sent anywhere?"

No. Storm Checker runs entirely on your computer. Your code never leaves your machine.

## 🚀 Getting Help

### Documentation
- **Installation Issues**: Check our [Installation Guide](docs/installation.md)
- **Usage Examples**: See our [Usage Guide](docs/usage.md)
- **Configuration**: Read our [Configuration Guide](docs/configuration.md)

### Community Support
- **GitHub Issues**: [Report bugs or request features](https://github.com/80-20-Human-In-The-Loop/storm-checker/issues)
- **Discussions**: [Ask questions and share ideas](https://github.com/80-20-Human-In-The-Loop/storm-checker/discussions)

### Quick Troubleshooting

```bash
# Check if Storm Checker is working
stormcheck mypy --help

# Update to latest version
pip install --upgrade storm-checker

# Test on a simple file
echo "def hello(name): return f'Hi {name}'" > test.py
stormcheck mypy test.py --edu
```

## 📄 License

GPL v3 License - see [LICENSE](LICENSE) file for details.

**What this means**: You can use Storm Checker freely, modify it, and distribute it. If you distribute modified versions, you must share your improvements under the same license. This keeps the educational benefits available to everyone.

## 🙏 Acknowledgments

- **MyPy Team**: For the excellent type checker that powers our analysis
- **EduLite Community**: First adopters who showed us the educational potential
- **Open Source Community**: For inspiration and feedback
- **Contributors**: Everyone who helps make type safety more accessible

## 💫 Our Mission

> "In a world where code complexity grows daily, we're not just building tools – we're building understanding. Every type error fixed is a developer who learned something new. Every AI automation is a human freed to focus on what matters most. Join us in making Python development more joyful, one type hint at a time."

---

**Made with ❤️ by the 80-20 Human in The Loop community**

*When we write for everyone, we build software for everyone. When we build for everyone, we change the world.*
