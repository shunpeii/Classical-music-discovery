# Development rules

- Preserve existing behavior and public URL.
- Run npm run check (lint, typecheck, build) for every change; fix failures before deployment.
- Never claim checks passed without actual results.
- Centralize shared components and URL resolution; avoid unrelated changes.
- Verify data references and image assets; do not label unverified concerts as verified.

- UI/UX changes must stay on a dedicated feature branch until the user explicitly approves merging into main.
- Verify the feature branch using manual Pages deployment and npm run check before requesting approval.
