# Frontend keyboard accessibility

## Interaction rules

- Native links, buttons, inputs, selects, textareas, file controls, and form submission keep browser-standard Tab/Shift+Tab, Enter, and Space behavior.
- Visible `:focus-visible` styling is shared across controls, including textareas and programmatically focusable elements.
- Horizontal tab sets use one Tab stop; Left/Right arrows move and activate tabs, with Home/End moving to the first/last tab.
- Catalog family, variant, and Style Option card grids use physical arrow direction to focus the nearest visible card. Enter/Space activate the focused native button. Tab remains available to leave each grid.
- In a Family drawer, variant rows are scoped to that Family. Enter opens the focused variant details and moves focus to the next-step action; Enter again activates the existing Designs route. Back-to-list restores focus to the chosen variant card.
- Custom listboxes open with ArrowUp/ArrowDown; arrows, Home/End, Enter, Escape, and Tab have local listbox behavior. They do not consume keys while the user is typing in a text input.
- Modal dialogs keep focus inside while open, close through their explicit close/cancel control on Escape, and return focus to the invoking element. Tab remains available to move between modal controls.
- Arrow keys are not registered as app-wide shortcuts and are not intercepted in text fields, numeric entry, or page scrolling.

## Validation expectation

Run the frontend unit suite, typecheck, lint, and production build. Manually verify representative Shop and Main Supplier journeys using only a keyboard at desktop width and a narrow/mobile viewport. Check focus visibility, dialog open/close and focus restoration, tabs, grids, dropdowns, form validation/submission, pagination, file picker access, and that text-entry/scrolling arrow keys retain native behavior.
