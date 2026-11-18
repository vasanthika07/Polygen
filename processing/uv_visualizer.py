import os
import logging
import numpy as np
from typing import Dict, Any, List, Optional, Tuple

logger = logging.getLogger(__name__)

# Aesthetic palette for color-coding distinct UV islands
CHART_PALETTE = [
    (56, 189, 248),   # Sky blue
    (168, 85, 247),   # Purple
    (244, 114, 182),  # Pink
    (52, 211, 153),   # Emerald
    (251, 191, 36),   # Amber
    (248, 113, 113),  # Red-coral
    (129, 140, 248),  # Indigo
    (45, 212, 191),   # Teal
    (251, 146, 60),   # Orange
    (163, 230, 53),   # Lime
    (232, 121, 249),  # Fuchsia
    (96, 165, 250),   # Blue
    (34, 197, 94),    # Green
    (234, 179, 8),    # Yellow
    (239, 68, 68),    # Red
    (14, 165, 233),   # Cyan
    (167, 139, 250),  # Violet
    (244, 63, 94),    # Rose
    (20, 184, 166),   # Mint
    (245, 158, 11),   # Gold
]

class UVVisualizer:
    """
    Renders 2D UV texture coordinate layouts into preview images.
    Features:
    - Neutral dark studio grid backdrop representing [0, 1] x [0, 1] UV space.
    - Color-coded UV islands with semi-transparent tinted face fills.
    - Antialiased inner wireframe triangle edges.
    - Bold boundary seam edge highlights outlining island perimeters.
    - Telemetry banner detailing resolution, island count, utilization %, and overlap status.
    """

    @classmethod
    def render_uv_layout(
        cls,
        uvs: np.ndarray,
        indices: np.ndarray,
        islands: Optional[List[Dict[str, Any]]] = None,
        output_image_path: Optional[str] = None,
        image_size: Tuple[int, int] = (1024, 1024),
        utilization: Optional[float] = None,
        overlap_info: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Renders a 2D UV layout image and saves it to output_image_path.
        Returns the absolute path to the rendered image.
        """
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        from matplotlib.patches import Polygon as MplPolygon
        from matplotlib.collections import PatchCollection, LineCollection

        w, h = image_size
        dpi = 150
        fig_w, fig_h = w / dpi, h / dpi

        fig, ax = plt.subplots(figsize=(fig_w, fig_h), dpi=dpi)
        fig.patch.set_facecolor("#0b0f19")
        ax.set_facecolor("#111827")

        # 1. Subtle background grid
        grid_ticks = np.linspace(0.0, 1.0, 11)
        ax.set_xticks(grid_ticks)
        ax.set_yticks(grid_ticks)
        ax.grid(True, color="#1e293b", linestyle="--", linewidth=0.5, alpha=0.7)

        # 2. Group faces by island for individual chart coloring
        uvs_arr = np.asarray(uvs, dtype=np.float32)
        indices_arr = np.asarray(indices, dtype=np.int32)
        total_faces = len(indices_arr)

        face_chart_idx = np.zeros(total_faces, dtype=np.int32)
        num_charts = 1

        if islands and len(islands) > 0:
            num_charts = len(islands)
            for c_idx, isl in enumerate(islands):
                f_list = isl.get("faces", [])
                for f in f_list:
                    if f < total_faces:
                        face_chart_idx[f] = c_idx

        # 3. Create polygon patches for UV triangles
        patches = []
        face_colors = []

        for f_idx in range(total_faces):
            tri_uv = uvs_arr[indices_arr[f_idx]]
            poly = MplPolygon(tri_uv, closed=True)
            patches.append(poly)

            c_idx = face_chart_idx[f_idx]
            rgb = CHART_PALETTE[c_idx % len(CHART_PALETTE)]
            # Convert RGB tuple to 0-1 float
            face_colors.append((rgb[0] / 255.0, rgb[1] / 255.0, rgb[2] / 255.0, 0.65))

        collection = PatchCollection(
            patches,
            facecolors=face_colors,
            edgecolors="#1e293b",
            linewidths=0.4,
            alpha=0.85,
        )
        ax.add_collection(collection)

        # 4. Extract and highlight boundary edges (seams) for each island
        seam_lines = []
        if islands and len(islands) > 0:
            for isl in islands:
                isl_faces = isl.get("faces", [])
                if len(isl_faces) == 0:
                    continue
                # Map edges in this island
                edge_count = {}
                for f in isl_faces:
                    tri = indices_arr[f]
                    edges = [(tri[0], tri[1]), (tri[1], tri[2]), (tri[2], tri[0])]
                    for e0, e1 in edges:
                        canonical = (min(e0, e1), max(e0, e1))
                        edge_count[canonical] = edge_count.get(canonical, 0) + 1
                
                # Boundary edges appear exactly once in the island
                for (e0, e1), count in edge_count.items():
                    if count == 1:
                        p0 = uvs_arr[e0]
                        p1 = uvs_arr[e1]
                        seam_lines.append([p0, p1])

        if len(seam_lines) > 0:
            lines_col = LineCollection(seam_lines, colors="#f8fafc", linewidths=1.0, alpha=0.9)
            ax.add_collection(lines_col)

        # 5. Format frame and canvas bounds
        ax.set_xlim(-0.02, 1.02)
        ax.set_ylim(-0.02, 1.02)
        ax.set_aspect("equal")

        # Invert Y axis to match conventional texture coordinate orientation (V=0 at top)
        ax.invert_yaxis()

        ax.tick_params(colors="#64748b", labelsize=7)
        for spine in ax.spines.values():
            spine.set_color("#334155")
            spine.set_linewidth(1.0)

        # 6. Telemetry overlay banner
        util_str = f"{utilization*100:.1f}%" if utilization is not None else "N/A"
        overlap_str = "Clean (0.0% overlap)"
        if overlap_info and overlap_info.get("has_overlap"):
            overlap_str = f"Overlap: {overlap_info.get('overlap_pairs_count', 0)} pairs"

        title_text = (
            f"PolyGen UV Layout  |  Resolution: {w}x{h}  |  Charts: {num_charts}  |  "
            f"Atlas Util: {util_str}  |  {overlap_str}"
        )
        ax.set_title(title_text, color="#e2e8f0", fontsize=8, pad=8, fontweight="medium")

        # 7. Save output file
        if output_image_path is None:
            output_image_path = os.path.abspath("storage/thumbnails/latest_uv_layout.png")

        abs_out = os.path.abspath(output_image_path)
        os.makedirs(os.path.dirname(abs_out), exist_ok=True)
        plt.savefig(abs_out, bbox_inches="tight", facecolor=fig.get_facecolor(), edgecolor="none")
        plt.close(fig)

        logger.info(f"UV layout preview successfully generated and saved to: {abs_out}")
        return abs_out

uv_visualizer = UVVisualizer()
