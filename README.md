# Octomind Action

Run [Octomind](https://github.com/Muvon/octomind) AI agent in your GitHub Actions workflows.

## Quick Start

```yaml
- uses: muvon/octomind-action@v1
  with:
    prompt: "Review this code for issues"
  env:
    OPENROUTER_API_KEY: ${{ secrets.OPENROUTER_API_KEY }}
```

## Inputs

| Input | Required | Default | Description |
|-------|----------|---------|-------------|
| `prompt` | **yes** | — | Task or message to send to octomind |
| `role` | no | config default | Role to use (e.g. `developer:rust`) |
| `model` | no | — | Model override (e.g. `openrouter:anthropic/claude-sonnet-4`) |
| `name` | no | — | Session name — creates or resumes a named session |
| `resume` | no | — | Resume a specific session by name |
| `resume_recent` | no | `false` | Resume the most recent session for the current directory |
| `sandbox` | no | `true` | Restrict filesystem writes to the current working directory |
| `hook` | no | — | Comma-separated webhook hook names to activate |
| `version` | no | `latest` | Octomind version to install |
| `tap` | no | — | Tap to add before run (`user/repo` format) |
| `tap_path` | no | — | Local path for tap (local directory instead of GitHub clone) |
| `config` | no | — | Path to octomind config file |
| `comment` | no | `none` | PR comment mode: `full`, `compact` (collapsible), `none` |
| `github_token` | no | `${{ github.token }}` | GitHub token for PR commenting |

## Outputs

| Output | Description |
|--------|-------------|
| `result` | Last assistant message content |
| `session_id` | Session ID (for resuming in subsequent steps) |
| `cost` | Session cost as JSON (`{"tokens": N, "cost": N}`) |
| `raw_output` | Full JSONL output for advanced parsing |
| `exit_code` | Process exit code |

## API Keys

Pass provider API keys via the `env` block. Octomind reads them automatically:

```yaml
env:
  OPENROUTER_API_KEY: ${{ secrets.OPENROUTER_API_KEY }}
  # or any of:
  # ANTHROPIC_API_KEY, OPENAI_API_KEY, DEEPSEEK_API_KEY,
  # CLOUDFLARE_API_TOKEN, AWS_ACCESS_KEY_ID + AWS_SECRET_ACCESS_KEY
```

## Examples

### PR Review with Comment

```yaml
name: Code Review
on:
  pull_request:
    types: [opened, synchronize]

jobs:
  review:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: muvon/octomind-action@v1
        with:
          role: developer:rust
          prompt: "Review this PR for security issues and suggest fixes"
          comment: true
        env:
          OPENROUTER_API_KEY: ${{ secrets.OPENROUTER_API_KEY }}
```

### Custom Tap

```yaml
- uses: muvon/octomind-action@v1
  with:
    role: reviewer:security
    prompt: "Audit the changes in this PR"
    tap: myorg/security-agents
    comment: true
  env:
    ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
```

### Using Outputs

```yaml
- uses: muvon/octomind-action@v1
  id: review
  with:
    prompt: "Analyze code quality"
  env:
    OPENROUTER_API_KEY: ${{ secrets.OPENROUTER_API_KEY }}

- run: |
    echo "Result: ${{ steps.review.outputs.result }}"
    echo "Cost: ${{ steps.review.outputs.cost }}"
    echo "Session: ${{ steps.review.outputs.session_id }}"
```

### Named Session with Model Override

```yaml
- uses: muvon/octomind-action@v1
  with:
    prompt: "Explain the architecture"
    model: anthropic:claude-sonnet-4
    name: arch-review
  env:
    ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
```

## Caching

The action installs the octomind binary to `$RUNNER_TOOL_CACHE/octomind/<version>/` and skips download if already present. For cross-job caching:

```yaml
- uses: actions/cache@v4
  with:
    path: ${{ runner.tool_cache }}/octomind
    key: octomind-v0.23.1

- uses: muvon/octomind-action@v1
  with:
    version: "0.23.1"
    prompt: "Run analysis"
  env:
    OPENROUTER_API_KEY: ${{ secrets.OPENROUTER_API_KEY }}
```

## License

Apache-2.0
