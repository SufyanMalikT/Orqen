# Orqen — AI Development Instructions

## Project purpose

Orqen is a developer toolkit for API testing and documentation, code reviews, debugging, and AI-assisted developer workflows.

## Architecture

- Backend: Python, Django, Django REST Framework, PostgreSQL.
- Frontend: React, TypeScript, Vite, Tailwind CSS.
- Background jobs: Celery and Redis when required.
- AI providers: Gemini initially, with an architecture that can support other providers later.
- Repository: one repository containing backend and frontend.

## Working rules

1. Inspect the existing code and relevant configuration before making changes.
2. Follow the established project structure and existing conventions.
3. Work on one clearly defined task at a time.
4. Do not implement unrelated features or perform broad refactoring.
5. Explain important architectural decisions in beginner-friendly language.
6. Use Django and DRF conventions; avoid unnecessary abstractions.
7. Keep secrets in environment variables. Never commit `.env` files or expose server-side credentials in frontend code.
8. Validate input, enforce authentication and permissions where required, and handle errors appropriately.
9. Write or update tests for meaningful functionality and bug fixes.
10. Do not claim a test or command succeeded unless it was actually executed successfully.
11. Never silently discard existing user changes.
12. Do not reset databases, delete migrations, or run destructive commands without explicit approval.
13. Do not install new dependencies without explaining why they are needed.
14. Do not make unrelated changes to the frontend while working on the backend, or vice versa.

## Development workflow

For every task:

1. Inspect relevant files and identify dependencies.
2. Summarize the proposed changes before implementation when the task affects architecture or multiple files.
3. Implement the smallest complete solution.
4. Run relevant checks and tests.
5. Report files changed, commands executed, results, and any remaining issues.
6. Explain important code decisions and what the developer should learn from them.

## Definition of done

A task is complete only when its acceptance criteria are met, relevant checks have been run, changes have been reviewed, and any unverified behavior or known limitations have been clearly reported.