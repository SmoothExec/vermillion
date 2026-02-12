#!/usr/bin/env python3
"""
Vermillion Logo Generator — Generate logo concepts using OpenAI gpt-image-1.

Generates logo design concepts for Vermillion master-planned community
across 4 distinct creative directions. Uses the OpenAI image generation API.

Usage:
    OPENAI_API_KEY="sk-..." python3 generate_logo.py --concept 1 --variations 3
    OPENAI_API_KEY="sk-..." python3 generate_logo.py --all --variations 3
    OPENAI_API_KEY="sk-..." python3 generate_logo.py --concept 2 --variations 1 --quality medium

Requires: pip3 install Pillow httpx
"""

import os
import sys
import argparse
import base64
import time
from pathlib import Path
from typing import Optional
from PIL import Image
import io
import httpx

# --- Configuration ---

API_URL = "https://api.openai.com/v1/images/generations"
MODEL = "gpt-image-1"
FALLBACK_MODEL = "dall-e-3"

CONCEPT_DIRS = {
    1: "concepts/01-kiln-mark",
    2: "concepts/02-earthen-strata",
    3: "concepts/03-winding-path",
    4: "concepts/04-vermillion-leaf",
}

# Brand color reference for prompts
BRAND_COLORS = {
    "deep_vermillion": "#7A3428",
    "bright_vermillion": "#C84C30",
    "corten_brown": "#8B5E3C",
    "cream": "#F5F0E8",
    "forest_green": "#4A5E3A",
}

# --- Concept Prompts ---

STYLE_SUFFIX = (
    "Professional logo design. Clean, minimal, vector-style rendering with crisp edges. "
    "The logo should work at small sizes and large scales. "
    "Solid flat colors only — no photographic textures, no gradients, no 3D effects, no shadows. "
    "Place the logo on a clean white background. "
    "The word 'VERMILLION' must be spelled correctly and be clearly legible. "
    "This is for a premium master-planned residential community — the design should feel "
    "elevated, sophisticated, and timeless, not generic or clipart-like."
)

CONCEPT_PROMPTS = {
    1: {
        "name": "The Kiln Mark",
        "prompt": (
            "Design a logo for 'VERMILLION', a luxury master-planned community in Sanford, North Carolina. "
            "This concept honors the region's brick-making heritage — Sanford was the 'Brick Capital of the USA.' "
            "\n\n"
            "MARK: Create a geometric icon inspired by brick kiln architecture. The mark should reference "
            "the shape of a traditional kiln arch or brick gateway — two angled forms meeting at a peak, "
            "suggesting the letter 'V'. The geometry should feel architectural, solid, and crafted — "
            "like something carved from brick or formed in a kiln. Keep the mark simple enough to work "
            "as a standalone icon at small sizes. "
            "\n\n"
            "WORDMARK: Below or beside the mark, set 'VERMILLION' in an elegant modern serif typeface "
            "with high stroke contrast (thin horizontals, thick verticals) — similar to Didot, Bodoni, "
            "or Playfair Display. Use generous letter-spacing. Optionally include a tagline line beneath "
            "in a lighter weight or small caps. "
            "\n\n"
            "COLOR: Use deep vermillion red ({deep_vermillion}) for the mark and type on white background. "
            "The overall feeling should be: heritage, craft, permanence, warmth. "
            "\n\n"
            "{style}"
        ).format(deep_vermillion=BRAND_COLORS["deep_vermillion"], style=STYLE_SUFFIX),
    },
    2: {
        "name": "Earthen Strata",
        "prompt": (
            "Design a logo for 'VERMILLION', a luxury master-planned community in Sanford, North Carolina. "
            "This concept is inspired by the unique geology of the site — where ancient coastal sand meets "
            "Piedmont clay, creating layers of earth in warm tones. "
            "\n\n"
            "MARK: Create an abstract mark based on horizontal geological strata — layered lines or bands "
            "that suggest earth cross-sections. The layers should flow with gentle organic curves (not rigid), "
            "evoking a rolling hillscape or river valley. The strata should subtly form the shape of a 'V' "
            "or a landscape horizon. Use 2-3 tones: cream/sand at the top transitioning to deep vermillion "
            "red at the base, suggesting sand meeting clay. "
            "\n\n"
            "WORDMARK: Set 'VERMILLION' in an elegant extended serif typeface with refined letter-spacing. "
            "The type should feel grounded and substantial — similar to a Didone or transitional serif. "
            "\n\n"
            "COLOR: Cream/sand ({cream}) at top of strata, transitioning to deep vermillion ({deep_vermillion}) "
            "at the base. Wordmark in deep vermillion. White background. "
            "The overall feeling should be: geological depth, grounded, layered, timeless, natural elegance. "
            "\n\n"
            "{style}"
        ).format(
            cream=BRAND_COLORS["cream"],
            deep_vermillion=BRAND_COLORS["deep_vermillion"],
            style=STYLE_SUFFIX,
        ),
    },
    3: {
        "name": "The Winding Path",
        "prompt": (
            "Design a logo for 'VERMILLION', a luxury master-planned community in Sanford, North Carolina. "
            "This concept celebrates the community's network of winding trails, linear parks, and streams "
            "that thread neighbors together through a pastoral landscape. "
            "\n\n"
            "MARK: Create an organic, flowing mark made of one or two continuous curving lines that suggest "
            "a winding trail or stream viewed from above. The path should meander gracefully, with the curves "
            "subtly forming the letter 'V'. The line weight should be confident but not heavy — think of a "
            "single elegant brushstroke or a path drawn on a landscape plan. The mark should feel alive and "
            "organic, not rigid or geometric. "
            "\n\n"
            "WORDMARK: Set 'VERMILLION' in a refined serif or humanist typeface — slightly warmer and more "
            "approachable than a strict Didone, but still elegant. Consider moderate letter-spacing. "
            "\n\n"
            "COLOR: The path/mark in vermillion red ({bright_vermillion}), with optional touches of muted "
            "forest green ({forest_green}) to suggest the landscape. Wordmark in a dark warm tone. White background. "
            "The overall feeling should be: connection, nature, movement, discovery, pastoral beauty. "
            "\n\n"
            "{style}"
        ).format(
            bright_vermillion=BRAND_COLORS["bright_vermillion"],
            forest_green=BRAND_COLORS["forest_green"],
            style=STYLE_SUFFIX,
        ),
    },
    4: {
        "name": "The Vermillion Leaf",
        "prompt": (
            "Design a logo for 'VERMILLION', a luxury master-planned community in Sanford, North Carolina. "
            "This concept represents planting roots, natural sanctuary, and renewal — a community where "
            "residents plant their own roots in a landscape of preserved streams and rolling countryside. "
            "\n\n"
            "MARK: Create a stylized leaf or botanical element rendered in vermillion red. The leaf should "
            "be simplified and iconic — not a realistic botanical illustration, but an elegant, minimal "
            "abstraction. The leaf's veins or internal lines could subtly reference brick patterns or the "
            "linear parks that connect the community. The leaf shape should have a slight sense of being "
            "rooted — perhaps a visible stem or connection to the ground. "
            "\n\n"
            "WORDMARK: Set 'VERMILLION' in a classic, refined serif typeface with high stroke contrast. "
            "The type should pair harmoniously with the organic mark — structured elegance meeting nature. "
            "\n\n"
            "COLOR: The leaf mark in vermillion red ({bright_vermillion}) or deep vermillion ({deep_vermillion}). "
            "Optional accent of forest green ({forest_green}) for a secondary element. "
            "Wordmark in deep vermillion or dark brown. White background. "
            "The overall feeling should be: rooted, natural, sanctuary, renewal, organic elegance. "
            "\n\n"
            "{style}"
        ).format(
            bright_vermillion=BRAND_COLORS["bright_vermillion"],
            deep_vermillion=BRAND_COLORS["deep_vermillion"],
            forest_green=BRAND_COLORS["forest_green"],
            style=STYLE_SUFFIX,
        ),
    },
}


def generate_image(api_key: str, prompt: str, size: str = "1024x1024", quality: str = "high") -> Optional[bytes]:
    """Call OpenAI image generation API and return PNG bytes."""
    headers = {
        "Authorization": f"Bearer {api_key}",
    }

    payload = {
        "model": MODEL,
        "prompt": prompt,
        "size": size,
        "quality": quality,
        "n": 1,
        "output_format": "png",
    }

    print(f"  Calling {MODEL} ({size}, {quality})...")

    with httpx.Client(timeout=120.0) as client:
        try:
            response = client.post(API_URL, headers=headers, json=payload)
            response.raise_for_status()
        except httpx.HTTPStatusError as e:
            error_body = e.response.text
            print(f"  API error ({e.response.status_code}): {error_body[:300]}")
            if MODEL != FALLBACK_MODEL:
                print(f"  Trying fallback model: {FALLBACK_MODEL}...")
                payload["model"] = FALLBACK_MODEL
                payload.pop("output_format", None)
                payload["response_format"] = "b64_json"
                try:
                    response = client.post(API_URL, headers=headers, json=payload)
                    response.raise_for_status()
                except httpx.HTTPStatusError as e2:
                    print(f"  Fallback also failed ({e2.response.status_code}): {e2.response.text[:300]}")
                    return None
            else:
                return None

    data = response.json()

    # gpt-image-1 returns b64 in data[0].b64_json, dall-e-3 may return url or b64
    if "data" in data and len(data["data"]) > 0:
        item = data["data"][0]
        if "b64_json" in item:
            return base64.b64decode(item["b64_json"])
        elif "url" in item:
            # Download from URL
            with httpx.Client(timeout=60.0) as dl_client:
                img_resp = dl_client.get(item["url"])
                img_resp.raise_for_status()
                return img_resp.content

    print("  Unexpected response format")
    return None


def save_image(image_bytes: bytes, output_path: Path) -> None:
    """Save PNG bytes to file."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "wb") as f:
        f.write(image_bytes)
    # Also verify it's a valid image
    img = Image.open(io.BytesIO(image_bytes))
    print(f"  Saved: {output_path} ({img.size[0]}x{img.size[1]})")


def run_concept(api_key: str, concept_id: int, variations: int, quality: str, size: str, base_dir: Path) -> int:
    """Generate variations for a single concept. Returns count of successful generations."""
    concept = CONCEPT_PROMPTS[concept_id]
    output_dir = base_dir / CONCEPT_DIRS[concept_id]
    output_dir.mkdir(parents=True, exist_ok=True)

    print(f"\n{'='*60}")
    print(f"Concept {concept_id}: {concept['name']}")
    print(f"Output: {output_dir}")
    print(f"Generating {variations} variation(s)...")
    print(f"{'='*60}")

    success_count = 0

    for i in range(1, variations + 1):
        # Check if already exists
        filename = f"v{i:02d}.png"
        output_path = output_dir / filename

        if output_path.exists():
            print(f"\n  [{i}/{variations}] Skipping (already exists): {filename}")
            success_count += 1
            continue

        print(f"\n  [{i}/{variations}] Generating {filename}...")

        # Add variation seed to prompt for diversity
        variation_suffix = ""
        if i > 1:
            variation_hints = [
                " Explore a different compositional arrangement.",
                " Try a bolder, more minimal interpretation.",
                " Emphasize the typography more prominently.",
                " Make the mark/icon more abstract and simplified.",
                " Try a horizontal lockup layout.",
            ]
            variation_suffix = variation_hints[(i - 2) % len(variation_hints)]

        prompt = concept["prompt"] + variation_suffix

        image_bytes = generate_image(api_key, prompt, size=size, quality=quality)

        if image_bytes:
            save_image(image_bytes, output_path)
            success_count += 1
        else:
            print(f"  FAILED to generate {filename}")

        # Rate limiting — small pause between calls
        if i < variations:
            time.sleep(1)

    return success_count


def main():
    parser = argparse.ArgumentParser(description="Generate Vermillion logo concepts via OpenAI API")
    parser.add_argument("--concept", type=int, choices=[1, 2, 3, 4],
                        help="Which concept to generate (1-4)")
    parser.add_argument("--all", action="store_true",
                        help="Generate all 4 concepts")
    parser.add_argument("--variations", type=int, default=3,
                        help="Number of variations per concept (default: 3)")
    parser.add_argument("--quality", choices=["low", "medium", "high"], default="high",
                        help="Image quality (default: high)")
    parser.add_argument("--size", default="1024x1024",
                        help="Output size (default: 1024x1024)")
    parser.add_argument("--list", action="store_true",
                        help="List all concepts and their prompts")

    args = parser.parse_args()
    base_dir = Path(__file__).parent

    if args.list:
        for cid, concept in CONCEPT_PROMPTS.items():
            print(f"\nConcept {cid}: {concept['name']}")
            print(f"  Dir: {CONCEPT_DIRS[cid]}")
            print(f"  Prompt ({len(concept['prompt'])} chars):")
            print(f"  {concept['prompt'][:200]}...")
        return

    if not args.concept and not args.all:
        parser.print_help()
        print("\nError: specify --concept N or --all")
        sys.exit(1)

    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        print("Error: OPENAI_API_KEY environment variable not set")
        print("Usage: OPENAI_API_KEY='sk-...' python3 generate_logo.py --concept 1")
        sys.exit(1)

    concepts_to_run = list(range(1, 5)) if args.all else [args.concept]
    total_success = 0
    total_attempted = 0

    for cid in concepts_to_run:
        count = run_concept(api_key, cid, args.variations, args.quality, args.size, base_dir)
        total_success += count
        total_attempted += args.variations

    print(f"\n{'='*60}")
    print(f"DONE: {total_success}/{total_attempted} images generated successfully")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()


# --- Extra prompt variations for iteration ---
EXTRA_PROMPTS = {
    "1-monogram": {
        "name": "Kiln Mark - Monogram V",
        "dir": "concepts/01-kiln-mark",
        "prompt": (
            "Design a standalone monogram mark for 'VERMILLION', a luxury community in Sanford, NC. "
            "The mark is the letter 'V' formed from two angular brick-like forms meeting at a pointed base, "
            "creating a kiln arch or gateway silhouette. The interior is a pointed arch negative space. "
            "Minimal, geometric, architectural. Deep vermillion red (#7A3428) on white background. "
            "No text — just the icon/monogram mark by itself, centered on a clean white square. "
            "Professional vector-style rendering, flat color, no gradients, no 3D effects."
        ),
    },
    "2-landscape": {
        "name": "Earthen Strata - Wide Landscape",
        "dir": "concepts/02-earthen-strata",
        "prompt": (
            "Design a horizontal/landscape-oriented logo for 'VERMILLION', a luxury community in Sanford, NC. "
            "LEFT SIDE: An abstract mark of 3-4 flowing horizontal strata lines representing geological layers "
            "where coastal sand meets Piedmont clay. Lines flow with gentle organic curves. Colors transition "
            "from cream/sand (#F5F0E8) at top to deep vermillion (#7A3428) at bottom. The strata form a "
            "subtle landscape silhouette. "
            "RIGHT SIDE: The word 'VERMILLION' in an elegant Didone serif (like Bodoni or Didot) with high "
            "stroke contrast, vertically centered next to the mark. "
            "Horizontal lockup layout. Clean white background. "
            "Professional logo design, vector-style, flat colors, no gradients in the type."
        ),
    },
    "2-abstract": {
        "name": "Earthen Strata - Abstract V",
        "dir": "concepts/02-earthen-strata",
        "prompt": (
            "Design a logo for 'VERMILLION', a luxury master-planned community. "
            "MARK: A bold, simplified 'V' shape made of 3-4 horizontal wavy strata bands — like a geological "
            "cross-section cut into a V form. The top band is cream/sand colored (#F5F0E8), middle bands "
            "transition through terracotta, bottom band is deep vermillion (#7A3428). The edges of the V "
            "are clean but the strata lines inside have gentle organic wave movement. "
            "WORDMARK: 'VERMILLION' below in an elegant modern serif with wide letter-spacing. "
            "Clean white background. Flat vector style. Professional luxury real estate branding."
        ),
    },
    "3-minimal": {
        "name": "Winding Path - Minimal",
        "dir": "concepts/03-winding-path",
        "prompt": (
            "Design a minimalist logo for 'VERMILLION', a luxury master-planned community. "
            "MARK: A single continuous flowing S-curve line in vermillion red (#C84C30) that suggests "
            "a winding trail through a landscape. The line should be elegant and confident — like a single "
            "calligraphic stroke. It subtly forms the letter 'V' through its S-curve shape. "
            "The line tapers slightly at its ends. Very minimal — just the one flowing line. "
            "WORDMARK: 'VERMILLION' below in refined serif type with generous tracking. "
            "Clean white background. Ultra-minimal, sophisticated. No additional decoration."
        ),
    },
    "4-veined": {
        "name": "Vermillion Leaf - Brick Veins",
        "dir": "concepts/04-vermillion-leaf",
        "prompt": (
            "Design a logo for 'VERMILLION', a luxury community honoring Sanford NC's brick-making heritage. "
            "MARK: A stylized leaf shape in deep vermillion red (#7A3428). Inside the leaf, instead of "
            "natural veins, use a subtle herringbone or stretcher-bond brick pattern — the internal "
            "lines reference brick laying patterns while the overall shape is clearly a leaf. This "
            "symbolizes the marriage of nature and brick heritage. The leaf should have a thin stem "
            "extending below. Keep it simple and iconic. "
            "WORDMARK: 'VERMILLION' in an elegant serif typeface below the mark. "
            "White background. Professional vector-style logo, flat colors."
        ),
    },
}
