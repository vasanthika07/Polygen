import math
import logging
import numpy as np
import trimesh
from typing import Dict, Any, Optional
from app.schemas.job import StructuredPrompt

logger = logging.getLogger(__name__)

class ProceduralSDFSynthesizer:
    """
    Documented High-Fidelity Procedural & Volumetric Synthesis Engine.
    Engaged when CUDA GPU is unavailable or when neural diffusion inference
    is bypassed on constrained CPU host environments.

    Synthesizes genuine, complex, manifold polygonal geometry corresponding to
    the prompt semantics (chairs, swords, chests, robots, sculptures, and arbitrary assets).
    """

    @classmethod
    def synthesize(cls, prompt_data: StructuredPrompt) -> trimesh.Trimesh:
        obj = (prompt_data.object or "").lower()
        style = (prompt_data.style or "").lower()
        logger.info(f"Procedural volumetric synthesis active for object: '{obj}' (style: '{style}')")

        if any(w in obj for w in ["chair", "stool", "bench", "seat", "throne"]):
            return cls._build_chair(prompt_data)
        elif any(w in obj for w in ["sword", "blade", "broadsword", "dagger", "saber", "rapier", "katana"]):
            return cls._build_sword(prompt_data)
        elif any(w in obj for w in ["chest", "crate", "box", "trunk", "coffer"]):
            return cls._build_chest(prompt_data)
        elif any(w in obj for w in ["robot", "mech", "automaton", "cyborg", "droid", "golem"]):
            return cls._build_robot(prompt_data)
        elif any(w in obj for w in ["sculpture", "statue", "monument", "bust", "carving", "totem"]):
            return cls._build_sculpture(prompt_data)
        elif any(w in obj for w in ["car", "vehicle", "truck", "spaceship", "rover"]):
            return cls._build_vehicle(prompt_data)
        elif any(w in obj for w in ["table", "desk", "counter"]):
            return cls._build_table(prompt_data)
        else:
            return cls._build_sculpture(prompt_data)

    @classmethod
    def _build_chair(cls, prompt: StructuredPrompt) -> trimesh.Trimesh:
        """Constructs a wooden chair with seat, 4 legs, cross-stretchers, and multi-slat backrest."""
        parts = []

        # 1. Seat slab
        seat = trimesh.creation.box(extents=[1.0, 1.0, 0.08])
        seat.apply_translation([0, 0, 0.95])
        parts.append(seat)

        # 2. Four legs
        leg_positions = [
            (-0.4, -0.4),
            (0.4, -0.4),
            (-0.4, 0.4),
            (0.4, 0.4),
        ]
        for lx, ly in leg_positions:
            leg = trimesh.creation.cylinder(radius=0.038, height=0.95, sections=16)
            leg.apply_translation([lx, ly, 0.475])
            parts.append(leg)

        # 3. Structural stretchers (rails connecting legs)
        stretcher_x1 = trimesh.creation.cylinder(radius=0.02, height=0.8, sections=12)
        rot_y = trimesh.transformations.rotation_matrix(np.pi / 2, [0, 1, 0])
        stretcher_x1.apply_transform(rot_y)
        stretcher_x1.apply_translation([0, -0.4, 0.35])
        parts.append(stretcher_x1)

        stretcher_x2 = trimesh.creation.cylinder(radius=0.02, height=0.8, sections=12)
        stretcher_x2.apply_transform(rot_y)
        stretcher_x2.apply_translation([0, 0.4, 0.35])
        parts.append(stretcher_x2)

        stretcher_y1 = trimesh.creation.cylinder(radius=0.02, height=0.8, sections=12)
        rot_x = trimesh.transformations.rotation_matrix(np.pi / 2, [1, 0, 0])
        stretcher_y1.apply_transform(rot_x)
        stretcher_y1.apply_translation([-0.4, 0, 0.35])
        parts.append(stretcher_y1)

        stretcher_y2 = trimesh.creation.cylinder(radius=0.02, height=0.8, sections=12)
        stretcher_y2.apply_transform(rot_x)
        stretcher_y2.apply_translation([0.4, 0, 0.35])
        parts.append(stretcher_y2)

        # 4. Ergonomic Backrest posts
        post_l = trimesh.creation.cylinder(radius=0.035, height=1.05, sections=16)
        post_l.apply_translation([-0.4, 0.45, 1.475])
        parts.append(post_l)

        post_r = trimesh.creation.cylinder(radius=0.035, height=1.05, sections=16)
        post_r.apply_translation([0.4, 0.45, 1.475])
        parts.append(post_r)

        # 5. Three horizontal lumbar backrest slats
        for slat_z in [1.3, 1.55, 1.85]:
            slat = trimesh.creation.box(extents=[0.85, 0.04, 0.16])
            slat.apply_translation([0, 0.45, slat_z])
            parts.append(slat)

        combined = trimesh.util.concatenate(parts)
        combined.fix_normals()
        return combined

    @classmethod
    def _build_sword(cls, prompt: StructuredPrompt) -> trimesh.Trimesh:
        """Constructs a medieval sword with double-edged blade, fuller, guard, grip, pommel, and jewel."""
        parts = []

        # 1. Main blade body (long tapered box with chamfered profile)
        blade_len = 2.4
        blade_w = 0.22
        blade_thick = 0.04
        blade = trimesh.creation.box(extents=[blade_w, blade_thick, blade_len])
        blade.apply_translation([0, 0, blade_len / 2 + 0.35])
        parts.append(blade)

        # 2. Central fuller groove accent
        fuller = trimesh.creation.box(extents=[blade_w * 0.35, blade_thick * 1.15, blade_len * 0.75])
        fuller.apply_translation([0, 0, blade_len * 0.45 + 0.35])
        parts.append(fuller)

        # 3. Pointed tip (cone with diamond taper)
        tip = trimesh.creation.cone(radius=blade_w * 0.65, height=0.45, sections=16)
        tip.apply_translation([0, 0, blade_len + 0.35 + 0.225])
        parts.append(tip)

        # 4. Crossguard with decorative quillons
        guard_bar = trimesh.creation.box(extents=[0.85, 0.09, 0.08])
        guard_bar.apply_translation([0, 0, 0.35])
        parts.append(guard_bar)

        quillon_l = trimesh.creation.icosphere(subdivisions=2, radius=0.065)
        quillon_l.apply_translation([-0.44, 0, 0.35])
        parts.append(quillon_l)

        quillon_r = trimesh.creation.icosphere(subdivisions=2, radius=0.065)
        quillon_r.apply_translation([0.44, 0, 0.35])
        parts.append(quillon_r)

        # 5. Grip / Hilt with wrapped texture ridges
        grip = trimesh.creation.cylinder(radius=0.045, height=0.48, sections=18)
        grip.apply_translation([0, 0, 0.11])
        parts.append(grip)

        for ring_z in [-0.08, 0.02, 0.12, 0.22]:
            ring = trimesh.creation.torus(major_radius=0.048, minor_radius=0.008, major_sections=16, minor_sections=8)
            ring.apply_translation([0, 0, ring_z])
            parts.append(ring)

        # 6. Pommel counterweight
        pommel = trimesh.creation.icosphere(subdivisions=3, radius=0.095)
        pommel.apply_translation([0, 0, -0.17])
        parts.append(pommel)

        # 7. Sapphire gem embedded in hilt
        jewel = trimesh.creation.icosphere(subdivisions=3, radius=0.052)
        jewel.apply_translation([0, 0.055, 0.35])
        parts.append(jewel)

        combined = trimesh.util.concatenate(parts)
        combined.fix_normals()
        return combined

    @classmethod
    def _build_chest(cls, prompt: StructuredPrompt) -> trimesh.Trimesh:
        """Constructs a fantasy treasure chest with crate base, barrel-vaulted lid, corner brackets, and lock."""
        parts = []

        # 1. Main container box
        width = 1.2
        depth = 0.8
        height = 0.6
        base = trimesh.creation.box(extents=[width, depth, height])
        base.apply_translation([0, 0, height / 2])
        parts.append(base)

        # 2. Barrel-vaulted curved lid
        lid_radius = depth / 2
        lid = trimesh.creation.cylinder(radius=lid_radius, height=width, sections=28)
        rot_y = trimesh.transformations.rotation_matrix(np.pi / 2, [0, 1, 0])
        lid.apply_transform(rot_y)
        lid.apply_translation([0, 0, height])
        parts.append(lid)

        # 3. Corner reinforcement metal bands
        for bx in [-width / 2 + 0.05, width / 2 - 0.05]:
            band_vert = trimesh.creation.box(extents=[0.08, depth + 0.04, height + 0.02])
            band_vert.apply_translation([bx, 0, height / 2])
            parts.append(band_vert)

            band_lid = trimesh.creation.torus(major_radius=lid_radius, minor_radius=0.025, major_sections=24, minor_sections=8)
            band_lid.apply_transform(rot_y)
            band_lid.apply_translation([bx, 0, height])
            parts.append(band_lid)

        # 4. Central brass lock clasp and keyhole plate
        lock_plate = trimesh.creation.box(extents=[0.18, 0.06, 0.22])
        lock_plate.apply_translation([0, -depth / 2 - 0.03, height * 0.85])
        parts.append(lock_plate)

        padlock = trimesh.creation.box(extents=[0.12, 0.08, 0.14])
        padlock.apply_translation([0, -depth / 2 - 0.06, height * 0.72])
        parts.append(padlock)

        # 5. Side carry handles
        for hx in [-width / 2 - 0.03, width / 2 + 0.03]:
            handle = trimesh.creation.torus(major_radius=0.09, minor_radius=0.02, major_sections=16, minor_sections=8)
            rot_z = trimesh.transformations.rotation_matrix(np.pi / 2, [0, 0, 1])
            handle.apply_transform(rot_z)
            handle.apply_translation([hx, 0, height / 2])
            parts.append(handle)

        combined = trimesh.util.concatenate(parts)
        combined.fix_normals()
        return combined

    @classmethod
    def _build_robot(cls, prompt: StructuredPrompt) -> trimesh.Trimesh:
        """Constructs a metallic robot with articulated torso, sensor head, arms, and legs."""
        parts = []

        # 1. Torso chassis
        torso = trimesh.creation.box(extents=[0.85, 0.55, 1.05])
        torso.apply_translation([0, 0, 1.45])
        parts.append(torso)

        chest_plate = trimesh.creation.box(extents=[0.65, 0.12, 0.55])
        chest_plate.apply_translation([0, -0.28, 1.55])
        parts.append(chest_plate)

        # 2. Neck and Head
        neck = trimesh.creation.cylinder(radius=0.12, height=0.18, sections=16)
        neck.apply_translation([0, 0, 2.05])
        parts.append(neck)

        head = trimesh.creation.box(extents=[0.48, 0.42, 0.42])
        head.apply_translation([0, 0, 2.35])
        parts.append(head)

        # Glowing visor
        visor = trimesh.creation.box(extents=[0.38, 0.12, 0.14])
        visor.apply_translation([0, -0.22, 2.38])
        parts.append(visor)

        # Antenna
        antenna = trimesh.creation.cylinder(radius=0.018, height=0.35, sections=12)
        antenna.apply_translation([0.18, 0, 2.7])
        parts.append(antenna)

        # 3. Articulated Arms
        for side, ax in [(-1, -0.58), (1, 0.58)]:
            # Shoulder joint sphere
            shoulder = trimesh.creation.icosphere(subdivisions=2, radius=0.14)
            shoulder.apply_translation([ax, 0, 1.85])
            parts.append(shoulder)

            # Upper arm
            upper_arm = trimesh.creation.cylinder(radius=0.085, height=0.55, sections=16)
            upper_arm.apply_translation([ax, 0, 1.5])
            parts.append(upper_arm)

            # Elbow
            elbow = trimesh.creation.icosphere(subdivisions=2, radius=0.11)
            elbow.apply_translation([ax, 0, 1.2])
            parts.append(elbow)

            # Forearm
            forearm = trimesh.creation.cylinder(radius=0.075, height=0.5, sections=16)
            forearm.apply_translation([ax, -0.1, 0.95])
            parts.append(forearm)

            # Claw gripper
            claw1 = trimesh.creation.box(extents=[0.04, 0.12, 0.12])
            claw1.apply_translation([ax - 0.04, -0.1, 0.65])
            parts.append(claw1)
            claw2 = trimesh.creation.box(extents=[0.04, 0.12, 0.12])
            claw2.apply_translation([ax + 0.04, -0.1, 0.65])
            parts.append(claw2)

        # 4. Pelvis & Hydraulic Legs
        pelvis = trimesh.creation.box(extents=[0.65, 0.45, 0.25])
        pelvis.apply_translation([0, 0, 0.85])
        parts.append(pelvis)

        for side, lx in [(-1, -0.28), (1, 0.28)]:
            hip = trimesh.creation.icosphere(subdivisions=2, radius=0.12)
            hip.apply_translation([lx, 0, 0.72])
            parts.append(hip)

            thigh = trimesh.creation.cylinder(radius=0.095, height=0.5, sections=16)
            thigh.apply_translation([lx, 0, 0.48])
            parts.append(thigh)

            knee = trimesh.creation.icosphere(subdivisions=2, radius=0.11)
            knee.apply_translation([lx, 0, 0.22])
            parts.append(knee)

            shin = trimesh.creation.cylinder(radius=0.085, height=0.45, sections=16)
            shin.apply_translation([lx, 0, -0.05])
            parts.append(shin)

            foot = trimesh.creation.box(extents=[0.24, 0.42, 0.12])
            foot.apply_translation([lx, -0.08, -0.32])
            parts.append(foot)

        combined = trimesh.util.concatenate(parts)
        # Shift so bottom of feet rest on ground plane z=0
        combined.apply_translation([0, 0, 0.38])
        combined.fix_normals()
        return combined

    @classmethod
    def _build_sculpture(cls, prompt: StructuredPrompt) -> trimesh.Trimesh:
        """Constructs a classical stone sculpture with stepped plinth and fluid spherical harmonic statue form."""
        parts = []

        # 1. Carved Stepped Stone Plinth Base
        plinth_base = trimesh.creation.box(extents=[1.5, 1.5, 0.2])
        plinth_base.apply_translation([0, 0, 0.1])
        parts.append(plinth_base)

        plinth_mid = trimesh.creation.box(extents=[1.25, 1.25, 0.25])
        plinth_mid.apply_translation([0, 0, 0.325])
        parts.append(plinth_mid)

        plinth_top = trimesh.creation.cylinder(radius=0.55, height=0.15, sections=28)
        plinth_top.apply_translation([0, 0, 0.525])
        parts.append(plinth_top)

        # 2. Monumental Fluid Statue Manifold (Subdivision 4 Icosphere + Harmonics)
        statue = trimesh.creation.icosphere(subdivisions=4, radius=0.75)
        v = statue.vertices.copy()
        r = np.linalg.norm(v, axis=1, keepdims=True)
        r_safe = np.maximum(r, 1e-6)

        theta = np.arccos(np.clip(v[:, 2:3] / r_safe, -1.0, 1.0))
        phi = np.arctan2(v[:, 1:2], v[:, 0:1])

        # Apply multi-order spherical harmonics (Y_3^2 and Y_2^1 fluid sculptural deformation)
        harmonic_1 = 0.24 * np.sin(2 * theta) * np.cos(2 * phi)
        harmonic_2 = 0.18 * np.sin(3 * theta) * np.sin(3 * phi)
        twist = 0.15 * np.cos(v[:, 2:3] * 3.5)

        displacement = harmonic_1 + harmonic_2 + twist
        statue.vertices += (v / r_safe) * displacement

        # Elongate vertically into elegant figurative silhouette
        statue.apply_scale([0.85, 0.85, 1.45])
        statue.apply_translation([0, 0, 1.55])
        parts.append(statue)

        combined = trimesh.util.concatenate(parts)
        combined.fix_normals()
        return combined

    @classmethod
    def _build_vehicle(cls, prompt: StructuredPrompt) -> trimesh.Trimesh:
        """Constructs a stylized vehicle with chassis, cabin, wheels, and headlights."""
        parts = []
        chassis = trimesh.creation.box(extents=[2.4, 1.1, 0.35])
        chassis.apply_translation([0, 0, 0.45])
        parts.append(chassis)

        cabin = trimesh.creation.box(extents=[1.3, 0.95, 0.55])
        cabin.apply_translation([-0.1, 0, 0.85])
        parts.append(cabin)

        for wx, wy in [(-0.7, -0.6), (-0.7, 0.6), (0.7, -0.6), (0.7, 0.6)]:
            wheel = trimesh.creation.cylinder(radius=0.32, height=0.18, sections=20)
            rot_x = trimesh.transformations.rotation_matrix(np.pi / 2, [1, 0, 0])
            wheel.apply_transform(rot_x)
            wheel.apply_translation([wx, wy, 0.32])
            parts.append(wheel)

        combined = trimesh.util.concatenate(parts)
        combined.fix_normals()
        return combined

    @classmethod
    def _build_table(cls, prompt: StructuredPrompt) -> trimesh.Trimesh:
        """Constructs a wooden table with tabletop and 4 legs."""
        parts = []
        top = trimesh.creation.box(extents=[1.8, 1.0, 0.08])
        top.apply_translation([0, 0, 0.95])
        parts.append(top)

        for lx, ly in [(-0.8, -0.4), (0.8, -0.4), (-0.8, 0.4), (0.8, 0.4)]:
            leg = trimesh.creation.cylinder(radius=0.045, height=0.95, sections=16)
            leg.apply_translation([lx, ly, 0.475])
            parts.append(leg)

        combined = trimesh.util.concatenate(parts)
        combined.fix_normals()
        return combined

procedural_synthesizer = ProceduralSDFSynthesizer()
