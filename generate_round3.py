#!/usr/bin/env python3
"""
Vermillion Logo Generator — Round 3
Informed by Noa's 4 mood boards: Brick Heritage, Home, Clay/Land/Earth, Nature/Connection

Key learnings from rounds 1-2:
- Round 1-2 logos were too illustrative/complex
- Noa wants: typography-dominant, minimal, sophisticated, luxury hospitality feel
- Embossed/stamped/tactile aesthetic (clay seal, leather tag, wax stamp vibe)
- Simple geometric marks — ultra-minimal icons if any
- Warm earth tones — terracotta, cream, deep brown, muted vermillion
- Think "Sur La Terre", "Louve", "Ever House", "Golden Oaks", "Novaterra"

Usage:
    OPENAI_API_KEY="sk-..." python3 generate_round3.py
"""

import os
import sys
import base64
import time
from pathlib import Path
from typing import Optional
from PIL import Image
import io
import httpx

API_URL = "https://api.openai.com/v1/images/generations"
MODEL = "gpt-image-1"
FALLBACK_MODEL = "dall-e-3"

OUTPUT_DIR = Path(__file__).parent / "concepts" / "round3"

# Updated style suffix — more refined, less "vector logo" and more "brand identity"
STYLE_BASE = (
    "This is a premium brand identity design for a luxury master-planned residential community. "
    "The design should feel like it belongs on embossed stationery, a leather-bound portfolio, "
    "or stamped into terracotta clay. Clean, elegant, timeless. "
    "The word 'VERMILLION' must be spelled correctly with two L's. "
    "Place on a clean white background. No photorealistic textures. No 3D rendering. "
    "No stock photo elements. No clipart. This should look like it was designed by Pentagram or "
    "a top branding agency — sophisticated, restrained, confident."
)

# ============================================================
# CONCEPT PROMPTS — organized by Noa's mood board categories
# ============================================================

PROMPTS = {
    # --- BRICK HERITAGE (Mood Board 1) ---
    # Inspiration: "Brickhouse Premium", "Brickland", "Brickworks", "Brick Capital"
    # Clean typography with subtle brick/geometric references. Monograms.

    "r3-01-brick-wordmark": (
        "Design a typographic logo for 'VERMILLION' — a luxury community in Sanford, NC, "
        "the historic 'Brick Capital of the USA.' "
        "This is a WORDMARK-ONLY design — no icon, no symbol, just beautiful typography. "
        "Set 'VERMILLION' in an elegant high-contrast serif typeface (like Didot, Bodoni, or "
        "a refined transitional serif). Use wide letter-spacing. "
        "Below the wordmark, in much smaller light-weight sans-serif or small caps, set "
        "'A MATTAMY HOMES COMMUNITY' as a tagline. "
        "The type is set in a deep warm brown-red (#6B3028). "
        "The design should feel like upscale stationery or a luxury hotel brand. "
        "Extremely minimal — just type, perfectly set. " + STYLE_BASE
    ),

    "r3-02-brick-monogram": (
        "Design a monogram logo for 'VERMILLION' — a luxury community in Sanford, NC. "
        "Create a large elegant 'V' letterform as the primary mark. "
        "The 'V' should be rendered in a refined high-contrast serif style (Didot/Bodoni-inspired) "
        "with a subtle detail: thin horizontal lines within the letter strokes that reference "
        "brick coursing — like looking at the edge of a brick wall. Very subtle, not literal. "
        "Below the V monogram, set 'VERMILLION' in matching serif type with wide letter-spacing. "
        "Color: deep terracotta (#7A3428) on white. "
        "Think luxury hotel monogram — Ritz Carlton level sophistication. " + STYLE_BASE
    ),

    "r3-03-brick-minimal-B": (
        "Design a logo for 'VERMILLION' — a luxury master-planned community. "
        "MARK: A simple, bold geometric 'V' formed from two clean angular strokes. "
        "The strokes have flat squared-off ends (like cut brick edges). "
        "The 'V' is bold and confident, sitting above the wordmark. "
        "WORDMARK: 'VERMILLION' in a clean modern serif with generous tracking. "
        "Below that in tiny caps: 'SANFORD, NORTH CAROLINA' "
        "Color: solid deep vermillion (#7A3428) on white background. "
        "Ultra-clean, geometric, architectural. Like 'Brickworks' or 'Brick Capital' branding. " + STYLE_BASE
    ),

    "r3-04-brick-stamp": (
        "Design a logo for 'VERMILLION' that looks like it was stamped or pressed into material. "
        "The design is contained within a clean circle or rounded rectangle border. "
        "Inside: 'VERMILLION' in strong serif caps across the center, with 'SANFORD • NC' "
        "in small text along the bottom curve, and 'EST. 2026' at the top. "
        "Optional: a tiny geometric V or brick motif in the center above the main text. "
        "The whole thing should look like a wax seal, a pressed clay stamp, or a luxury "
        "brand badge. Single color: deep terracotta red (#7A3428) on white. "
        "Think ceramic maker's mark or artisan pottery stamp. " + STYLE_BASE
    ),

    # --- HOME (Mood Board 2) ---
    # Inspiration: "Ever House", "The Club Real Estate Co", "Victoria Levitan", "Quaint & Cozy"
    # Editorial, type-forward, warm tones, very clean

    "r3-05-home-editorial": (
        "Design a logo for 'VERMILLION' — a luxury master-planned community. "
        "This should look like an editorial magazine masthead or a luxury real estate brand. "
        "Set 'VERMILLION' in an elegant serif typeface — think Cormorant Garamond, "
        "Playfair Display, or Freight Big. The letters should be beautifully proportioned "
        "with high stroke contrast. "
        "Below in a thin sans-serif or italic, a subtitle: 'a place to call home' "
        "The entire design is type-only. No icons. No symbols. Just exquisite typography. "
        "Color: warm deep red (#8B4332) on white background. "
        "This should feel like 'The Club Real Estate Co' or 'Ever House' — refined, "
        "warm, inviting, editorial. " + STYLE_BASE
    ),

    "r3-06-home-mixed-type": (
        "Design a logo for 'VERMILLION' — a luxury master-planned community. "
        "Use a typographic contrast approach: 'VERMILLION' set with the first part "
        "'VERMIL' in a bold serif and 'LION' in an elegant italic serif — or the full word "
        "in bold serif with a decorative italic ampersand or 'V' initial drop cap. "
        "Below: 'A Mattamy Homes Community' in light-weight small caps sans-serif. "
        "The design plays with typographic weight and style within the word itself. "
        "Color: rich warm vermillion (#7A3428) on white. "
        "Editorial luxury feel, like a high-end lifestyle brand. " + STYLE_BASE
    ),

    "r3-07-home-house-icon": (
        "Design a minimal logo for 'VERMILLION' — a luxury master-planned community. "
        "MARK: An ultra-simplified, abstract house/roof shape made from just 2 thin lines "
        "forming a peak/chevron (like a very minimal roofline or inverted V). "
        "The lines are thin and elegant — not a children's drawing of a house, but an "
        "architect's abstraction. Think one thin line bent into a peak shape. "
        "WORDMARK: Below, 'VERMILLION' in refined serif type with wide letter-spacing. "
        "Color: warm terracotta (#7A3428) on white. "
        "Inspired by 'Quaint & Cozy' simplicity and 'Ever House' elegance. " + STYLE_BASE
    ),

    "r3-08-home-stacked": (
        "Design a stacked typographic logo for 'VERMILLION'. "
        "The word is split across two lines: 'VER' on top and 'MILLION' below, or "
        "'VERMIL' on top and 'LION' below — choose whichever break creates better visual balance. "
        "Use a bold, elegant serif typeface. The letters should be large and fill the space. "
        "Optional: a thin decorative line or small diamond ornament between the two lines. "
        "Below the stacked word, very small: 'SANFORD, NORTH CAROLINA' in light sans-serif. "
        "Color: deep vermillion red (#6B3028) on white. "
        "This should feel like a luxury hospitality brand — bold, confident, minimal. " + STYLE_BASE
    ),

    # --- CLAY / LAND / EARTH (Mood Board 3) ---
    # Inspiration: "Louve", "Ceramico", "Sur La Terre", "Sophia Hotel", "Studio Boheme"
    # Embossed/debossed, terracotta, leather, tactile, premium material

    "r3-09-clay-seal": (
        "Design a logo for 'VERMILLION' inspired by clay pottery and ceramic maker's marks. "
        "The logo is circular — like a wax seal or a stamp pressed into wet clay. "
        "In the center: a stylized 'V' monogram in a refined serif style. "
        "Around the 'V' in a circle: 'VERMILLION' along the top arc and "
        "'NORTH CAROLINA' along the bottom arc, both in elegant spaced-out capitals. "
        "Between the text arcs: small decorative dots or thin line dividers. "
        "Single color: terracotta red (#8B5E3C) on white background. "
        "The entire design should look like it could be embossed into leather or "
        "pressed into terracotta clay. Think ceramic studio branding. " + STYLE_BASE
    ),

    "r3-10-clay-earthy": (
        "Design a logo for 'VERMILLION' — a luxury community rooted in North Carolina's "
        "Piedmont clay earth. "
        "MARK: A simple abstract shape — either a circle, an arch, or a rounded rectangle — "
        "that evokes a piece of clay, a stone, or an earth form. Inside or overlapping this "
        "shape, the letter 'V' is subtly embedded, like it was carved or pressed into the surface. "
        "WORDMARK: 'VERMILLION' in elegant serif capitals with wide tracking beneath the mark. "
        "Color: warm earthy terracotta (#8B5E3C) on cream/white. "
        "Think 'Sur La Terre' or 'Ceramico' — handcrafted, tactile, earthy sophistication. " + STYLE_BASE
    ),

    "r3-11-clay-terre": (
        "Design a logo for 'VERMILLION' inspired by French/Italian earth-toned luxury brands. "
        "The design is purely typographic — 'VERMILLION' set in a refined, slightly condensed "
        "serif typeface. The letters have subtle warmth — slightly rounded terminals, or a "
        "humanist quality that feels hand-set rather than digital. "
        "Above the wordmark: a tiny icon — just a simple circle with a 'V' inside it, "
        "like a wax seal or a coin. Very small, like a maker's mark. "
        "Below the wordmark: 'A Mattamy Homes Community' in thin spaced small caps. "
        "Color: warm brown (#6B4A3A) on white background. "
        "Inspired by 'Louve' and 'Sur La Terre' — understated luxury, earth tones. " + STYLE_BASE
    ),

    "r3-12-clay-arch": (
        "Design a logo for 'VERMILLION' — a luxury master-planned community. "
        "MARK: A simple arch shape — like a doorway, a kiln opening, or a Roman arch. "
        "Inside the arch, the letter 'V' sits centered. The arch represents both "
        "architectural heritage (brick kilns of Sanford) and welcome/entry to the community. "
        "The arch line is thin and elegant, not heavy. "
        "WORDMARK: 'VERMILLION' in refined serif below the arch mark, with wide letter-spacing. "
        "Color: deep terracotta (#7A3428) on white. "
        "The feel is 'Sophia Hotel' meets artisan pottery — elegant, warm, grounded. " + STYLE_BASE
    ),

    # --- NATURE / CONNECTION (Mood Board 4) ---
    # Inspiration: "Novaterra", "Cross Farm", "Golden Oaks", "West Hollow", "Spruce & Fern"
    # Simple V marks, botanical motifs, serif + sans, deep greens and warm golds

    "r3-13-nature-simple-v": (
        "Design a logo for 'VERMILLION' — a luxury master-planned community in Sanford, NC. "
        "MARK: A simple, elegant 'V' shape — not a letter exactly, but an abstract mark that "
        "suggests both a valley/landscape and the initial letter. The V is formed from two "
        "thin tapered strokes, like brushstrokes or quill pen marks. Organic, not rigid. "
        "WORDMARK: 'VERMILLION' in a refined serif typeface below the mark. "
        "Beneath that: 'Sanford, North Carolina' in light sans-serif small text. "
        "Color: warm vermillion (#7A3428) for the V mark, dark charcoal for the text. "
        "Inspired by 'Novaterra' and 'Crimson Lane' — natural, warm, sophisticated. " + STYLE_BASE
    ),

    "r3-14-nature-golden-oak": (
        "Design a logo for 'VERMILLION' — a luxury community set among preserved natural landscapes. "
        "MARK: A single, elegant oak leaf rendered in minimal line art — just the outline and "
        "a center vein, in thin strokes. Or alternatively, a simple acorn icon. "
        "The leaf/acorn is very small and sits above the 'V' in VERMILLION or between elements. "
        "WORDMARK: 'VERMILLION' in elegant serif capitals with generous tracking. "
        "Below: 'A MATTAMY HOMES COMMUNITY' in tiny spaced sans-serif. "
        "Color: the leaf in a muted gold/bronze (#B8956A), the text in deep forest green (#2D3D2A). "
        "Inspired by 'Golden Oaks Country Club' — refined, prestigious, connected to nature. " + STYLE_BASE
    ),

    "r3-15-nature-bird": (
        "Design a logo for 'VERMILLION' — a luxury master-planned community. "
        "MARK: A tiny, ultra-minimal bird in flight — just 2-3 flowing lines suggesting wings, "
        "like a swift or a swallow. The bird is small and sits above the wordmark as an accent, "
        "not a dominant element. Think of the 'West Hollow' bird mark — tiny, elegant, subtle. "
        "WORDMARK: 'VERMILLION' in refined serif type, prominently sized, with wide tracking. "
        "The wordmark IS the logo; the bird is a grace note. "
        "Color: text in deep warm brown (#5A3A2A), bird accent in vermillion red (#C84C30). "
        "Pastoral, elegant, connected to nature without being rustic. " + STYLE_BASE
    ),

    "r3-16-nature-botanical": (
        "Design a logo for 'VERMILLION' — a luxury community in the Piedmont region of NC. "
        "MARK: A simple botanical sprig or fern frond — just 1-2 thin stems with small leaves, "
        "rendered in minimal line art. Very delicate and elegant. The botanical element sits "
        "beside the wordmark or integrated into it (like replacing a letter's serif with a leaf). "
        "WORDMARK: 'VERMILLION' in an elegant serif with moderate weight and wide letter-spacing. "
        "Color: botanical element in muted sage green (#7A8B6F), text in deep warm brown (#5A3A2A). "
        "Inspired by 'Spruce & Fern' and 'The Orchard' — botanical elegance, understated nature. " + STYLE_BASE
    ),

    # --- HYBRID / CROSS-CATEGORY ---
    # Combining the best of multiple mood boards

    "r3-17-hybrid-terra": (
        "Design a logo for 'VERMILLION' — a luxury master-planned community. "
        "This combines earth/clay warmth with typographic sophistication. "
        "Set 'VERMILLION' in a bold, elegant serif with high contrast (Didone style). "
        "The 'V' at the start is slightly larger or set in a different weight than the rest, "
        "acting as a subtle initial cap. "
        "Above the text: a thin horizontal line. Below: 'SANFORD • NORTH CAROLINA' in tiny "
        "spaced sans-serif with a bullet/dot separator. "
        "Clean, balanced, symmetrical layout. "
        "Color: deep terracotta red (#7A3428) on white. "
        "This should look like premium stationery for a luxury hotel or private club. " + STYLE_BASE
    ),

    "r3-18-hybrid-crest": (
        "Design a logo for 'VERMILLION' — a luxury master-planned community in Sanford, NC. "
        "Create a modern, minimal crest or shield shape — not ornate or heraldic, but simplified "
        "into a clean geometric form (soft-cornered shield or badge shape). "
        "Inside the crest: 'V' monogram in elegant serif, with thin decorative line work. "
        "Below the crest: 'VERMILLION' in refined serif caps with generous letter-spacing. "
        "Below that: 'A Mattamy Homes Community' in tiny sans-serif. "
        "Single color: warm terracotta (#7A3428) on white. "
        "Think modern country club meets artisan brand. Refined but warm. " + STYLE_BASE
    ),

    "r3-19-hybrid-land": (
        "Design a logo for 'VERMILLION' — a luxury community in North Carolina's Piedmont region. "
        "MARK: An abstract landscape silhouette — a single gentle rolling hill line or horizon line, "
        "very minimal, just one thin flowing curve suggesting the Piedmont rolling countryside. "
        "The hill line sits above the wordmark as a delicate accent. "
        "WORDMARK: 'VERMILLION' in elegant extended serif with wide tracking. "
        "Below: a thin rule line, then 'NORTH CAROLINA' in tiny spaced caps. "
        "Color: hill line in muted terracotta (#A0634A), text in deep brown-red (#6B3028). "
        "Minimal, grounded, sophisticated — landscape as brand element. " + STYLE_BASE
    ),

    "r3-20-hybrid-dual-tone": (
        "Design a logo for 'VERMILLION' using a sophisticated two-color approach. "
        "MARK: A simple 'V' monogram rendered in deep forest green (#2D3D2A). "
        "The V is set inside a thin circle outline, centered. Clean and geometric. "
        "WORDMARK: 'VERMILLION' below in refined serif type in deep terracotta red (#7A3428). "
        "Below that: 'Sanford, North Carolina' in tiny light sans-serif in the same green. "
        "The green-and-terracotta color pairing represents nature meeting earth/clay. "
        "Two colors only. Clean white background. Balanced, symmetrical, premium. " + STYLE_BASE
    ),

    # --- EXTRA TYPOGRAPHIC EXPLORATIONS ---

    "r3-21-type-condensed": (
        "Design a purely typographic logo for 'VERMILLION'. "
        "Use a condensed or semi-condensed elegant serif typeface — the letters are tall and narrow, "
        "creating a strong vertical rhythm. Think of luxury fashion house logos. "
        "All caps, generous letter-spacing despite the condensed letterforms. "
        "A thin hairline rule above and below the word. "
        "Below the bottom rule: 'EST. 2026' centered in tiny sans-serif. "
        "Single color: deep warm red-brown (#6B3028) on white. "
        "Dramatic, fashion-forward, typographic purity. " + STYLE_BASE
    ),

    "r3-22-type-italic": (
        "Design a logo for 'VERMILLION' featuring an elegant italic serif wordmark. "
        "The word 'Vermillion' is set in a refined italic serif (like an italic Didot or Baskerville) — "
        "note the mixed case: capital V, lowercase remainder. This gives it a softer, more "
        "approachable luxury feel compared to all-caps. "
        "Below in upright small caps sans-serif: 'A MATTAMY HOMES COMMUNITY' "
        "No icon. No mark. Just beautiful italic letterforms. "
        "Color: warm terracotta (#8B4332) on white. "
        "Think 'Victoria Levitan' from the mood board — editorial, personal, warm. " + STYLE_BASE
    ),

    "r3-23-type-ampersand": (
        "Design a logo for 'VERMILLION' with a decorative typographic element. "
        "Set 'VERMILLION' in clean serif capitals. In the center of the composition, "
        "a large decorative serif ampersand '&' or the word 'est.' in a contrasting "
        "calligraphic/script style — creating visual interest through typographic contrast. "
        "Layout options: 'VERMILLION' with an ornamental 'V' initial, or the word broken "
        "as 'VERMILLION' over a decorative line with 'Sanford & North Carolina' in script below. "
        "Color: deep vermillion (#7A3428) on white. "
        "Think 'Spruce & Fern' typographic play. Elegant, crafted, editorial. " + STYLE_BASE
    ),

    "r3-24-type-sans": (
        "Design a modern, clean logo for 'VERMILLION'. "
        "WORDMARK: 'VERMILLION' in a refined geometric sans-serif typeface — not cold or tech, "
        "but warm and humanist. Think Futura Medium, Brandon Grotesque, or Montserrat — "
        "clean geometry with a touch of warmth. All caps, very generous letter-spacing. "
        "Below: a thin line, then 'A MATTAMY HOMES COMMUNITY' in lighter weight, same typeface. "
        "MARK: Above the text, a simple geometric element — a thin diamond, a small 'V' angle, "
        "or just a dot. Very subtle. "
        "Color: deep warm brown-red (#6B3028) on white. Modern but warm, not corporate. " + STYLE_BASE
    ),
}


def generate_image(api_key: str, prompt: str, size: str = "1024x1024", quality: str = "high") -> Optional[bytes]:
    """Call OpenAI image generation API and return PNG bytes."""
    headers = {"Authorization": f"Bearer {api_key}"}
    payload = {
        "model": MODEL,
        "prompt": prompt,
        "size": size,
        "quality": quality,
        "n": 1,
        "output_format": "png",
    }

    print(f"  Calling {MODEL} ({size}, {quality})...")

    with httpx.Client(timeout=180.0) as client:
        try:
            response = client.post(API_URL, headers=headers, json=payload)
            response.raise_for_status()
        except httpx.HTTPStatusError as e:
            error_body = e.response.text
            print(f"  API error ({e.response.status_code}): {error_body[:300]}")
            if MODEL != FALLBACK_MODEL:
                print(f"  Trying fallback: {FALLBACK_MODEL}...")
                payload["model"] = FALLBACK_MODEL
                payload.pop("output_format", None)
                payload["response_format"] = "b64_json"
                try:
                    response = client.post(API_URL, headers=headers, json=payload)
                    response.raise_for_status()
                except httpx.HTTPStatusError as e2:
                    print(f"  Fallback failed ({e2.response.status_code}): {e2.response.text[:300]}")
                    return None
            else:
                return None

    data = response.json()
    if "data" in data and len(data["data"]) > 0:
        item = data["data"][0]
        if "b64_json" in item:
            return base64.b64decode(item["b64_json"])
        elif "url" in item:
            with httpx.Client(timeout=60.0) as dl_client:
                img_resp = dl_client.get(item["url"])
                img_resp.raise_for_status()
                return img_resp.content

    print("  Unexpected response format")
    return None


def main():
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        print("Error: OPENAI_API_KEY not set")
        sys.exit(1)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # Filter to only specified prompts if args given
    keys_to_run = list(PROMPTS.keys())
    if len(sys.argv) > 1:
        # Accept prompt keys or numbers like "r3-01" or "01"
        keys_to_run = []
        for arg in sys.argv[1:]:
            for k in PROMPTS.keys():
                if arg in k:
                    keys_to_run.append(k)

    total = len(keys_to_run)
    success = 0

    for i, key in enumerate(keys_to_run, 1):
        filename = f"{key}.png"
        output_path = OUTPUT_DIR / filename

        if output_path.exists():
            print(f"\n[{i}/{total}] SKIP (exists): {filename}")
            success += 1
            continue

        print(f"\n{'='*60}")
        print(f"[{i}/{total}] Generating: {key}")
        print(f"{'='*60}")

        image_bytes = generate_image(api_key, PROMPTS[key])

        if image_bytes:
            output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, "wb") as f:
                f.write(image_bytes)
            img = Image.open(io.BytesIO(image_bytes))
            print(f"  Saved: {output_path} ({img.size[0]}x{img.size[1]})")
            success += 1
        else:
            print(f"  FAILED: {key}")

        # Rate limit pause
        if i < total:
            time.sleep(1.5)

    print(f"\n{'='*60}")
    print(f"DONE: {success}/{total} logos generated")
    print(f"Output: {OUTPUT_DIR}")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
