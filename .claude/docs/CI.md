# Corporate Identity (CI) Guidelines

## Brand Name

- Always written in **lowercase**: `seeqnc`
- Never capitalize: ~~Seeqnc~~, ~~SEEQNC~~
- The name derives from "sequence" — referencing audio sequences used in music recognition

## Typography

### Primary Typeface: PP Neue Machina

- **Foundry**: Pangram Pangram
- **Classification**: Geometric sans-serif with monospace-like proportions and deep inktraps
- **Character**: Mechanical, futuristic, tech-forward — inspired by robotics and machines
- **Available weights**: Ultralight, Light, Regular, Medium, Bold, Ultrabold, Black (+ italics in v2.0)
- **Variants**: Plain and Inktrap

#### Usage

| Context               | Weight / Variant            |
|-----------------------|-----------------------------|
| Headlines / Hero text | Bold or Ultrabold (Inktrap) |
| Subheadings           | Medium                      |
| Body text             | Regular (Plain)             |
| UI labels / Captions  | Light or Regular            |

> **Note**: PP Neue Machina is a licensed commercial font. Ensure valid licenses are in place for web, app, and desktop
> usage. For fallback/system font stacks use: `"PP Neue Machina", "SF Mono", "Roboto Mono", monospace`

## Color Palette

### Primary Colors

<!-- ⚠️ VERIFY exact hex values against the brand book / Figma source of truth -->

| Role             | Color Name    | Hex (approx.) | Usage                                  |
|------------------|---------------|---------------|----------------------------------------|
| **Primary**      | seeqnc Yellow | `#F5D10D`*    | Logo, primary accent, CTAs, highlights |
| **Background**   | seeqnc Black  | `#0A0A0A`*    | Page backgrounds, dark surfaces        |
| **Text Primary** | Off-White     | `#F5F5F5`*    | Body text on dark backgrounds          |
| **Text Muted**   | Light Gray    | `#A0A0A0`*    | Secondary text, captions, placeholders |
| **Surface**      | Dark Gray     | `#1A1A1A`*    | Cards, elevated surfaces, containers   |

_*Approximate values — confirm against brand book or design tokens._

### Color Principles

- **Dark-first**: The brand uses a predominantly dark theme. Default to dark backgrounds with light text.
- **Yellow as accent, not background**: Use seeqnc Yellow sparingly for emphasis — logos, interactive elements, key data
  points. Never as a large background fill.
- **High contrast**: Maintain strong contrast ratios (WCAG AA minimum) between text and background.

## Logo

### Assets

- **Primary logo**: SVG wordmark (`logo.svg`) — lowercase "seeqnc" wordmark
- **Footer / mono variant**: `logo-footer.svg` — lighter or reversed variant for footers and secondary placements
- **Signet**: The standalone icon mark derived from audio sequence visualization

### Logo Rules

- Always use the SVG source files; never rasterize at low resolution
- Maintain adequate clear space around the logo (minimum: height of the letter "s" on all sides)
- Do not rotate, distort, recolor arbitrarily, or add effects (drop shadows, outlines, gradients)
- On dark backgrounds: use Yellow or White logo variant
- On light backgrounds (rare): use Black logo variant

## Visual Language — Sound Sequences

The core visual motif is derived from **audio sequences** — the "name-giving" concept of seeqnc. This translates into:

- **Geometric patterns**: Rectangular/bar-like shapes representing audio waveforms or spectrograms
- **The signet**: A compact icon built from these sequence shapes
- **Graphic patterns**: Used as backgrounds, section dividers, and decorative elements
- **Animations**: Large-scale motion graphics echoing audio visualization (pulsing, sequencing, rhythmic)

### Pattern Usage

- Use sequence patterns to reinforce the brand's connection to music and audio technology
- Keep patterns subtle on content-heavy pages; more prominent on hero sections and marketing materials
- Patterns should use brand colors only (Yellow on Black, White on Black, or subtle Gray on Dark Gray)

## Iconography

- **Style**: Minimal, line-based icons consistent with the geometric/technical aesthetic
- **Stroke weight**: Match the visual weight of PP Neue Machina Regular
- **Format**: SVG, single-color (adapt to context — White on dark, Black on light)
- Social icons used: LinkedIn, Instagram (SVG line variants)

## Imagery & Photography

- **Style**: High-contrast, atmospheric photography from the music and events world (DJ sets, festivals, live
  performances)
- **Treatment**: Dark, moody tones with selective color — often with yellow/warm accent lighting
- **Overlay**: Brand patterns or logo marks can be overlaid on photography in Yellow at reduced opacity

## Tone of Voice (for reference in design copy)

- **Technical yet accessible**: Explain complex AI/music-tech concepts simply
- **Confident and precise**: "AI-native content intelligence" — not vague, not overpromising
- **Industry-insider**: Speak the language of music rights, copyright, and content platforms
- **Action-oriented**: CTAs use `>>` arrows (e.g., "More >>", "Take me there >>", "Let's talk >>")

## Application Checklist

When creating any seeqnc-branded material, verify:

- [ ] Brand name is lowercase (`seeqnc`)
- [ ] PP Neue Machina is used (with correct license)
- [ ] Dark theme is the default
- [ ] Yellow accent is used sparingly and intentionally
- [ ] Logo has adequate clear space and is not distorted
- [ ] Sequence/pattern visual language is present where appropriate
- [ ] Photography follows dark, atmospheric style guidelines
- [ ] All text meets WCAG AA contrast minimums

---

> **⚠️ Important**: The hex color values marked with `*` in this document are approximations based on visual inspection
> of [seeqnc.com](https://www.seeqnc.com/). Replace these with the authoritative values from the brand book / Figma design
> tokens provided by dotsandlines.
