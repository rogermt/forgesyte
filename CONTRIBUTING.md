# ✅ **2. CONTRIBUTING.md**

```md
# Contributing to ForgeSyte

Thank you for contributing to ForgeSyte. This project values clarity, modularity, and reproducibility. Contributions that strengthen those qualities are especially welcome.

---

## Development Environment

### Backend (uv)

```bash
cd server
uv sync
uv run fastapi dev app/main.py
```

### Frontend (React)

```bash
cd web-ui
npm install
npm run dev
```

---

## Branching Strategy

- `main` — stable  
- `develop` — active development  
- `feature/<name>` — new features  

---

## Code Style

### Python
- Use `uvx ruff format` for formatting  
- Use type hints  
- Keep plugin contracts explicit  

### React/TypeScript
- Use Prettier  
- Prefer explicit types  

---

## Tests

Backend:

```bash
uv run pytest
```

Frontend:

```bash
npm test
```

---

## Pull Requests

Include:

- What changed  
- Why  
- How to test  
- Any breaking changes  

---

## Adding Plugins

See `PLUGIN_DEVELOPMENT.md`.

Plugins must:

- Implement `Plugin` class  
- Provide `metadata()`  
- Provide `analyze()`  
- Avoid heavy dependencies unless necessary  
```

---