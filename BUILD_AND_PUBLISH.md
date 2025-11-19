# Building and Publishing AxProtocol to PyPI

## Quick Start

### 1. Install Build Tools

```bash
pip install build twine
```

### 2. Build Package

```bash
python -m build
```

This creates:
- `dist/axprotocol-2.4.0-py3-none-any.whl` (wheel)
- `dist/axprotocol-2.4.0.tar.gz` (source distribution)

### 3. Test Installation Locally

```bash
pip install dist/axprotocol-2.4.0-py3-none-any.whl
```

Then test:
```python
from axprotocol import run_chain
print("✅ Import successful")
```

### 4. Upload to Test PyPI (Recommended First)

```bash
twine upload --repository testpypi dist/*
```

Test installation from Test PyPI:
```bash
pip install --index-url https://test.pypi.org/simple/ axprotocol
```

### 5. Upload to Production PyPI

```bash
twine upload dist/*
```

**Note:** You'll need PyPI credentials:
- Username: Your PyPI username
- Password: API token (recommended) or password

Create API token at: https://pypi.org/manage/account/token/

## Configuration

### PyPI Credentials

Create `~/.pypirc`:
```ini
[distutils]
index-servers =
    pypi
    testpypi

[pypi]
username = __token__
password = pypi-xxxxxxxxxxxxx

[testpypi]
repository = https://test.pypi.org/legacy/
username = __token__
password = pypi-xxxxxxxxxxxxx
```

Or use environment variables:
```bash
export TWINE_USERNAME=__token__
export TWINE_PASSWORD=pypi-xxxxxxxxxxxxx
```

## Version Management

Update version in:
1. `pyproject.toml` → `[project] version = "2.4.0"`
2. `axprotocol/__init__.py` → `__version__ = "2.4.0"`
3. `sentinel_api.py` → Uses `axprotocol.__version__`

## Pre-Publish Checklist

- [ ] All tests pass: `pytest verify/`
- [ ] Version updated in all files
- [ ] `README.md` is up to date
- [ ] `pyproject.toml` metadata is correct
- [ ] Package builds without errors
- [ ] Local installation test passes
- [ ] Imports work: `from axprotocol import run_chain`

## Post-Publish

1. Verify on PyPI: https://pypi.org/project/axprotocol/
2. Test installation: `pip install axprotocol`
3. Update documentation with installation instructions

## Troubleshooting

### "Package already exists"
- Version already published - increment version number

### "Invalid credentials"
- Check `.pypirc` or environment variables
- Verify API token is correct

### "Missing required files"
- Check `MANIFEST.in` includes all necessary files
- Verify `pyproject.toml` package-data configuration

### "Import errors after installation"
- Verify `axprotocol/__init__.py` exports are correct
- Check that `axp/` package is included in build

## FastAPI API Deployment

After publishing, users can install and run the API:

```bash
pip install axprotocol[api]
uvicorn sentinel_api:app --host 0.0.0.0 --port 8000
```

Or use the included script:
```bash
python sentinel_api.py
```

