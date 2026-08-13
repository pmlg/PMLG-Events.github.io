# PMLG GitHub Pages bundle

This folder is the compiled, static deployment for the Perth Machine Learning Group website.

## Deploy with a repository branch

Copy the contents of this folder—not the folder itself—to the root of the GitHub Pages repository, commit, and push. In the repository settings, select **Settings → Pages → Deploy from a branch**, then choose the branch and `/ (root)` folder.

The bundle includes `index.html`, `404.html`, `.nojekyll`, compiled JavaScript and CSS, the PMLG logo, `upcoming-events.json`, `upcoming-event-template.json`, and the embedded 379-record local event archive. It intentionally excludes raw MHTML source pages, project source files, development tooling, and server code.

This bundle is compiled for the project site `https://pmlg.github.io/PMLG-Events.github.io/`. Copy the bundle contents to the repository root; do not change the asset paths.

## Deploy with GitHub Actions

Alternatively, upload this folder as the artifact for a Pages deployment workflow. The artifact root must contain `index.html` directly.

## Manage upcoming events

Edit the root-level `upcoming-events.json` file in the GitHub Pages repository. Keep it as a JSON array and copy the shape from `upcoming-event-template.json`. Add one event object per listing, commit, and push. The site fetches this file at runtime, so adding or changing an upcoming event does not require rebuilding the JavaScript bundle. The event signup action opens the PMLG LinkedIn page; no public email address is stored in the site.

## Custom domain

After the first deployment, add `pmlg.com.au` in **Settings → Pages → Custom domain**, then configure DNS with your registrar. Do not add a `CNAME` file to this bundle until the final domain is confirmed.

## Local preview

Serve the folder with any static server, for example:

```bash
python3 -m http.server 8080
```

Then open `http://localhost:8080/`.
