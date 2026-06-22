# Setup

## Requirements

| | |
|---|---|
| GPU | RTX 4090 (24 GB) or ≥20 GB Ampere+ |
| CUDA toolkit | 12.1 or 12.4 (for compiling extensions) — `nvcc --version` |
| NVIDIA driver | 590+ — `nvidia-smi` |
| Python | 3.10 |
| Disk | ~25 GB free (weights + venv + scratch) |
| OS | Linux (Ubuntu 20.04+, WSL2) |

## Install

```bash
cd ossia-avatar
./avatar setup
```

`./avatar setup` (= `setup.sh`) does everything:

1. Creates `venv/` with Python 3.10
2. Installs PyTorch 2.5.1 (CUDA 12.4) + dependencies
3. Compiles the bundled engine's CUDA (`custom_rasterizer`) + C++ (mesh painter) extensions
4. Fetches the RealESRGAN checkpoint

Takes ~10 min. If your CUDA toolkit is elsewhere:

```bash
CUDA_HOME=/usr/local/cuda-12.4 ./avatar setup
```

## Verify

```bash
./avatar doctor
```

Expected:

```
torch        : 2.5.1+cu124
cuda available: True
gpu          : NVIDIA GeForce RTX 4090
engine       : present
realesrgan   : present
custom_raster: built
```

## First Run

```bash
./avatar single engine/assets/demo.png -o test.glb
```

First inference downloads model weights (~11 GB) to `~/.cache`. This is one-time; later runs are fast. Open `test.glb` in any glTF viewer.

## Troubleshooting

**`venv not found`** — run `./avatar setup`.

**`CUDA not available`** — check `nvidia-smi`. Reinstall the NVIDIA driver if it fails.

**Compile fails (`custom_rasterizer` / nvcc)** — ensure a CUDA toolkit is installed and pass it explicitly:
```bash
ls /usr/local/cuda*/bin/nvcc          # find it
CUDA_HOME=/usr/local/cuda-12.1 ./avatar setup
```

**`No space left on device` during setup** — free disk (need ~25 GB). The deps build is heavy; check `df -h /`.

**`custom_rasterizer has no attribute 'rasterize'` / `libc10.so`** — the CUDA extension didn't build. Re-run:
```bash
CUDA_HOME=/usr/local/cuda-12.1 \
  venv/bin/pip install --no-build-isolation -e engine/hy3dpaint/custom_rasterizer
```

**Out of memory** — use `single` (not `multi`), or lower `--resolution 512 --max-views 6`.

**Slow first run** — weights downloading (~11 GB), one-time.

## Moving / Sharing

The venv is not relocatable — if you move the repo, re-run `./avatar setup`.
Model weights live in `~/.cache/hy3dgen` and `~/.cache/huggingface`; back those up to avoid re-downloading.

## Docker (optional)

```dockerfile
FROM nvidia/cuda:12.4.1-cudnn-devel-ubuntu22.04
RUN apt-get update && apt-get install -y python3.10 python3.10-venv git build-essential wget
COPY . /app
WORKDIR /app
RUN ./avatar setup
ENTRYPOINT ["./avatar"]
```

```bash
docker build -t ossia-avatar .
docker run --gpus all -v $(pwd)/io:/app/io ossia-avatar single io/photo.jpg -o io/avatar.glb
```
