# Design Document — The Lenny Growth Assistant

## 1. Design Philosophy

The Lenny Growth Assistant is designed as a **premium, focused AI tool** for product and growth professionals. The UI draws inspiration from modern AI chat products (Claude, ChatGPT, Perplexity) while maintaining its own identity through a distinctive color palette and layout choices.

### Core Principles
1. **Content-first:** The conversation and generated artifacts are the star. Chrome and navigation should recede.
2. **Trust through transparency:** Always show which model is active, cite sources, and make the AI's limitations visible.
3. **Progressive disclosure:** Simple by default, powerful on demand. Advanced features (model toggle, artifact viewer) appear contextually.
4. **Speed feels good:** Streaming responses, optimistic UI updates, and skeleton loaders create a sense of responsiveness.

## 2. Color Palette & Design Tokens

### Dark Mode (Default)

```css
:root {
  /* Background layers */
  --bg-primary: #0f0f14;      /* Main background */
  --bg-secondary: #1a1a24;    /* Sidebar, cards */
  --bg-tertiary: #24243a;     /* Hover states, input fields */
  --bg-elevated: #2a2a42;     /* Active states, tooltips */

  /* Brand accent — warm amber/gold */
  --accent-primary: #f59e0b;
  --accent-hover: #fbbf24;
  --accent-muted: rgba(245, 158, 11, 0.15);

  /* Text */
  --text-primary: #f0f0f5;
  --text-secondary: #9898b0;
  --text-muted: #5a5a7a;

  /* Semantic */
  --success: #22c55e;
  --warning: #f59e0b;
  --error: #ef4444;
  --info: #3b82f6;

  /* Borders */
  --border-subtle: rgba(255, 255, 255, 0.06);
  --border-default: rgba(255, 255, 255, 0.1);

  /* Shadows */
  --shadow-sm: 0 1px 2px rgba(0, 0, 0, 0.3);
  --shadow-md: 0 4px 12px rgba(0, 0, 0, 0.4);
  --shadow-lg: 0 8px 32px rgba(0, 0, 0, 0.5);

  /* Typography */
  --font-sans: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
  --font-mono: 'JetBrains Mono', 'Fira Code', monospace;

  /* Spacing scale */
  --space-1: 4px;
  --space-2: 8px;
  --space-3: 12px;
  --space-4: 16px;
  --space-5: 24px;
  --space-6: 32px;
  --space-8: 48px;

  /* Border radius */
  --radius-sm: 6px;
  --radius-md: 10px;
  --radius-lg: 16px;
  --radius-full: 9999px;

  /* Transitions */
  --transition-fast: 150ms cubic-bezier(0.4, 0, 0.2, 1);
  --transition-base: 250ms cubic-bezier(0.4, 0, 0.2, 1);
  --transition-slow: 400ms cubic-bezier(0.4, 0, 0.2, 1);
}
```

### Why Amber/Gold?
- Warm amber evokes knowledge, insight, and growth — fitting for a product/growth assistant.
- High contrast against the dark background without the clinical feel of pure blue/white.
- Differentiates from competitors (Claude = orange, ChatGPT = green/white, Perplexity = blue).

## 3. Information Architecture

```
┌─────────────────────────────────────────────────────────┐
│  Header                                                  │
│  [Logo] The Lenny Growth Assistant    [Model Toggle] [⚙] │
├──────────┬──────────────────────────┬───────────────────┤
│ Sidebar  │    Chat Window           │  Artifact Viewer  │
│          │                          │  (slides in when  │
│ Sessions │  Message Thread          │   artifact is     │
│ list     │  (scrollable)            │   generated)      │
│          │                          │                   │
│ [+ New   │                          │  [Markdown/HTML   │
│  Chat]   │                          │   rendered view]  │
│          │                          │                   │
│          │  ┌────────────────────┐  │  [Copy] [Download]│
│          │  │ Input Bar          │  │                   │
│          │  │ [Type...] [Send ▶] │  │                   │
│          │  └────────────────────┘  │                   │
└──────────┴──────────────────────────┴───────────────────┘
```

### Layout Ratios
- **Sidebar:** 260px fixed width, collapsible on mobile
- **Chat Window:** Flexible, takes remaining space
- **Artifact Viewer:** 45% width when open, slides in from right with animation

### Mobile Responsive Behavior
- **< 768px:** Sidebar becomes a hamburger drawer; artifact viewer becomes a bottom sheet
- **768px – 1024px:** Sidebar collapses to icons; artifact viewer overlays
- **> 1024px:** Full three-column layout

## 4. Key Interaction States

### 4.1 Empty State (New Session)
- Centered welcome message with app name and tagline
- 3-4 suggested starter questions as clickable chips:
  - "What does Lenny say about product-market fit?"
  - "How should I approach my first growth hire?"
  - "What are the best onboarding frameworks?"
  - "Write a Ship 30 essay about retention strategies"
- Subtle animated gradient background on the welcome card

### 4.2 Loading / Streaming State
- **User message:** Appears immediately (optimistic)
- **Assistant response:** Typing indicator (3 pulsing dots) → streaming text appears word-by-word
- **Source citations:** Fade in after the main response completes
- **Artifact:** Slides in panel from right after generation completes

### 4.3 Error States
- **Model unavailable:** Toast notification with switch suggestion
- **Empty retrieval:** Inline message: "I couldn't find relevant information in Lenny's transcripts for this question."
- **Network error:** Retry button in message area
- **Rate limit:** Informational banner with cooldown timer

### 4.4 Source Citation Display
- Collapsible section below the answer
- Each source shows: episode title, guest name, and a brief excerpt
- Click to expand full retrieved chunk
- Links to original transcript (if URL available)

## 5. Component Design Specifications

### 5.1 Message Bubbles
- **User messages:** Right-aligned, amber accent background, rounded corners
- **Assistant messages:** Left-aligned, secondary background, full width
- Markdown rendering in assistant messages (headings, code blocks, lists, bold/italic)
- Subtle entrance animation (fade-up, 200ms)

### 5.2 Input Bar
- Fixed at bottom of chat window
- Glassmorphism effect (frosted glass backdrop)
- Auto-resize textarea (1-5 lines)
- Send button with amber accent, disabled when empty
- Keyboard shortcut: Enter to send, Shift+Enter for newline

### 5.3 Sidebar
- Session list with title, timestamp, and message count
- Active session highlighted with accent border
- Hover effect with subtle background shift
- "New Chat" button at top with `+` icon
- Delete session on hover (trash icon with confirmation)

### 5.4 Model Toggle
- Pill-shaped toggle in the header
- Shows current provider icon + name (e.g., 🦙 Ollama · llama3.1)
- Dropdown on click: list available providers with status indicators (🟢 available / 🔴 unavailable)
- Switching shows a brief toast confirmation

### 5.5 Artifact Viewer
- Side panel that slides in from the right
- Tab bar: "Preview" | "Code"
- Preview tab: Rendered Markdown or sandboxed HTML
- Code tab: Syntax-highlighted raw content
- Action bar: Copy to clipboard, Download as file
- Close button (X) to dismiss panel

## 6. Typography

| Element | Font | Size | Weight | Line Height |
|---------|------|------|--------|-------------|
| H1 | Inter | 28px | 700 | 1.3 |
| H2 | Inter | 22px | 600 | 1.35 |
| H3 | Inter | 18px | 600 | 1.4 |
| Body | Inter | 15px | 400 | 1.6 |
| Small | Inter | 13px | 400 | 1.5 |
| Code | JetBrains Mono | 14px | 400 | 1.5 |
| Input | Inter | 15px | 400 | 1.5 |

## 7. Micro-Animations

| Interaction | Animation | Duration |
|-------------|-----------|----------|
| Message appear | Fade up + scale(0.98→1) | 200ms |
| Typing indicator | 3 dots with staggered pulse | 1.4s loop |
| Sidebar hover | Background fade | 150ms |
| Artifact panel open | Slide in from right | 300ms ease-out |
| Artifact panel close | Slide out to right | 200ms ease-in |
| Model toggle switch | Scale bounce | 200ms |
| Button hover | Subtle lift + glow | 150ms |
| Source citation expand | Accordion slide | 250ms |
| Toast notification | Slide down + fade | 300ms in, 200ms out |

## 8. Accessibility Considerations

- **Color contrast:** All text meets WCAG AA (4.5:1 for body text, 3:1 for large text)
- **Keyboard navigation:** All interactive elements are focusable and operable via keyboard
- **Focus indicators:** Visible focus rings on all interactive elements (amber accent outline)
- **Screen reader support:** Semantic HTML, ARIA labels on icons, live regions for streaming messages
- **Reduced motion:** Respect `prefers-reduced-motion` media query — disable animations
- **Font scaling:** Layout handles up to 200% font size increase without breaking

## 9. Design Decisions & Rationale

| Decision | Rationale |
|----------|-----------|
| Dark mode default | Matches the "professional tool" aesthetic; reduces eye strain for long research sessions |
| Amber accent over blue | Differentiates from competitors; warm tone fits "growth/knowledge" brand |
| Three-column layout | Chat + artifact side-by-side mirrors Claude's artifact viewer — familiar UX pattern |
| Streaming responses | Critical for local LLMs which can be slow; gives immediate feedback |
| Source citations below answer | Non-intrusive but accessible; users who care about grounding can verify |
| Sandboxed iframe for HTML | Security-first approach; clearly communicates what's allowed |
| Glassmorphism input bar | Modern aesthetic that elevates the otherwise functional input area |
| Collapsible sidebar | Maximizes chat space on smaller screens without losing navigation |
