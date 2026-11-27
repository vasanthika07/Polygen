"""
PolyGen – Interactive 3D Ambient WebGL Background System
Provides Three.js and Canvas 3D hardware-accelerated ambient background effects
for Streamlit and Gradio dashboards.

Features:
- Rotating dual-gimbal 3D wireframe polyhedra (Icosahedron & Octahedron)
- Dynamic 3D cybernetic terrain grid with undulating vertex waves
- Deep-space glowing particle constellation with additive blending
- Real-time mouse parallax & gyroscopic camera tracking
- Non-blocking execution (pointer-events: none, z-index: 0, 60fps low-overhead)
- Offline-resilient fallback with native 3D perspective projection
"""

def get_3d_background_script() -> str:
    """Returns the production-grade WebGL Three.js background engine script."""
    return """
<script>
(function() {
    var win = window;
    var doc = document;
    try {
        if (window.parent && window.parent.document) {
            doc = window.parent.document;
            win = window.parent;
        }
    } catch(e) {
        win = window;
        doc = document;
    }

    var CANVAS_ID = "polygen-ambient-3d-canvas";

    function startEngine() {
        if (doc.getElementById(CANVAS_ID)) {
            return;
        }

        var canvas = doc.createElement("canvas");
        canvas.id = CANVAS_ID;
        canvas.style.position = "fixed";
        canvas.style.top = "0";
        canvas.style.left = "0";
        canvas.style.width = "100vw";
        canvas.style.height = "100vh";
        canvas.style.zIndex = "0";
        canvas.style.pointerEvents = "none";
        canvas.style.opacity = "0.55";
        canvas.style.transition = "opacity 1.5s ease-in-out";

        if (doc.body) {
            doc.body.insertBefore(canvas, doc.body.firstChild);
        } else {
            return;
        }

        // ---------------------------------------------------------------------
        // Native 3D Perspective Projection Engine (Runs if Three.js unavailable)
        // ---------------------------------------------------------------------
        function runNative3DFallback() {
            var ctx = canvas.getContext("2d");
            if (!ctx) return;

            var width = canvas.width = win.innerWidth || 1280;
            var height = canvas.height = win.innerHeight || 800;
            var fov = 400;
            var mouseX = 0, mouseY = 0, targetMouseX = 0, targetMouseY = 0;

            win.addEventListener("mousemove", function(e) {
                targetMouseX = (e.clientX - width / 2) * 0.0005;
                targetMouseY = (e.clientY - height / 2) * 0.0005;
            }, { passive: true });

            win.addEventListener("resize", function() {
                width = canvas.width = win.innerWidth || 1280;
                height = canvas.height = win.innerHeight || 800;
            }, { passive: true });

            // Generate 3D Particles
            var numParticles = 120;
            var particles = [];
            for (var i = 0; i < numParticles; i++) {
                particles.push({
                    x: (Math.random() - 0.5) * 1200,
                    y: (Math.random() - 0.5) * 800,
                    z: (Math.random() - 0.5) * 1000 + 400,
                    vx: (Math.random() - 0.5) * 0.5,
                    vy: (Math.random() - 0.5) * 0.5,
                    vz: (Math.random() - 0.5) * 0.5,
                    hue: Math.random() > 0.5 ? "56, 189, 248" : "168, 85, 247"
                });
            }

            // Icosahedron Vertices for Central Polyhedron
            var phi = (1 + Math.sqrt(5)) / 2;
            var scale = 140;
            var icoRaw = [
                [-1, phi, 0], [1, phi, 0], [-1, -phi, 0], [1, -phi, 0],
                [0, -1, phi], [0, 1, phi], [0, -1, -phi], [0, 1, -phi],
                [phi, 0, -1], [phi, 0, 1], [-phi, 0, -1], [-phi, 0, 1]
            ];
            var icoVerts = icoRaw.map(function(v) {
                return { x: v[0] * scale, y: v[1] * scale, z: v[2] * scale };
            });

            var rotX = 0, rotY = 0;

            function animate() {
                ctx.clearRect(0, 0, width, height);

                mouseX += (targetMouseX - mouseX) * 0.05;
                mouseY += (targetMouseY - mouseY) * 0.05;
                rotX += 0.006 + mouseY;
                rotY += 0.008 + mouseX;

                var cx = width * 0.72;
                var cy = height * 0.45;

                // Draw Central 3D Icosahedron
                var projected = icoVerts.map(function(v) {
                    var cosY = Math.cos(rotY), sinY = Math.sin(rotY);
                    var x1 = v.x * cosY + v.z * sinY;
                    var z1 = -v.x * sinY + v.z * cosY;

                    var cosX = Math.cos(rotX), sinX = Math.sin(rotX);
                    var y2 = v.y * cosX - z1 * sinX;
                    var z2 = v.y * sinX + z1 * cosX + 600;

                    var scaleProj = fov / Math.max(10, z2);
                    return {
                        x: cx + x1 * scaleProj,
                        y: cy + y2 * scaleProj,
                        z: z2,
                        scale: scaleProj
                    };
                });

                ctx.lineWidth = 1.2;
                for (var i = 0; i < projected.length; i++) {
                    for (var j = i + 1; j < projected.length; j++) {
                        var dx = icoVerts[i].x - icoVerts[j].x;
                        var dy = icoVerts[i].y - icoVerts[j].y;
                        var dz = icoVerts[i].z - icoVerts[j].z;
                        var d = Math.sqrt(dx * dx + dy * dy + dz * dz);
                        if (d < scale * 2.2) {
                            ctx.strokeStyle = "rgba(56, 189, 248, 0.35)";
                            ctx.beginPath();
                            ctx.moveTo(projected[i].x, projected[i].y);
                            ctx.lineTo(projected[j].x, projected[j].y);
                            ctx.stroke();
                        }
                    }
                    ctx.fillStyle = "rgba(168, 85, 247, 0.8)";
                    ctx.beginPath();
                    ctx.arc(projected[i].x, projected[i].y, 3 * projected[i].scale, 0, Math.PI * 2);
                    ctx.fill();
                }

                // Draw Floating Particles
                for (var p = 0; p < particles.length; p++) {
                    var pt = particles[p];
                    pt.x += pt.vx;
                    pt.y += pt.vy;
                    pt.z += pt.vz;
                    if (pt.z < 50) pt.z = 1000;
                    if (pt.z > 1000) pt.z = 50;

                    var pScale = fov / pt.z;
                    var px = (width / 2) + pt.x * pScale;
                    var py = (height / 2) + pt.y * pScale;

                    if (px >= 0 && px <= width && py >= 0 && py <= height) {
                        var alpha = (1 - pt.z / 1000) * 0.7;
                        ctx.fillStyle = "rgba(" + pt.hue + ", " + alpha + ")";
                        ctx.beginPath();
                        ctx.arc(px, py, Math.max(1, 2.5 * pScale), 0, Math.PI * 2);
                        ctx.fill();
                    }
                }

                win.requestAnimationFrame(animate);
            }
            win.requestAnimationFrame(animate);
        }

        // ---------------------------------------------------------------------
        // Three.js Hardware-Accelerated 3D WebGL Engine
        // ---------------------------------------------------------------------
        function initThreeScene() {
            var THREE = win.THREE;
            if (!THREE) {
                runNative3DFallback();
                return;
            }

            try {
                var renderer = new THREE.WebGLRenderer({
                    canvas: canvas,
                    alpha: true,
                    antialias: true,
                    powerPreference: "high-performance"
                });
                renderer.setPixelRatio(Math.min(win.devicePixelRatio || 1, 2));
                renderer.setSize(win.innerWidth || 1280, win.innerHeight || 800);

                var scene = new THREE.Scene();
                var camera = new THREE.PerspectiveCamera(55, (win.innerWidth || 1280) / (win.innerHeight || 800), 0.1, 1000);
                camera.position.z = 28;

                // 1. Central Complex Group (Icosahedron + Octahedron + Core)
                var centralGroup = new THREE.Group();
                
                var icoGeom = new THREE.IcosahedronGeometry(7.5, 1);
                var icoMat = new THREE.MeshBasicMaterial({
                    color: 0x38bdf8,
                    wireframe: true,
                    transparent: true,
                    opacity: 0.32
                });
                var icoMesh = new THREE.Mesh(icoGeom, icoMat);
                centralGroup.add(icoMesh);

                var octGeom = new THREE.OctahedronGeometry(4.8, 0);
                var octMat = new THREE.MeshBasicMaterial({
                    color: 0xa855f7,
                    wireframe: true,
                    transparent: true,
                    opacity: 0.45
                });
                var octMesh = new THREE.Mesh(octGeom, octMat);
                centralGroup.add(octMesh);

                var coreGeom = new THREE.SphereGeometry(1.6, 16, 16);
                var coreMat = new THREE.MeshBasicMaterial({
                    color: 0x60a5fa,
                    wireframe: true,
                    transparent: true,
                    opacity: 0.55
                });
                var coreMesh = new THREE.Mesh(coreGeom, coreMat);
                centralGroup.add(coreMesh);

                centralGroup.position.set(11, 2.5, -4);
                scene.add(centralGroup);

                // 2. Secondary Floating Polyhedral Crystals in background
                var crystalGroup = new THREE.Group();
                var crystalConfigs = [
                    { geom: new THREE.DodecahedronGeometry(2.5, 0), pos: [-16, 9, -12], color: 0x818cf8, rotSpeed: 0.01 },
                    { geom: new THREE.OctahedronGeometry(2.0, 0), pos: [-18, -8, -8], color: 0x38bdf8, rotSpeed: -0.012 },
                    { geom: new THREE.IcosahedronGeometry(2.8, 0), pos: [19, -9, -14], color: 0xc084fc, rotSpeed: 0.009 },
                    { geom: new THREE.TetrahedronGeometry(1.8, 0), pos: [5, 13, -10], color: 0x22d3ee, rotSpeed: -0.015 }
                ];

                var crystalMeshes = [];
                crystalConfigs.forEach(function(cfg) {
                    var cMat = new THREE.MeshBasicMaterial({
                        color: cfg.color,
                        wireframe: true,
                        transparent: true,
                        opacity: 0.28
                    });
                    var cMesh = new THREE.Mesh(cfg.geom, cMat);
                    cMesh.position.set(cfg.pos[0], cfg.pos[1], cfg.pos[2]);
                    crystalGroup.add(cMesh);
                    crystalMeshes.push({ mesh: cMesh, speed: cfg.rotSpeed });
                });
                scene.add(crystalGroup);

                // 3. Cybernetic Undulating Terrain Grid (Floor)
                var planeGeom = new THREE.PlaneGeometry(90, 90, 28, 28);
                planeGeom.rotateX(-Math.PI / 2.3);
                var planeMat = new THREE.MeshBasicMaterial({
                    color: 0x1e3a8a,
                    wireframe: true,
                    transparent: true,
                    opacity: 0.22
                });
                var planeMesh = new THREE.Mesh(planeGeom, planeMat);
                planeMesh.position.set(0, -14, -8);
                scene.add(planeMesh);
                var planePositions = planeGeom.attributes.position;

                // 4. Glowing Particle Constellation Field
                var particleCount = 450;
                var particleGeom = new THREE.BufferGeometry();
                var particlePos = new Float32Array(particleCount * 3);
                var particleColors = new Float32Array(particleCount * 3);

                for (var p = 0; p < particleCount; p++) {
                    particlePos[p * 3] = (Math.random() - 0.5) * 85;
                    particlePos[p * 3 + 1] = (Math.random() - 0.5) * 65;
                    particlePos[p * 3 + 2] = (Math.random() - 0.5) * 60 - 5;

                    var isCyan = Math.random() > 0.45;
                    particleColors[p * 3] = isCyan ? 0.22 : 0.65;
                    particleColors[p * 3 + 1] = isCyan ? 0.74 : 0.33;
                    particleColors[p * 3 + 2] = isCyan ? 0.97 : 0.96;
                }

                particleGeom.setAttribute("position", new THREE.BufferAttribute(particlePos, 3));
                particleGeom.setAttribute("color", new THREE.BufferAttribute(particleColors, 3));

                var pCanvas = doc.createElement("canvas");
                pCanvas.width = 32;
                pCanvas.height = 32;
                var pCtx = pCanvas.getContext("2d");
                var grad = pCtx.createRadialGradient(16, 16, 0, 16, 16, 16);
                grad.addColorStop(0, "rgba(255, 255, 255, 1)");
                grad.addColorStop(0.3, "rgba(56, 189, 248, 0.9)");
                grad.addColorStop(0.7, "rgba(168, 85, 247, 0.4)");
                grad.addColorStop(1, "rgba(0, 0, 0, 0)");
                pCtx.fillStyle = grad;
                pCtx.fillRect(0, 0, 32, 32);

                var pTexture = new THREE.CanvasTexture(pCanvas);
                var particleMat = new THREE.PointsMaterial({
                    size: 1.4,
                    map: pTexture,
                    vertexColors: true,
                    transparent: true,
                    blending: THREE.AdditiveBlending,
                    depthWrite: false
                });
                var particleSystem = new THREE.Points(particleGeom, particleMat);
                scene.add(particleSystem);

                // 5. Interactive Mouse Parallax Tracking
                var mouseX = 0, mouseY = 0;
                var targetX = 0, targetY = 0;

                win.addEventListener("mousemove", function(e) {
                    targetX = (e.clientX - (win.innerWidth || 1280) / 2) * 0.00045;
                    targetY = (e.clientY - (win.innerHeight || 800) / 2) * 0.00045;
                }, { passive: true });

                win.addEventListener("resize", function() {
                    var w = win.innerWidth || 1280;
                    var h = win.innerHeight || 800;
                    camera.aspect = w / h;
                    camera.updateProjectionMatrix();
                    renderer.setSize(w, h);
                }, { passive: true });

                // 6. Smooth Animation Loop
                var clock = new THREE.Clock();

                function render() {
                    var elapsed = clock.getElapsedTime();

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

                    var pulse = 1.0 + Math.sin(elapsed * 2.0) * 0.12;
                    coreMesh.scale.set(pulse, pulse, pulse);

                    crystalMeshes.forEach(function(item) {
                        item.mesh.rotation.x += item.speed;
                        item.mesh.rotation.y += item.speed * 1.5;
                    });

                    var posArr = planePositions.array;
                    for (var i = 0; i < posArr.length; i += 3) {
                        var vx = posArr[i];
                        var vy = posArr[i + 1];
                        posArr[i + 2] = Math.sin(vx * 0.18 + elapsed * 1.2) * Math.cos(vy * 0.18 + elapsed * 1.2) * 1.4;
                    }
                    planePositions.needsUpdate = true;

                    particleSystem.rotation.y = elapsed * 0.03;
                    particleSystem.rotation.x = Math.sin(elapsed * 0.02) * 0.05;

                    renderer.render(scene, camera);
                    win.requestAnimationFrame(render);
                }

                win.requestAnimationFrame(render);
            } catch(err) {
                console.warn("PolyGen Three.js background initialization error, starting 3D Canvas:", err);
                runNative3DFallback();
            }
        }

        // ---------------------------------------------------------------------
        // Script Loader: Load Three.js CDN with graceful fallback
        // ---------------------------------------------------------------------
        if (win.THREE) {
            initThreeScene();
        } else {
            var script = doc.createElement("script");
            script.src = "https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js";
            script.async = true;
            script.onload = function() {
                initThreeScene();
            };
            script.onerror = function() {
                console.warn("Three.js CDN unreachable, starting Native 3D Canvas Fallback engine.");
                runNative3DFallback();
            };
            doc.head.appendChild(script);
        }
    }

    if (doc.readyState === "complete" || doc.readyState === "interactive") {
        setTimeout(startEngine, 30);
    } else {
        doc.addEventListener("DOMContentLoaded", startEngine);
    }
})();
</script>
"""

def inject_streamlit_3d_background():
    """Injects the 3D background into the Streamlit parent document and styles containers."""
    import streamlit as st
    import streamlit.components.v1 as components

    st_css = """
    <style>
        .stApp {
            background: transparent !important;
        }
        [data-testid="stAppViewContainer"] {
            background: radial-gradient(circle at 50% 25%, rgba(13, 18, 31, 0.72) 0%, rgba(6, 9, 14, 0.90) 100%) !important;
        }
        [data-testid="stHeader"] {
            background: transparent !important;
        }
        [data-testid="stSidebar"] {
            background: rgba(10, 15, 26, 0.85) !important;
            backdrop-filter: blur(14px) !important;
            border-right: 1px solid rgba(59, 130, 246, 0.22) !important;
        }
        .hero-banner, .metric-card {
            backdrop-filter: blur(12px) !important;
        }
    </style>
    """
    st.markdown(st_css, unsafe_allow_html=True)
    components.html(get_3d_background_script(), height=0, width=0)

def get_gradio_3d_background_html() -> str:
    """Returns the HTML/JS snippet for Gradio."""
    return get_3d_background_script()
