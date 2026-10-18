## Project Scope and Working Rules

- The book and its technical documentation are written in English.
  SystemVerilog is the primary RTL language; CORE-V Wally is the main SoC case.
- Preserve the distinction between the general reference book and its optional
  twelve-week teaching adoption. See [architecture](docs/architecture.md).
- Follow the [accessibility requirements](docs/accessibility.md), including the
  route without a physical FPGA and grayscale readability.
- Edit authoritative catalogues and generators, then regenerate their outputs.
  Keep source listings, executable lab code and provenance consistent.
- Scope every result to its actual source, configuration, tool and execution
  boundary. Never turn an unexecuted check into a PASS or silently relax a gate.
- Keep generated book renders, downloads and local build/work artifacts out of
  commits. Preserve deliberately versioned lab reference evidence and unrelated
  working-tree changes. Follow `.gitattributes` for exact lab/evidence bytes.
- Use the [development guide](docs/development.md) for source ownership,
  shell/container conventions and change-appropriate validation.

## Project Knowledge Maintenance

Maintain persistent project knowledge across sessions.

- Keep AGENTS.md concise and focused on permanent
  project rules, conventions, and constraints.
- Record significant architectural decisions in
  docs/architecture.md or docs/decisions.md.
- Maintain accessibility requirements in
  docs/accessibility.md.
- After substantial changes, review whether any
  permanent project knowledge needs updating.
- Update the relevant documentation when necessary.
- Do not document temporary experiments or
  unverified assumptions as established facts.
- Preserve existing decisions unless explicitly
  superseded.
- Report documentation changes at the end of
  each substantial task.
