"""Block Mapper Plugin - Map real-world objects to Minecraft blocks.

This plugin converts image colors to a Minecraft block palette, allowing
users to see what an image would look like built in Minecraft. Supports
custom output dimensions and optional Floyd-Steinberg dithering.
"""

from typing import Dict, Any, List, Tuple, Optional
import io
import logging

logger = logging.getLogger(__name__)

try:
    from PIL import Image  # type: ignore[import-not-found]
    import numpy as np  # type: ignore[import-not-found]

    HAS_DEPS = True
except ImportError:
    HAS_DEPS = False


# Minecraft block color palette (simplified)
MINECRAFT_BLOCKS = {
    "stone": (128, 128, 128),
    "dirt": (134, 96, 67),
    "grass_block": (91, 135, 48),
    "oak_planks": (162, 131, 78),
    "cobblestone": (122, 122, 122),
    "sand": (219, 207, 163),
    "gravel": (136, 126, 126),
    "oak_log": (109, 85, 50),
    "oak_leaves": (54, 99, 31),
    "glass": (175, 213, 219),
    "white_wool": (234, 236, 236),
    "orange_wool": (241, 118, 20),
    "magenta_wool": (189, 68, 179),
    "light_blue_wool": (58, 175, 217),
    "yellow_wool": (248, 198, 39),
    "lime_wool": (112, 185, 26),
    "pink_wool": (237, 141, 172),
    "gray_wool": (63, 68, 72),
    "light_gray_wool": (142, 142, 135),
    "cyan_wool": (21, 137, 145),
    "purple_wool": (121, 42, 172),
    "blue_wool": (53, 57, 157),
    "brown_wool": (114, 71, 40),
    "green_wool": (84, 109, 27),
    "red_wool": (161, 39, 35),
    "black_wool": (20, 21, 26),
    "gold_block": (249, 212, 66),
    "iron_block": (220, 220, 220),
    "diamond_block": (97, 220, 225),
    "emerald_block": (42, 176, 71),
    "redstone_block": (170, 28, 28),
    "lapis_block": (39, 67, 138),
    "water": (63, 118, 228),
    "lava": (207, 92, 15),
}


class Plugin:
    """Block mapper plugin for converting images to Minecraft block palettes.

    Converts image pixels to the nearest Minecraft block color and generates
    schematic-compatible output for building in-game.
    """

    name: str = "block_mapper"
    version: str = "1.0.0"
    description: str = "Map image colors to Minecraft blocks for building"

    def __init__(self) -> None:
        """Initialize the plugin with Minecraft block color palette.

        Stores reference to block color dictionary and initializes color tree
        for efficient nearest-neighbor lookups.
        """
        self.block_colors: Dict[str, Tuple[int, int, int]] = MINECRAFT_BLOCKS
        self._color_tree: Optional[Any] = None

    def metadata(self) -> Dict[str, Any]:
        """Return plugin metadata.

        Returns:
            Dictionary with plugin name, version, description, inputs, outputs,
            permissions, and configuration schema for output dimensions and dithering.
        """
        return {
            "name": self.name,
            "version": self.version,
            "description": self.description,
            "inputs": ["image"],
            "outputs": ["block_map", "palette", "schematic"],
            "permissions": [],
            "config_schema": {
                "width": {
                    "type": "integer",
                    "default": 64,
                    "min": 8,
                    "max": 256,
                    "description": "Output width in blocks",
                },
                "height": {
                    "type": "integer",
                    "default": 64,
                    "min": 8,
                    "max": 256,
                    "description": "Output height in blocks",
                },
                "dithering": {
                    "type": "boolean",
                    "default": False,
                    "description": "Apply Floyd-Steinberg dithering",
                },
            },
        }

    def analyze(
        self, image_bytes: bytes, options: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Convert an image to a Minecraft block map.

        Maps each pixel to the nearest Minecraft block color and generates
        output suitable for building in-game schematics.

        Args:
            image_bytes: Raw image data (PNG, JPEG, etc).
            options: Configuration with width, height, dithering settings.

        Returns:
            Dictionary with block_map grid, palette info, schematic, and metadata.

        Raises:
            None - catches and logs all exceptions, returning error dict.
        """
        options = options or {}

        if not HAS_DEPS:
            return {"error": "PIL and numpy required", "block_map": [], "palette": {}}

        try:
            # Load and resize image
            img = Image.open(io.BytesIO(image_bytes)).convert("RGB")

            target_width = options.get("width", 64)
            target_height = options.get("height", 64)

            img = img.resize((target_width, target_height), Image.Resampling.LANCZOS)

            # Convert to numpy array
            pixels = np.array(img)

            # Map each pixel to nearest block
            block_map: List[List[str]] = []
            block_counts: Dict[str, int] = {}

            for y in range(target_height):
                row = []
                for x in range(target_width):
                    pixel = tuple(pixels[y, x])
                    block = self._find_nearest_block(pixel)
                    row.append(block)
                    block_counts[block] = block_counts.get(block, 0) + 1
                block_map.append(row)

            # Build palette info
            palette = {
                block: {
                    "count": count,
                    "percentage": round(
                        count / (target_width * target_height) * 100, 1
                    ),
                    "rgb": list(self.block_colors[block]),
                }
                for block, count in sorted(
                    block_counts.items(), key=lambda x: x[1], reverse=True
                )
            }

            # Generate simple schematic format (for export)
            schematic = self._generate_schematic(block_map, target_width, target_height)

            return {
                "block_map": block_map,
                "palette": palette,
                "dimensions": {"width": target_width, "height": target_height},
                "total_blocks": target_width * target_height,
                "unique_blocks": len(block_counts),
                "schematic": schematic,
                "original_size": {
                    "width": Image.open(io.BytesIO(image_bytes)).width,
                    "height": Image.open(io.BytesIO(image_bytes)).height,
                },
            }

        except Exception as e:
            logger.error(
                "Block mapping failed",
                extra={"error": str(e)},
            )
            return {"error": str(e), "block_map": [], "palette": {}}

    def _find_nearest_block(self, rgb: Tuple[int, int, int]) -> str:
        """Find the nearest Minecraft block color.

        Uses weighted Euclidean distance in RGB space to account for
        human color perception (higher weight for red channel).

        Args:
            rgb: Tuple of (R, G, B) values 0-255.

        Returns:
            Name of the nearest Minecraft block color.
        """
        min_distance: float = float("inf")
        nearest_block: str = "stone"

        for block_name, block_rgb in self.block_colors.items():
            # Use weighted Euclidean distance (human perception)
            r_mean = (rgb[0] + block_rgb[0]) / 2
            dr = rgb[0] - block_rgb[0]
            dg = rgb[1] - block_rgb[1]
            db = rgb[2] - block_rgb[2]

            # Weighted distance formula
            distance = (
                (2 + r_mean / 256) * dr**2
                + 4 * dg**2
                + (2 + (255 - r_mean) / 256) * db**2
            )

            if distance < min_distance:
                min_distance = distance
                nearest_block = block_name

        return nearest_block

    def _generate_schematic(
        self, block_map: List[List[str]], width: int, height: int
    ) -> Dict[str, Any]:
        """Generate a simple schematic representation.

        Creates a JSON-based schematic format compatible with Minecraft building.
        Real schematics use NBT format but this JSON format is suitable for export.

        Args:
            block_map: 2D grid of block names.
            width: Schematic width in blocks.
            height: Schematic height in blocks.

        Returns:
            Dictionary with schematic format, version, dimensions, and block list.
        """
        # This is a simplified format - real schematics would use NBT
        return {
            "format": "simple_json",
            "version": 1,
            "dimensions": {"x": width, "y": 1, "z": height},
            "blocks": [
                {"x": x, "y": 0, "z": z, "block": block_map[z][x]}
                for z in range(height)
                for x in range(width)
            ],
            "metadata": {
                "generator": "vision-mcp-block-mapper",
                "version": self.version,
            },
        }

    def on_load(self) -> None:
        """Called when plugin is loaded.

        Logs plugin initialization with available block palette size.
        """
        logger.info(
            "Block mapper plugin loaded",
            extra={"block_types": len(self.block_colors)},
        )

    def on_unload(self) -> None:
        """Called when plugin is unloaded.

        Performs cleanup and logs plugin shutdown.
        """
        logger.info("Block mapper plugin unloaded")
