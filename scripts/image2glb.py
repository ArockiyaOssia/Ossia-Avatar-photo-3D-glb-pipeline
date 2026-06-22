#!/usr/bin/env python
"""image2glb.py — single photo -> textured 3D avatar (.glb).

Shape (flow-matching DiT) then PBR paint, run sequentially so peak VRAM stays
under ~24 GB. Engine is the bundled Hunyuan3D under ../engine.
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

MODEL_REPO = "tencent/Hunyuan3D-2.1"


def preprocess(image_path):
    image = Image.open(image_path).convert("RGBA")
    if image.getchannel("A").getextrema()[0] == 255:
        print("[1/3] removing background ...")
        image = BackgroundRemover()(image)
    else:
        print("[1/3] input already has an alpha cutout; keeping it")
    return image


def generate_shape(image, steps, octree_resolution):
    print("[2/3] generating 3D shape (flow-matching DiT) ...")
    pipe = Hunyuan3DDiTFlowMatchingPipeline.from_pretrained(MODEL_REPO)
    mesh = pipe(image=image, num_inference_steps=steps,
                octree_resolution=octree_resolution, output_type="trimesh")[0]
    del pipe
    torch.cuda.empty_cache()
    return mesh


def paint_textures(mesh_path, image, out_obj, max_views, resolution):
    print("[3/3] painting PBR textures ...")
    conf = Hunyuan3DPaintConfig(max_views, resolution)
    conf.realesrgan_ckpt_path = "hy3dpaint/ckpt/RealESRGAN_x4plus.pth"
    conf.multiview_cfg_path = "hy3dpaint/cfgs/hunyuan-paint-pbr.yaml"
    conf.custom_pipeline = "hy3dpaint/hunyuanpaintpbr"
    pipe = Hunyuan3DPaintPipeline(conf)
    pipe(mesh_path=mesh_path, image_path=image, output_mesh_path=out_obj)
    return out_obj.replace(".obj", ".glb")


def main():
    ap = argparse.ArgumentParser(description="Single photo -> textured 3D avatar (.glb)")
    ap.add_argument("image")
    ap.add_argument("-o", "--out", default="avatar.glb")
    ap.add_argument("--steps", type=int, default=50)
    ap.add_argument("--octree", type=int, default=384)
    ap.add_argument("--max-views", type=int, default=6)
    ap.add_argument("--resolution", type=int, default=512)
    ap.add_argument("--workdir", default=os.path.join(_engine.ENGINE, "outputs"))
    args = ap.parse_args()

    img_path = _engine.userpath(args.image)
    out_path = _engine.userpath(args.out)
    os.makedirs(args.workdir, exist_ok=True)

    image = preprocess(img_path)
    image.save(os.path.join(args.workdir, "input_rgba.png"))

    mesh = generate_shape(image, args.steps, args.octree)
    raw_glb = os.path.join(args.workdir, "shape.glb")
    mesh.export(raw_glb)
    print(f"      shape -> {raw_glb}  (verts={len(mesh.vertices)}, faces={len(mesh.faces)})")

    out_obj = os.path.join(args.workdir, "textured.obj")
    glb = paint_textures(raw_glb, image, out_obj, args.max_views, args.resolution)
    if not os.path.exists(glb):
        raise SystemExit(f"paint stage did not produce a GLB at {glb}")
    os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)
    shutil.copyfile(glb, out_path)
    print(f"\nDone. Textured avatar -> {out_path}  ({os.path.getsize(out_path)/1e6:.1f} MB)")


if __name__ == "__main__":
    main()
