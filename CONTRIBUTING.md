# Contributing to Ossia Avatar

Thank you for your interest! Here's how to contribute.

## Code of Conduct

Be respectful, inclusive, and professional. 

## Issues & Bugs

1. **Check existing issues** before opening a new one.
2. **Provide details**:
   - OS, GPU, CUDA version, Python version
   - Full error message + stack trace
   - Minimal reproducible example
3. **Label appropriately**: `bug`, `enhancement`, `question`, `docs`

## Pull Requests

1. **Fork** the repo.
2. **Create a branch**: `git checkout -b feature/my-feature`
3. **Make changes**: follow the style below.
4. **Test locally**: run your changes with a sample image.
5. **Commit with clear messages**: `git commit -m "Add feature X"`
6. **Push & open a PR**: describe what it does, why, and how to test.

## Code Style

- Python: PEP 8 (black-style)
- Use type hints where feasible
- Comment the "why", not the "what"
- Keep functions focused and testable

Example:

```python
def generate_shape(image_dict: dict[str, Image.Image], steps: int) -> trimesh.Trimesh:
    """Fuse multiple views into a 3D mesh via flow-matching DiT."""
    pipe = load_pipeline()
    mesh = pipe(image=image_dict, num_inference_steps=steps)
    return mesh
```

## Adding Features

### New Pipeline

If you want to add a new model (e.g., MICA for face reconstruction):

1. Create `scripts/image2mica.py` (follow the pattern of existing scripts).
2. Document it in `README.md` (new section under "Pipelines").
3. Add to `examples/` with sample outputs.
4. Update `requirements.txt` with new deps.

### New Output Format

If adding `.ply`, `.usdz`, etc.:

1. Modify the inference scripts to export.
2. Update `SETUP.md` with any new dependencies.
3. Add examples to `examples/`.
4. Document in `README.md` (Output Formats section).

### Optimization

If improving speed/memory:

1. Profile before/after (include benchmark results in PR).
2. Test on multiple GPU types (RTX 4090, A100, etc. if possible).
3. Ensure multi-view still works (the slowest path).

## Testing

No formal test suite yet, but:

1. Test with at least 3 different input photos (various lighting, poses).
2. Test both single and multi-view pipelines.
3. Verify output `.glb` opens in a viewer.
4. Check VRAM usage: `nvidia-smi` during run.

## Documentation

- Keep `README.md` and `SETUP.md` in sync with code.
- Update docstrings when you change function signatures.
- If adding a new arg, document it in the script's `--help` and `README.md`.

## Roadmap

We're tracking:

- [ ] Gaussian splat export
- [ ] Batch processing
- [ ] Face-specialized models (MICA)
- [ ] REST API
- [ ] Web UI

Interested in any of these? Open an issue to coordinate before starting.

## Questions?

- **Usage Q**: Open an issue labeled `question`.
- **Technical Discussion**: Open a Discussion (if available).
- **Direct Contact**: See repo README for contact info.

---

Happy coding! 🎉
