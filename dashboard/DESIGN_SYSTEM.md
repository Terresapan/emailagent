# Dashboard Design System: "The Monolith"

**Core Concept:** Deep Obsidian background with a single, sharp International Orange accent.

## Semantic Utilities

### Accent Abstraction (The "One Color" Rule)
Use these for **functional colors** (links, icons, active states). Never use hardcoded colors.
| Class | Usage |
|-------|-------|
| `.text-accent` | Icons, active headers, links (`text-brand-orange`) |
| `.bg-accent` | Active indicators (`bg-brand-orange`) |
| `.border-accent` | Active borders (`border-brand-orange`) |

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

## Color Palette

| Name | Hex | Functional Role |
|------|-----|-----------------|
| **Accent** | `#FF3B00` | Focus, Action, Branding (International Orange) |
| **Obsidian** | `#050505` | App Background (Deep Black) |
| **Surface** | `#1A1A24` | Cards |
| **Text** | `#F2E9E4` | Primary Readability |

## Files
- `src/app/globals.css` - Utilities defined here
- `tailwind.config.js` - Color definitions
