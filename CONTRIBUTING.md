# Contributing to Study Buddy AI

Thank you for your interest in contributing! This document outlines the process for getting involved.

## Getting Started

1. **Fork** the repository on GitHub
2. **Clone** your fork locally:
   ```bash
   git clone https://github.com/YOUR_USERNAME/Study-Buddy-AI.git
   cd Study-Buddy-AI
   ```
3. **Install** dependencies:
   ```bash
   pip install -e .
   pip install ruff
   ```
4. **Copy** the env template and add your Groq key:
   ```bash
   cp .env.example .env
   ```

## Development Workflow

```bash
# Create a feature branch
git checkout -b feat/your-feature-name

# Make your changes, then lint
ruff check . --fix

# Commit using conventional commits
git commit -m "feat: add topic suggestion dropdown"

# Push and open a PR
git push origin feat/your-feature-name
```

## Commit Message Convention

We use [Conventional Commits](https://www.conventionalcommits.org/):

| Prefix | Use for |
|---|---|
| `feat:` | New features |
| `fix:` | Bug fixes |
| `docs:` | Documentation changes |
| `refactor:` | Code restructuring (no behaviour change) |
| `ci:` | CI/CD pipeline changes |
| `chore:` | Dependency updates, tooling |

## Code Style

- All Python code is linted with **ruff** — PRs that fail the lint check will not be merged.
- Use **type hints** on all function signatures.
- Write **docstrings** on all public classes and methods.
- Keep functions focused — if a function does more than one thing, split it.

## Pull Request Guidelines

- Target the `main` branch.
- Describe what changed and why in the PR description.
- Reference any related issues with `Closes #N`.
- Keep PRs small and focused — one feature or fix per PR.

## Questions?

Open a [GitHub Discussion](https://github.com/ArchanaChetan07/Study-Buddy-AI/discussions) or file an issue.
