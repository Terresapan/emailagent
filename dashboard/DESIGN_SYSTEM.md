# Dashboard Design System: "Neu-Editorial"

## Aesthetic Direction

**Style:** Luxury/Refined + Editorial/Magazine fusion  
**Core Concept:** Exclusive intelligence briefing with magazine-quality typography

### What Makes It Unforgettable
- **Giant Typography** — Headlines that feel like magazine covers
- **Purple/Teal Palette** — Sophisticated, non-generic color pairing
- **Editorial Grid** — Asymmetric 8+4 column structure

---

## Color Palette (HSL)

| Name | HSL Value | Hex | Usage |
|------|-----------|-----|-------|
| **Background** | `240 21% 12%` | Deep Indigo | App background |
| **Card** | `240 21% 15%` | Elevated Indigo | Card surfaces |
| **Primary** | `267 83% 81%` | Lavender Purple | Buttons, rings |
| **Accent** | `189 71% 73%` | Teal/Cyan | Icons, tags, links |
| **Foreground** | `226 64% 88%` | Soft Gray-White | Body text |
| **Muted** | `227 24% 72%` | Muted Gray | Secondary text |

---

## Typography

| Role | Font | Weight |
|------|------|--------|
| **Display** | Playfair Display | 600-700 |
| **Body** | DM Sans | 400-500 |

---

## Semantic Utilities

### Accent Abstraction
```css
.text-accent   { color: hsl(var(--accent)); }
.bg-accent     { background-color: hsl(var(--accent)); }
.border-accent { border-color: hsl(var(--accent)); }
```

### Item Patterns
| Class | Usage |
|-------|-------|
| `.item-card` | List item container |
| `.item-title` | Primary text (White) |
| `.item-description` | Secondary text (Muted) |
| `.item-tag` | Accent-colored tag |
| `.item-tag-neutral` | Neutral gray tag |

### Cards & Sections
| Class | Usage |
|-------|-------|
| `.card-title` | Main header (24px Serif) |
| `.card-title-sm` | Compact header (16px Bold) |
| `.section-header` | Sub-header |
| `.section-label` | Uppercase label |

---

## Design Principles (from SKILL.md)

| Principle | Application |
|-----------|-------------|
| **Anti-Generic** | Custom Purple/Teal avoids common palettes |
| **Intentionality** | Semantic utilities for all patterns |
| **Editorial** | Giant headlines, magazine grid |
| **Refined** | Controlled motion, subtle glass effects |

---

## Files
- `src/app/globals.css` — CSS variables & utilities
- `tailwind.config.js` — Color definitions
- `backend/sources/gmail/client.py` — Email template (aligned)
