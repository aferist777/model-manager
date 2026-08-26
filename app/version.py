"""App version + changelog (shown in Help)."""

APP_VERSION = "0.15.1"

# newest first; each entry: version, date (YYYY-MM-DD), list of changes
CHANGELOG = [
    {"version": "0.15.1", "date": "2026-07-27", "changes": [
        "Fixed saving photo carousels: every slide shared one filename and overwrote the others — the playlist index now keeps each a distinct file, kept in order.",
        "A carousel with one broken slide no longer fails the whole save; errors reading the files are surfaced instead of stalling on “Saving…”.",
    ]},
    {"version": "0.15.0", "date": "2026-07-27", "changes": [
        "New model is now photo-driven: name + gender on top, your reference photos on the left, the generated character on the right, one Analyze & Generate button between them.",
        "Gemini 2.5 Flash reads the uploaded photos and writes the description; the configured T2I model (⚙ settings) renders the character.",
        "Removed the whole casting flow — Hermes, candidate cards, saved-description library and the 3:2 sheet.",
        "Workspace preview follows the image's own aspect ratio instead of forcing 3:2; list avatars are cut from the face.",
    ]},
    {"version": "0.14.2", "date": "2026-07-24", "changes": [
        "Appearance tab shows the character sheet instead of the retired portrait / full-body images; the 👤 / 🧍 toggle is gone.",
        "The sheet is shown whole at 3:2 and pinned to the top of the column instead of being centre-cropped.",
        "Model list and header avatars are cut from the sheet's portrait panel, not from the middle of the sheet.",
    ]},
    {"version": "0.14.1", "date": "2026-07-24", "changes": [
        "Fixed Generate sheets failing with a bare \"False\" — the click signal's checked flag was landing in the model argument.",
        "Select all / Deselect all above the candidate grid.",
        "The casting director now treats the brief as a direction and casts people you did not describe, instead of restating the brief.",
        "Candidate cards are compact: smaller sheet strip and a truncated blurb (More still has everything).",
        "The whole interface and every agent answer are English; only your own brief may be in any language.",
        "Casting answers survive unescaped quotes inside JSON — fields are recovered key by key when parsing fails.",
    ]},
    {"version": "0.14.0", "date": "2026-07-24", "changes": [
        "Character creation rebuilt around casting: a free-text brief goes to Hermes 4 405B (OpenRouter) playing casting director, one request per candidate, run in parallel.",
        "Candidates arrive as cards two per row — short blurb, More for the full write-up, Save to a reusable library, and a Generated / Saved switch.",
        "Tick several candidates and render their character sheets at once; exactly one sheet is bound to the model with Use this.",
        "Character sheet is a fixed 3:2 layout at 4K: portrait plus two macro insets on the left, full body front in the centre, back view on the right, neutral leotard, no lettering.",
        "The structured appearance sheet from the casting agent is stored with the model and drives every later generation.",
        "Removed: dropdown parameters, the two-stage portrait/body generator, the mannequin, and Bio / Character-personality from the profile.",
    ]},
    {"version": "0.13.0", "date": "2026-07-23", "changes": [
        "Drafts are now one big image filling the preview column, paged with ‹ › and a counter — no more thumbnail strips.",
        "Extra details and Additional details stay hidden until the first portrait exists.",
        "Generate button is only as wide as its label.",
        "New edit model: prunaai/z-image-turbo-img2img (single reference, strength slider).",
        "Model cards have a hover × to delete, with confirmation; the model's own image files go with it.",
        "Unhandled errors no longer close the app — they are logged to data/crash.log and shown in a dialog.",
    ]},
    {"version": "0.12.0", "date": "2026-07-23", "changes": [
        "Replicate engine: FLUX.2 [pro], FLUX.2 klein 4B, Nano Banana 2, GPT Image 2, Ideogram v3 Quality and Z-Image Turbo, alongside kie.ai.",
        "Generation settings split into two columns — T2I for fresh generations, I2I for edits — each with its own aggregator, model, price, measured average time and that model's real parameters.",
        "Prompts rewritten per model dialect (FLUX / Gemini / Ideogram / turbo / GPT) with a realism kit: pores, subsurface scattering, asymmetry, flyaways, camera and lens — and a ban list of the words that cause the plastic look.",
        "Body type moved to the portrait stage (it shapes the face too) and is locked on the body stage so the full body matches the portrait.",
        "Extra detail images now require a note saying what to take from each one and where to put it; the note plus the images go through a Gemini beautify agent before generation.",
        "apply works on the note alone — extra images are optional for it.",
    ]},
    {"version": "0.11.0", "date": "2026-07-23", "changes": [
        "Generation feedback: the target image area blurs and shows a spinner, a slim progress bar and an adaptive countdown (the first run of a kind counts up, later ones predict from measured times).",
        "All controls lock while a generation is running — no double-clicking Generate.",
        "Reference images now actually reach the model: imgbb hosting uploads the portrait, the mannequin and the three extra-detail slots for kie.ai image_input.",
        "Character profile popup is wider with three info columns; Other notes removed.",
        "Splitter handles widened to 5px so panes are easy to resize.",
    ]},
    {"version": "0.10.0", "date": "2026-07-22", "changes": [
        "Stage 2 (body) is live: body params (body type, height, build, posture), a new full-body mannequin, Generate body → full-body drafts, saved to the model.",
        "Appearance preview has a portrait / full-body toggle in the top-right corner.",
    ]},
    {"version": "0.9.2", "date": "2026-07-22", "changes": [
        "Click a generated image (drafts double-click, profile portrait, appearance preview, stage-2 portrait) to view it full-size; click outside to close.",
        "Edit→Generate is now the full two-stage flow tied to the model: portrait saved on the stage-1→2 transition; if a portrait already exists, opens straight at stage 2 with the portrait filling the preview column.",
    ]},
    {"version": "0.9.1", "date": "2026-07-22", "changes": [
        "rnd fills only required fields; new fx button randomizes only the optional ones (kept 'Random' by default).",
        "Generate drafts moved under the dropdowns; additional-details apply button is square, right of the box, orange when active.",
        "Saved dropdown selections (Model.appearance) preload when a portrait already exists; saved only on explicit Save.",
    ]},
    {"version": "0.9.0", "date": "2026-07-22", "changes": [
        "Two-stage character generator: Stage 1 face (required ★ dropdowns gate Generate; additional details unlock after first draft), Stage 2 body shell with a T-pose mannequin.",
        "Removed the Features dropdown; Body/Height move to Stage 2.",
        "Portrait generator prefills the model name; model list cards are thinner.",
    ]},
    {"version": "0.8.0", "date": "2026-07-22", "changes": [
        "Profile editor: Generate opens the 9:16 portrait generator on top; shows read-only Gender/Ethnicity/Age/Body/Height.",
        "Content tab: platform filter toggles for posts.",
        "Model list shows only avatar + name; Appearance tab is view-only.",
        "Reference ★/🗑 buttons clearly show enabled vs disabled.",
    ]},
    {"version": "0.7.0", "date": "2026-07-21", "changes": [
        "Reference tiles: click to select, double-click to view; ★ favorite and 🗑 delete toolbar (favorites shown first).",
        "Content tab: single Create post button opens a platform → type → reference flow.",
        "Instagram webview scrollbar hidden to free space.",
    ]},
    {"version": "0.6.0", "date": "2026-07-21", "changes": [
        "Instagram opens on the Reels page; address bar above the webview.",
        "Save button downloads the open reel/carousel (yt-dlp, WebView2 login) into References.",
        "Reference cards show real thumbnails with a corner delete + type badge; click opens a viewer (video plays, carousels page).",
        "Old link references get a 'Download' button; 9:16 portrait slot added to the profile editor.",
    ]},
    {"version": "0.5.0", "date": "2026-07-21", "changes": [
        "Edit button opens a full character profile editor (bio, personality, socials, notes) with unsaved-changes guard.",
        "Social media fields (Instagram/Telegram/TikTok/YouTube) on the Appearance tab.",
        "rnd now also generates a gender-appropriate English name.",
        "Instagram webview fills the whole panel (fixed high-DPI right/bottom gap).",
    ]},
    {"version": "0.4.0", "date": "2026-07-21", "changes": [
        "Instagram panel now uses embedded Edge WebView2 — reels and video play.",
        "Persistent Instagram login (survives restarts).",
        "Compact character generator: two-column dropdowns, smaller rows.",
        "Generation settings (gear): aggregator + engine params (resolution/format/aspect/drafts).",
    ]},
    {"version": "0.3.0", "date": "2026-07-21", "changes": [
        "Top menu bar: File / Settings / Help.",
        "Settings → API keys, stored in Windows Credential Manager.",
        "Character generator: dropdowns with descriptions, rnd auto-fill (no conflicting traits), additional-details field.",
        "Per-parameter 'g' buttons for targeted edits after the first generation.",
        "Draft generation via kie.ai nano-banana-2-lite.",
    ]},
    {"version": "0.2.0", "date": "2026-07-21", "changes": [
        "References moved to a shared board on the References tab.",
        "Instagram panel cleaned up; login/password stored via the OS credential store.",
        "Compact fonts, larger element spacing, launches maximized.",
    ]},
    {"version": "0.1.0", "date": "2026-07-21", "changes": [
        "Initial 3-pane shell: model list, workspace tabs, Instagram webview.",
        "Create-model wizard and reference cards.",
    ]},
]
