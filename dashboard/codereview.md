# General Frontend Code Review & Deployment Checklist

Use this checklist to ensure code quality, design consistency, responsiveness, and build stability for Next.js frontend projects.

## 1. Responsiveness & Layout
- [ ] **Mobile First (< 768px)**
    - [ ] **Navigation**: Sidebars/drawers must be collapsed by default and close upon selection.
    - [ ] **Typography**: Headers and large text must scale (`clamp()`) or wrap (`break-words`) to prevent truncation.
    - [ ] **Content Width**: Ensure no horizontal scrolling occurs due to fixed widths or overflowing content (use `[overflow-wrap:anywhere]` for user-generated content).
    - [ ] **Touch Targets**: Interactive elements should have adequate size (min 44px) for touch.
- [ ] **Tablet & Desktop (>= 768px)**
    - [ ] **Layout Transitions**: Layouts should adapt gracefully (e.g., auto-expanding sidebars, changing grid columns).
    - [ ] **WhiteSpace**: Use appropriate spacing for larger screens.

## 2. Design & UI Consistency
- [ ] **Typography**:
    - [ ] Use consistent font families and weights variables.
    - [ ] Ensure fluid scaling for major headings.
- [ ] **Colors & Theming**:
    - [ ] Use CSS variables or Tailwind utility classes for colors to ensure dark mode compatibility.
    - [ ] Verify text contrast ratios for accessibility.
- [ ] **Component Parity**:
    - [ ] Similar components (e.g., cards, lists) should share base styles and spacing.

## 3. Component Behavior & State
- [ ] **Feedback**:
    - [ ] Buttons and links must have hover, active, and focus states.
    - [ ] Loading states (skeletons/spinners) must be present for async operations.
- [ ] **Error Handling**:
    - [ ] UI should gracefully handle API errors or empty states.
- [ ] **Hydration**:
    - [ ] Ensure no hydration mismatches (e.g., nesting invalid HTML tags).

## 4. Next.js & Code Quality
- [ ] **Linting & Formatting**:
    - [ ] Run `npm run lint` and resolving all warnings.
    - [ ] Ensure code follows project formatting rules (Prettier).
- [ ] **Performance**:
    - [ ] Optimize images using `next/image`.
    - [ ] Defer heavy scripts or styles where possible.
- [ ] **Console Logs**:
    - [ ] Remove `console.log` statements used for debugging.
    - [ ] Check browser console for runtime errors.

## 5. Deployment Readiness (Vercel)
- [ ] **Build Check**:
    - [ ] Run `npm run build` locally to ensure a successful compilation.
- [ ] **Environment**:
    - [ ] Verify all `NEXT_PUBLIC_` variables are defined in the deployment dashboard.
- [ ] **Configuration**:
    - [ ] Ensure `next.config.js` and `package.json` scripts are correctly set up for the platform.
