# Contributing

This project is designed for small-team collaboration. The main branch is protected for reviewed work, and each contributor should use a feature branch for changes.

## 1. Start from the latest main branch

```bash
git checkout main
git pull origin main
```

## 2. Create a feature branch

Use a short, descriptive branch name:

```bash
git checkout -b feature/student-portal
git checkout -b fix/login-flow
git checkout -b chore/setup-docs
```

## 3. Make changes and commit often

```bash
git add .
git commit -m "Describe the change"
```

## 4. Push your branch

```bash
git push origin feature/student-portal
```

## 5. Open a pull request

Open a pull request from your feature branch into `main` and ask for review before merging. Keep each PR focused on one change.

## 6. Keep branches in sync

Before starting new work, or before merging a branch, pull the latest main branch again:

```bash
git checkout main
git pull origin main
git checkout feature/student-portal
git merge main
```

## 7. Avoid direct commits to main

Do not push directly to `main` unless you are the repository owner or a designated maintainer. This prevents overwrite conflicts and makes review easier.

## 8. Recommended team flow

- Person A: `feature/student-portal`
- Person B: `feature/admin-dashboard`
- Reviewer: `main`

Both contributors can work in parallel on separate branches, and the admin or team lead can merge reviewed changes after approval.
