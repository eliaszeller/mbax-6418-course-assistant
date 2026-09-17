# Contributing

## Branches

Use a personal or design branch from the latest `main`:

```bash
git switch main
git pull --ff-only origin main
git switch -c team/<your-name>-<design>
```

Keep competing implementations in separate branches until the comparison is complete. Do not rewrite another contributor's branch.

## Commits and pull requests

Use focused conventional commits such as `feat: add pdf ingestion` or `test: cover source validation`. Every pull request should include:

- the design choice and alternatives considered;
- tests run and their results;
- evidence of source/page/slide preservation;
- security checks confirming no secrets or course files were added;
- limitations and unchecked cases;
- the issue number it addresses.

## Ownership

Before substantial work, claim the corresponding GitHub issue and coordinate overlapping changes in the issue thread. Maintainers will compare implementations using the shared completion checks rather than choosing based on branch size.

## Sensitive data

Never commit course downloads, generated indexes, student responses, endpoint URLs containing credentials, API keys, or logs containing prompts and secrets. Use `.env.example` with dummy values only.
