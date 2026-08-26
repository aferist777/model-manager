"""Shared prompt material: the realism kit, reference-role blocks and the
beautify agent.

Dialect notes kept for the pipelines that build their own prompts:

Each engine wants a different dialect, so prompts are composed from shared
blocks and then serialised per `style`:

  flux    — FLUX.2 pro / klein. Order matters: subject → action → style →
            context. 30–80 words. NEGATION IS NOT SUPPORTED, so every rule is
            phrased positively. Reference roles are stated explicitly.
  gemini  — Nano Banana 2. Narrative prose, never keyword soup. Edits must say
            out loud what stays unchanged. Multi-ref formula:
            [references] + [relationship instruction] + [new scenario].
  ideogram— Ideogram v3. Short descriptive sentence; realism comes from
            style_type=Realistic, and magic_prompt is turned off so it doesn't
            rewrite our parameters.
  zimage  — Z-Image Turbo. Short and concrete; long prompts hurt turbo models.
  gpt     — GPT Image 2. Imperative instruction, it follows orders literally.

REALISM: the "AI plastic" look comes from retouched training data, so we ask
for the imperfections back (pores, subsurface scattering, asymmetry, flyaways)
and never use the words that override them — see AVOID_WORDS.
"""

# Words that push every model straight back into airbrushed CGI. One of these
# in a prompt cancels out every texture term, so they are banned everywhere
# (including in whatever the beautify agent returns).
AVOID_WORDS = [
    "flawless", "perfect skin", "hyperrealistic", "8k", "4k", "masterpiece",
    "beauty filter", "airbrushed", "smooth skin", "porcelain doll", "cgi",
    "3d render", "highly detailed", "ultra detailed", "stunning", "gorgeous",
]

# ---------------------------------------------------------------- realism kit
SKIN = ("unretouched skin with visible pores and natural subsurface scattering, "
        "fine vellus hair on the cheeks, a few faint freckles and small blemishes, "
        "subtle shadows under the eyes, slight natural facial asymmetry, "
        "uneven natural skin tone, a few loose flyaway hairs, natural lip texture")

LIGHT_PORTRAIT = ("soft daylight from a large window on the left with a gentle falloff "
                  "across the face, soft shadow on the right cheek")
LIGHT_BODY = "even soft studio light from two large softboxes, soft shadow under the feet"

LENS_PORTRAIT = ("shot on a Canon EOS R5 with an 85mm f/1.8 lens at eye level, "
                 "shallow depth of field, sharp focus on the eyes")
LENS_BODY = ("shot on a Canon EOS R5 with a 50mm f/5.6 lens from chest height, "
             "full-length framing with the whole body inside the frame")

GRADE = "neutral colour grading, fine natural film grain, straight out of camera"

# Framing is phrased as what the frame CONTAINS. "shoulders out of frame" reads
# as a negation and every model happily renders shoulders anyway. Word order
# matters too, so the shot type leads the whole prompt.
SHOT_PORTRAIT = ("A photorealistic extreme close-up beauty headshot, the head alone filling "
                 "the entire frame, cropped at the top of the hair and at the jawline")
FRAMING_PORTRAIT = ("the face occupies the full height of the frame, macro-tight headshot "
                    "crop, plain seamless light-grey studio background")
FRAMING_BODY = ("full body from head to toe, standing straight and facing the camera, "
                "feet shoulder-width apart, arms relaxed at the sides, barefoot, "
                "plain seamless light-grey studio background")

WARDROBE = ("wearing a smooth matte dark-grey bodysuit with one uniform unbroken surface, "
            "bare skin and hair the only visible detail, so markings can be added later")

EXPRESSION = "relaxed neutral expression, lips closed, looking straight into the lens"


# ---------------------------------------------------------------- shared bits
def refs_block(roles, style: str = "flux") -> str:
    """Explain the role of every attached reference image, in send order.

    `roles` is a list of ("face" | "pose" | "detail", extra_text) tuples that
    must line up 1:1 with the image list handed to the API."""
    if not roles:
        return ""
    lines = []
    for i, (kind, extra) in enumerate(roles, start=1):
        n = f"image {i}"
        if kind == "base":
            lines.append(f"{n} is the photograph to edit: keep the same person and the "
                         f"same photograph, change only what is asked below")
        elif kind == "face":
            lines.append(f"{n} is this character's face: keep the same person, the same "
                         f"bone structure, the same eyes, nose, mouth and hairline")
        elif kind == "pose":
            lines.append(f"{n} is a grey mannequin used only as a pose and framing guide: "
                         f"copy its stance and full-body framing, and render a real human "
                         f"body with real skin instead of its grey surface")
        else:
            txt = extra or "a detail to add to the character"
            lines.append(f"{n} shows {txt}, integrated into the photograph with matching "
                         f"perspective, lighting and skin contact")
    if style == "gemini":
        return "Use the attached references as follows: " + "; ".join(lines) + "."
    return "Reference images: " + "; ".join(f"{l[0].upper()}{l[1:]}" for l in lines) + "."


def _join(parts) -> str:
    return " ".join(p.strip().rstrip(".") + "." for p in parts if p and p.strip())


# ---------------------------------------------------------------- beautify agent
BEAUTIFY_SYSTEM = (
    "You are a prompt engineer for photorealistic image models. You receive a user's "
    "note (any language) and the reference images it talks about, in order. "
    "Rewrite the note as ONE English paragraph of at most 70 words that tells an image "
    "model exactly what to take from each reference image and where to place it on the "
    "person: name the body part, the side, the approximate size and how it sits on the "
    "skin or body. Refer to the references as 'image 1', 'image 2', … in the same order "
    "they were attached. Describe what you SEE in each image concretely (a tattoo and its "
    "motif, a prosthesis and its material, a wheelchair and its type). "
    "Write only positive statements — never say what should be absent. "
    "Never use these words: " + ", ".join(AVOID_WORDS) + ". "
    "Do not describe the person's face, lighting or camera. "
    "Output only the paragraph, with no preamble, no quotes and no markdown."
)


def beautify_user_request(note: str, n_images: int) -> str:
    """The user-turn text sent to the beautify agent alongside the images."""
    if n_images:
        return (f"{n_images} reference image(s) attached, in order.\n"
                f"User note: {note.strip() or '(no note)'}")
    return f"User note: {note.strip()}"


def strip_banned(text: str) -> str:
    """Last line of defence: drop banned words from agent-written text."""
    out = text or ""
    low = out.lower()
    for w in AVOID_WORDS:
        i = low.find(w)
        while i >= 0:
            out = (out[:i] + out[i + len(w):]).replace("  ", " ")
            low = out.lower()
            i = low.find(w)
    return out.replace(" ,", ",").replace(" .", ".").strip()
