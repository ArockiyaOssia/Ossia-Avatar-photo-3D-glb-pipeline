# Ossia Avatar

Turn photos into 3D head avatars (`.glb`) — single image or multi-view fusion — with PBR texturing. Self-contained: bundles a patched Hunyuan3D engine; one command to set up, one to run.

```
photo.jpg  ──►  [ shape DiT ]  ──►  [ PBR paint ]  ──►  avatar.glb
```

## Install (once)

```bash
git clone <your-repo-url> ossia-avatar
cd ossia-avatar
./avatar setup
```

`setup.sh` creates a Python 3.10 venv, installs PyTorch (CUDA 12.4) + deps, compiles the bundled CUDA/C++ extensions, and fetches the RealESRGAN checkpoint. ~10 min. See [SETUP.md](SETUP.md).

## Use — one CLI, three modes

```bash
# Single photo  ->  textured avatar
./avatar single photo.jpg -o avatar.glb

# Multi-view (4 angles)  ->  fused, more accurate avatar
./avatar multi --front f.jpg --left l.jpg --right r.jpg --back b.jpg -o avatar_hq.glb

# Geometry only (no texture)  ->  mesh + optional wireframe render
./avatar mesh photo.jpg -o mesh.glb --render
```

Helpers:

```bash
./avatar doctor        # check GPU / CUDA / engine / models
./avatar download      # pre-fetch model weights (optional)
./avatar help          # usage
```

> First run downloads model weights (~11 GB) and caches them. Later runs are fast.

## Commands & options

### `single` — photo → textured `.glb`
```bash
./avatar single PHOTO -o OUT.glb [--steps 50] [--octree 384] \
                                 [--max-views 6] [--resolution 512]
```
Fast (~2–3 min, ~10 GB VRAM). Face accurate; back/sides inferred.

### `multi` — 4 photos → fused `.glb`
```bash
./avatar multi --front F --left L --right R --back B -o OUT.glb \
               [--steps 50] [--octree 384] [--max-views 6] [--resolution 512]
```
Best quality (~5–8 min, ~21 GB VRAM). `--front` required; others optional but recommended.
View tags map to fixed camera angles: `front=0°, left=90°, back=180°, right=270°`.

### `mesh` — photo → geometry-only `.glb`
```bash
./avatar mesh PHOTO -o OUT.glb [--render] [--steps 50] [--octree 512]
```
No texture. `--render` also writes white-clay + wireframe PNGs to the workdir.

**Higher quality (multi-view):** `--resolution 768 --max-views 9 --octree 512 --steps 75`
(peaks ~23 GB VRAM on a 24 GB card — near the limit).

## Requirements

| | |
|---|---|
| GPU | RTX 4090 (24 GB) or ≥20 GB Ampere+ |
| CUDA | 12.1 or 12.4 toolkit (for compiling extensions) |
| Python | 3.10 |
| Disk | ~25 GB free (weights + scratch) |
| OS | Linux (Ubuntu 20.04+, WSL2) |

Check yours: `./avatar doctor`

## Output

`.glb` (binary glTF) — single file, works everywhere:

```html
<model-viewer src="avatar.glb" camera-controls auto-rotate></model-viewer>
```

```js
// three.js — load + wireframe toggle
new THREE.GLTFLoader().load('avatar.glb', g => {
  scene.add(g.scene);
  g.scene.traverse(o => { if (o.material) o.material.wireframe = true; });
});
```

The paint stage also writes `textured.obj` + `*.jpg` maps (albedo / metallic / roughness) in the workdir for Blender/Maya.

## Accuracy & limits (honest)

- **Single-view**: front is faithful; hair becomes a smooth cap; back is guessed.
- **Multi-view**: accurate head geometry + hair volume from all angles; texture is still projected from the front view.
- **Hair**: volume only, no strand detail (model limitation). True photoreal needs Gaussian splatting (not glTF).

## Troubleshooting

| Symptom | Fix |
|---|---|
| `venv not found` | `./avatar setup` |
| `CUDA not available` | check `nvidia-smi`; reinstall driver |
| Out of memory | use `single`, or lower `--resolution 512 --max-views 6` |
| Slow first run | weights downloading (~11 GB) — normal, one-time |
| Compile fails | ensure CUDA toolkit; `CUDA_HOME=/usr/local/cuda-12.4 ./avatar setup` |

More in [SETUP.md](SETUP.md).

## Layout

```
ossia-avatar/
├── avatar              # unified CLI (setup / single / multi / mesh / doctor)
├── setup.sh            # builds venv + deps + compiles engine extensions
├── scripts/            # pipeline entrypoints (image2glb, image2glb_mv, shape_only)
│   └── _engine.py      # engine bootstrap + 2mv config auto-remap
├── engine/             # bundled, patched Hunyuan3D engine (hy3dshape + hy3dpaint)
├── examples/           # sample usage + how to view .glb
├── SETUP.md  CONTRIBUTING.md  LICENSE  requirements.txt
```

## License

MIT (this wrapper). Bundled Hunyuan3D engine is under the Tencent Hunyuan
Non-Commercial License — see `engine/LICENSE` / `engine/Notice.txt`.

## Credits

Built on [Hunyuan3D 2.1 / 2mv](https://github.com/Tencent-Hunyuan/Hunyuan3D-2.1) (Tencent).
