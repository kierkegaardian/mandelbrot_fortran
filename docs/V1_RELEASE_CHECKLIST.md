# MandelQuest v1.0 Release Checklist

Target release window: May 25-31, 2026
Target platforms: Windows 10+, macOS 11+, Ubuntu LTS

## Security and Privacy
- [ ] Parent PIN is configured and enforced for Parent tab access.
- [ ] Parent lockout and clear-lock workflow validated.
- [ ] Core learning flows run without required outbound network access.
- [ ] Local data paths and backup steps are documented.
- [ ] Family Sync is labeled beta, defaults off, and cannot be enabled without an operator-supplied server config.
- [ ] Family Sync privacy copy matches the client payload and local-only exclusions.

## Accessibility and UX Baseline
- [ ] Keyboard-only flow validated for Profile, Quiz, Parent, and Dashboard.
- [ ] Readability/accessibility presets apply globally as expected.
- [ ] Contrast and font-size defaults are readable on small and large displays.

## Reliability and Data Integrity
- [ ] Full automated test suite passes with zero failures.
- [ ] No DB `ResourceWarning` or unclosed-handle warnings in test logs.
- [ ] DB migrations are idempotent on fresh and existing databases.
- [ ] Quiz resume persistence survives app restart.

## Offline and Dependency Fallbacks
- [ ] Offline mode blocks external lesson launches.
- [ ] Missing `pdftotext` is handled with user-facing guidance (no traceback).
- [ ] Missing ImageMagick is handled with user-facing guidance for `make png`.

## Packaging and Compatibility
- [ ] Package artifacts built for Linux, macOS, and Windows CI matrix.
- [ ] Smoke-tested on clean baseline environments for each target OS.
- [ ] Install/run troubleshooting validated against current artifacts.

## Documentation and Launch
- [ ] `README.md` reflects final offline, backup/recovery, and parent-control instructions.
- [ ] Repository Settings -> Pages uses GitHub Actions as its publishing source.
- [ ] `Publish Docs Site` passes its public-doc validation and deploys from `master`.
- [ ] Public launch surface is live (`docs/index.html`, `docs/privacy.html`, `docs/support.html`, `docs/coverage.html`).
- [ ] Sample worksheet and first-15-minutes guide are published for family evaluation.
- [ ] Beta feedback and bug-report intake path is documented and reachable.
- [ ] Known limitations section is current.
- [ ] Release notes drafted for tag `v1.0.0`.
- [ ] Rollback plan documented for first-week issues.

## Known Limitations (v1.0)
- No hosted cloud/LAN sync service ships with v1. The operator-configured Family Sync beta is disabled by default and is not part of the normal v1 support promise.
- Advanced Geometry proofs, Algebra 2 depth, and post-Algebra-1 tracks are incomplete for homeschool-complete coverage.
- Historical PDF ingestion features require optional system binaries and are non-core.
- Packaging smoke validation across all baseline OS versions still requires final manual pass before release tag.
