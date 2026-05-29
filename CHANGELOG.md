# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](http://keepachangelog.com/en/1.0.0/)
and this project adheres to [Semantic Versioning](http://semver.org/spec/v2.0.0.html).

<!-- insertion marker -->
## [0.1.0-beta-1](https://github.com/Daniel-Brai/feedbase/releases/tag/0.1.0-beta-1) - 2026-05-29

<small>[Compare with 0.1.0-alpha.2](https://github.com/Daniel-Brai/feedbase/compare/0.1.0-alpha.2...0.1.0-beta-1)</small>

### Bug Fixes

- update redis client for notifications to avoid thread issues for sse transport (#5) ([22e3706](https://github.com/Daniel-Brai/feedbase/commit/22e37062d474f269f2ae01b7b751cee84b3445c2) by Daniel Brai).

### Code Refactoring

- update notifications `deliver_later` to be optionally proxied to job `deliver_later` via set (#6) ([dc2801f](https://github.com/Daniel-Brai/feedbase/commit/dc2801f7c8fec1597e8bcefa37fb1c9459f887d9) by Daniel Brai).
- add a helper method for notification testing ([6c9694f](https://github.com/Daniel-Brai/feedbase/commit/6c9694fc2c606f993fa94e922fbdd058c731a90b) by Daniel Brai).

## [0.1.0-alpha.2](https://github.com/Daniel-Brai/feedbase/releases/tag/0.1.0-alpha.2) - 2026-05-28

<small>[Compare with 0.1.0-alpha.1](https://github.com/Daniel-Brai/feedbase/compare/0.1.0-alpha.1...0.1.0-alpha.2)</small>

## [0.1.0-alpha.1](https://github.com/Daniel-Brai/feedbase/releases/tag/0.1.0-alpha.1) - 2026-05-28

<small>[Compare with first commit](https://github.com/Daniel-Brai/feedbase/compare/f26daa8220597b482f9aa0d348be03c06e9e96f8...0.1.0-alpha.1)</small>

