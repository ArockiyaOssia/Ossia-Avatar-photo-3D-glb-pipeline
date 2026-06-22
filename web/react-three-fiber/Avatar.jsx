"use client";
// Drop-in React Three Fiber avatar for Next.js / React portfolios.
//
// 1. npm i three @react-three/fiber @react-three/drei
// 2. Put your exported avatar at  public/avatar.glb
//    (textured)  and/or  public/avatar_mesh.glb  (geometry-only, for wireframe)
// 3. <Avatar src="/avatar.glb" />            // textured, auto-rotates, drag to orbit
//    <Avatar src="/avatar_mesh.glb" wireframe />   // wireframe "hologram" look
//
// See ../README.md for full integration notes.

import { Suspense, useEffect, useRef } from "react";
import { Canvas } from "@react-three/fiber";
import { useGLTF, OrbitControls, Stage, Html } from "@react-three/drei";

function Model({ src, wireframe = false, color = "#9bd3ff" }) {
  const { scene } = useGLTF(src);
  const ref = useRef();

  useEffect(() => {
    scene.traverse((o) => {
      if (!o.isMesh) return;
      o.castShadow = o.receiveShadow = true;
      if (wireframe && o.material) {
        o.material.wireframe = true;
        if (o.material.color) o.material.color.set(color);
        o.material.metalness = 0.0;
        o.material.roughness = 1.0;
      }
    });
  }, [scene, wireframe, color]);

  return <primitive ref={ref} object={scene} />;
}

export default function Avatar({
  src = "/avatar.glb",
  wireframe = false,
  autoRotate = true,
  height = 520,
}) {
  return (
    <Canvas
      shadows
      camera={{ position: [0, 0.1, 2.6], fov: 35 }}
      style={{ width: "100%", height }}
      dpr={[1, 2]}
    >
      <Suspense fallback={<Html center>loading avatar…</Html>}>
        <Stage environment="city" intensity={0.5} adjustCamera={1.1}>
          <Model src={src} wireframe={wireframe} />
        </Stage>
      </Suspense>
      <OrbitControls
        enablePan={false}
        autoRotate={autoRotate}
        autoRotateSpeed={1.2}
        minPolarAngle={Math.PI / 3}
        maxPolarAngle={Math.PI / 1.8}
      />
    </Canvas>
  );
}

// Preload so the hero pops in fast.
useGLTF.preload("/avatar.glb");
