# Examples

This directory contains sample outputs from the Ossia Avatar pipeline.

## Files

### Single-View (photo → avatar)

```
sample_photo.jpg          # Input: frontal portrait
sample_avatar_single.glb  # Output: textured mesh
```

Usage:

```bash
python scripts/image2glb.py examples/sample_photo.jpg -o my_avatar.glb
```

### Multi-View (4 angles → fused avatar)

```
sample_front.jpg          # Front angle
sample_left.jpg           # Left (90°)
sample_right.jpg          # Right (90°)
sample_back.jpg           # Back (180°)
sample_avatar_multiview.glb # Output: fused & textured mesh
```

Usage:

```bash
python scripts/image2glb_mv.py \
  --front examples/sample_front.jpg \
  --left examples/sample_left.jpg \
  --right examples/sample_right.jpg \
  --back examples/sample_back.jpg \
  -o my_avatar_hq.glb \
  --resolution 768 --max-views 9
```

## Viewing .glb Files

### Browser (Web)

Use a free online viewer:

- **Don McCurdy's glTF Viewer**: https://gltf-viewer.donmccurdy.com
- **Babylon.js Viewer**: https://www.babylonjs-playground.com

Just drag & drop the .glb file.

### Desktop Apps

- **Blender** (import → Assets/3D Viewport)
- **Meshlab** (File → Open)
- **ViewSTL** (free, cross-platform)
- **model-viewer** (embed in HTML)

### Three.js (Web Integration)

```html
<script src="https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js"></script>
<script src="https://cdn.jsdelivr.net/npm/three@0.128/examples/js/loaders/GLTFLoader.js"></script>
<div id="canvas"></div>

<script>
  const scene = new THREE.Scene();
  const loader = new THREE.GLTFLoader();
  loader.load('sample_avatar_multiview.glb', (gltf) => {
    scene.add(gltf.scene);
  });
</script>
```

## Quality Comparison

### Single-View

- ✓ Fast generation
- ✓ Face is accurate to input
- ✗ Back/sides are guessed
- ✗ Hair is smooth (no strand detail)

### Multi-View

- ✓ All 4 views inform geometry
- ✓ Better hair volume
- ✓ Accurate back-of-head
- ⚠️ Texture is projected from front only
- ⚠️ Takes longer (~5–8 min)

## Tips

1. **Preparing Photos for Multi-View**

   - Keep consistent lighting across all 4 angles
   - Maintain the same head tilt/rotation across views
   - Remove or minimize background clutter
   - Pre-crop to bust/shoulders (consistent framing)

2. **Post-Processing in Blender**

   - Import the .glb
   - Adjust materials (lower roughness for shinier skin)
   - Bake texture resolution if needed
   - Re-export as .glb

3. **For Web**

   - Decimate mesh to ~100k tris for fast loading
   - Use compressed textures (WebP)
   - Host .glb + textures on a CDN

4. **For 3D Printing**

   - Export geometry-only version (`scripts/shape_only.py`)
   - Check for manifold mesh in Blender/Meshlab before printing
   - Scale as needed (Hunyuan outputs ~1:1 head scale)

## Troubleshooting

**Mesh looks broken/inverted**: Check face winding order in Blender. Usually not an issue with our output.

**Texture is stretched**: This is normal for single-view (texture projected from front). Multi-view helps but front still dominates.

**File won't open**: Verify it's valid glTF (`file *.glb` should say "glTF-Binary"). Try a different viewer.

---

Have examples to share? Open an issue or PR!
