---
name: 数学题库管理系统
description: Friendly math question bank for Chinese middle/high school — teachers manage, students practice
colors:
  primary: "#2563eb"
  primary-hover: "#1d4ed8"
  primary-light: "#3b82f6"
  primary-accent: "#4a90d9"
  green: "#16a34a"
  green-hover: "#15803d"
  green-text: "#166534"
  green-bg: "#dcfce7"
  red: "#dc2626"
  red-hover: "#b91c1c"
  red-text: "#991b1b"
  red-bg: "#fee2e2"
  amber-text: "#854d0e"
  amber-bg: "#fef9c3"
  amber-bar: "#f59e0b"
  bg-page: "#f5f7fa"
  bg-card: "#ffffff"
  bg-hover: "#f3f4f6"
  text-primary: "#1e293b"
  text-body: "#333333"
  text-secondary: "#374151"
  text-muted: "#6b7280"
  border: "#e5e7eb"
  border-input: "#d1d5db"
  tag-bg: "#e0e7ff"
  tag-text: "#3730a3"
  grade-bg: "#dbeafe"
  grade-text: "#1e40af"
  category-bg: "#fce7f3"
  category-text: "#9d174d"
  toast-bg: "#1f2937"
  toast-text: "#ffffff"
typography:
  body:
    fontFamily: "-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'PingFang SC', 'Microsoft YaHei', sans-serif"
    fontSize: "0.9rem"
    fontWeight: 400
    lineHeight: 1.6
  display:
    fontFamily: "-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'PingFang SC', 'Microsoft YaHei', sans-serif"
    fontSize: "2rem"
    fontWeight: 700
    lineHeight: 1.2
  headline:
    fontFamily: "-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'PingFang SC', 'Microsoft YaHei', sans-serif"
    fontSize: "1.5rem"
    fontWeight: 600
    lineHeight: 1.3
  label:
    fontFamily: "-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'PingFang SC', 'Microsoft YaHei', sans-serif"
    fontSize: "0.85rem"
    fontWeight: 500
    lineHeight: 1.4
rounded:
  sm: "4px"
  md: "8px"
  lg: "12px"
  xl: "16px"
  full: "999px"
spacing:
  xs: "0.25rem"
  sm: "0.5rem"
  md: "1rem"
  lg: "1.5rem"
  xl: "2rem"
  "2xl": "3rem"
components:
  button-primary:
    backgroundColor: "{colors.primary}"
    textColor: "#ffffff"
    rounded: "{rounded.md}"
    padding: "0.6rem 1.2rem"
  button-primary-hover:
    backgroundColor: "{colors.primary-hover}"
  button-success:
    backgroundColor: "{colors.green}"
    textColor: "#ffffff"
    rounded: "{rounded.md}"
    padding: "0.6rem 1.2rem"
  button-danger:
    backgroundColor: "{colors.red}"
    textColor: "#ffffff"
    rounded: "{rounded.md}"
    padding: "0.6rem 1.2rem"
  button-outline:
    backgroundColor: "transparent"
    textColor: "{colors.text-secondary}"
    rounded: "{rounded.md}"
    padding: "0.6rem 1.2rem"
  card:
    backgroundColor: "{colors.bg-card}"
    textColor: "{colors.text-body}"
    rounded: "{rounded.lg}"
    padding: "1.5rem"
  input:
    backgroundColor: "{colors.bg-card}"
    textColor: "{colors.text-body}"
    rounded: "{rounded.md}"
    padding: "0.6rem 0.8rem"
  tag:
    backgroundColor: "{colors.tag-bg}"
    textColor: "{colors.tag-text}"
    rounded: "{rounded.full}"
    padding: "0.2rem 0.6rem"
---

# Design System: 数学题库管理系统

## 1. Overview

**Creative North Star: "The Study Companion"**

This design system embodies a friendly, organized learning environment — like a well-structured study desk where everything has its place. The interface is warm without being cutesy, efficient without being cold. It speaks to students who might feel anxious about math with encouraging visual cues, while giving teachers the density and speed they need.

The palette is anchored by a trustworthy blue primary, supported by semantic greens (success/correct), reds (errors/wrong), and ambers (warnings). Neutral surfaces are clean and spacious, letting mathematical content breathe. Shadows are used sparingly — surfaces lift slightly on hover, cards have subtle depth at rest, but nothing feels heavy or floating.

**Key Characteristics:**
- Warm but professional — approachable for students, efficient for teachers
- Content-first — math formulas and questions are always the visual focus
- Encouraging — progress is visible, correct answers feel rewarding
- Organized — clear hierarchy, no screen feels cluttered
- Responsive — works equally well on desktop (teacher workflow) and mobile (student practice)

## 2. Colors

The palette is restrained and semantic — one primary accent (blue) carrying navigation and actions, with functional colors (green, red, amber) doing real communication work.

### Primary
- **Trust Blue** (#2563eb): The primary action color. Used for navigation bar, primary buttons, links, focus rings, and active states. Conveys reliability and calm authority — appropriate for an educational tool.
- **Deep Blue** (#1d4ed8): Hover state for primary elements. Slightly darker to indicate interactivity.
- **Light Blue** (#3b82f6): Secondary emphasis — tag backgrounds, lighter accents, active outline buttons.
- **Accent Blue** (#4a90d9): Softer accent for hover highlights on draggable items and interactive cards.

### Semantic
- **Success Green** (#16a34a): Correct answers, positive actions, mastery markers. The "you got it right" color.
- **Error Red** (#dc2626): Wrong answers, destructive actions, validation errors. Clear and unambiguous.
- **Warning Amber** (#f59e0b): Difficulty level 2, caution states. Warm enough to notice without alarming.

### Neutral
- **Page Gray** (#f5f7fa): The light mode page background. Clean, not warm, not cool — just neutral.
- **Card White** (#ffffff): Card and surface background. Creates clear separation from the page.
- **Text Primary** (#1e293b): Headings and important text. Near-black but softer than pure black.
- **Text Body** (#333333): Body text. Comfortable reading weight against white/light backgrounds.
- **Text Muted** (#6b7280): Secondary information, timestamps, metadata. Clearly subordinate but readable.
- **Border Gray** (#e5e7eb): Subtle dividers and card borders. Visible enough to define edges, quiet enough to disappear.

### Named Rules

**The Semantic Color Rule.** Green means correct, red means wrong, amber means caution. These colors are never used decoratively — they always communicate status. A green element without status meaning is a design error.

**The Blue-Only Primary Rule.** The primary accent is blue and only blue. Buttons, links, focus rings, active states — all blue. No competing accent colors. The semantic colors (green/red/amber) exist in their own lane.

## 3. Typography

**Display Font:** System font stack (-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'PingFang SC', 'Microsoft YaHei', sans-serif)
**Body Font:** Same system stack (single-family approach for consistency across platforms)

**Character:** Clean, legible, platform-native. The system stack ensures Chinese characters render beautifully on every device without loading custom fonts. The typography is functional rather than decorative — it supports reading, it doesn't call attention to itself.

### Hierarchy
- **Display** (700 weight, 2rem / 32px, line-height 1.2): Hero headlines on the homepage. Used sparingly — one per page maximum.
- **Headline** (600 weight, 1.5rem / 24px, line-height 1.3): Page titles and section headers. The workhorse heading size.
- **Title** (600 weight, 1rem / 16px, line-height 1.4): Card titles, question headings, table headers.
- **Body** (400 weight, 0.9rem / 14.4px, line-height 1.6): All readable content. Max line length should stay within 65–75ch for comfortable reading.
- **Label** (500 weight, 0.85rem / 13.6px): Buttons, form labels, navigation items, badges. Slightly smaller but still readable.
- **Caption** (400 weight, 0.75rem / 12px): Tags, difficulty badges, timestamps. The smallest readable size.

### Named Rules

**The Content-First Rule.** Mathematical content (rendered by MathJax) is the visual focus of every screen. The UI exists to present and organize questions, not to showcase itself. Typography never competes with formula rendering.

## 4. Elevation

The system uses **light lift** — subtle shadows that create gentle depth without heaviness. Surfaces are flat at rest; shadows appear as feedback (hover, focus, modal overlay). The vocabulary is intentionally small: just a few shadow levels that serve distinct purposes.

### Shadow Vocabulary
- **Rest** (`0 1px 3px rgba(0,0,0,0.08)`: Cards and surfaces at rest. Barely visible — just enough to separate from the page background.
- **Hover** (`0 2px 8px rgba(0,0,0,0.1)`: Interactive elements on hover. A gentle lift that says "this is clickable."
- **Focus** (`0 0 0 3px rgba(37,99,235,0.1)`: Focus ring glow. Blue-tinted to match the primary accent.
- **Modal** (`rgba(0,0,0,0.5)` backdrop): Full-screen overlay. The only "heavy" shadow — reserved for modal dialogs.

### Named Rules

**The Flat-By-Default Rule.** Surfaces start flat. Shadows are feedback, not decoration. If an element has a shadow at rest, it should feel intentional — cards need it to separate from the page, but buttons don't need it until hover.

## 5. Components

### Buttons
- **Shape:** Gently rounded (8px radius) — friendly but not bubbly.
- **Primary:** Solid blue fill (#2563eb), white text. The main action button. Confident and clear.
- **Hover / Focus:** Deepens to #1d4ed8 on hover. Focus ring adds a 3px blue glow. Transition: 0.2s ease.
- **Success / Danger:** Green and red fills for semantic actions (submit correct, delete). Same shape as primary.
- **Outline:** Transparent background, 1px border, gray text. Used for secondary actions. Fills with blue on active state.
- **Sizes:** Small (0.4rem 0.8rem), default (0.6rem 1.2rem), large (0.8rem 1.8rem).

### Cards
- **Corner Style:** Gently rounded (12px radius).
- **Background:** White (#ffffff) in light mode, dark slate (#1e293b) in dark mode.
- **Shadow Strategy:** Rest shadow at 0 1px 3px. Hover lifts to 0 2px 8px. The card says "I'm here" at rest, "I'm interactive" on hover.
- **Border:** 1px solid #e5e7eb — visible enough to define edges in light mode.
- **Internal Padding:** 1.5rem (24px) — spacious but not wasteful.

### Inputs / Fields
- **Style:** Clean rectangle with 8px radius, 1px border (#d1d5db), white background.
- **Focus:** Border shifts to blue (#2563eb), adds a 3px blue glow ring. Clear "you're typing here" signal.
- **Error:** Border shifts to red, with a red glow ring. Always paired with text feedback.

### Navigation
- **Style:** Sticky top bar, solid blue background (#2563eb), white text. Fixed at 56px height.
- **Typography:** 0.9rem, 500 weight for nav items. Brand name at 1.25rem, 700 weight.
- **Hover:** White text on semi-transparent white background (rgba(255,255,255,0.15)). Subtle but discoverable.
- **Mobile:** Collapses to hamburger menu. Full-width dropdown with vertical layout. Theme toggle stays visible.

### Tags / Chips
- **Style:** Pill-shaped (999px radius), small (0.2rem 0.6rem padding), 0.75rem text.
- **Background:** Soft indigo (#e0e7ff) with darker indigo text (#3730a3) for general tags.
- **Grade Badge:** Soft blue (#dbeafe) with deep blue text (#1e40af).
- **Category Badge:** Soft pink (#fce7f3) with deep pink text (#9d174d).

### Difficulty Badges
- **Level 1 (Easy):** Green background (#dcfce7), green text (#166534). "You can do this."
- **Level 2 (Medium):** Amber background (#fef9c3), amber text (#854d0e). "A bit challenging."
- **Level 3 (Hard):** Red background (#fee2e2), red text (#991b1b). "Bring your A-game."

### Toast Notifications
- **Style:** Fixed bottom-right, dark background (#1f2937), white text, 8px radius.
- **Animation:** Slides up from below (0.3s ease). Temporary by nature — appears, delivers message, fades.

## 6. Do's and Don'ts

### Do:
- **Do** use the semantic colors (green/red/amber) only for status communication — correct/wrong/caution. They lose meaning when decorative.
- **Do** keep mathematical content as the visual focus. The UI exists to serve the questions, not overshadow them.
- **Do** use subtle shadows (rest + hover) to create depth. One or two shadow levels, not a gradient of five.
- **Do** maintain generous whitespace around math formulas. They need room to breathe.
- **Do** use the system font stack. It renders Chinese characters beautifully without custom font loading.
- **Do** provide text labels alongside color indicators (icons + color, not color alone) for accessibility.
- **Do** keep buttons at 8px radius — friendly and confident without being bubbly.

### Don't:
- **Don't** use dense, chaotic data layouts with overwhelming tables and no visual hierarchy — this is the primary anti-reference from PRODUCT.md.
- **Don't** use generic corporate SaaS dashboard patterns — soulless Bootstrap templates, cookie-cutter admin panels.
- **Don't** use border-left or border-right greater than 1px as a colored accent stripe. Never intentional.
- **Don't** use gradient text (background-clip: text). Decorative, never meaningful. Use solid colors.
- **Don't** use glassmorphism (blurs and glass cards) as a default treatment. Rare and purposeful, or nothing.
- **Don't** pair a 1px border with a wide drop shadow (≥16px blur) on the same element. Pick one, not both.
- **Don't** use border-radius ≥ 24px on cards. Cards top out at 12–16px; full-pill is fine for tags and buttons.
- **Don't** animate layout properties (width, height, padding) unless truly needed. Prefer transform and opacity.
- **Don't** put content that overflows its container. Test headings at every breakpoint; reduce clamp max if needed.
