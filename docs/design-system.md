# Sharp Operations Design System

## Summary
- Dark-first monitoring UI is the default.
- Light mode is supported through the same token set and layout rules.
- Use lines, density, and alignment before using filled surfaces.
- Keep copy short and operational.
- Use strong status colors only for risk and state changes.

## Tokens
### Color
- `bg/base`: dark `#0a0a0a`, light `#fafbfc`
- `bg/elevated`: dark `#111111`, light `#ffffff`
- `bg/muted`: dark `#171717`, light `#eef2f6`
- `border/subtle`: dark `#292929`, light `#cfd6df`
- `text/strong`: dark `#fafafa`, light `#1f2937`
- `text/base`: dark `#e5e5e5`, light `#334155`
- `text/muted`: dark `#a3a3a3`, light `#64748b`
- `danger`: `#ff453a`
- `warning`: `#ffb020`
- `success`: `#22c55e`
- `info`: `#3b82f6`

### Typography
- Page title: `28px / 700 / -0.04em`
- Section title: `14px / 600 / 0.12em uppercase`
- KPI value: `40px / 700 / -0.05em`
- Table header: `11px / 600 / 0.12em uppercase`
- Body text: `13-14px / 400`
- Numeric UI uses tabular figures.

### Layout
- Header height: `48px`
- Sidebar width: open `240px`, compact `64px`
- Page horizontal padding: `16-24px`
- Section gap: `16-24px`
- Inner padding: `16px`
- Table row height target: `44px`
- Radius: `0-2px`
- Shadow: none

## Layout Rules
- App shell is fixed two-column on desktop and single-column with drawer on mobile.
- Use one scroll container per page area. Avoid nested vertical scroll where possible.
- Table overflow is horizontal only when required.
- KPI uses a strip, not independent cards.
- Active navigation is shown with line, text weight, and contrast.

## Component Contracts
### `AppShell`
- Fixed-width sidebar with compact mode.
- Compact mode shows short labels only.
- Theme toggle is available from shell controls.

### `PageHeader`
- Contains title, optional meta text, and minimal actions.
- No explanatory subtitle.

### `MetricStrip` / `MetricBlock`
- Displays operational KPIs in one strip.
- Neutral metrics stay monochrome.
- Risk metrics may use warning or danger color.

### `SectionFrame`
- Generic bordered container for dense content.
- Use for charts, tables, details, and alerts.

### `ControlBar`
- One-line control surface for search, date selection, refresh, and filters.
- Wraps on narrow screens without forcing horizontal overflow.

### `StatusBadge`
- Flat rectangular badge.
- Tones: `high`, `medium`, `low`, `neutral`.

### `EmptyState`
- Short title plus optional one-line guidance.
- Avoid long explanations.

### `DataTable`
- Border-separated rows.
- Uppercase compact headers.
- Row expansion stays visually attached to the row, not separate card UI.

## Copy Rules
- Prefer noun labels: `対象日`, `クリック数`, `CV数`, `再読込`, `詳細`.
- Avoid helper sentences unless the state would otherwise be ambiguous.
- Empty and error states may contain one short line of guidance.
- All Japanese strings must remain UTF-8 in app code and tests.

## Usage Rules
- Reuse system components before adding page-local wrappers.
- Document a new visual pattern here before reusing it.
- Avoid page-local color decisions outside the token set.
- Do not reintroduce rounded card UI or shadow hierarchy without updating this spec.
