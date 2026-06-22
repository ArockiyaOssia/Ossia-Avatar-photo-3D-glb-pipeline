#!/usr/bin/env python
"""shape_only.py — single image -> untextured geometry mesh (.glb) + white/wireframe renders."""
import os
import sys
import argparse
import math

import _engine  # noqa: F401  (sets cwd + sys.path to the bundled engine)
import numpy as np
import torch
import trimesh
from PIL import Image

_engine.apply_torchvision_fix()
from hy3dshape.rembg import BackgroundRemover
from hy3dshape.pipelines import Hunyuan3DDiTFlowMatchingPipeline


def main():
    ap = argparse.ArgumentParser(description="Single image -> geometry mesh (.glb), no texture")
    ap.add_argument("image")
    ap.add_argument("-o", "--out", default="mesh.glb")
    ap.add_argument("--steps", type=int, default=50)
    ap.add_argument("--octree", type=int, default=512)
    ap.add_argument("--render", action="store_true", help="also write clay + wireframe PNGs")
    ap.add_argument("--workdir", default=os.path.join(_engine.ENGINE, "outputs", "shape"))
    a = ap.parse_args()
    os.makedirs(a.workdir, exist_ok=True)
    out_path = _engine.userpath(a.out)

    img = Image.open(_engine.userpath(a.image)).convert("RGBA")
    if img.getchannel("A").getextrema()[0] == 255:
        print("[1/3] removing background ...")
        img = BackgroundRemover()(img)

    print("[2/3] generating shape ...")
    pipe = Hunyuan3DDiTFlowMatchingPipeline.from_pretrained("tencent/Hunyuan3D-2.1")
    mesh = pipe(image=img, num_inference_steps=a.steps, octree_resolution=a.octree,
                output_type="trimesh")[0]
    del pipe
    torch.cuda.empty_cache()
    geom = trimesh.Trimesh(vertices=mesh.vertices, faces=mesh.faces, process=False)
    os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)
    geom.export(out_path)
    print(f"      mesh -> {out_path}  verts={len(geom.vertices)} faces={len(geom.faces)}")

    if not a.render:
        print("Done.")
        return

    print("[3/3] rendering clay + wireframe ...")
    os.environ["PYOPENGL_PLATFORM"] = "egl"
    import open3d as o3d
    m = o3d.io.read_triangle_mesh(out_path)
    m.compute_vertex_normals()
    bb = m.get_axis_aligned_bounding_box()
    c, ext = bb.get_center(), float(np.max(bb.get_extent()))
    r = o3d.visualization.rendering.OffscreenRenderer(800, 800)
    r.scene.set_background([1, 1, 1, 1])
    mat = o3d.visualization.rendering.MaterialRecord()
    mat.shader = "defaultLit"
    r.scene.add_geometry("m", m, mat)
    ls = o3d.geometry.LineSet.create_from_triangle_mesh(m)
    ls.paint_uniform_color([0.1, 0.1, 0.12])
    wr = o3d.visualization.rendering.OffscreenRenderer(800, 800)
    wr.scene.set_background([1, 1, 1, 1])
    wmat = o3d.visualization.rendering.MaterialRecord()
    wmat.shader, wmat.line_width = "unlitLine", 0.6
    wr.scene.add_geometry("w", ls, wmat)
    for name, ang in [("front", 0), ("side", 75)]:
        aa = math.radians(ang)
        eye = [c[0] + ext * 1.9 * math.sin(aa), c[1] + ext * 0.1, c[2] + ext * 1.9 * math.cos(aa)]
        r.setup_camera(45.0, c, eye, [0, 1, 0])
        o3d.io.write_image(f"{a.workdir}/clay_{name}.png", r.render_to_image())
        wr.setup_camera(45.0, c, eye, [0, 1, 0])
        o3d.io.write_image(f"{a.workdir}/wire_{name}.png", wr.render_to_image())
        print("rendered", name)
    print(f"Done. Renders in {a.workdir}")


if __name__ == "__main__":
    main()
