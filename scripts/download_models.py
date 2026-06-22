#!/usr/bin/env python
"""Pre-download model weights into the caches the engine expects.

- Shape models (dit-v2-1, dit-v2-mv) -> ~/.cache/hy3dgen  (where smart_load_model looks)
- Paint + DINOv2 -> default HuggingFace cache (where from_pretrained looks)
- The 2mv config is auto-remapped to the bundled engine's namespace.

Optional: first inference auto-downloads everything anyway. This just front-loads it.
"""
import os
import sys
import argparse

import _engine  # noqa: F401  (sets sys.path; provides ensure_mv_config_patched)


def main():
    ap = argparse.ArgumentParser(description="Pre-download Hunyuan3D weights")
    ap.add_argument("--mode", choices=["single", "multi", "both"], default="both")
    args = ap.parse_args()

    from huggingface_hub import snapshot_download
    hy3dgen = os.environ.get("HY3DGEN_MODELS", os.path.expanduser("~/.cache/hy3dgen"))

    if args.mode in ("single", "both"):
        print(">> shape single (dit-v2-1 + vae) -> hy3dgen cache")
        snapshot_download("tencent/Hunyuan3D-2.1",
                          allow_patterns=["hunyuan3d-dit-v2-1/*", "hunyuan3d-vae-v2-1/*"],
                          local_dir=os.path.join(hy3dgen, "tencent", "Hunyuan3D-2.1"))

    if args.mode in ("multi", "both"):
        print(">> shape multi-view (dit-v2-mv) -> hy3dgen cache")
        snapshot_download("tencent/Hunyuan3D-2mv",
                          allow_patterns=["hunyuan3d-dit-v2-mv/config.yaml",
                                          "hunyuan3d-dit-v2-mv/model.fp16.ckpt"],
                          local_dir=os.path.join(hy3dgen, "tencent", "Hunyuan3D-2mv"))
        _engine.ensure_mv_config_patched()

    print(">> paint (pbr) -> HuggingFace cache")
    snapshot_download("tencent/Hunyuan3D-2.1", allow_patterns=["hunyuan3d-paintpbr-v2-1/*"])

    print(">> DINOv2-giant -> HuggingFace cache")
    snapshot_download("facebook/dinov2-giant")

    print("\nAll models downloaded. First inference will skip the download step.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
