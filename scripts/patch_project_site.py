from pathlib import Path

project = Path('/home/ubuntu/pmlg-website')

vite = project / 'vite.config.ts'
text = vite.read_text(encoding='utf-8')
text = text.replace(
    'export default defineConfig({\n  // Project-site deployment target: https://pmlg.github.io/PMLG-Events.github.io/\n  base: "/PMLG-Events.github.io/",',
    'const DEPLOY_BASE = "/PMLG-Events.github.io/";\n\nexport default defineConfig({\n  // Keep the Manus preview at root while emitting project-site URLs for production.\n  base: process.env.NODE_ENV === "production" ? DEPLOY_BASE : "/",',
)
vite.write_text(text, encoding='utf-8')

app = project / 'client/src/App.tsx'
text = app.read_text(encoding='utf-8')
text = text.replace('import { Route, Switch } from "wouter";', 'import { Route, Router as WouterRouter, Switch } from "wouter";')
text = text.replace('function Router() {\n  return (\n    <Switch>', 'function Router() {\n  return (\n    <WouterRouter base={import.meta.env.BASE_URL.replace(/\\/$/, "")}>\n      <Switch>')
text = text.replace('    </Switch>\n  );\n}', '      </Switch>\n    </WouterRouter>\n  );\n}', 1)
app.write_text(text, encoding='utf-8')

for relative in [
    'client/src/pages/Home.tsx',
    'client/src/pages/About.tsx',
    'client/src/pages/Events.tsx',
    'client/src/pages/Impact.tsx',
    'client/src/pages/Values.tsx',
]:
    path = project / relative
    page = path.read_text(encoding='utf-8')
    page = page.replace('src="/logo.png"', 'src={`${import.meta.env.BASE_URL}logo.png`}')
    path.write_text(page, encoding='utf-8')

index = project / 'client/index.html'
html = index.read_text(encoding='utf-8')
html = html.replace('href="/logo.png"', 'href="%BASE_URL%logo.png"')
index.write_text(html, encoding='utf-8')

bundle_script = project / 'scripts/build_github_pages_bundle.py'
text = bundle_script.read_text(encoding='utf-8')
text = text.replace(
    'The compiled paths assume a root-hosted site, such as a custom domain (`pmlg.com.au`) or `pmlg.github.io`. If you deploy as a project site under `username.github.io/repository-name/`, rebuild the project with a matching Vite `base` path before publishing.',
    'This bundle is compiled for the project site `https://pmlg.github.io/PMLG-Events.github.io/`. Copy the bundle contents to the repository root; do not change the asset paths.',
)
bundle_script.write_text(text, encoding='utf-8')

print('patched project-site configuration')
