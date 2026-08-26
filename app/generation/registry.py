"""Image-model registry.

Every model is data: its provider, which modes it can serve (t2i / i2i), how
many reference images it takes, its price, the prompt dialect it wants, and its
real tunable parameters (taken from the live Replicate schemas). The settings
popup renders itself from this list, and `build_payload` turns our generic
settings into that model's exact input object.

Prices are Replicate's published rates. Everything the app generates is 2:3.
"""

CHAR_ASPECT = "2:3"

T2I = "t2i"
I2I = "i2i"


def P(key, label, options, default, desc, kind="enum"):
    return {"key": key, "label": label, "options": options,
            "default": default, "desc": desc, "kind": kind}


MODELS = [
    {
        "id": "prunaai/z-image-turbo",
        "provider": "replicate",
        "label": "Z-Image Turbo",
        "modes": [T2I],
        "max_refs": 0,
        "style": "zimage",
        "price": "$0.0025 / $0.005 / $0.01 per image (≤0.5 / 1 / 2 MP)",
        "desc": "6B, the cheapest and fastest. Text-to-image only, takes no references. "
                "Wants short concrete prompts; guidance stays at 0 as turbo models require.",
        "params": [
            P("size", "Size", ["832x1248 (1 МП)", "1024x1536 (1.6 МП)", "672x1008 (0.7 МП)"],
              "832x1248 (1 МП)", "Always 2:3. More pixels costs more and takes longer."),
            P("num_inference_steps", "Steps", ["6", "8", "10", "12"], "8",
              "8 is the turbo default. More barely helps and only slows it down."),
            P("output_format", "Format", ["png", "jpg", "webp"], "png",
              "png is lossless, which suits later editing."),
            P("go_fast", "Fast mode", ["off", "on"], "off",
              "Extra optimisations: faster, slightly less stable."),
        ],
    },
    {
        "id": "prunaai/z-image-turbo-img2img",
        "provider": "replicate",
        "label": "Z-Image Turbo img2img",
        "modes": [I2I],
        "max_refs": 1,
        "style": "zimage",
        "price": "≈$0.005 per image (z-image-turbo rate, 1 MP)",
        "desc": "The same turbo, but it edits an existing frame. Takes exactly ONE reference, "
                "so it cannot merge a face onto a body — it is a cheap edit of the "
                "current image. Strength controls how far it goes.",
        "params": [
            P("strength", "Edit strength", ["0.3", "0.4", "0.5", "0.6", "0.7", "0.85"], "0.5",
              "0 changes nothing, 1 repaints it. 0.4–0.6 alters a detail and keeps the face."),
            P("num_inference_steps", "Steps", ["6", "8", "10", "12"], "8",
              "8 is the turbo default."),
            P("output_format", "Format", ["png", "jpg", "webp"], "png", "png is lossless."),
        ],
    },
    {
        "id": "black-forest-labs/flux-2-pro",
        "provider": "replicate",
        "label": "FLUX.2 [pro]",
        "modes": [T2I, I2I],
        "max_refs": 8,
        "style": "flux",
        "price": "$0.015 + $0.015 per input and output MP (≈$0.03 for a 1 MP image)",
        "desc": "Black Forest Labs flagship: the best photorealism here, up to 8 references at once. "
                "It does not understand negation, so prompts are positive only.",
        "params": [
            P("resolution", "Resolution", ["0.5 MP", "1 MP", "2 MP", "4 MP"], "1 MP",
              "BFL recommends 2 MP or less; the longest side caps at 2048 px."),
            P("safety_tolerance", "Content filter", ["1", "2", "3", "4", "5"], "2",
              "1 is strictest, 5 is loosest."),
            P("output_format", "Format", ["png", "jpg", "webp"], "png",
              "png is lossless."),
            P("output_quality", "Quality", ["80", "90", "95", "100"], "95",
              "For jpg/webp. png ignores it."),
        ],
    },
    {
        "id": "black-forest-labs/flux-2-klein-4b",
        "provider": "replicate",
        "label": "FLUX.2 klein 4B",
        "modes": [T2I, I2I],
        "max_refs": 5,
        "style": "flux",
        "price": "$1 per 1000 input MP + $1 per 1000 output MP (≈$0.002 for a 1 MP image)",
        "desc": "A 4-step distillation: sub-second images for almost nothing. "
                "Up to 5 references. Good for fast drafts rather than final work.",
        "params": [
            P("output_megapixels", "Resolution", ["0.25", "0.5", "1", "2", "4"], "1",
              "Megapixels on the output image."),
            P("output_format", "Format", ["png", "jpg", "webp"], "png", "png is lossless."),
            P("output_quality", "Quality", ["80", "90", "95", "100"], "95",
              "For jpg/webp."),
            P("go_fast", "Fast mode", ["off", "on"], "off",
              "Optimised run: faster, a little less predictable."),
        ],
    },
    {
        "id": "google/nano-banana-2",
        "provider": "replicate",
        "label": "Nano Banana 2 (Gemini 3.1 Flash Image)",
        "modes": [T2I, I2I],
        "max_refs": 14,
        "style": "gemini",
        "price": "$0.067 (1K) · $0.101 (2K) · $0.151 (4K) per image",
        "desc": "Best here at holding an identity and at merging several references "
                "(up to 14). Wants flowing prose, not a pile of tags. "
                "The default for character sheets and for edits.",
        "params": [
            P("resolution", "Resolution", ["1K", "2K", "4K"], "1K",
              "1K is $0.067, 2K is $0.101, 4K is $0.151 per image."),
            P("output_format", "Format", ["png", "jpg"], "png", "png is lossless."),
        ],
    },
    {
        "id": "ideogram-ai/ideogram-v3-quality",
        "provider": "replicate",
        "label": "Ideogram v3 Quality",
        "modes": [T2I],
        "max_refs": 0,
        "style": "ideogram",
        "price": "$0.09 per image",
        "desc": "The most expensive and the most film-like in texture. It takes no identity reference, "
                "only masked inpainting and style transfer, so it is generate-only.",
        "params": [
            P("style_type", "Style", ["Realistic", "Auto", "General", "None"], "Realistic",
              "Realistic is the photographic render; that is what characters need."),
            P("magic_prompt_option", "Magic Prompt", ["Off", "Auto", "On"], "Off",
              "Ideogram rewrites the prompt its own way; off, so nothing is lost."),
            P("style_preset", "Preset", ["None", "Editorial", "Golden Hour", "Analog Nostalgia",
                                         "Monochrome", "High Contrast"], "None",
              "An artistic preset on top of the style. Rarely wanted for base characters."),
        ],
    },
    {
        "id": "openai/gpt-image-2",
        "provider": "replicate",
        "label": "GPT Image 2",
        "modes": [T2I, I2I],
        "max_refs": 10,
        "style": "gpt",
        "price": "depends on quality (low / medium / high); needs your own OpenAI key or the Replicate proxy",
        "desc": "Follows a literal instruction better than anything else here, which suits precise edits. "
                "Less realistic than FLUX and Nano Banana; skin has to be spelled out.",
        "params": [
            P("quality", "Quality", ["low", "medium", "high", "auto"], "high",
              "Drives price and time directly: low is cheap and coarse, high is costly and detailed."),
            P("background", "Background", ["opaque", "auto", "transparent"], "opaque",
              "Studio shots want opaque."),
            P("output_format", "Format", ["png", "jpeg", "webp"], "png", "png is lossless."),
            P("moderation", "Moderation", ["auto", "low"], "auto",
              "low filters less, but not every account may use it."),
        ],
    },
    {
        "id": "kie/nano-banana-2-lite",
        "provider": "kie",
        "label": "nano-banana-2-lite",
        "modes": [T2I, I2I],
        "max_refs": 14,
        "style": "gemini",
        "price": "≈4 kie.ai credits per image",
        "desc": "The light Nano Banana through kie.ai: cheap and fast, up to 14 references. "
                "Holds an identity less well than the full model, but fine for drafts.",
        "params": [
            P("resolution", "Resolution", ["1K", "2K", "4K"], "1K",
              "Higher resolution costs more and takes longer."),
            P("output_format", "Format", ["png", "jpg"], "png", "png is lossless."),
        ],
    },
]

MODEL_BY_ID = {m["id"]: m for m in MODELS}

PROVIDERS = [("replicate", "Replicate"), ("kie", "kie.ai")]

BEAUTIFY_MODEL = "google/gemini-2.5-flash"

DEFAULTS = {
    T2I: "prunaai/z-image-turbo",
    I2I: "google/nano-banana-2",
}


def models_for(mode: str, provider: str = None):
    return [m for m in MODELS
            if mode in m["modes"] and (provider is None or m["provider"] == provider)]


def provider_of(model_id: str) -> str:
    return (MODEL_BY_ID.get(model_id) or {}).get("provider", "replicate")


def param_defaults(model_id: str) -> dict:
    m = MODEL_BY_ID.get(model_id) or {}
    return {p["key"]: p["default"] for p in m.get("params", [])}


def supports_refs(model_id: str) -> bool:
    return (MODEL_BY_ID.get(model_id) or {}).get("max_refs", 0) > 0


def style_of(model_id: str) -> str:
    return (MODEL_BY_ID.get(model_id) or {}).get("style", "flux")


def _bool(v):
    return str(v).lower() in ("on", "true", "1", "yes")


def build_payload(model_id: str, prompt: str, refs=None, params=None,
                  aspect: str = CHAR_ASPECT) -> dict:
    """Turn our generic settings into this model's exact input object."""
    m = MODEL_BY_ID[model_id]
    p = dict(param_defaults(model_id))
    p.update(params or {})
    refs = [r for r in (refs or []) if r][: m["max_refs"]]
    out = {"prompt": prompt}
    CHAR = aspect

    if model_id == "prunaai/z-image-turbo":
        w, h = p["size"].split(" ")[0].split("x")
        out.update(width=int(w), height=int(h),
                   num_inference_steps=int(p["num_inference_steps"]),
                   guidance_scale=0,                      # required for turbo
                   go_fast=_bool(p["go_fast"]),
                   output_format=p["output_format"], output_quality=95)

    elif model_id == "prunaai/z-image-turbo-img2img":
        out.update(strength=float(p["strength"]),
                   num_inference_steps=int(p["num_inference_steps"]),
                   guidance_scale=0,
                   output_format=p["output_format"], output_quality=95)
        if refs:
            out["image"] = refs[0]          # single reference only

    elif model_id == "black-forest-labs/flux-2-pro":
        out.update(aspect_ratio=CHAR, resolution=p["resolution"],
                   safety_tolerance=int(p["safety_tolerance"]),
                   output_format=p["output_format"],
                   output_quality=int(p["output_quality"]))
        if refs:
            out["input_images"] = refs

    elif model_id == "black-forest-labs/flux-2-klein-4b":
        out.update(aspect_ratio=CHAR, output_megapixels=p["output_megapixels"],
                   go_fast=_bool(p["go_fast"]), output_format=p["output_format"],
                   output_quality=int(p["output_quality"]))
        if refs:
            out["images"] = refs

    elif model_id == "google/nano-banana-2":
        out.update(aspect_ratio=CHAR, resolution=p["resolution"],
                   output_format=p["output_format"])
        if refs:
            out["image_input"] = refs

    elif model_id == "ideogram-ai/ideogram-v3-quality":
        out.update(aspect_ratio=CHAR, style_type=p["style_type"],
                   magic_prompt_option=p["magic_prompt_option"],
                   style_preset=p["style_preset"])

    elif model_id == "openai/gpt-image-2":
        out.update(aspect_ratio=CHAR, quality=p["quality"],
                   background=p["background"], output_format=p["output_format"],
                   moderation=p["moderation"], number_of_images=1)
        if refs:
            out["input_images"] = refs

    return out
