# Contributing to AI Email Automation Agent

Thank you for your interest in improving the AI Email Automation Agent!

## Development Workflow

1. Fork the repository on GitHub.
2. Clone your fork locally:
   ```bash
   git clone https://github.com/akashchandradas7/ai-email-automation-agent.git
   cd ai-email-automation-agent
   ```
3. Create a feature branch:
   ```bash
   git checkout -b feature/your-feature-name
   ```
4. Set up the development environment:
   ```bash
   make setup
   ```
5. Implement changes, add unit tests, and verify:
   ```bash
   make test
   make lint
   ```
6. Commit using conventional commit format (`feat:`, `fix:`, `docs:`, `test:`, `refactor:`).
7. Push to your branch and open a Pull Request.

## Code Standards
- Python 3.10+
- Type hints on all function and method signatures.
- Clean docstrings following Google/PEP 257 format.
- Code style enforced with Ruff.
