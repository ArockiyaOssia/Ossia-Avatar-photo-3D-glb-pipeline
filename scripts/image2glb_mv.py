#!/usr/bin/env python
"""image2glb_mv.py — MULTI-VIEW photos -> one fused textured 3D avatar (.glb).

Uses the multi-view model (tencent/Hunyuan3D-2mv, DinoImageEncoderMV) to FUSE
several calibrated views into a single mesh, then bakes PBR texture with the 2.1
painter using the front view. View tags map to fixed indices via MVImageProcessorV2:
front->0, left->1, back->2, right->3.

The 2mv config ships with the old hy3dgen.shapegen.* namespace; this script
downloads only the needed files and remaps the config to the bundled engine.
"""
import os
import sys
import argparse
import shutil

import _engine  # noqa: F401  (sets cwd + sys.path to the bundled engine)
import torch
from PIL import Image

_engine.apply_torchvision_fix()
from hy3dshape.rembg import BackgroundRemover
from hy3dshape.pipelines import Hunyuan3DDiTFlowMatchingPipeline
from textureGenPipeline import Hunyuan3DPaintPipeline, Hunyuan3DPaintConfig

MV_REPO = "tencent/Hunyuan3D-2mv"
MV_SUBFOLDER = "hunyuan3d-dit-v2-mv"
VALID_VIEWS = ["front", "left", "back", "right"]


def ensure_mv_model():
    """Download only config + ckpt for the mv model, then remap its config."""
    from huggingface_hub import snapshot_download
    base = os.environ.get("HY3DGEN_MODELS", os.path.expanduser("~/.cache/hy3dgen"))
    dst = os.path.join(base, "tencent", "Hunyuan3D-2mv")
    sub = os.path.join(dst, MV_SUBFOLDER)
    cfg, ckpt = os.path.join(sub, "config.yaml"), os.path.join(sub, "model.fp16.ckpt")
    if not (os.path.exists(cfg) and os.path.exists(ckpt)):
        print("[engine] downloading Hunyuan3D-2mv (config + ckpt) ...")
        snapshot_download(
            MV_REPO,
            allow_patterns=[f"{MV_SUBFOLDER}/config.yaml", f"{MV_SUBFOLDER}/model.fp16.ckpt"],
            local_dir=dst,
        )
    _engine.ensure_mv_config_patched()


def load_cutout(path, remover):
    image = Image.open(path).convert("RGBA")
    if image.getchannel("A").getextrema()[0] == 255:
        image = remover(image)
    return image


def generate_shape_mv(views, steps, octree_resolution):
    print(f"[2/3] fusing {len(views)} views into a 3D shape (Hunyuan3D-2mv) ...")
    ensure_mv_model()
    pipe = Hunyuan3DDiTFlowMatchingPipeline.from_pretrained(MV_REPO, subfolder=MV_SUBFOLDER)
    mesh = pipe(image=views, num_inference_steps=steps,
                octree_resolution=octree_resolution, output_type="trimesh")[0]
    del pipe
    torch.cuda.empty_cache()
    return mesh


def paint_textures(mesh_path, front_image, out_obj, max_views, resolution):
    print("[3/3] painting PBR textures (front view) ...")
    conf = Hunyuan3DPaintConfig(max_views, resolution)
    conf.realesrgan_ckpt_path = "hy3dpaint/ckpt/RealESRGAN_x4plus.pth"
    conf.multiview_cfg_path = "hy3dpaint/cfgs/hunyuan-paint-pbr.yaml"
    conf.custom_pipeline = "hy3dpaint/hunyuanpaintpbr"
    pipe = Hunyuan3DPaintPipeline(conf)
    pipe(mesh_path=mesh_path, image_path=front_image, output_mesh_path=out_obj)
    return out_obj.replace(".obj", ".glb")


def main():
    ap = argparse.ArgumentParser(description="Multi-view photos -> fused textured 3D avatar (.glb)")
    for v in VALID_VIEWS:
        ap.add_argument(f"--{v}", default=None, help=f"{v} view image")
    ap.add_argument("-o", "--out", default="avatar_mv.glb")
    ap.add_argument("--steps", type=int, default=50)
    ap.add_argument("--octree", type=int, default=384)
    ap.add_argument("--max-views", type=int, default=6)
    ap.add_argument("--resolution", type=int, default=512)
    ap.add_argument("--workdir", default=os.path.join(_engine.ENGINE, "outputs", "mv"))
    args = ap.parse_args()

    paths = {v: getattr(args, v) for v in VALID_VIEWS if getattr(args, v)}
    if "front" not in paths:
        raise SystemExit("a --front view is required (also used for texturing)")
    os.makedirs(args.workdir, exist_ok=True)

    print(f"[1/3] removing backgrounds for views: {', '.join(paths)} ...")
    remover = BackgroundRemover()
    views = {}
    for tag, p in paths.items():
        img = load_cutout(_engine.userpath(p), remover)
        img.save(os.path.join(args.workdir, f"view_{tag}.png"))
        views[tag] = img

    mesh = generate_shape_mv(views, args.steps, args.octree)
    raw_glb = os.path.join(args.workdir, "shape.glb")
    mesh.export(raw_glb)
    print(f"      fused shape -> {raw_glb}  (verts={len(mesh.vertices)}, faces={len(mesh.faces)})")

    out_obj = os.path.join(args.workdir, "textured.obj")
    glb = paint_textures(raw_glb, views["front"], out_obj, args.max_views, args.resolution)
    if not os.path.exists(glb):
        raise SystemExit(f"paint stage did not produce a GLB at {glb}")
    out_path = _engine.userpath(args.out)
    os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)
    shutil.copyfile(glb, out_path)
    print(f"\nDone. Multi-view avatar -> {out_path}  ({os.path.getsize(out_path)/1e6:.1f} MB)")


if __name__ == "__main__":
    main()
