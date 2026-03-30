# TODO - GradePlotter Rewrite Decisions

## Confirmed decisions
- Stack: Python + Flask
- User mode: Mostly read-only consumption
- Access model: Admin (me) + Viewer roles
- V1 consumption priority: Download/shared-folder style access

## Open product decisions
- Should v1 include a web gallery immediately, or start with filesystem browsing + manifest files only?
- Should we keep exact legacy output paths/filenames for backward compatibility in v1?
- Which existing report outputs are mandatory in v1 vs can be deferred to v1.1?
- Should non-PNG outputs (text reports) also be indexed in the same gallery/API?

## Security and permissions decisions
- Preferred auth method for local deployment: password login, OS user mapping, or reverse-proxy auth?
- Should Viewer users be allowed to see instructor-level breakdowns for all courses?
- Should any student-level identifiers be excluded/redacted from generated outputs and metadata?
- Retention policy: keep all run artifacts forever, or prune old runs?

## Data and operations decisions
- What is the canonical source directory for new CSV files?
- Should generation be manual (button/command), scheduled nightly, or both?
- Do we need one-click rerun of last successful configuration?
- Which run parameters should be locked down so Viewer cannot influence them?

## Migration and rollout decisions
- Cutover plan: big-bang replacement or side-by-side legacy + new for one term?
- Who will validate parity of each graph/report type before cutover?
- Acceptance criteria for parity: exact match or tolerances for chart rendering differences?
- Target date for v1 parity complete.

## Implementation checkpoints
- [x] Create initial rewrite plan and decision log
- [x] Build v2 data model and CSV loader
- [x] Build v2 analysis engine for histogram and multiyear plots
- [x] Build v2 plot generation CLI
- [x] Build Flask read-only gallery with Admin/Viewer login
- [x] Add manifest indexing and run history
- [x] Add legacy-style graph output parity for histograms and multiyear trends
- [ ] Validate output parity against legacy on fixture data
