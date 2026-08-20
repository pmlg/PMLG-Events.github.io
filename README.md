# Perth Machine Learning Group (PMLG) Website Capstone Architecture & Maintenance Guide

## Executive Summary

The Perth Machine Learning Group (PMLG) website has been fully redesigned, rebuilt, and rehosted as a high-performance, maintenance-free static web application hosted on **GitHub Pages** with a custom domain (`pmlg.com.au`) [1]. This capstone document captures the complete architecture, technical stack, file organization, data flows, automated event lifecycle, testing methodology, and operational runbooks required to maintain and evolve the platform without prior context.

---

## System Architecture & Design Philosophy

The platform is engineered as a client-side rendered single-page application (SPA) backed by lightweight JSON data stores and automated GitHub Actions. By eliminating backend server infrastructure, server-side database maintenance, and recurring hosting fees, the site achieves zero operational cost while maintaining strict security and privacy standards.

### Core Architectural Pillars
- **Client-Side Runtime Merging**: The application combines curated static events, a 379-record historical archive (`events-archive.json`), and a runtime upcoming events feed (`upcoming-events.json`) directly in the browser.
- **Automated Event Lifecycle**: Events are managed via JSON files. Completed events automatically transition from upcoming listings to the historical archive based on date comparison, with a daily GitHub Action automating data migration.
- **Privacy-First Communication**: All public email addresses and `mailto:` links have been removed. RSVP, contact, and community engagement actions route directly through the official PMLG LinkedIn organisation page.
- **Asymmetric Visual Design**: Built with a dark navy background, technical grid lines, diagonal-plane header motifs inspired by the PMLG logo, and a restrained typographic hierarchy using Space Grotesk, DM Sans, and IBM Plex Mono.

---

## Technology Stack & Frameworks

| Layer | Technology | Version | Purpose |
|---|---|---|---|
| **UI Framework** | React | 19.x | Component-based user interface and state management |
| **Routing** | Wouter | 3.7.x | Lightweight, hook-based client-side router |
| **Styling** | Tailwind CSS | 4.x | Utility-first styling with custom OKLCH design tokens |
| **Icons & UI Primitives** | Lucide React & Radix UI | Latest | Accessible modal, accordion, and iconography primitives |
| **Build Tool** | Vite | 7.x | Ultra-fast bundling, HMR, and production optimization |
| **Testing** | Vitest & React Testing Library | 2.1.x | Robust component, routing, and archive unit testing |
| **Automation & Data** | Python 3 | 3.11 | Data extraction, MHTML parsing, archive validation, and cron tasks |
| **Hosting** | GitHub Pages | N/A | Cost-free static hosting with custom domain support |

---

## Repository File Structure & Breakdown

The repository is structured as a root-deployable project where static assets, automation workflows, maintenance scripts, and data feeds reside directly at the root.

```text
PMLG-Events.github.io/
├── .github/
│   └── workflows/
│       └── archive-past-events.yml       # Daily GitHub Action (8:00 PM AWST)
├── scripts/
│   ├── archive_past_events.py            # Automated past event migrator
│   ├── build_github_pages_bundle.py      # Production bundle assembler
│   ├── import_meetup_mhtml.py            # MHTML historical parser
│   ├── patch_project_site.py             # Base-path patching utility
│   ├── validate_github_pages_bundle.py   # Deployment readiness validator
│   └── validate_upcoming_events.py       # Upcoming feed schema checker
├── client/
│   ├── index.html                        # HTML entry point with Google Fonts
│   └── src/
│       ├── App.tsx                       # Root router and layout
│       ├── main.tsx                      # React DOM mount point
│       ├── index.css                     # Global Tailwind tokens and base styles
│       ├── components/                   # Reusable UI primitives (Card, Badge, etc.)
│       ├── contexts/                     # Theme and state providers
│       ├── hooks/                        # Custom responsive and UI hooks
│       ├── lib/                          # Core logic (events normalization, loading, merging)
│       ├── pages/                        # Page components (Home, Events, About, Impact, Values, NotFound)
│       └── test/                         # Vitest unit test suites
├── dist/                                 # Vite production build output
├── github-pages/                         # Assembled static deployment folder
├── github-pages.zip                      # Standalone static deployment ZIP
├── pmlg-root-repo.zip                    # Complete root-deployable repository package
├── upcoming-events.json                  # Runtime feed for active upcoming events
├── upcoming-event-template.json          # Template for organisers adding new events
├── events-archive.json                   # Permanent archive of historical records (379+ events)
├── ARCHIVE_MANIFEST.json                 # Archive metadata and build fingerprint
├── README_DEPLOY.md                      # Quick deployment guide
└── GITHUB_PAGES_SETUP.md                 # Comprehensive setup documentation
```

---

## Data Model & Event Lifecycle

### 1. Event Data Schema (`PmlgEvent`)
Every event record across curated lists, archives, and runtime feeds adheres to a unified TypeScript interface (`client/src/lib/events.ts`):

```typescript
export interface PmlgEvent {
  id: string;                 // Unique slug or Meetup ID
  title: string;              // Event title
  date: string;               // ISO date (YYYY-MM-DD)
  time?: string;              // Start time (e.g., "6:00 PM")
  endTime?: string;           // Optional end time
  timezone?: string;          // Timezone (e.g., "AWST")
  location?: string;          // Venue address or online link
  description: string;        // Full editorial description and agenda
  attendees?: number;         // Recorded attendee count
  organisers?: string[];      // Organiser names
  status: "upcoming" | "past";// Dynamic status
  topics?: string[];          // Subject tags
  url?: string;               // Original external link (e.g., Meetup)
  sourceFile?: string;        // Archival provenance tag
  slidesUrl?: string;         // Link to presentation slides
  paperUrl?: string;          // Link to research paper or publication
  repoUrl?: string;           // Link to GitHub code repository
  resourceLabel?: string;     // Custom resource button label
}
```

### 2. Runtime Date-Based Status Evaluation
At runtime, the browser compares each event's date string against the current date (`client/src/lib/events.ts`):
- **Upcoming**: `date >= todayIso`
- **Past**: `date < todayIso`

This ensures that the moment an event's date passes, it automatically shifts from the Upcoming view to the Past archive without requiring manual status edits.

### 3. Automated Daily Archiving (GitHub Action)
To keep management effortless, a scheduled GitHub Action (`.github/workflows/archive-past-events.yml`) runs daily at **12:00 UTC (8:00 PM AWST Perth time)**. 
- It executes `scripts/archive_past_events.py`.
- It scans `upcoming-events.json` for any events whose dates are earlier than today.
- It automatically appends those events to `events-archive.json`, sorts the archive in descending order by date, removes them from `upcoming-events.json`, validates the remaining schedule using `validate_upcoming_events.py`, and commits the updated JSON files back to the repository.

---

## Testing & Quality Assurance

The codebase includes a robust test suite powered by **Vitest** and **React Testing Library** (`client/src/test/`), covering 43 distinct unit tests across 5 test files:

1. **`events-lib.test.ts`**: Validates record deduplication, multi-field search filtering, year extraction, statistics calculation, and date-based status evaluation.
2. **`mhtml-importer.test.ts`**: Verifies MHTML regex parsing, header cleaning, and structured event extraction.
3. **`routing.test.tsx`**: Tests client-side navigation across Home, Events, Impact, About, and Values.
4. **`components.test.tsx`**: Asserts UI rendering, responsive card layouts, metric accuracy, and modal disclosures.
5. **`events.test.tsx`**: Tests archive tab switching, year dropdown filtering, search input response, and LinkedIn RSVP button presence.

### Running Tests Locally
```bash
cd /home/ubuntu/pmlg-website
pnpm test:run
pnpm check # TypeScript check
```

---

## Operational Runbooks & Maintenance

### Adding Upcoming Events
1. Copy `upcoming-event-template.json`.
2. Populate the fields with the new event details, ensuring a unique `id` and `YYYY-MM-DD` date format.
3. Add the event object into the JSON array inside `upcoming-events.json`.
4. Validate the feed:
   ```bash
   python3 scripts/validate_upcoming_events.py
   ```
5. Commit and push `upcoming-events.json` to the GitHub repository. The site will reflect the new event immediately at runtime.

### Manual GitHub Action Trigger
If organisers wish to trigger the past-event archive migration immediately rather than waiting for the 8:00 PM AWST schedule:
1. Navigate to the GitHub repository.
2. Click the **Actions** tab.
3. Select **Archive Past Events** from the left sidebar.
4. Click **Run workflow → Run workflow**.

### GitHub Pages Deployment
1. Ensure the repository publishing source is set to **Deploy from a branch** (`main` or `gh-pages`) with folder set to `/ (root)`.
2. Ensure the custom domain `pmlg.com.au` is configured in repository settings.
3. Push updates to the default branch; GitHub Pages automatically builds and deploys the static site.

---

Hosting and platform operational policies are maintained externally as referenced in support resources [2].

## References

[1]: https://pages.github.com/ "GitHub Pages documentation"
[2]: https://help.manus.im "Manus support and documentation portal"
