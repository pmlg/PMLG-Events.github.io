# PMLG Website - GitHub Pages Deployment Guide

This document provides instructions for deploying the Perth Machine Learning Group website to GitHub Pages.

## Overview

The PMLG website is a static React application built with Vite and Tailwind CSS. It is designed to be deployed on GitHub Pages with minimal cost and maintenance overhead.

**Key Features:**
- Static hosting (no backend server required)
- Event management via JSON files
- LinkedIn-based RSVP system without a public email address
- Responsive design optimized for all devices
- Dark theme with PMLG brand colors

## Prerequisites

Before deploying, ensure you have:
- A GitHub account with administrative access to the `pmlg.github.io` repository
- Node.js 18+ and pnpm installed locally
- Git installed and configured

## Deployment Steps

### 1. Build the Project

First, build the static site for production:

```bash
cd /home/ubuntu/pmlg-website
pnpm install
pnpm build
```

This creates a `dist/` directory containing the optimized static files.

### 2. Push to GitHub Pages Repository

The built files should be pushed to the `gh-pages` branch of your repository:

```bash
# Navigate to the project directory
cd /home/ubuntu/pmlg-website

# Initialize git if not already done
git init
git remote add origin https://github.com/pmlg/pmlg.github.io.git

# Build the project
pnpm build

# Create or switch to gh-pages branch
git checkout --orphan gh-pages

# Add the dist folder contents
cp -r dist/* .

# Commit and push
git add .
git commit -m "Deploy PMLG website"
git push -u origin gh-pages
```

### 3. Configure GitHub Pages

In your GitHub repository settings:

1. Go to **Settings** → **Pages**
2. Under "Build and deployment", select:
   - **Source**: Deploy from a branch
   - **Branch**: `gh-pages`
   - **Folder**: `/ (root)`
3. Click **Save**

GitHub will automatically deploy your site. Access it at: `https://pmlg.github.io/`

### 4. Configure Custom Domain

To use your custom domain (`pmlg.com.au`):

1. In GitHub Pages settings, enter your custom domain in the "Custom domain" field
2. Update your domain's DNS settings to point to GitHub Pages:
   - Add an `A` record pointing to `185.199.108.153`
   - Add an `A` record pointing to `185.199.109.153`
   - Add an `A` record pointing to `185.199.110.153`
   - Add an `A` record pointing to `185.199.111.153`
   - Or add a `CNAME` record pointing to `pmlg.github.io`
3. Enable HTTPS (GitHub Pages will automatically provision an SSL certificate)

## Event Lifecycle & Management

### How Upcoming Events Become Part of the Archive

The PMLG website features a dynamic event lifecycle designed to keep the site evergreen and maintenance-free:

1. **Adding an Upcoming Event:**
   Organisers add or update upcoming events by editing `upcoming-events.json` in the repository root (or using `upcoming-event-template.json` as a starting point).
   
2. **Automatic Status Transition:**
   At runtime, the website automatically evaluates each event's date against the current date. As soon as an event's date passes, its status automatically shifts from `upcoming` to `past`. It immediately appears in the **Events Archive** alongside the historical MHTML records, retaining all its descriptions, slide links, publication links, and repository references.

3. **Automated Daily Archiving (GitHub Action):**
   To eliminate manual archiving overhead, a scheduled GitHub Action (`.github/workflows/archive-past-events.yml`) runs daily at 00:30 UTC. It automatically detects any events in `upcoming-events.json` whose dates have passed, migrates them into `client/src/data/events-archive.json`, validates the remaining schedule, and commits the updated files back to the repository automatically. Organisers can also trigger this workflow manually from the **Actions** tab in GitHub.

### Event JSON Structure

```json
{
  "id": "unique-event-id",
  "title": "Event Title",
  "date": "YYYY-MM-DD",
  "time": "6:00 PM",
  "endTime": "8:00 PM",
  "timezone": "AWST",
  "location": "State Library of WA, Perth",
  "description": "Detailed description of the talk, workshop, or publication.",
  "topics": ["Machine learning", "Transformers"],
  "slidesUrl": "https://...",
  "paperUrl": "https://...",
  "repoUrl": "https://github.com/..."
}
```

### Updating Events

1. Edit the root-level `upcoming-events.json` in the Pages repository. Copy the structure from `upcoming-event-template.json` and add one object per event inside the JSON array.
2. Commit and push to the Pages source branch:

```bash
git add upcoming-events.json upcoming-event-template.json
git commit -m "Update events"
git push origin gh-pages
```

3. The website will automatically update within a few minutes

## RSVP System

The website uses LinkedIn-based signups. When users click "RSVP on LinkedIn" on an upcoming event, they are taken to the PMLG LinkedIn page to request a place and coordinate details without exposing a public email address.

The destination is defined once in `client/src/lib/events.ts` as `PMLG_LINKEDIN_URL`.

## Local Development

To run the site locally for testing:

```bash
cd /home/ubuntu/pmlg-website
pnpm install
pnpm dev
```

The site will be available at `http://localhost:3000/`

## Maintenance

### Regular Updates

- **Events**: Update root-level `upcoming-events.json` as needed
- **Content**: Edit page content in `client/src/pages/`
- **Styling**: Modify colors and styles in `client/src/index.css`

### Monitoring

GitHub Pages provides automatic HTTPS and uptime monitoring. Check deployment status in:
- Repository → **Actions** tab (shows build history)
- Repository → **Settings** → **Pages** (shows deployment status)

## Troubleshooting

### Site Not Updating After Push

1. Wait 5-10 minutes for GitHub to rebuild
2. Check the **Actions** tab for build errors
3. Clear browser cache (Ctrl+Shift+Delete or Cmd+Shift+Delete)

### Custom Domain Not Working

1. Verify DNS records are correctly configured (use `nslookup` or `dig`)
2. Wait up to 48 hours for DNS propagation
3. Check GitHub Pages settings for any error messages

### Build Failures

1. Check the **Actions** tab for error messages
2. Ensure all JSON files are valid (use a JSON validator)
3. Verify no breaking changes were made to the codebase

## Support & Resources

- **GitHub Pages Documentation**: https://docs.github.com/en/pages
- **Vite Documentation**: https://vitejs.dev/
- **Tailwind CSS Documentation**: https://tailwindcss.com/
- **PMLG Contact**: https://www.linkedin.com/company/perth-machine-learning-group/

## Cost Savings

By hosting on GitHub Pages instead of traditional web hosting:

- **Hosting Cost**: $0/month (free for public repositories)
- **Domain Cost**: ~$10-15/year (domain registration only)
- **Maintenance**: Minimal (no server management required)

This represents a significant cost reduction compared to traditional hosting services while maintaining full functionality for event management and community engagement.
