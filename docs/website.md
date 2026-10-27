# Asset Studio website (EA3–EA5B)

The public website lives in [`apps/web/`](../apps/web/). It is a React, TypeScript, Vite, Tailwind CSS, and Lucide application. It has no authentication, database, server runtime, or dependency on private catalog files in browser code. Its pages are Overview, Explore, Collections, project collection details, showcase detail, Asset Health, and About. It is primarily a creative showcase for FM Work, with downloads available only for separately approved files.

## Local commands

Use Node 24 or later and the repository's pnpm version:

```sh
pnpm install --frozen-lockfile
pnpm web:dev
pnpm web:build
pnpm web:preview
```

The app also builds independently with `pnpm --filter @ecosystem-assets/web build`. Its `dev` and `build` scripts run the catalog preparation step. `web:build` adds the final public-output audit. The local UI check needs a running dev server and a Playwright Chromium browser already installed for this repository:

```sh
pnpm web:ui-check
```

That check covers the empty catalog, theme persistence, navigation, direct routes, keyboard focus, mobile menu, unavailable or malformed catalog responses, and a browser-mocked synthetic catalog for gallery, detail, request, download, and collection behavior. It saves QA screenshots under the ignored `apps/web/.generated/` directory. The non-browser security tests run with `pnpm test:web-security`.

## Catalog and publication boundary

[`scripts/prepare-web.mjs`](../scripts/prepare-web.mjs) runs the existing catalog generator and stops on validation errors. It prepares **only** `apps/web/.generated/public/` through a staging directory, writes `catalog.json` from the generated **public catalog**, and copies only approved preview and download bytes into `published/`. Vite's `publicDir` points to that directory. The browser fetches `/catalog.json` and validates its structure before rendering. Missing or malformed data shows an error with a retry action. It never imports the internal catalog or private validation report.

The publication allowlist remains empty, so the production catalog has zero assets, showcases, and collections. For a later owner-approved entry, the generator validates the physical ID, pinned SHA-256, role, rights assertion, approver and date, Momee exclusion, and file format. It emits a deterministic `/published/<SHA-256 of ID>.<format>` URL. Preview approval is independent from download approval. The delivery step rejects traversal and symlinks, checks the source byte count and hash, and copies only the approved file. Copying `projects/`, `incoming/`, `catalog-output/`, documentation, or the repository root into a web root is forbidden. See [the catalog publication model](catalog.md#showcase-publication-ea5b) for an entry example and approval gates.

[`scripts/verify-web-dist.mjs`](../scripts/verify-web-dist.mjs) compares the built catalog to a fresh public catalog generated from the current allowlist. It permits only `index.html`, `catalog.json`, Vite's JavaScript/CSS files, and exact approved `published/` URLs. It requires every approved preview and download binary, verifies its size and hash, and rejects symlinks, unexpected files, stale catalogs, and private asset paths in built text. The synthetic fixtures live under `tests/fixtures/` or temporary directories, outside catalog inventory and static output; the production build audit fails if one is copied in.

## Navigation and themes

The app uses a small History API router, with ordinary anchor links and `popstate` support. `/collections/:projectId` opens a project only when it has public showcases. `/assets/:projectId/:slug` opens one showcase. Vercel rewrites the six non-root route patterns to `index.html`, so direct page refresh works while static files are served normally. The desktop sidebar and page header stay visible while scrolling; the sidebar becomes a keyboard-accessible mobile menu. Both navigation layouts link to Support and to the Gateway for more projects.

Explore displays one card per public showcase, with its first approved media item as the representative image. It supports title, description, project, tag, and public caption search; project, category, and preview format filters; name and preview-size sorting; grid and list views; clear filters; and distinct empty and no-results states. These controls use URL query parameters (`q`, `project`, `category`, `format`, `sort`, `view`) for sharing and browser back/forward. Collection cards group showcases by project, show counts and facets, and link to project details. Image media use contained sizing and a transparency grid; missing previews show a fallback. Detail pages show ordered gallery media, captions, public metadata, related showcases, and approved download options. Showcase-only entries show no original download links.

The **Request Asset** action uses `VITE_PUBLIC_CONTACT_EMAIL` from `apps/web/.env.example`. Set it to an owner-approved public address in the build environment before release. The app then creates a `mailto:` message with the public showcase title and ID and an intended-use prompt. It includes no private repository path. When unset or invalid, the control is disabled with a setup note; no address is invented. Requests are reviewed individually and do not guarantee access or permission to reuse the work. There is no backend or request tracking.

Light and dark themes use shared CSS tokens. The user's choice is stored in `localStorage`; if no choice exists, the system preference is used. The header also switches the interface between English and Indonesian, remembering the choice in `localStorage` and initially following the browser language. Published showcase titles, descriptions, captions, categories, and tags remain in their source language. The UI includes a skip link, visible focus styles, semantic navigation, and reduced-motion support.

## Vercel preparation

The tracked [`vercel.json`](../vercel.json) is configuration only; EA4 does not deploy. Connect the repository with its root as the project root. Set Node.js to 24.x and add the Vercel environment variable `ENABLE_EXPERIMENTAL_COREPACK=1` so dependency installation uses the root package's pinned pnpm 11.17.0. Leave Vercel's Install Command at its default; an explicit `pnpm install` override can select an older pnpm. Enable Git LFS in the Vercel project's Git settings so the catalog generator receives hydrated binary content; it fails safely when it sees LFS pointers. The config specifies `pnpm web:build` and output directory `apps/web/dist`. Do not add `projects/`, `incoming/`, `catalog-output/`, or the repository root to Vercel's static output. Keep the Vercel project private until the owner chooses to deploy the public site.

## Known limits

- There are no approved public assets or showcases, so the gallery and collections display real empty states. No private statistics or demo assets are bundled.
- The public Asset Health page describes the publication boundary. Detailed internal validation findings stay in the private repository.
- The lightweight router covers the documented routes. New route shapes need a matching Vercel rewrite and route test.
- Preview files are public bytes and can be saved from the browser. Only approve derivatives and screenshots suitable for unrestricted public viewing; the interface cannot prevent copying them.
- There is no ZIP bundle, 3D viewer, email backend, or authentication. Technical model statistics are not shown until approved public metadata exists.
- Browser UI checks require local Chromium; production build and security checks do not.
