<div align="center">

# Ossia Avatar

**Turn a photo into a spinning 3D head — textured or wireframe — and put it on your website.**

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python 3.10](https://img.shields.io/badge/Python-3.10-3776ab?logo=python&logoColor=white)](https://www.python.org/)
[![CUDA 12.4](https://img.shields.io/badge/CUDA-12.4-76b900?logo=nvidia&logoColor=white)](https://developer.nvidia.com/cuda-toolkit)
[![Hunyuan3D 2.1](https://img.shields.io/badge/Engine-Hunyuan3D--2.1-ff6b35)](https://github.com/Tencent-Hunyuan/Hunyuan3D-2.1)
[![Live Demo](https://img.shields.io/badge/Live%20Demo-portfolio-blueviolet)](https://portfolio-nine-dusky-15.vercel.app/)

</div>

---

## What it does

```
photo.jpg  ──►  [ shape DiT ]  ──►  [ PBR paint ]  ──►  avatar.glb
```

Runs **Hunyuan3D 2.1** (Tencent) locally on an RTX 4090.  
Two stages: shape generation (flow-matching DiT) → PBR texture painting → `.glb` export.  
One command to set up, one to run.

---

## Demo

<table>
<tr>
<td align="center"><b>Input photo</b></td>
<td align="center"><b>Textured .glb</b></td>
<td align="center"><b>Wireframe .glb</b></td>
</tr>
<tr>
<td align="center"><img src="assets/demo_input.png" width="220" alt="Input photo"/></td>
<td align="center"><img src="assets/demo_output_textured.png" width="220" alt="Textured 3D avatar"/></td>
<td align="center"><img src="assets/demo_output_wire.png" width="220" alt="Wireframe mesh"/></td>
</tr>
</table>

> **Live on the web:** [portfolio-nine-dusky-15.vercel.app](https://portfolio-nine-dusky-15.vercel.app/) — Next.js + React Three Fiber hero powered by a `.glb` from this pipeline.

---

## Quick start

```bash
git clone https://github.com/ArockiyaOssia/Ossia-Avatar-photo-3D-glb-pipeline ossia-avatar
cd ossia-avatar
./avatar setup          # one-time: venv + deps + CUDA extensions (~10 min)
./avatar single photo.jpg -o avatar.glb
```

First run also downloads model weights (~11 GB). Subsequent runs are fast.

---

## CLI — three modes

```bash
# Single photo  →  textured .glb  (~2–3 min, ~10 GB VRAM)
./avatar single  photo.jpg           -o avatar.glb

# 4 angles  →  fused, more accurate .glb  (~5–8 min, ~21 GB VRAM)
./avatar multi   --front f.jpg --left l.jpg --right r.jpg --back b.jpg \
                 -o avatar_hq.glb

# Geometry only  →  mesh + optional clay/wireframe PNGs
./avatar mesh    photo.jpg           -o mesh.glb --render
```

Helpers:
```bash
./avatar doctor    # GPU / CUDA / engine / model check
./avatar download  # pre-fetch model weights
./avatar help
```

---

## Commands & options

### `single` — photo → textured `.glb`

```bash
./avatar single PHOTO -o OUT.glb [--steps 50] [--octree 384] \
                                 [--max-views 6] [--resolution 512]
```

Fast (~2–3 min, ~10 GB VRAM). Front face is faithful; sides/back inferred.

### `multi` — 4 photos → fused `.glb`

```bash
./avatar multi --front F --left L --right R --back B -o OUT.glb \
               [--steps 50] [--octree 384] [--max-views 6] [--resolution 512]
```

Best quality (~5–8 min, ~21 GB VRAM). `--front` required; others optional but recommended.  
View tags: `front=0°  left=90°  back=180°  right=270°`.

### `mesh` — photo → geometry-only `.glb`

```bash
./avatar mesh PHOTO -o OUT.glb [--render] [--steps 50] [--octree 512]
```

No texture. `--render` writes `clay_front.png`, `clay_side.png`, `wire_front.png`, `wire_side.png`.

**Higher quality:** `--resolution 768 --max-views 9 --octree 512 --steps 75`  
(peaks ~23 GB VRAM on a 24 GB card).

---

## Put yourself on your website

Take the `.glb` and drop a **live, spinning 3D you** into your portfolio — textured head or glowing wireframe.

```bash
./avatar single photo.jpg -o public/avatar.glb         # textured head
./avatar mesh   photo.jpg -o public/avatar_mesh.glb    # geometry-only (wireframe)
```

Pick your stack — full guide + files in [`web/`](web/README.md):

**React Three Fiber (Next.js)** — [`web/react-three-fiber/Avatar.jsx`](web/react-three-fiber/Avatar.jsx)

```bash
npm i three @react-three/fiber @react-three/drei
```

```jsx
import Avatar from "@/components/Avatar";  // copy Avatar.jsx here

<Avatar src="/avatar.glb" />                 {/* textured, auto-rotates  */}
<Avatar src="/avatar_mesh.glb" wireframe />  {/* hologram wireframe look */}
```

**Zero-build** — [`web/model-viewer.html`](web/model-viewer.html)

```html
<script type="module"
  src="https://ajax.googleapis.com/ajax/libs/model-viewer/3.5.0/model-viewer.min.js"></script>
<model-viewer src="avatar.glb" camera-controls auto-rotate></model-viewer>
```

**Plain three.js** — [`web/three-wireframe.html`](web/three-wireframe.html) — textured⇄wireframe toggle, no build step.

---

## Requirements

| | |
|---|---|
| GPU | RTX 4090 (24 GB) or ≥ 20 GB Ampere+ |
| CUDA | 12.1 or 12.4 toolkit (for compiling extensions) |
| Python | 3.10 |
| Disk | ~25 GB free (weights + scratch) |
| OS | Linux (Ubuntu 20.04+, WSL2) |

Check yours: `./avatar doctor`

---

## Output

`.glb` — single file, works everywhere:

```html
<!-- Drop in any web page -->
<model-viewer src="avatar.glb" camera-controls auto-rotate></model-viewer>
```

```js
// three.js — load + wireframe toggle
new THREE.GLTFLoader().load('avatar.glb', g => {
  scene.add(g.scene);
  g.scene.traverse(o => { if (o.material) o.material.wireframe = true; });
});
```

The paint stage also writes `textured.obj` + `*.jpg` maps (albedo / metallic / roughness / normal) in the workdir — importable in Blender/Maya.

---

## Accuracy & limits

- **Single-view:** front is faithful; hair → smooth cap; back is guessed.
- **Multi-view:** accurate head + hair volume from all angles; texture projected from front.
- **Hair:** volume only — no strand detail (DiT model limitation). True photoreal requires Gaussian splatting.

---

## Troubleshooting

| Symptom | Fix |
|---|---|
| `venv not found` | `./avatar setup` |
| `CUDA not available` | check `nvidia-smi`; reinstall driver |
| Out of memory | use `single`, or `--resolution 512 --max-views 6` |
| Slow first run | weights downloading (~11 GB) — normal, one-time |
| Compile fails | `CUDA_HOME=/usr/local/cuda-12.4 ./avatar setup` |

More in [SETUP.md](SETUP.md).

---

## Repo layout

```
ossia-avatar/
├── avatar              # unified CLI  (setup / single / multi / mesh / doctor)
├── setup.sh            # builds venv + deps + compiles CUDA/C++ extensions
├── scripts/            # pipeline entrypoints
│   ├── _engine.py      # engine bootstrap + 2mv config auto-remap
│   ├── image2glb.py    # single → textured .glb
│   ├── image2glb_mv.py # multi-view → fused .glb
│   └── shape_only.py   # geometry-only .glb + optional renders
├── engine/             # bundled, patched Hunyuan3D 2.1 (hy3dshape + hy3dpaint)
├── web/                # embed kit: model-viewer / three.js / React Three Fiber
├── assets/             # demo images
├── examples/           # sample usage notes
└── SETUP.md  CONTRIBUTING.md  LICENSE
```

---

## License

MIT (this wrapper). Bundled Hunyuan3D engine is under the [Tencent Hunyuan Non-Commercial License](engine/LICENSE).

---

## Credits

Built on [Hunyuan3D 2.1 / 2mv](https://github.com/Tencent-Hunyuan/Hunyuan3D-2.1) by Tencent.
