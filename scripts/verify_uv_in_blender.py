"""
Standalone Headless Blender UV Verification Script
Can be run directly inside Blender:
    blender --background --python scripts/verify_uv_in_blender.py -- <path_to_mesh>
"""
import sys
import os
import json

def verify_uv_in_blender():
    try:
        import bpy
        import bmesh
    except ImportError:
        print("[ERROR] bpy module is only available when run inside Blender.")
        sys.exit(1)

    # Locate mesh file passed after '--'
    argv = sys.argv
    if "--" not in argv:
        print("[ERROR] Please provide a mesh file path after '--'")
        sys.exit(1)

    mesh_path = argv[argv.index("--") + 1]
    if not os.path.exists(mesh_path):
        print(f"[ERROR] Mesh file not found: {mesh_path}")
        sys.exit(1)

    print(f"[BLENDER] Loading mesh: {mesh_path}")

    # Reset Blender scene to empty
    bpy.ops.wm.read_factory_settings(use_empty=True)

    ext = os.path.splitext(mesh_path)[1].lower()
    if ext == ".obj":
        bpy.ops.wm.obj_import(filepath=mesh_path)
    elif ext in [".glb", ".gltf"]:
        bpy.ops.import_scene.gltf(filepath=mesh_path)
    elif ext == ".ply":
        bpy.ops.wm.ply_import(filepath=mesh_path)
    else:
        print(f"[ERROR] Unsupported file extension: {ext}")
        sys.exit(1)

    # Find imported mesh object
    imported_objs = [obj for obj in bpy.context.scene.objects if obj.type == 'MESH']
    if not imported_objs:
        print("[ERROR] No mesh object found after import")
        sys.exit(1)

    mesh_obj = imported_objs[0]
    mesh_data = mesh_obj.data

    # Check active UV layer
    uv_layers = mesh_data.uv_layers
    if len(uv_layers) == 0:
        report = {
            "verified_in_blender": False,
            "error": "No UV layer found on imported mesh",
            "uv_layers_count": 0,
        }
        print(json.dumps(report))
        sys.exit(1)

    active_uv = uv_layers.active
    uv_name = active_uv.name

    # Inspect UV coordinates with BMesh
    bm = bmesh.new()
    bm.from_mesh(mesh_data)
    bm.faces.ensure_lookup_table()
    uv_layer = bm.loops.layers.uv.verify()

    u_coords = []
    v_coords = []
    degenerate_count = 0
    inverted_count = 0

    for face in bm.faces:
        if len(face.loops) >= 3:
            poly_uvs = [loop[uv_layer].uv for loop in face.loops]
            for uv in poly_uvs:
                u_coords.append(uv.x)
                v_coords.append(uv.y)

            # Check 2D signed area of triangle
            u0, v0 = poly_uvs[0].x, poly_uvs[0].y
            u1, v1 = poly_uvs[1].x, poly_uvs[1].y
            u2, v2 = poly_uvs[2].x, poly_uvs[2].y
            signed_area = 0.5 * ((u1 - u0) * (v2 - v0) - (u2 - u0) * (v1 - v0))
            if abs(signed_area) < 1e-8:
                degenerate_count += 1
            elif signed_area < 0:
                inverted_count += 1

    u_min, u_max = min(u_coords), max(u_coords)
    v_min, v_max = min(v_coords), max(v_coords)

    # Detect UV islands via seam connectivity
    islands_count = 0
    visited_faces = set()
    for face in bm.faces:
        if face.index not in visited_faces:
            islands_count += 1
            queue = [face]
            visited_faces.add(face.index)
            while queue:
                current = queue.pop()
                for edge in current.edges:
                    if not edge.seam:
                        for neighbor in edge.link_faces:
                            if neighbor.index not in visited_faces:
                                visited_faces.add(neighbor.index)
                                queue.append(neighbor)

    bm.free()

    is_within_bounds = (u_min >= -1e-4 and v_min >= -1e-4 and u_max <= 1.0001 and v_max <= 1.0001)

    report = {
        "verified_in_blender": True,
        "blender_version": bpy.app.version_string,
        "object_name": mesh_obj.name,
        "vertex_count": len(mesh_data.vertices),
        "polygon_count": len(mesh_data.polygons),
        "uv_layer_name": uv_name,
        "uv_bounds": {
            "u_min": round(u_min, 5),
            "u_max": round(u_max, 5),
            "v_min": round(v_min, 5),
            "v_max": round(v_max, 5),
        },
        "is_within_0_1_bounds": is_within_bounds,
        "uv_islands_detected": islands_count,
        "degenerate_uv_faces": degenerate_count,
        "inverted_uv_faces": inverted_count,
        "status": "VALID_BLENDER_UV" if is_within_bounds and degenerate_count == 0 else "WARNINGS_FOUND"
    }

    out_json = os.path.splitext(mesh_path)[0] + "_blender_eval.json"
    with open(out_json, "w") as f:
        json.dump(report, f, indent=2)

    print(f"[BLENDER] Verification complete. Report saved to: {out_json}")
    print(json.dumps(report, indent=2))

if __name__ == "__main__":
    verify_uv_in_blender()
