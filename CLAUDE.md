# CLAUDE.md

## Repository Overview

This is a personal document repository that version-controls a professional resume/CV. It contains no application source code, build systems, or runtime dependencies.

- **Owner:** Patrick Low Beng Chee (bclow004)
- **Purpose:** Version-controlled resume/CV document
- **Primary file:** `README.md` — HTML-formatted resume rendered as a GitHub profile or portfolio page

## Repository Structure

```
/
├── CLAUDE.md       # AI assistant guide (this file)
└── README.md       # Professional resume/CV (HTML in Markdown)
```

There are no source code directories, configuration files, or dependency manifests.

## Branch Structure

- `master` — Main branch containing the latest resume content
- Feature/task branches may be created for specific updates

## Content Format

`README.md` uses **inline HTML within Markdown** for formatting:
- `<b>`, `<font>`, `<br />`, `<p>` tags for structure and emphasis
- Horizontal rules via `________________________________________` (underscores)
- Bulleted lists use `•` character with tab indentation rather than Markdown list syntax
- Mailto link in the header uses an `<a>` tag

## Development Workflow

There is no build, test, lint, or CI/CD pipeline. Changes consist of direct edits to `README.md`.

### Making Changes

1. Edit `README.md` directly
2. Preserve the existing HTML-in-Markdown formatting style
3. Commit with a clear message describing what was updated
4. Push to the appropriate branch

## Conventions for AI Assistants

- **No code to build or test.** Do not look for or suggest build/test commands.
- **Preserve HTML formatting.** The resume uses inline HTML deliberately for rendering control. Do not convert to pure Markdown.
- **Maintain section structure.** The resume follows this order: Contact Info, Experience Summary, Key Capabilities, Professional Experience (reverse chronological), Education, Awards, Skills and Professional Development.
- **Keep content professional.** This is a career document — maintain formal, concise language.
- **Respect the separator convention.** Sections are divided by lines of underscore characters (`________________________________________`).
- **Do not remove or alter factual career details** without explicit instruction from the owner.
