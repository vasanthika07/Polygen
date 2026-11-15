"""
Comprehensive domain dictionary and taxonomy for 3D generative asset extraction.
Provides deterministic lexical mappings for objects, categories, materials,
colors, surface finishes, lighting, special effects, and geometric constraints.
"""

from typing import Dict, List, Set

CATEGORIES: Dict[str, List[str]] = {
    "weapons": [
        "broadsword", "sword", "katana", "claymore", "rapier", "saber", "scimitar",
        "dagger", "knife", "blade", "battleaxe", "axe", "halberd", "warhammer", "hammer",
        "mace", "flail", "spear", "lance", "pike", "trident", "bow", "crossbow",
        "longbow", "shield", "buckler", "rifle", "pistol", "blaster", "cannon",
        "staff", "wand", "glaive", "polearm"
    ],
    "furniture": [
        "chair", "armchair", "throne", "stool", "bench", "couch", "sofa", "loveseat",
        "table", "dining table", "coffee table", "desk", "workstation", "nightstand",
        "bookshelf", "bookcase", "shelf", "cabinet", "cupboard", "wardrobe", "credenza",
        "bed", "four-poster bed", "hammock", "lamp", "lantern", "chandelier", "sconce",
        "mirror", "chest of drawers", "dresser", "barstool"
    ],
    "vehicles": [
        "car", "sports car", "supercar", "sedan", "truck", "pickup", "van",
        "motorcycle", "bike", "bicycle", "scooter", "rover", "buggy",
        "spaceship", "starfighter", "cruiser", "shuttle", "rocket", "ufo",
        "airplane", "jet", "fighter jet", "glider", "helicopter", "airship", "zeppelin",
        "boat", "ship", "galleon", "pirate ship", "sailboat", "yacht", "submarine",
        "tank", "hovercraft", "train", "locomotive", "carriage", "wagon"
    ],
    "architecture": [
        "castle", "fortress", "citadel", "keep", "tower", "watchtower", "bastion",
        "cathedral", "church", "temple", "shrine", "chapel", "monastery", "pagoda",
        "cottage", "cabin", "hut", "house", "mansion", "villa", "palace",
        "bunker", "shelter", "base", "outpost", "space station",
        "bridge", "aqueduct", "viaduct", "gate", "gateway", "arch", "archway",
        "pillar", "column", "obelisk", "monolith", "pyramid", "ruins", "wall"
    ],
    "animals": [
        "dragon", "wyvern", "drake", "wolf", "hound", "dog", "fox", "coyote",
        "lion", "tiger", "leopard", "panther", "cheetah", "jaguar", "cat",
        "bear", "grizzly", "polar bear", "stag", "deer", "elk", "moose", "antelope",
        "horse", "stallion", "steed", "unicorn", "pegasus",
        "eagle", "hawk", "falcon", "owl", "raven", "crow", "phoenix", "griffin", "gryphon",
        "snake", "serpent", "viper", "cobra", "lizard", "gecko", "chameleon",
        "spider", "scorpion", "beetle", "crab", "shark", "whale", "dolphin", "octopus"
    ],
    "fantasy_props": [
        "treasure chest", "chest", "crate", "barrel", "urn", "vase", "cauldron",
        "potion", "potion bottle", "flask", "vial", "elixir",
        "magic orb", "orb", "crystal ball", "crystal", "gem", "runestone", "relic",
        "tome", "spellbook", "grimoire", "scroll", "map", "compass",
        "amulet", "talisman", "pendant", "necklace", "ring", "crown", "circlet", "tiara",
        "chalice", "goblet", "cup", "horn", "grail",
        "portal", "gate", "altar", "brazier", "totem", "hourglass"
    ]
}

MATERIAL_SYNONYMS: Dict[str, str] = {
    # Metals
    "rusted iron": "rusted metal",
    "weathered iron": "rusted metal",
    "corroded iron": "rusted metal",
    "rusted metal": "rusted metal",
    "rust": "rusted metal",
    "rusted": "rusted metal",
    "rusty": "rusted metal",
    "steel": "forged steel",
    "forged steel": "forged steel",
    "stainless steel": "polished steel",
    "polished steel": "polished steel",
    "damascus": "damascus steel",
    "damascus steel": "damascus steel",
    "iron": "cast iron",
    "cast iron": "cast iron",
    "bronze": "antique bronze",
    "antique bronze": "antique bronze",
    "brass": "tarnished brass",
    "copper": "oxidized copper",
    "gold": "ornate gold",
    "golden": "ornate gold",
    "silver": "burnished silver",
    "titanium": "brushed titanium",
    "chrome": "reflective chrome",
    "metallic": "polished metal",
    "metal": "brushed metal",
    
    # Gems & Minerals
    "sapphire": "blue sapphire",
    "blue sapphire": "blue sapphire",
    "ruby": "red ruby",
    "red ruby": "red ruby",
    "emerald": "green emerald",
    "green emerald": "green emerald",
    "diamond": "faceted diamond",
    "obsidian": "black obsidian",
    "amethyst": "purple amethyst",
    "quartz": "translucent quartz",
    "crystal": "glowing crystal",
    "marble": "white marble",
    "granite": "rough granite",
    "stone": "weathered stone",
    "rock": "rough stone",
    "sandstone": "chiseled sandstone",
    "cobblestone": "aged cobblestone",
    
    # Wood & Organics
    "wood": "aged wood",
    "wooden": "aged wood",
    "oak": "carved oak wood",
    "carved oak": "carved oak wood",
    "mahogany": "polished mahogany",
    "pine": "rustic pine",
    "driftwood": "weathered driftwood",
    "bark": "tree bark",
    "leather": "worn leather",
    "hide": "tanned hide",
    "fur": "thick animal fur",
    "bone": "ancient bone",
    "ivory": "carved ivory",
    "antler": "polished antler",
    "cloth": "woven fabric",
    "fabric": "textured fabric",
    "velvet": "rich velvet",
    "silk": "smooth silk",
    
    # Synthetics & Glass
    "glass": "translucent glass",
    "stained glass": "stained glass",
    "carbon fiber": "woven carbon fiber",
    "ceramic": "glazed ceramic",
    "porcelain": "fine porcelain",
    "concrete": "reinforced concrete"
}

COLOR_SYNONYMS: Dict[str, str] = {
    # Dark & Earthy
    "dark brown": "dark brown",
    "brown": "dark brown",
    "tan": "tan",
    "beige": "warm beige",
    "steel grey": "steel grey",
    "grey": "slate grey",
    "gray": "slate grey",
    "charcoal": "dark charcoal",
    "black": "jet black",
    "dark": "deep dark",
    
    # Blues
    "blue": "blue",
    "azure": "azure blue",
    "sapphire": "deep sapphire blue",
    "cyan": "glowing cyan",
    "navy": "navy blue",
    "teal": "deep teal",
    "sky blue": "sky blue",
    
    # Reds & Warm
    "red": "crimson red",
    "crimson": "crimson red",
    "scarlet": "vivid scarlet",
    "rust": "rust orange",
    "orange": "burnt orange",
    "amber": "warm amber",
    "yellow": "golden yellow",
    "gold": "burnished gold",
    "golden": "burnished gold",
    "brass": "warm brass",
    "bronze": "antique bronze",
    
    # Greens
    "green": "emerald green",
    "emerald": "emerald green",
    "olive": "olive green",
    "forest green": "deep forest green",
    "lime": "neon green",
    "moss": "mossy green",
    
    # Purples & Whites
    "purple": "royal purple",
    "violet": "deep violet",
    "magenta": "neon magenta",
    "white": "pure white",
    "bone white": "bone white",
    "silver": "polished silver"
}

STYLE_PATTERNS: Dict[str, List[str]] = {
    "fantasy medieval": [
        "medieval", "fantasy", "sword", "broadsword", "knight", "castle", "dragon",
        "shield", "armor", "dungeon", "sorcerer", "magic", "rune", "hilt", "blade",
        "goblet", "throne", "ancient", "gothic"
    ],
    "sci-fi cyberpunk": [
        "sci-fi", "scifi", "cyberpunk", "cyber", "neon", "laser", "futuristic",
        "holographic", "mech", "robot", "cyborg", "android", "plasma", "spaceship",
        "starfighter", "visor", "nanotech", "quantum"
    ],
    "steampunk victorian": [
        "steampunk", "victorian", "brass", "copper", "clockwork", "gear", "cogs",
        "steam", "boiler", "airship", "zeppelin", "barometer", "goggles"
    ],
    "photorealistic": [
        "realistic", "hyperrealistic", "photorealistic", "ultra realistic", "lifelike",
        "real-world", "detailed 8k", "studio lighting"
    ],
    "stylized cartoon": [
        "stylized", "cartoon", "low-poly", "pixar", "toon", "hand-painted",
        "chibi", "cute", "anime", "cell-shaded", "isometric"
    ],
    "modern minimalist": [
        "modern", "minimalist", "contemporary", "sleek", "scandinavian", "bauhaus",
        "clean lines", "industrial design", "matte finish"
    ]
}

SURFACE_DETAIL_TERMS: Set[str] = {
    "rust", "rusted", "scratches", "scratched", "corrosion", "corroded",
    "weathering", "weathered", "patina", "chiseled", "carved", "engraved",
    "runes", "filigree", "battle damage", "dents", "dented", "worn",
    "polished", "glossy", "matte", "cracks", "cracked", "bevelled",
    "rough", "smooth", "hammered", "rivets", "stitched", "embossed",
    "moss", "mossy", "oxidized", "brushed"
}

LIGHTING_TERMS: Dict[str, str] = {
    "cinematic": "cinematic dramatic lighting with directional highlights",
    "studio": "neutral three-point studio lighting with balanced fill",
    "dramatic": "high-contrast dramatic rim lighting",
    "volumetric": "moody volumetric fog and atmospheric lighting",
    "neon": "vibrant neon cyberpunk lighting with colored reflections",
    "golden hour": "warm sunset golden hour sunlight",
    "dark": "low-key gothic ambient shadows"
}

SPECIAL_EFFECTS_TERMS: Dict[str, str] = {
    "glowing": "emissive glow",
    "glow": "emissive glow",
    "blue sapphire in the hilt": "blue emissive glow",
    "luminescent": "bioluminescent radiance",
    "radiant": "radiant energy aura",
    "neon": "neon illumination",
    "fire": "flaming particle fire",
    "flame": "flaming fire aura",
    "plasma": "plasma conduit beam",
    "sparks": "electric spark discharge",
    "electricity": "crackling lightning arcs",
    "smoke": "drifting smoke plume",
    "moss covered": "mossy organic overgrowth"
}

CATEGORY_GEOMETRY_RULES: Dict[str, List[str]] = {
    "weapons": [
        "watertight manifold mesh without self-intersections",
        "bilateral symmetry along primary blade axis",
        "sharp bevelled cutting edge geometry",
        "tapered cross-guard and balanced ergonomic pommel hilt",
        "clean quad-dominant topology suitable for rigging"
    ],
    "furniture": [
        "planar resting base aligned with ground plane (y=0)",
        "orthogonally aligned weight-bearing legs and joints",
        "ergonomic contours for seat and armrests",
        "bevelled perimeter edges to avoid razor-sharp polygon boundaries",
        "symmetric volumetric silhouette"
    ],
    "vehicles": [
        "aerodynamic streamlined hull contouring",
        "bilateral wheel and chassis symmetry",
        "isolated modular wheel geometries with ground clearance",
        "recessed cockpit or windshield cavity",
        "hard-surface bevelled panels with uniform edge loops"
    ],
    "architecture": [
        "modular structural grid alignment",
        "stable planar foundation footprint",
        "watertight exterior masonry walls without non-manifold leaks",
        "recessed arched entryways and window frame embrasures",
        "level vertical load-bearing pillars and battlements"
    ],
    "animals": [
        "anatomical bilateral limb and feature symmetry",
        "organic continuous manifold skin mesh without topological breaks",
        "t-pose or neutral rest pose with ground-contact paws/feet",
        "curved muscle and joint geometry suitable for deformation skinning",
        "smooth vertex normal transitions along fur/scales"
    ],
    "fantasy_props": [
        "compact volumetric center of mass",
        "stable resting base or integrated floating connection anchors",
        "intricately carved relief details on surface shells",
        "embedded cavity for magical gems or emissive cores",
        "clean watertight glTF export compliance"
    ]
}

CATEGORY_TEXTURE_RULES: Dict[str, List[str]] = {
    "weapons": [
        "1024x1024 or 2048x2048 PBR texture channels (Albedo, Tangent Normal, Roughness, Metallic)",
        "micro-scratches and edge wear masks in roughness channel",
        "metalness channel masked for blade steel vs organic grip wrap",
        "emissive channel map for glowing gems or runes"
    ],
    "furniture": [
        "high-fidelity diffuse albedo with realistic wood/leather grain",
        "subtle normal map depicting chiseled reliefs and grain crevices",
        "low metallic (0.0) with localized varnish roughness highlights",
        "ambient occlusion baking to accent mortise-and-tenon joints"
    ],
    "vehicles": [
        "metallic automotive clearcoat albedo with carbon accent trim",
        "normal map detailing panel seams, bolt rivets, and air intakes",
        "high specular reflection with variable tire rubber roughness",
        "emissive headlight and tail glow maps"
    ],
    "architecture": [
        "weathered stone masonry albedo with mortar joint variations",
        "chiseled brick depth encoded in tangent normal map",
        "roughness variations indicating water drainage and moss growth",
        "ambient occlusion map emphasizing arched overhangs and eaves"
    ],
    "animals": [
        "detailed organic albedo depicting natural skin/fur patterning",
        "high-frequency normal map for muscle strands, scales, or fur tufts",
        "dielectric roughness map with moist specular accents on nose/eyes",
        "optional bioluminescent emissive mask for fantasy variants"
    ],
    "fantasy_props": [
        "richly saturated albedo featuring aged metals and mystical inlays",
        "high-contrast normal map capturing chiseled glyphs and filigree",
        "separated roughness maps for tarnished metal vs crystalline facets",
        "high-intensity emissive map for magical glows and pulsing cores"
    ]
}

STANDARD_NEGATIVE_PROMPT: List[str] = [
    "low polygon budget breakdown",
    "blurry low-resolution texture",
    "non-manifold geometry",
    "floating disconnected artifact polygons",
    "self-intersecting degenerate faces",
    "asymmetric warping on symmetric assets",
    "unwelded open boundary seams",
    "overexposed flat white highlights",
    "distorted UV stretching"
]

