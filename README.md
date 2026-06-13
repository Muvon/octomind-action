# Octomind Action

GitHub Actions for [Octomind](https://github.com/Muvon/octomind) — a session-based AI development agent — in your CI/CD workflows. Automate code reviews, generate code, run analysis, and orchestrate multi-step pipelines with any AI provider.

This repo ships two actions:

| Action | Reference | Runs |
|--------|-----------|------|
| **Run** | `muvon/octomind-action@v1` or `muvon/octomind-action/run@v1` | `octomind run` — a single agent/session from a prompt |
| **Workflow** | `muvon/octomind-action/workflow@v1` | `octomind workflow` — a multi-step pipeline from a TOML file |

> `muvon/octomind-action@v1` is an alias for `muvon/octomind-action/run@v1` — both run the same `run` action.

## Features

- **Multi-provider** — OpenRouter, Anthropic, OpenAI, DeepSeek, Google, AWS Bedrock, Cloudflare
- **Role-based agents** — Use specialized roles from the built-in registry or custom taps
- **Multi-step workflows** — Drive TOML pipelines (sequential, parallel, loop, conditional)
- **PR commenting** — Post results directly to pull requests (full or collapsible)
- **Session support** — Named sessions with resume capability across workflow runs
- **Structured outputs** — Both actions emit JSONL parsed into `result`, `cost`, and more
- **Binary caching** — Skips download when already installed

## Quick Start

### Run

```yaml
- uses: muvon/octomind-action@v1
  with:
    prompt: "Review this code for issues"
  env:
    OPENROUTER_API_KEY: ${{ secrets.OPENROUTER_API_KEY }}
```

### Workflow

```yaml
- uses: muvon/octomind-action/workflow@v1
  with:
    workflow_file: .octomind/review.toml
    input: "Review the changes in this PR"
  env:
    OPENROUTER_API_KEY: ${{ secrets.OPENROUTER_API_KEY }}
```

## Run inputs

`muvon/octomind-action@v1` · `muvon/octomind-action/run@v1`

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

### Run outputs

| Output | Description |
|--------|-------------|
| `result` | Last assistant message content |
| `session_id` | Session ID for resuming in subsequent steps |
| `cost` | Session cost as JSON (`{"tokens": N, "cost": N}`) |
| `raw_output` | Full JSONL output for advanced parsing |
| `exit_code` | Process exit code |

## Workflow inputs

`muvon/octomind-action/workflow@v1`

| Input | Required | Default | Description |
|-------|----------|---------|-------------|
| `workflow_file` | **yes** | — | Path to the workflow TOML file |
| `input` | **yes** | — | Input passed to the workflow via stdin (`{{input}}` in steps) |
| `dry_run` | no | `false` | Validate and print the execution plan without running |
| `version` | no | `latest` | Octomind version to install |
| `tap` | no | — | Tap to add before run |
| `config` | no | — | Path to octomind config file |
| `comment` | no | `none` | PR comment mode: `full`, `compact`, or `none` |
| `github_token` | no | `${{ github.token }}` | GitHub token for PR commenting |

### Workflow outputs

| Output | Description |
|--------|-------------|
| `result` | Final workflow result (last step output) |
| `cost` | Aggregated cost as JSON (`{"tokens": N, "cost": N}`) |
| `raw_output` | Full JSONL output for advanced parsing |
| `exit_code` | Process exit code |

> Workflows have no single resumable session, so there is no `session_id` output.

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

### PR Code Review (run)

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

### Multi-step pipeline (workflow)

```yaml
name: Develop
on: workflow_dispatch

jobs:
  develop:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - uses: muvon/octomind-action/workflow@v1
        with:
          workflow_file: .octomind/develop.toml
          input: "Add retry with backoff to the HTTP client"
          comment: full
        env:
          OPENROUTER_API_KEY: ${{ secrets.OPENROUTER_API_KEY }}
```

A minimal `develop.toml`:

```toml
name = "develop"

[[steps]]
name   = "context"
role   = "developer:context"
prompt = "Gather the key files and lines for this spec:\n{{input}}"

[[steps]]
name   = "implement"
role   = "developer:general"
prompt = "Implement the spec using this context:\n<context>{{context}}</context>\n\nSpec:\n{{input}}"
```

### Validate a workflow (dry-run)

```yaml
- uses: muvon/octomind-action/workflow@v1
  with:
    workflow_file: .octomind/develop.toml
    input: "noop"
    dry_run: true
```

### Compact PR comment

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
- uses: muvon/octomind-action/run@v1
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

## Repository layout

| Path | Purpose |
|------|---------|
| `action.yml` | Root action — Marketplace listing and `@v1` entry point (= `run`) |
| `run/action.yml` | The `run` action (`/run@v1`) |
| `workflow/action.yml` | The `workflow` action (`/workflow@v1`) |
| `_core/action.yml` | Internal shared engine (install + invoke + parse + comment). Not for direct use |

The public actions are thin facades that delegate to `_core`, so install, output parsing, and PR commenting live in one place.

## License

[Apache-2.0](LICENSE)
