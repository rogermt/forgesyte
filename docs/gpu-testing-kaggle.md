# GPU Testing on Kaggle - Week 3

Run full end-to-end video processing pipeline with real YOLO models.

## Setup (Kaggle Notebook)

```bash
# Clone repositories
git clone https://github.com/rogermt/forgesyte.git
git clone https://github.com/rogermt/forgesyte-plugins.git
git clone https://github.com/roboflow/sports.git

cd forgesyte
```

## Install Backend + GPU Support

```bash
cd server

# Sync dependencies
uv sync

# Install GPU PyTorch
uv pip install torch torchvision --index-url https://download.pytorch.org/whl/cu118

# Install plugins package (sports.common)
cd ../forgesyte-plugins/plugins/forgesyte-yolo-tracker
uv pip install -e .
```

## Run GPU Tests

```bash
cd /path/to/forgesyte/server

# Run ALL tests with GPU plugin tests
RUN_MODEL_TESTS=1 RUN_INTEGRATION_TESTS=1 uv run pytest --cov=app -v
```

## Expected Results

- ✅ 733+ tests pass
- ✅ Backend endpoints working with real models
- ✅ GPU detection/tracking working
- ✅ Coverage ≥ 80%

## Test Categories

### CPU Tests (Run Anywhere)
```bash
uv run pytest tests/api/ -v
```

### GPU Model Tests (Kaggle Only)
```bash
RUN_MODEL_TESTS=1 uv run pytest tests/integration/
```

### Integration Tests (Full Pipeline)
```bash
RUN_MODEL_TESTS=1 RUN_INTEGRATION_TESTS=1 uv run pytest tests/
```

## Troubleshooting

### CUDA Out of Memory
```bash
# Reduce batch size in plugin config
# Or test with smaller frames (480p instead of 1080p)
```

### Model Files Missing
```bash
# Download to forgesyte-plugins/plugins/forgesyte-yolo-tracker/models/
# - football-player-detection-v3.pt
# - football-ball-detection-v2.pt
# - football-pitch-detection-v1.pt
```

### ImportError for sports.common
```bash
# Ensure sports package installed
cd ~/sports
pip install -e .
```

## Next Steps After GPU Tests

1. ✅ All GPU tests passing
2. ✅ Export feature integrated
3. ✅ End-to-end video processing working
4. Deploy to production

---

**Timeline**: Week 3 Day 3-5
**Status**: Ready to run on Kaggle GPU
