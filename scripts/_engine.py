"""Shared engine bootstrap for Ossia Avatar scripts.

Resolves the bundled Hunyuan3D engine (../engine), puts it on sys.path, switches
the working directory into it (paint configs use engine-relative paths), and
applies the torchvision compatibility shim. Also exposes a helper that repairs
the Hunyuan3D-2mv config (whose published `target:` paths use the old
`hy3dgen.shapegen.*` namespace) to this engine's `hy3dshape.*` classes.
"""
import os
import sys

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.dirname(SCRIPT_DIR)
ENGINE = os.environ.get("OSSIA_ENGINE", os.path.join(REPO_ROOT, "engine"))

if not os.path.isdir(os.path.join(ENGINE, "hy3dshape")):
    sys.exit(f"engine not found at {ENGINE}. Run setup.sh, or set OSSIA_ENGINE.")

# Capture where the user invoked us, BEFORE switching into the engine dir, so
# relative input/output paths still resolve against the caller's location.
ORIG_CWD = os.getcwd()

os.chdir(ENGINE)
sys.path.insert(0, os.path.join(ENGINE, "hy3dpaint"))
sys.path.insert(0, os.path.join(ENGINE, "hy3dshape"))
sys.path.insert(0, ENGINE)  # torchvision_fix.py lives at the engine root


def userpath(p):
    """Resolve a user-supplied path against the original CWD (not the engine dir)."""
    return p if os.path.isabs(p) else os.path.normpath(os.path.join(ORIG_CWD, p))


def apply_torchvision_fix():
    try:
        from torchvision_fix import apply_fix
        apply_fix()
    except Exception as exc:  # noqa: BLE001
        print(f"[warn] torchvision_fix not applied: {exc}")


# Map the 2.0-era namespace in the published 2mv config to this engine's classes.
_MV_TARGET_REMAP = {
    "hy3dgen.shapegen.models.Hunyuan3DDiT": "hy3dshape.models.denoisers.hunyuan3ddit.Hunyuan3DDiT",
    "hy3dgen.shapegen.models.ShapeVAE": "hy3dshape.models.autoencoders.ShapeVAE",
    "hy3dgen.shapegen.models.SingleImageEncoder": "hy3dshape.models.conditioner.SingleImageEncoder",
    "hy3dgen.shapegen.schedulers.FlowMatchEulerDiscreteScheduler": "hy3dshape.schedulers.FlowMatchEulerDiscreteScheduler",
    "hy3dgen.shapegen.preprocessors.MVImageProcessorV2": "hy3dshape.preprocessors.MVImageProcessorV2",
    "hy3dgen.shapegen.pipelines.Hunyuan3DDiTFlowMatchingPipeline": "hy3dshape.pipelines.Hunyuan3DDiTFlowMatchingPipeline",
}


def ensure_mv_config_patched():
    """Rewrite the cached Hunyuan3D-2mv config targets to this engine, if needed.

    Safe to call repeatedly; only writes when the old namespace is present. Runs
    before from_pretrained so a freshly downloaded config loads correctly.
    """
    base = os.environ.get("HY3DGEN_MODELS", os.path.expanduser("~/.cache/hy3dgen"))
    cfg = os.path.join(base, "tencent/Hunyuan3D-2mv/hunyuan3d-dit-v2-mv/config.yaml")
    if not os.path.exists(cfg):
        return  # not downloaded yet; from_pretrained will fetch, then this runs again
    text = open(cfg).read()
    if "hy3dgen.shapegen" not in text:
        return
    if not os.path.exists(cfg + ".orig"):
        open(cfg + ".orig", "w").write(text)
    for old, new in _MV_TARGET_REMAP.items():
        text = text.replace(old, new)
    open(cfg, "w").write(text)
    print("[engine] remapped Hunyuan3D-2mv config to hy3dshape namespace")
