# ForgeSyte Plugin Development Guide

ForgeSyte plugins are Python modules that implement a simple, explicit contract. They allow you to extend the vision capabilities of the ForgeSyte core without modifying the server itself.

---

## Plugin Structure

```
server/app/plugins/<plugin_name>/
└─ plugin.py
```

---

## Plugin Interface

```python
class Plugin:
    name = "my_plugin"

    def metadata(self):
        return {
            "name": self.name,
            "description": "What this plugin does",
            "inputs": ["image"],
            "outputs": ["json"],
            "version": "0.1.0"
        }

    def analyze(self, image_bytes: bytes):
        # return dict
```

---

## Running with uv

```bash
cd server
uv run fastapi dev app/main.py
```

---

## Testing Your Plugin

```bash
curl -X POST "http://localhost:8000/v1/analyze?plugin=my_plugin" \
     -F "file=@image.png"
```

Then:

```bash
curl http://localhost:8000/v1/jobs/<job_id>
```

---

## Guidelines

- Keep dependencies minimal  
- Use deterministic outputs  
- Document any model requirements  
- Use structured JSON  
- Avoid loading large models repeatedly  
