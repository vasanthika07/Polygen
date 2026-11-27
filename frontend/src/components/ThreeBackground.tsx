import React, { useEffect, useRef } from 'react';
import * as THREE from 'three';

/**
 * PolyGen Interactive 3D Ambient WebGL Background System
 * 
 * Provides hardware-accelerated ambient 3D geometric visualization:
 * - Dual-gimbal rotating 3D wireframe polyhedra (Icosahedron & Octahedron)
 * - Secondary floating polyhedral crystals (Dodecahedron, Tetrahedron, Octahedron)
 * - Dynamic 3D cyber terrain grid with undulating vertex waves
 * - Deep-space glowing particle constellation with additive blending
 * - Interactive mouse parallax & gyroscopic camera tracking
 * - Non-blocking execution (pointer-events: none, z-index: 0, 60fps)
 */
export const ThreeBackground: React.FC = () => {
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const container = containerRef.current;
    if (!container) return;

    // Create fixed background canvas
    const canvas = document.createElement('canvas');
    canvas.className = 'fixed inset-0 w-full h-full pointer-events-none z-0';
    canvas.style.opacity = '0.55';
    canvas.style.transition = 'opacity 1.2s ease-in-out';
    container.appendChild(canvas);

    let renderer: THREE.WebGLRenderer;
    try {
      renderer = new THREE.WebGLRenderer({
        canvas,
        alpha: true,
        antialias: true,
        powerPreference: 'high-performance',
      });
    } catch (e) {
      console.warn('WebGL not supported for ThreeBackground:', e);
      return;
    }

    renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 2));
    renderer.setSize(window.innerWidth, window.innerHeight);

    const scene = new THREE.Scene();
    const camera = new THREE.PerspectiveCamera(55, window.innerWidth / window.innerHeight, 0.1, 1000);
    camera.position.z = 28;

    // 1. Central Complex (Icosahedron + Octahedron + Pulsing Core)
    const centralGroup = new THREE.Group();

    const icoGeom = new THREE.IcosahedronGeometry(7.5, 1);
    const icoMat = new THREE.MeshBasicMaterial({
      color: 0x38bdf8,
      wireframe: true,
      transparent: true,
      opacity: 0.32,
    });
    const icoMesh = new THREE.Mesh(icoGeom, icoMat);
    centralGroup.add(icoMesh);

    const octGeom = new THREE.OctahedronGeometry(4.8, 0);
    const octMat = new THREE.MeshBasicMaterial({
      color: 0xa855f7,
      wireframe: true,
      transparent: true,
      opacity: 0.45,
    });
    const octMesh = new THREE.Mesh(octGeom, octMat);
    centralGroup.add(octMesh);

    const coreGeom = new THREE.SphereGeometry(1.6, 16, 16);
    const coreMat = new THREE.MeshBasicMaterial({
      color: 0x60a5fa,
      wireframe: true,
      transparent: true,
      opacity: 0.55,
    });
    const coreMesh = new THREE.Mesh(coreGeom, coreMat);
    centralGroup.add(coreMesh);

    centralGroup.position.set(11, 2.5, -4);
    scene.add(centralGroup);

    // 2. Secondary Floating Polyhedral Crystals in background
    const crystalGroup = new THREE.Group();
    const crystalConfigs = [
      { geom: new THREE.DodecahedronGeometry(2.5, 0), pos: [-16, 9, -12], color: 0x818cf8, speed: 0.01 },
      { geom: new THREE.OctahedronGeometry(2.0, 0), pos: [-18, -8, -8], color: 0x38bdf8, speed: -0.012 },
      { geom: new THREE.IcosahedronGeometry(2.8, 0), pos: [19, -9, -14], color: 0xc084fc, speed: 0.009 },
      { geom: new THREE.TetrahedronGeometry(1.8, 0), pos: [5, 13, -10], color: 0x22d3ee, speed: -0.015 },
    ];

    const crystalMeshes: { mesh: THREE.Mesh; speed: number }[] = [];
    crystalConfigs.forEach((cfg) => {
      const cMat = new THREE.MeshBasicMaterial({
        color: cfg.color,
        wireframe: true,
        transparent: true,
        opacity: 0.28,
      });
      const cMesh = new THREE.Mesh(cfg.geom, cMat);
      cMesh.position.set(cfg.pos[0] as number, cfg.pos[1] as number, cfg.pos[2] as number);
      crystalGroup.add(cMesh);
      crystalMeshes.push({ mesh: cMesh, speed: cfg.speed });
    });
    scene.add(crystalGroup);

    // 3. Cybernetic Undulating Terrain Grid (Floor)
    const planeGeom = new THREE.PlaneGeometry(90, 90, 28, 28);
    planeGeom.rotateX(-Math.PI / 2.3);
    const planeMat = new THREE.MeshBasicMaterial({
      color: 0x1e3a8a,
      wireframe: true,
      transparent: true,
      opacity: 0.22,
    });
    const planeMesh = new THREE.Mesh(planeGeom, planeMat);
    planeMesh.position.set(0, -14, -8);
    scene.add(planeMesh);
    const planePositions = planeGeom.attributes.position;

    // 4. Glowing Particle Constellation Field
    const particleCount = 450;
    const particleGeom = new THREE.BufferGeometry();
    const particlePos = new Float32Array(particleCount * 3);
    const particleColors = new Float32Array(particleCount * 3);

    for (let p = 0; p < particleCount; p++) {
      particlePos[p * 3] = (Math.random() - 0.5) * 85;
      particlePos[p * 3 + 1] = (Math.random() - 0.5) * 65;
      particlePos[p * 3 + 2] = (Math.random() - 0.5) * 60 - 5;

      const isCyan = Math.random() > 0.45;
      particleColors[p * 3] = isCyan ? 0.22 : 0.65;
      particleColors[p * 3 + 1] = isCyan ? 0.74 : 0.33;
      particleColors[p * 3 + 2] = isCyan ? 0.97 : 0.96;
    }

    particleGeom.setAttribute('position', new THREE.BufferAttribute(particlePos, 3));
    particleGeom.setAttribute('color', new THREE.BufferAttribute(particleColors, 3));

    // Dynamic radial glow circle texture
    const pCanvas = document.createElement('canvas');
    pCanvas.width = 32;
    pCanvas.height = 32;
    const pCtx = pCanvas.getContext('2d');
    if (pCtx) {
      const grad = pCtx.createRadialGradient(16, 16, 0, 16, 16, 16);
      grad.addColorStop(0, 'rgba(255, 255, 255, 1)');
      grad.addColorStop(0.3, 'rgba(56, 189, 248, 0.9)');
      grad.addColorStop(0.7, 'rgba(168, 85, 247, 0.4)');
      grad.addColorStop(1, 'rgba(0, 0, 0, 0)');
      pCtx.fillStyle = grad;
      pCtx.fillRect(0, 0, 32, 32);
    }

    const pTexture = new THREE.CanvasTexture(pCanvas);
    const particleMat = new THREE.PointsMaterial({
      size: 1.4,
      map: pTexture,
      vertexColors: true,
      transparent: true,
      blending: THREE.AdditiveBlending,
      depthWrite: false,
    });
    const particleSystem = new THREE.Points(particleGeom, particleMat);
    scene.add(particleSystem);

    // 5. Interactive Mouse Parallax Tracking
    let mouseX = 0;
    let mouseY = 0;
    let targetX = 0;
    let targetY = 0;

    const handleMouseMove = (e: MouseEvent) => {
      targetX = (e.clientX - window.innerWidth / 2) * 0.00045;
      targetY = (e.clientY - window.innerHeight / 2) * 0.00045;
    };

    const handleResize = () => {
      const w = window.innerWidth;
      const h = window.innerHeight;
      camera.aspect = w / h;
      camera.updateProjectionMatrix();
      renderer.setSize(w, h);
    };

    window.addEventListener('mousemove', handleMouseMove, { passive: true });
    window.addEventListener('resize', handleResize, { passive: true });

    // 6. Animation Loop
    const clock = new THREE.Clock();
    let animId: number;

    const render = () => {
      const elapsed = clock.getElapsedTime();

      mouseX += (targetX - mouseX) * 0.04;
      mouseY += (targetY - mouseY) * 0.04;

      camera.position.x = 28 * Math.sin(mouseX);
      camera.position.y = mouseY * 12;
      camera.lookAt(0, 0, 0);

      centralGroup.rotation.y = elapsed * 0.15;
      centralGroup.rotation.x = Math.sin(elapsed * 0.1) * 0.25;

      icoMesh.rotation.y = elapsed * 0.2;
      icoMesh.rotation.z = elapsed * 0.1;

      octMesh.rotation.y = -elapsed * 0.25;
      octMesh.rotation.x = elapsed * 0.15;

      const pulse = 1.0 + Math.sin(elapsed * 2.0) * 0.12;
      coreMesh.scale.set(pulse, pulse, pulse);

      crystalMeshes.forEach((item) => {
        item.mesh.rotation.x += item.speed;
        item.mesh.rotation.y += item.speed * 1.5;
      });

      const posArr = planePositions.array as Float32Array;
      for (let i = 0; i < posArr.length; i += 3) {
        const vx = posArr[i];
        const vy = posArr[i + 1];
        posArr[i + 2] = Math.sin(vx * 0.18 + elapsed * 1.2) * Math.cos(vy * 0.18 + elapsed * 1.2) * 1.4;
      }
      planePositions.needsUpdate = true;

      particleSystem.rotation.y = elapsed * 0.03;
      particleSystem.rotation.x = Math.sin(elapsed * 0.02) * 0.05;

      renderer.render(scene, camera);
      animId = requestAnimationFrame(render);
    };

    render();

    // Clean up Three.js WebGL resources on unmount
    return () => {
      cancelAnimationFrame(animId);
      window.removeEventListener('mousemove', handleMouseMove);
      window.removeEventListener('resize', handleResize);
      renderer.dispose();
      icoGeom.dispose();
      icoMat.dispose();
      octGeom.dispose();
      octMat.dispose();
      coreGeom.dispose();
      coreMat.dispose();
      planeGeom.dispose();
      planeMat.dispose();
      particleGeom.dispose();
      particleMat.dispose();
      pTexture.dispose();
      if (canvas.parentNode) {
        canvas.parentNode.removeChild(canvas);
      }
    };
  }, []);

  return (
    <div
      ref={containerRef}
      className="fixed inset-0 pointer-events-none z-0 overflow-hidden"
      aria-hidden="true"
    />
  );
};
