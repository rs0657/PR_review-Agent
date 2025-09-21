# Optional Tools Installation

This document covers additional tools that can enhance the PR Review Agent but are not included in the standard requirements.txt due to installation complexity.

## ast-grep

`ast-grep` is a powerful code search and linting tool that can provide additional code analysis capabilities.

### Installation Options:

1. **Using Cargo (Rust package manager):**
   ```bash
   cargo install ast-grep
   ```

2. **Using npm:**
   ```bash
   npm install -g @ast-grep/cli
   ```

3. **Download binary from GitHub releases:**
   - Visit: https://github.com/ast-grep/ast-grep/releases
   - Download the appropriate binary for your platform

4. **Using package managers:**
   - **macOS (Homebrew):** `brew install ast-grep`
   - **Linux (various):** Check your distribution's package manager

### Usage in PR Review Agent:

Once installed, ast-grep can be used for:
- Advanced code pattern matching
- Custom linting rules
- Code structure analysis
- Refactoring suggestions

The PR Review Agent will automatically detect if ast-grep is available and use it for enhanced analysis.

## Other Optional Tools

### Additional Code Quality Tools:
- **mypy**: Static type checker for Python
- **bandit**: Security linter for Python
- **safety**: Checks for known security vulnerabilities in dependencies

Install these with:
```bash
pip install mypy bandit safety
```

## Configuration

To enable optional tools, update your `.env` file:
```
ENABLE_AST_GREP=true
ENABLE_MYPY=true
ENABLE_BANDIT=true
```

The agent will gracefully fallback to core analyzers if optional tools are not available.