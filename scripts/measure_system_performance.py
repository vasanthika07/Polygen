"""
PolyGen System Performance Profiling & Empirical Benchmark Engine
Measures exact wall-clock timings, memory consumption, GPU telemetry,
mesh decimation ratios, file sizes, and binary load durations.
"""

import os
import sys
import time
import json
import psutil
import trimesh
import numpy as np

# Ensure root workspace and backend are in path
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, BASE_DIR)
sys.path.insert(0, os.path.join(BASE_DIR, "backend"))

os.environ["AI_BACKEND"] = "procedural"
from app.config import settings
settings.AI_BACKEND = "procedural"

import torch
from ai_models.text_to_3d.hardware import hardware_detector
from app.services.prompt_engine import prompt_engine
from ai_models.text_to_3d.generator import text_to_3d_generator
from processing.mesh_cleaner import mesh_cleaner
from processing.uv_unwrapper import uv_unwrapper
from processing.texture_baker import texture_baker
from processing.mesh_optimizer import mesh_optimizer
from processing.glb_exporter import glb_exporter

BENCHMARK_PROMPTS = [
    {
        "id": "rusted_sword",
        "title": "Rusted Medieval Broadsword",
        "prompt": "A rusted medieval broadsword with weathered steel blade, chipped edge, leather-wrapped crossguard, and a glowing blue sapphire gemstone in the hilt.",
        "polygon_budget": 5000,
        "style": "fantasy",
    },
    {
        "id": "glowing_sapphire",
        "title": "Glowing Sapphire Crystal",
        "prompt": "A cut glowing blue sapphire gemstone crystal with luminous facets and emissive magical aura.",
        "polygon_budget": 3000,
        "style": "crystal",
    },
    {
        "id": "granite_sculpture",
        "title": "Weathered Granite Gargoyle",
        "prompt": "An ancient weathered granite stone gargoyle sculpture with rough chiseled stone texture and moss accents.",
        "polygon_budget": 7500,
        "style": "gothic",
    },
    {
        "id": "carved_chest",
        "title": "Carved Oak Treasure Chest",
        "prompt": "An ornate carved oak wooden treasure chest with reinforced iron banding and heavy padlock.",
        "polygon_budget": 6000,
        "style": "medieval",
    },
]

def run_performance_benchmarks():
    print("=" * 80)
    print("POLYGEN PERFORMANCE PROFILING & EMPIRICAL BENCHMARK SUITE")
    print("=" * 80)

    # Hardware & System Environment Telemetry
    hw_info = hardware_detector.get_hardware_info()
    process = psutil.Process(os.getpid())
    system_ram_gb = round(psutil.virtual_memory().total / (1024 ** 3), 2)
    cpu_count = psutil.cpu_count(logical=True)
    cuda_available = torch.cuda.is_available()
    device_name = torch.cuda.get_device_name(0) if cuda_available else "CPU (Host Architecture)"
    
    print(f"System Hardware Profile:")
    print(f"  CPU Logical Cores : {cpu_count}")
    print(f"  System RAM        : {system_ram_gb} GB")
    print(f"  PyTorch Device    : {device_name} (CUDA={cuda_available})")
    print(f"  PyTorch Version   : {torch.__version__}")
    print(f"  PID               : {os.getpid()}")
    print("-" * 80)

    benchmark_output_dir = os.path.join(BASE_DIR, "storage", "benchmarks")
    os.makedirs(benchmark_output_dir, exist_ok=True)

    results = []

    for item in BENCHMARK_PROMPTS:
        prompt_id = item["id"]
        title = item["title"]
        prompt_text = item["prompt"]
        budget = item["polygon_budget"]
        style = item["style"]

        print(f"\n[BENCHMARK] Scenario: {title}")
        print(f"  Prompt: \"{prompt_text}\"")
        print(f"  Budget: {budget} polygons | Style: {style}")

        # Baseline memory
        start_mem_mb = process.memory_info().rss / (1024 * 1024)
        total_start = time.perf_counter()

        # Step 1: Prompt Analysis
        t0 = time.perf_counter()
        structured = prompt_engine.process(
            raw_prompt=prompt_text,
            style_override=style,
            polygon_budget=budget,
        )
        t_prompt_ms = round((time.perf_counter() - t0) * 1000, 2)
        print(f"  1. Prompt Analysis       : {t_prompt_ms:7.2f} ms")

        # Step 2: 3D Geometry Generation
        t0 = time.perf_counter()
        raw_obj_path = os.path.join(benchmark_output_dir, f"{prompt_id}_raw.obj")
        raw_mesh, gen_meta = text_to_3d_generator.generate(structured, raw_obj_path)
        t_mesh_gen_ms = round((time.perf_counter() - t0) * 1000, 2)
        print(f"  2. 3D Geometry Generation: {t_mesh_gen_ms:7.2f} ms ({len(raw_mesh.vertices)} verts, {len(raw_mesh.faces)} faces)")

        # Step 3: Mesh Processing / Cleaning
        t0 = time.perf_counter()
        clean_path = os.path.join(benchmark_output_dir, f"{prompt_id}_cleaned.obj")
        cleaned_mesh, clean_stats = mesh_cleaner.clean(raw_mesh, output_path=clean_path)
        t_clean_ms = round((time.perf_counter() - t0) * 1000, 2)
        print(f"  3. Mesh Processing/Clean : {t_clean_ms:7.2f} ms ({clean_stats['cleaned_vertices']} verts, {clean_stats['cleaned_faces']} faces)")

        # Step 4: UV Parameterization & Unwrapping
        t0 = time.perf_counter()
        unwrap_path = os.path.join(benchmark_output_dir, f"{prompt_id}_unwrapped.obj")
        preview_uv_path = os.path.join(benchmark_output_dir, f"{prompt_id}_uv.png")
        unwrapped_mesh, uv_stats = uv_unwrapper.unwrap(
            cleaned_mesh,
            output_path=unwrap_path,
            preview_path=preview_uv_path,
            resolution=1024,
        )
        t_uv_ms = round((time.perf_counter() - t0) * 1000, 2)
        print(f"  4. UV Mapping (xatlas)   : {t_uv_ms:7.2f} ms ({uv_stats.get('chart_count', 1)} charts, {len(unwrapped_mesh.vertices)} verts)")

        # Step 5: AI Texture Synthesis & Baking
        t0 = time.perf_counter()
        tex_dir = os.path.join(benchmark_output_dir, f"{prompt_id}_textures")
        tex_preview = os.path.join(benchmark_output_dir, f"{prompt_id}_tex_preview.png")
        tex_paths = texture_baker.generate_pbr_set(
            prompt_data=structured,
            output_dir=tex_dir,
            mesh=unwrapped_mesh,
            resolution=1024,
            preview_path=tex_preview,
        )
        t_texture_ms = round((time.perf_counter() - t0) * 1000, 2)
        print(f"  5. PBR Texture Synthesis : {t_texture_ms:7.2f} ms ({len(tex_paths)} maps @ 1024x1024)")

        # Step 6: Mesh Decimation & Optimization
        t0 = time.perf_counter()
        optimized_mesh, opt_stats = mesh_optimizer.optimize(
            mesh=unwrapped_mesh,
            target_polygon_budget=budget,
        )
        t_optimize_ms = round((time.perf_counter() - t0) * 1000, 2)
        print(f"  6. Mesh Decimation (QEM) : {t_optimize_ms:7.2f} ms ({opt_stats['initial_faces']} -> {opt_stats['optimized_faces']} faces, -{opt_stats['reduction_ratio']}%)")

        # Step 7: GLB Export & Validation
        t0 = time.perf_counter()
        glb_path = os.path.join(benchmark_output_dir, f"{prompt_id}.glb")
        export_stats = glb_exporter.export(
            mesh=optimized_mesh,
            texture_paths=tex_paths,
            output_glb_path=glb_path,
        )
        t_export_ms = round((time.perf_counter() - t0) * 1000, 2)
        glb_size_bytes = export_stats["file_size_bytes"]
        glb_size_mb = export_stats["file_size_mb"]
        print(f"  7. GLB 2.0 Binary Export : {t_export_ms:7.2f} ms (File Size: {glb_size_mb:.2f} MB / {glb_size_bytes:,} bytes)")

        # Step 8: Client Viewer Load & Parse Emulation
        t0 = time.perf_counter()
        # Load binary directly into Trimesh to simulate Three.js GLTFLoader parsing buffer
        with open(glb_path, "rb") as f:
            glb_buffer = f.read()
        reloaded = trimesh.load(trimesh.util.wrap_as_stream(glb_buffer), file_type="glb")
        t_viewer_load_ms = round((time.perf_counter() - t0) * 1000, 2)
        print(f"  8. Viewer Buffer Parse   : {t_viewer_load_ms:7.2f} ms (Parsed geometry scene successfully)")

        total_duration_s = round(time.perf_counter() - total_start, 2)
        end_mem_mb = process.memory_info().rss / (1024 * 1024)
        peak_delta_mem_mb = round(max(0.0, end_mem_mb - start_mem_mb), 2)
        print(f"  => TOTAL PIPELINE DURATION : {total_duration_s:.2f} s | Memory Delta: {peak_delta_mem_mb:.2f} MB")

        scenario_result = {
            "id": prompt_id,
            "title": title,
            "prompt": prompt_text,
            "polygon_budget": budget,
            "timings_ms": {
                "prompt_analysis": t_prompt_ms,
                "geometry_generation": t_mesh_gen_ms,
                "mesh_processing": t_clean_ms,
                "uv_mapping": t_uv_ms,
                "texture_generation": t_texture_ms,
                "mesh_optimization": t_optimize_ms,
                "glb_export": t_export_ms,
                "viewer_load_parse": t_viewer_load_ms,
                "total_duration_s": total_duration_s,
            },
            "geometry": {
                "raw_vertices": len(raw_mesh.vertices),
                "raw_faces": len(raw_mesh.faces),
                "cleaned_vertices": clean_stats["cleaned_vertices"],
                "cleaned_faces": clean_stats["cleaned_faces"],
                "optimized_vertices": len(optimized_mesh.vertices),
                "optimized_faces": len(optimized_mesh.faces),
                "face_reduction_ratio": opt_stats["reduction_ratio"],
                "is_watertight": clean_stats.get("watertight_after", clean_stats.get("watertight", False)),
            },
            "output_asset": {
                "glb_file_bytes": glb_size_bytes,
                "glb_file_mb": glb_size_mb,
                "texture_maps": list(tex_paths.keys()),
                "texture_resolution": "1024x1024",
                "validation_passed": export_stats["is_valid"],
            },
            "memory_mb": {
                "start": round(start_mem_mb, 2),
                "end": round(end_mem_mb, 2),
                "delta": peak_delta_mem_mb,
            }
        }
        results.append(scenario_result)

    # Save benchmark telemetry results to JSON
    json_path = os.path.join(BASE_DIR, "docs", "benchmark_metrics.json")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump({
            "environment": {
                "cpu_cores": cpu_count,
                "ram_gb": system_ram_gb,
                "device": device_name,
                "cuda": cuda_available,
                "torch_version": torch.__version__,
            },
            "scenarios": results,
        }, f, indent=2)

    print("\n" + "=" * 80)
    print("BENCHMARK SUMMARY TABLE")
    print("=" * 80)
    print(f"{'Asset':<24} | {'Budget':<7} | {'Faces':<12} | {'GLB Size':<9} | {'Pipeline':<10} | {'Viewer Parse':<12}")
    print("-" * 80)
    for r in results:
        g = r["geometry"]
        t = r["timings_ms"]
        a = r["output_asset"]
        faces_str = f"{g['raw_faces']}->{g['optimized_faces']}"
        size_str = f"{a['glb_file_mb']:.2f} MB"
        total_str = f"{t['total_duration_s']:.2f} s"
        viewer_str = f"{t['viewer_load_parse']:.1f} ms"
        print(f"{r['title']:<24} | {r['polygon_budget']:<7} | {faces_str:<12} | {size_str:<9} | {total_str:<10} | {viewer_str:<12}")
    print("=" * 80)
    print(f"Metrics saved to {json_path}")
    return results

if __name__ == "__main__":
    run_performance_benchmarks()
