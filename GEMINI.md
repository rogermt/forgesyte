# Project Context for Gemini CLI

<!-- 
This is a template GEMINI.md file for providing context to Gemini CLI.
Copy this to your project root and customize it for your specific needs.
-->

## Project Overview

**Project Name**: [Your Project Name]
**Technology Stack**: [e.g., React + TypeScript + Node.js]
**Purpose**: [Brief description of what this project does]

## Code Standards

### General Principles
- Write clean, readable, and maintainable code
- Follow established patterns and conventions
- Prioritize simplicity and clarity
- Include comprehensive documentation

### Language-Specific Guidelines
<!-- Customize based on your primary language -->

#### JavaScript/TypeScript
- Use TypeScript for all new code
- Follow ESLint configuration
- Use Prettier for consistent formatting
- Prefer async/await over Promise chains
- Use meaningful variable and function names

#### Python
- Follow PEP 8 style guidelines
- Use type hints for all functions
- Write comprehensive docstrings
- Prefer pathlib over os.path for file operations

## Development Workflow

### Setup Commands
```bash
# Install dependencies
npm install  # or pip install -r requirements.txt

# Start development server
npm run dev  # or python manage.py runserver

# Run tests
npm test    # or pytest

# Build for production
npm run build  # or python setup.py build
```

### Code Quality Tools

#### Mandatory Commands
Run these before committing any code:

```bash
# Format code
npm run format     # or black . && isort .

# Lint code
npm run lint       # or ruff check --fix .

# Type checking
npm run type-check # or mypy .

# Run tests
npm test          # or pytest
```

## Project Structure

```
project-root/
├── src/                 # Source code
│   ├── components/      # Reusable components
│   ├── utils/          # Utility functions
│   └── types/          # Type definitions
├── tests/              # Test files
├── docs/               # Documentation
└── config/             # Configuration files
```

## Testing Standards

- Aim for 80%+ test coverage
- Write unit tests for all business logic
- Include integration tests for key workflows
- Use meaningful test descriptions
- Mock external dependencies

## Documentation Requirements

- Update README.md for significant changes
- Document all public APIs
- Include inline comments for complex logic
- Maintain changelog for releases

## Deployment & Infrastructure

### Environment Variables
<!-- List key environment variables -->
- `NODE_ENV`: Development environment
- `API_BASE_URL`: Backend API endpoint
- `DATABASE_URL`: Database connection string

### Deployment Process
1. Ensure all tests pass
2. Update version numbers
3. Build production assets
4. Deploy to staging for testing
5. Deploy to production

## Security Considerations

- Never commit secrets or API keys
- Use environment variables for sensitive data
- Validate all user inputs
- Follow OWASP security guidelines
- Regular dependency updates

## Performance Guidelines

- Optimize for Core Web Vitals (if web app)
- Lazy load non-critical resources
- Implement proper caching strategies
- Monitor bundle sizes
- Use appropriate data structures

## Team Preferences

### Communication
- Use descriptive commit messages
- Link issues in pull requests
- Provide clear PR descriptions
- Request reviews from relevant team members

### Code Review Checklist
- [ ] Code follows style guidelines
- [ ] Tests are included and passing
- [ ] Documentation is updated
- [ ] No security vulnerabilities
- [ ] Performance considerations addressed

## Domain-Specific Context

<!-- Add any domain-specific information -->
### [Industry/Domain] Specific Requirements
- [Regulatory compliance requirements]
- [Industry standards to follow]
- [Domain-specific terminology]

## Additional Instructions for AI

When working with this codebase:

1. **Always follow the established patterns** found in existing code
2. **Prioritize maintainability** over clever solutions
3. **Include error handling** for all external calls
4. **Write self-documenting code** with clear variable names
5. **Consider edge cases** and validation
6. **Follow the testing philosophy** established in the project
7. **Respect the architecture** and don't introduce unnecessary complexity

# Gemini CLI Python Development Standards

To ensure code is production-ready, maintainable, and resilient, all AI agents must adhere to the following standards when contributing to the **Gemini CLI** project.

## Core Principles
*   **Prioritize Simplicity:** Write clean, readable, and maintainable code, avoiding unnecessary complexity.
*   **Maintainability over Cleverness:** Choose obvious solutions over "clever" hacks to ensure long-term project health.
*   **Self-Documenting Code:** Use meaningful variable and function names to reduce the need for excessive comments.

## 2. Python Language Standards
*   **Style Guidelines:** Strictly follow **PEP 8** style guidelines.
*   **Type Safety:** Use **type hints** for all functions and modules. For monetary values, rates, or high-precision math, always use the **`Decimal` type** instead of floats to avoid precision errors.
*   **Path Management:** Prefer **`pathlib`** over `os.path` for all file and directory operations.
*   **Documentation:** Write comprehensive **docstrings** for all classes and functions.
*   **Configuration:** Manage configuration via **environment variables** or configuration files (using Pydantic Settings) rather than hard-coding sensitive values.

```python
# Standard: Type hints, Decimal for currency, and input validation
from decimal import Decimal
from fastapi import Query
from pydantic import BaseModel

class Product(BaseModel):
    price: Decimal  # Financial precision

def process_payment(
    amount: Decimal = Query(..., gt=0),  # Validation guardrail
    currency_code: str = Query(..., min_length=3, max_length=3)
) -> None:
    pass
```

## Architectural Design & Patterns
*   **Separation of Concerns:** Decouple the API layer from core logic by extracting business rules into **dedicated service classes**.
*   **Decoupling with Protocols:** Leverage **Protocols** (structural typing) to define interfaces, ensuring components interact through contracts rather than concrete implementations.
*   **The Registry Pattern:** Avoid long `if-elif` chains for algorithms or exporters. Use a **central registry** (dictionary or decorator-based) to map keys to behaviors, allowing for easy extensibility without modifying core code.
*   **Composition over Inheritance:** Prefer composition or **mixins** to add functionality rather than creating brittle, deep inheritance hierarchies.
*   **Avoid Singletons:** Do not use the Singleton pattern; Python **modules** are the idiomatic way to handle shared global state.

```python
# Standard: Registry Pattern to replace long if-elif chains
from typing import Callable

COMMAND_REGISTRY: dict[str, Callable] = {}

def register_command(name: str):
    def decorator(func: Callable):
        COMMAND_REGISTRY[name] = func
        return func
    return decorator

@register_command("export_pdf")
def export_to_pdf(data: dict):
    # logic here
    pass
```

## Resilience and Error Handling
*   **The Retry Pattern:** Wrap all operations involving **external services, APIs, or LLMs** in retry logic to handle transient failures.
*   **Exponential Backoff:** Implement retries with a delay that increases exponentially to prevent overloading a failing service.
*   **Specific Exceptions:** Catch specific errors rather than using generic `try-except` blocks. Provide meaningful feedback, such as raising a **404 error** if a resource is missing.
*   **Fallbacks:** Design systems with backup routes or default behaviors if a primary external call fails after all retry attempts.

```python
# Standard: Retry logic with exponential backoff using Tenacity
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
def call_gemini_api(prompt: str):
    # This will automatically retry on transient network failures
    pass
```

## Performance and Observability
*   **Structured Logging:** Replace all `print` statements with **logging** using Python's built-in `logging` module to allow for better monitoring and integration with services like Sentry.
*   **Lazy Loading & Generators:** Use **generators (`yield`)** for large datasets to stream data row-by-row, keeping memory overhead low.
*   **Strategic Caching:** Use `functools.cache` for expensive computations and implement **TTL (Time-To-Live) caches** for data that changes over time, like API-fetched exchange rates.
*   **Health Checks:** Include a **`/health`** endpoint in all services so infrastructure (e.g., Kubernetes) can monitor availability.

## Testing Standards
*   **Isolated Environments:** Use **in-memory databases** (like SQLite) for testing to ensure a clean setup and prevent pollution of production data.
*   **Coverage Goals:** Aim for **80%+ test coverage**, ensuring success paths, invalid inputs, and edge cases are all verified.
*   **Mocking:** Always mock external dependencies to ensure tests are fast and reliable.

## Development Workflow & Mandatory Tools
Before committing any code, the following tools must be run to ensure compliance:
1.  **Formatting:** `black . && isort .`
2.  **Linting:** `ruff check --fix .`
3.  **Type Checking:** `mypy .`
4.  **Testing:** `pytest`



---

*Last Updated: [Date]*
*Version: [Version]* 