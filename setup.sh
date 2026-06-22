#!/usr/bin/env bash
# Ossia Avatar — one-time setup. Builds venv, installs deps, compiles the bundled
# engine's CUDA/C++ extensions, and ensures the RealESRGAN checkpoint.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ENGINE="$ROOT/engine"
VENV="$ROOT/venv"
PY="$VENV/bin/python"
PIP="$VENV/bin/pip"

# CUDA toolkit for compiling extensions (override with CUDA_HOME=... ./setup.sh)
: "${CUDA_HOME:=$(ls -d /usr/local/cuda-12.1 /usr/local/cuda-12.4 /usr/local/cuda 2>/dev/null | head -1)}"
export CUDA_HOME PATH="$CUDA_HOME/bin:$PATH" TORCH_CUDA_ARCH_LIST="${TORCH_CUDA_ARCH_LIST:-8.9}"

echo "================ Ossia Avatar Setup ================"
echo "engine    : $ENGINE"
echo "CUDA_HOME : ${CUDA_HOME:-<not found>}"

echo "[1/6] Python 3.10 venv ..."
PY310="$(command -v python3.10 || command -v python3)"
"$PY310" -m venv "$VENV"
"$PIP" install -q -U pip wheel 'setuptools<70'
"$PY" --version

echo "[2/6] PyTorch 2.5.1 (CUDA 12.4) ..."
"$PIP" install -q --no-cache-dir torch==2.5.1 torchvision==0.20.1 torchaudio==2.5.1 \
    --index-url https://download.pytorch.org/whl/cu124
"$PY" -c "import torch; assert torch.cuda.is_available(); print('  CUDA OK:', torch.cuda.get_device_name(0))"

echo "[3/6] Python dependencies ..."
# --no-build-isolation: build basicsr/deepspeed against the torch we just installed,
# instead of pulling a second (huge) torch+CUDA stack into an isolated build env.
"$PIP" install -q --no-cache-dir --no-build-isolation -r "$ENGINE/requirements.local.txt"

echo "[4/6] Compile custom_rasterizer (CUDA) ..."
( cd "$ENGINE/hy3dpaint/custom_rasterizer" && "$PIP" install -q --no-cache-dir --no-build-isolation -e . )

echo "[5/6] Compile mesh painter (C++) ..."
( cd "$ENGINE/hy3dpaint/DifferentiableRenderer"
  SUFFIX="$("$PY" -c 'import sysconfig; print(sysconfig.get_config_var("EXT_SUFFIX"))')"
  rm -f mesh_inpaint_processor.cpython-*.so
  c++ -O3 -Wall -shared -std=c++11 -fPIC \
      $("$PY" -m pybind11 --includes) $("$PY"-config --includes 2>/dev/null || true) \
      $("$PY" -c 'import sysconfig; print("-I"+sysconfig.get_path("include"))') \
      mesh_inpaint_processor.cpp -o "mesh_inpaint_processor${SUFFIX}" )

echo "[6/6] RealESRGAN checkpoint ..."
CKPT="$ENGINE/hy3dpaint/ckpt/RealESRGAN_x4plus.pth"
if [ ! -f "$CKPT" ]; then
  mkdir -p "$ENGINE/hy3dpaint/ckpt"
  wget -q --show-progress \
    https://github.com/xinntao/Real-ESRGAN/releases/download/v0.1.0/RealESRGAN_x4plus.pth \
    -O "$CKPT"
fi

echo "[verify] imports ..."
"$PY" - <<'PYV'
import sys, os
root = os.path.dirname(os.path.abspath("setup.sh"))
sys.path.insert(0, os.path.join(os.getcwd(), "engine", "hy3dpaint"))
import torch, custom_rasterizer  # noqa
print("  torch", torch.__version__, "| cuda", torch.cuda.is_available(), "| custom_rasterizer OK")
PYV

cat <<'EOF'

================ Setup complete ================

Next:
  ./avatar single  photo.jpg -o avatar.glb
  ./avatar multi   --front f.jpg --left l.jpg --right r.jpg --back b.jpg -o avatar_hq.glb
  ./avatar mesh    photo.jpg -o mesh.glb --render
  ./avatar doctor

First run downloads model weights (~11 GB, cached afterward).
EOF
