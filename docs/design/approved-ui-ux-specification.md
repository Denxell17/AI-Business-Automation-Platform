# ABAP Approved UI/UX Specification

## Document Status

- **Product:** ABAP — AI Business Automation Platform
- **Direction:** A — Balanced Operations
- **Design system:** B — Quiet Precision
- **Dark background:** Original Soft Graphite achievable-dashboard treatment
- **Status treatment:** B — Shape-coded outline
- **Approval state:** Approved for phased implementation by the project owner
- **Canonical dashboard reference:**
  `assets/abap-final-dashboard-proposal.png`
- **Approved logo concept reference:**
  `assets/abap-approved-logo-reference.png`

The dashboard reference is a design target, not implemented application code.
Values shown as em dashes are runtime placeholders and must never be replaced
with fabricated product data.

## 1. Product and Design Objective

ABAP should feel intelligent, capable, clear, controlled, and dependable. The
interface must support daily operational work without becoming a monitoring
console or a marketing dashboard. Information hierarchy should come from type,
spacing, alignment, borders, and restrained surfaces rather than decoration.

The design must preserve ABAP's server-rendered FastAPI/Jinja architecture,
role and permission boundaries, signed sessions, CSRF protection, and separate
payroll authorization.

## 2. Brand System

### Approved Identity

Preserve the recognizable ABAP wordmark, A-and-dot motif, blue/cyan identity,
and integrated forward-motion path.

The application sidebar uses exactly one ABAP wordmark lockup with the
descriptor **AI Business Automation Platform**. Do not place a separate compact
A icon beside the wordmark; this creates a duplicated-A appearance.

Use the compact A-and-dot icon alone only where space genuinely requires it,
such as the favicon and collapsed/mobile header.

### Production Logo Requirements

The approved raster concept is not production master artwork. Before visual
implementation is considered complete, reconstruct it as exact SVG artwork
with:

- Full logo with descriptor
- Wordmark-only version
- Compact A-and-dot icon
- Monochrome version
- Reversed version
- Transparent raster exports
- Consistent geometry and clear-space rules
- Minimum-size rules
- Simplified small-size artwork without thin motion details

The controlled cobalt-to-cyan gradient is permitted inside the logo only.

## 3. Color System

### Dark Theme — Approved Primary Theme

| Token | Approximate value | Purpose |
| --- | --- | --- |
| Canvas | `#1B1F24` | Main workspace background |
| Sidebar | `#15191E` | Primary navigation background |
| Surface | `#242A31` | Standard panels and controls |
| Raised surface | `#2B323A` | Selected or elevated content |
| Border | `#46515E` | Dividers and control boundaries |
| Primary text | `#F4F6F8` | Headings and primary content |
| Secondary text | `#C1C9D2` | Supporting content |
| Interaction | `#3B82F6` | Links, selected state, primary action |
| Focus | `#75B5FF` | High-visibility offset focus ring |

The selected treatment is the original Soft Graphite dashboard—not the later
Cool Graphite, Midnight Navy, Slate Blue, Neutral Charcoal, or Warm Graphite
comparison variants.

### Optional Light Theme

The light theme is required for accessibility and user preference. Use a soft,
professional off-white canvas near `#F6F8FB`, a quiet cool-gray sidebar near
`#EEF2F6`, white or near-white surfaces, cool-gray borders near `#CBD5E1`, dark
slate primary text near `#172033`, and readable secondary text near `#526173`.

Do not create harsh all-white expanses. The light theme must preserve the same
information architecture and component behavior as the dark theme.

### Color Rules

- Cobalt is the routine interaction color.
- Cyan is a small brand accent, primarily inside the logo.
- Use flat fills; no gradients outside the logo.
- Do not use glow, glassmorphism, blur, neon, or large saturated areas.
- Do not use pure white on pure black.
- Validate final token combinations against WCAG 2.2 AA.

## 4. Typography and Density

- Preferred family: Inter Variable with practical system fallbacks.
- Use type size, weight, spacing, and alignment for hierarchy.
- Use tabular numerals for payroll, counts, dates, durations, and executions.
- Keep body text comfortably readable at browser zoom and text enlargement.
- Use moderate information density: efficient for daily operators without the
  compressed feel of a technical console.
- Keep persistent labels on forms; placeholders are never labels.

## 5. Shape, Surface, and Motion

- Default component radius: approximately 8px.
- Acceptable range: 6–10px according to component size.
- Use thin cool-gray borders and near-zero shadows.
- Avoid nested card-on-card patterns when dividers or whitespace are enough.
- Use one primary action per action group.
- Respect `prefers-reduced-motion`.
- Avoid flashing, pulsing, parallax, decorative animation, and unnecessary
  movement.

## 6. Status System

Never communicate status through color alone. Every status combines shape,
symbol, persistent text, and restrained color.

- **Completed:** circle + check + text + restrained green
- **Running:** diamond-derived shape + activity symbol + text + cobalt blue
- **Failed:** rounded-square or octagonal shape + X + text + restrained red
- **Enabled:** circle + check + text
- **Disabled:** distinct outlined shape + minus + text + neutral gray

Amber is reserved for warning or attention states; it is not used for normal
workflow execution or schedule availability.

Standard directories and tables use quiet outlined statuses. Strong filled
states or status rails are reserved for genuinely urgent attention items.

Database-backed wording takes precedence over generic design vocabulary.
Workflow and agent executions use Running, Completed, and Failed. Workflow
schedules use Enabled and Disabled.

## 7. Information Architecture and Navigation

Group navigation by user purpose and show entries only when authorized.

### Workspace

- Dashboard
- Employees
- Workflows
- Agent templates
- AI Assistant
- Reports

### Administration

- Activity log
- User accounts

### Resources

- System health
- API documentation

System Health and API Documentation are secondary resources, not primary daily
modules. Do not add Integrations, Settings, Billing, Data, or other competitor-
inspired modules until corresponding ABAP functionality exists.

The sidebar footer shows the authenticated account, role, and sign-out action.
The responsive header may use the compact logo icon and a clearly labelled menu.

## 8. Dashboard Specification

### Purpose

The Dashboard is an operational overview, not a module launcher and not a
marketing analytics page. It should answer:

1. What records and automation are present?
2. What is currently running or failing?
3. What is scheduled next?
4. What recently happened?
5. What action can this user take now?

### Header

- Eyebrow: **Operational overview**
- Heading: **Dashboard**
- Supporting copy: system activity, attention items, and useful actions
- One permission-aware primary action, normally **Create workflow** for an
  authorized administrator

Do not add global search or notification controls until those features exist.

### Summary Metrics

- Employees — current employee records
- Departments — derived from workforce records
- Active workflows — current workflow lifecycle state
- Failed runs — workflow execution history

Counts must be loaded from current records. Empty, loading, unavailable, and
permission-denied states must be explicit.

### Operational Panels

- **Workflow operations:** recent workflow executions with Running, Completed,
  and Failed states
- **Department headcounts:** accessible current workforce distribution; a table
  or labelled list remains available if a visual display is used
- **Upcoming schedules:** enabled or disabled daily/weekly schedule records and
  evaluated next occurrence where available
- **Recent activity:** entries from the existing protected activity log
- **Agent executions:** recent Agent Template executions with database-backed
  states
- **System readiness:** one truthful readiness result based on the existing
  readiness check
- **Quick actions:** Add employee, Create workflow, Open AI Assistant, and View
  reports, filtered by permission

Do not imply separate database, API, file-storage, email, automation-engine, or
AI-service health checks when ABAP currently has one readiness check.

## 9. Employee Management

- Preserve search, filter, sorting, directory, profile, edit, and deletion
  capabilities.
- Use an operational table with clear column labels and restrained row actions.
- Reflow rows into readable labelled groups on narrow screens when a horizontal
  table no longer fits.
- Confirm destructive actions and explain their consequences.
- Keep payroll and salary information behind its existing separate permission
  boundaries.
- Department headcounts may be reused on the Dashboard because they are already
  derivable from the workforce report.
- Do not show employee-growth trends until durable employee creation timestamps
  exist.

## 10. Workflows and Schedules

- Preserve workflow lifecycle states: Draft, Active, and Inactive.
- Preserve ordered tasks and the current manual task type.
- Preserve execution states: Running, Completed, and Failed.
- Preserve schedule types and enabled state from stored records.
- Show execution results and safe failure messages without exposing private
  exception details.
- Do not imply autonomous background execution beyond verified scheduler/worker
  capability.

## 11. Agent Templates and AI Assistant

Agent Templates and the general AI Assistant are distinct existing features.
Do not add a second chatbot.

- Agent Template directories show lifecycle status, model name, and permitted
  actions.
- Agent execution history shows request, result or safe error, timestamps, and
  database-backed status according to authorization.
- The AI Assistant uses a focused working interface with persistent input
  labelling, clear submit state, loading feedback, recoverable errors, and
  readable output.
- Do not use promotional robot artwork or unsupported AI-impact claims inside
  the operational application.

## 12. Reports, Activity, Accounts, and Resources

- Reports retain truthful workforce summaries and permission-aware CSV export.
- Activity history remains protected and readable; parsing or structuring log
  entries for the Dashboard is a backend/data presentation addition.
- User-account screens preserve administrator/viewer roles, active state, and
  permission-aware actions.
- System health and readiness wording must match the actual endpoint response.
- API documentation remains a secondary developer resource.

## 13. Landing and Login

- Replace the narrower Employee Management System positioning with the ABAP
  platform identity.
- Use the approved ABAP logo and truthful copy such as **Business automation,
  under control.**
- Do not claim unsupported integrations, security certifications, ROI, or AI
  outcomes.
- Keep authentication errors specific enough to recover while avoiding account
  enumeration or private system detail.

## 14. Responsive Behavior

- Desktop uses the persistent grouped sidebar and balanced operational grid.
- Tablet reduces columns and keeps priority information first.
- Mobile uses the compact logo, labelled navigation disclosure, single-column
  content, and intentionally reflowed tables or labelled record groups.
- Do not merely shrink the desktop interface.
- Controls should approach a comfortable 44px target where practical.
- Browser zoom and text enlargement must not clip content or hide actions.

## 15. Accessibility Requirements

- Target WCAG 2.2 AA contrast and interaction principles.
- Support keyboard navigation and a high-contrast offset focus ring.
- Preserve semantic headings, labels, captions, skip navigation, and alerts.
- Keep visible labels and recognizable symbols.
- Accommodate protanopia, deuteranopia, tritanopia, grayscale perception, and
  visual sensitivities.
- Never rely on red versus green alone.
- Make errors explain what happened and how the user can recover.
- Ensure loading, empty, unavailable, success, warning, and failure states are
  understandable without motion.
- Respect reduced-motion preferences.

## 16. Product-Truth and Implementation Classification

### UI-Only Changes

- Brand application and navigation grouping
- Typography, spacing, surfaces, borders, controls, and focus styling
- Responsive reflow and component states
- Existing page presentation improvements

### Frontend/Template Changes

- New Dashboard layout and permission-aware component rendering
- Reusable status, empty-state, alert, and action components
- Theme preference control and dark/light token application
- Accessible table/list presentation for Dashboard information

### Small Backend/Data Additions

- Aggregate employee and department totals for the home route
- Aggregate workflow lifecycle and execution status counts
- Load recent workflow and Agent Template executions for the Dashboard
- Load and evaluate relevant workflow schedules
- Load recent protected activity entries
- Expose the existing readiness result to the server-rendered Dashboard
- Add focused tests for aggregation, authorization, failures, and empty states

### Substantial Future Functionality

- Global cross-module search
- Notification center
- Integrations directory
- Billing or plan management
- General settings module
- Employee-growth history without employee creation timestamps
- ROI, productivity, hours-saved, or AI-impact analytics
- Multi-service operational health without real service-specific checks

Success-rate reporting is not approved until its population, time window,
formula, exclusions, and empty-data behavior are explicitly defined.

## 17. Exceptions and Unresolved Work

- Reconstruct and approve production SVG logo masters before final asset
  integration.
- Validate exact color tokens in-browser against actual component surfaces.
- Define how a user selects and persists the optional light theme.
- Define Dashboard aggregation boundaries and query performance before coding.
- Confirm final mobile reflow with rendered browser prototypes.
- Preserve all current authorization and payroll boundaries during redesign.

## 18. Implementation Gate

This specification authorizes planning and estimation only. It does not itself
authorize changes to application templates, CSS, JavaScript, Python, database
schemas, or production assets.

Implementation begins only after the project owner explicitly approves this specification
and asks Codex to begin implementation.

the project owner gave that approval on September 12, 2026. Phase 2 design foundations
were completed on September 13, 2026: approved dark/light tokens, reusable
buttons, panels, alerts, empty states, tables, accessible shape-coded statuses,
local SVG icons, and production-oriented ABAP logo assets.

Phase 3 was completed on September 13, 2026: the approved ABAP identity,
purpose-grouped permission-aware navigation, authenticated-account footer,
device-local theme preference, and keyboard-safe responsive navigation drawer
were integrated into the shared application shell. Existing routes, backend
authorization, and business behavior were preserved. The next gated step is
Phase 4, implementation of the key ABAP screens beginning with the operational
Dashboard.

The Phase 3 review correction established dark as the first-use default while
preserving an explicit saved theme choice, replaced the legacy duplicated-A
login treatment with the approved wordmark, kept the account footer visible
while navigation scrolls independently, and moved the active navigation rail
inside its selected item.
