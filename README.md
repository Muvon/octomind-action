# Octomind Action

A GitHub Action to run [Octomind](https://github.com/Muvon/octomind) — a session-based AI development agent — directly in your CI/CD workflows. Automate code reviews, generate code, run analysis, and more with any AI provider.

## Features

- **Multi-provider** — OpenRouter, Anthropic, OpenAI, DeepSeek, Google, AWS Bedrock, Cloudflare
- **Role-based agents** — Use specialized roles from the built-in registry or custom taps
- **PR commenting** — Post results directly to pull requests (full or collapsible)
- **Session support** — Named sessions with resume capability across workflow runs
- **Custom taps** — Extend with your own agent registry
- **Binary caching** — Skips download when already installed

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
| `sandbox` | no | `false` | Restrict filesystem writes to the current working directory |
| `hook` | no | — | Comma-separated webhook hook names to activate |
| `version` | no | `latest` | Octomind version to install |
| `tap` | no | — | Tap to add before run (e.g. `user/repo` or `user/repo ./local/path`) |
| `config` | no | — | Path to octomind config file |
| `comment` | no | `none` | PR comment mode: `full`, `compact` (collapsible), or `none` |
| `github_token` | no | `${{ github.token }}` | GitHub token for PR commenting |

## Outputs

| Output | Description |
|--------|-------------|
| `result` | Last assistant message content |
| `session_id` | Session ID for resuming in subsequent steps |
| `cost` | Session cost as JSON (`{"tokens": N, "cost": N}`) |
| `raw_output` | Full JSONL output for advanced parsing |
| `exit_code` | Process exit code |

## API Keys

Octomind supports multiple AI providers. Pass the relevant API key via the `env` block:

| Provider | Environment Variable |
|----------|---------------------|
| [OpenRouter](https://openrouter.ai/) | `OPENROUTER_API_KEY` |
| [Anthropic](https://console.anthropic.com/) | `ANTHROPIC_API_KEY` |
| [OpenAI](https://platform.openai.com/) | `OPENAI_API_KEY` |
| [DeepSeek](https://platform.deepseek.com/) | `DEEPSEEK_API_KEY` |
| [Cloudflare](https://dash.cloudflare.com/) | `CLOUDFLARE_API_TOKEN` |
| [AWS Bedrock](https://aws.amazon.com/bedrock/) | `AWS_ACCESS_KEY_ID` + `AWS_SECRET_ACCESS_KEY` + `AWS_REGION` |
| [Google Vertex AI](https://cloud.google.com/vertex-ai) | `GOOGLE_APPLICATION_CREDENTIALS` |

```yaml
env:
  OPENROUTER_API_KEY: ${{ secrets.OPENROUTER_API_KEY }}
```

## Examples

### PR Code Review

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
          comment: full
        env:
          OPENROUTER_API_KEY: ${{ secrets.OPENROUTER_API_KEY }}
```

### Compact PR Comment

```yaml
- uses: muvon/octomind-action@v1
  with:
    prompt: "Summarize changes in this PR"
    comment: compact
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
    comment: full
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

### Model Override

```yaml
- uses: muvon/octomind-action@v1
  with:
    prompt: "Explain the architecture"
    model: anthropic:claude-sonnet-4
  env:
    ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
```

### Named Session

```yaml
# First run — creates the session
- uses: muvon/octomind-action@v1
  with:
    prompt: "Analyze the codebase structure"
    name: analysis
  env:
    OPENROUTER_API_KEY: ${{ secrets.OPENROUTER_API_KEY }}

# Later step — resumes with context
- uses: muvon/octomind-action@v1
  with:
    prompt: "Now suggest improvements based on your analysis"
    resume: analysis
  env:
    OPENROUTER_API_KEY: ${{ secrets.OPENROUTER_API_KEY }}
```

## Caching

The binary is installed to `$RUNNER_TOOL_CACHE/octomind/<version>/` and reused within the same job. For cross-job caching:

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

[Apache-2.0](LICENSE)
