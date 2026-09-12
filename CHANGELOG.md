# Changelog

## [1.0.0](https://github.com/matchdav/eigenhelm/compare/v0.10.2...v1.0.0) (2026-09-12)


### ⚠ BREAKING CHANGES

* prepare v1.0.0 open-source release

### Features

* centralize limits, cache dir, and registry defaults ([#101](https://github.com/matchdav/eigenhelm/issues/101)) ([2df0eac](https://github.com/matchdav/eigenhelm/commit/2df0eac7c8bdac8913eed199b6cb29f562fe89cd))
* centralize threshold constants and npz keys ([#99](https://github.com/matchdav/eigenhelm/issues/99)) ([6aca529](https://github.com/matchdav/eigenhelm/commit/6aca52963cef47276b167c0eee3ef281c775f5a5))
* prepare v1.0.0 open-source release ([6348aa4](https://github.com/matchdav/eigenhelm/commit/6348aa4713757584ad5021f4e06873d80c171e7c))


### Bug Fixes

* **calibration:** restore meaningful Python self-evaluation ([#82](https://github.com/matchdav/eigenhelm/issues/82)) ([6a3a23d](https://github.com/matchdav/eigenhelm/commit/6a3a23d976c3ca97d053d7b7c73108e517a3342c))
* **docs:** update agent instructions to use `gh` command for issue management ([1511a26](https://github.com/matchdav/eigenhelm/commit/1511a263d2db9c54120cf62123c5eb1db3ccc0be))
* **evaluate:** CLI threshold flags override config file ([#96](https://github.com/matchdav/eigenhelm/issues/96)) ([924d985](https://github.com/matchdav/eigenhelm/commit/924d9857f427de751a24ff52551f614176c8deea))
* **precommit:** prevent TypeError when thresholds block is omitted ([#95](https://github.com/matchdav/eigenhelm/issues/95)) ([dee7dab](https://github.com/matchdav/eigenhelm/commit/dee7dabe7c23f60825135f5699ab60d114e4eba5))
* **scorecard:** treat missing NCD exemplar identically to unconfigured ([#97](https://github.com/matchdav/eigenhelm/issues/97)) ([bc0f605](https://github.com/matchdav/eigenhelm/commit/bc0f60575b083c84b42a2a5ea0c236f806140c34))
* **scoring:** recover Q4 NCD value when active but outside top-N violations ([#72](https://github.com/matchdav/eigenhelm/issues/72)) ([b4e8795](https://github.com/matchdav/eigenhelm/commit/b4e8795f54815fbc6286868cb8f6c75d1979887c))


### Documentation

* document self-eval calibration findings ([#79](https://github.com/matchdav/eigenhelm/issues/79)) ([3bb19b7](https://github.com/matchdav/eigenhelm/commit/3bb19b723ef6fab027c07267a4047f5b915fe7de))
* fix stale project structure, test counts, Class C status ([#84](https://github.com/matchdav/eigenhelm/issues/84)) ([f491a71](https://github.com/matchdav/eigenhelm/commit/f491a716ac81b2f76aa242538583b9bb939e71d0))
* reconcile CLAUDE.md, README, and specs with shipped implementation ([#86](https://github.com/matchdav/eigenhelm/issues/86)) ([822d1ab](https://github.com/matchdav/eigenhelm/commit/822d1ab723adfc9702b58c791917398dbde3e5ec))

## [0.10.2](https://github.com/matchdav/eigenhelm/compare/v0.10.1...v0.10.2) (2026-08-20)


### Bug Fixes

* **action:** accept (don't crash) when no evaluable files are in the range ([#71](https://github.com/matchdav/eigenhelm/issues/71)) ([f8b4b32](https://github.com/matchdav/eigenhelm/commit/f8b4b32af396bc98dfd230fff5d90686d4c9873e))
* **action:** treat warn/reject as quality decisions, not crashes ([#66](https://github.com/matchdav/eigenhelm/issues/66)) ([#69](https://github.com/matchdav/eigenhelm/issues/69)) ([ebfd9c6](https://github.com/matchdav/eigenhelm/commit/ebfd9c64f175ed9ed96d2d9a0d264ea5bd43544d))

## [0.10.1](https://github.com/matchdav/eigenhelm/compare/v0.10.0...v0.10.1) (2026-08-20)


### Bug Fixes

* bind exemplar bytes and identity to close concurrency hazard ([#62](https://github.com/matchdav/eigenhelm/issues/62)) ([#64](https://github.com/matchdav/eigenhelm/issues/64)) ([4e61af5](https://github.com/matchdav/eigenhelm/commit/4e61af547b83b03ca38102df4c5c87d5cb040801))
* remove .squad references ([8910ec7](https://github.com/matchdav/eigenhelm/commit/8910ec7380c5be9fd98fbe013bdcde36648460bd))
* stop the squad ([2867e82](https://github.com/matchdav/eigenhelm/commit/2867e82c27748236dabea4e01d6a3abf1ec02051))
* stop the squad, part 2 ([18439f2](https://github.com/matchdav/eigenhelm/commit/18439f2e6346cd02d0b93e57e67a80e5afbaa2b4))
* update action.yml for improved version handling and error reporting ([7c5c4c6](https://github.com/matchdav/eigenhelm/commit/7c5c4c6d8fced0f3fa293287231be8be9fcfa3cf))

## [0.10.0](https://github.com/matchdav/eigenhelm/compare/v0.9.0...v0.10.0) (2026-04-28)


### Features

* GitHub Action — composite action, auto-diff, SARIF, fail-on policy ([#59](https://github.com/matchdav/eigenhelm/issues/59)) ([75c1ece](https://github.com/matchdav/eigenhelm/commit/75c1ece892f71c81269af1d093a31647e8ca23a4))
* publish Docker image to GHCR on release ([#53](https://github.com/matchdav/eigenhelm/issues/53)) ([2eea564](https://github.com/matchdav/eigenhelm/commit/2eea564e0c93de49f1698e6490fc0362a3a8363f))
* test coverage initiative — 82% to 95% (1219 → 1750 tests) ([9eedaa4](https://github.com/matchdav/eigenhelm/commit/9eedaa4b4af3136fa471f6715c57b72056b55a0d))


### Bug Fixes

* lint cleanup and test file rename after coverage merge ([94b00c8](https://github.com/matchdav/eigenhelm/commit/94b00c8d8433c659dc7c12ced442dbf09a796c40))


### Documentation

* add model registry references throughout ([399ba00](https://github.com/matchdav/eigenhelm/commit/399ba0068e5e85eb5a9f1fb92242639eff4d6847))
* fix context rot in action version and architecture map ([#63](https://github.com/matchdav/eigenhelm/issues/63)) ([c615ef8](https://github.com/matchdav/eigenhelm/commit/c615ef8171288c58ba8ed62c618633273fc175f3))
* update models/README.md schema and add GitHub Action section to public README ([387efac](https://github.com/matchdav/eigenhelm/commit/387efacb9e4334b2616e8b0280ffa4fc8e5687cb))

## [0.9.0](https://github.com/matchdav/eigenhelm/compare/v0.8.0...v0.9.0) (2026-04-02)


### Features

* add support for excluding files and directories from evaluation using glob patterns ([b037a4c](https://github.com/matchdav/eigenhelm/commit/b037a4cd9f6e2388e9cc952db02f0c1807fde200))


### Documentation

* improve clarity in README and integration guides, update scoring terminology and instructions ([5b5a1f6](https://github.com/matchdav/eigenhelm/commit/5b5a1f6e2101d5418c65d158579f97e8a18a6989))
* update README and documentation for clarity and accuracy, emphasizing high-quality code metrics ([75f21c5](https://github.com/matchdav/eigenhelm/commit/75f21c5ce987db338b50a9893fe6e1bad2156767))

## [0.8.0](https://github.com/matchdav/eigenhelm/compare/v0.7.0...v0.8.0) (2026-03-31)


### Features

* add case study for FastAPI full-stack template and update navigation ([951a956](https://github.com/matchdav/eigenhelm/commit/951a956ed669f18e9fcbece03eaa7e2dc19ae7d6))
* enhance training workflow to support polyglot corpus and update manifest detection ([3fa6b4d](https://github.com/matchdav/eigenhelm/commit/3fa6b4d424bf190f1cb06e9b7acb298fe4eb1303))
* implement training and publishing workflow for models ([76b769d](https://github.com/matchdav/eigenhelm/commit/76b769d75a130c6c621a21dac18b92f001b8420f))


### Documentation

* add recommendations for strengthening eigenhelm's case studies and narrative ([ff6f20c](https://github.com/matchdav/eigenhelm/commit/ff6f20c94653f4187323470acd2795ad332a76ea))
* elevator pitch ([b7b3744](https://github.com/matchdav/eigenhelm/commit/b7b37448f51ec067646c017055c6b334076c5407))
* fix stale stuff ([ce70fe2](https://github.com/matchdav/eigenhelm/commit/ce70fe2a634c2fea7afdffc83b79edbc83dafb87))
* tighten the case study with reproducibility anchors ([0dd1679](https://github.com/matchdav/eigenhelm/commit/0dd16796104988c073da4a36876c2a7b47314d36))
* update FastAPI case study with additional model training details and clarify evaluation results ([f5d1151](https://github.com/matchdav/eigenhelm/commit/f5d11515fe4cd8cf9f0235576eeae987bbd4ca32))
* update README and case studies with new findings and improved clarity ([92fc1c6](https://github.com/matchdav/eigenhelm/commit/92fc1c6d07c6206d7e08676d9b0224ea9ab9dd7f))
* update README and why-eigenhelm to clarify eigenhelm's structural quality focus and benefits ([3f29578](https://github.com/matchdav/eigenhelm/commit/3f29578b405294b980eb4ae8ed5ba4ff8bd0e9cf))

## [0.7.0](https://github.com/matchdav/eigenhelm/compare/v0.6.0...v0.7.0) (2026-03-24)


### Features

* add Makefile with clean target for environment cleanup ([c002080](https://github.com/matchdav/eigenhelm/commit/c002080f7707413dd5987a3f0273ad0714be1d2f))
* implement model management CLI and registry integration ([807a2fd](https://github.com/matchdav/eigenhelm/commit/807a2fd22f51a556fc1b9fdcae28822d20b650c4))
* MCP layer ([ee5b274](https://github.com/matchdav/eigenhelm/commit/ee5b274e86ef5c10338c28a095108c15444c5de7))


### Bug Fixes

* update pre-commit documentation to clarify file evaluation criteria ([93e2e77](https://github.com/matchdav/eigenhelm/commit/93e2e77794d9f11182ea296504256091606dea2b))

## [0.6.0](https://github.com/matchdav/eigenhelm/compare/v0.5.0...v0.6.0) (2026-03-20)


### Features

* enhance pre-commit hook with project config loading and evaluation logic ([f225e2c](https://github.com/matchdav/eigenhelm/commit/f225e2c3b6cc9ebe0a85e9aed3202f8458d282ac))


### Bug Fixes

* pipe output with mkdirp for non-existent targets ([eda740b](https://github.com/matchdav/eigenhelm/commit/eda740bfb0449172916d2423aaa23e2b47794227))


### Documentation

* consistency sweep ([94a7bd3](https://github.com/matchdav/eigenhelm/commit/94a7bd30e7a4deea12906784b4bef5b4e5b74f54))

## [0.5.0](https://github.com/matchdav/eigenhelm/compare/v0.4.0...v0.5.0) (2026-03-20)


### Features

* add barrel file detection and corresponding unit tests ([02cf8fe](https://github.com/matchdav/eigenhelm/commit/02cf8fe03a02fc44fe5ed74154331b1b5c3e6447))
* add skill CLI command and corresponding skill documentation ([4e60d53](https://github.com/matchdav/eigenhelm/commit/4e60d53d2dfce08b8b3c17df2ce3218e7fc0b6d6))
* implement is_pure_types detection and add corresponding unit tests ([b6736e7](https://github.com/matchdav/eigenhelm/commit/b6736e7b743afbebd4ee682d06a692fd2b3f4127))


### Bug Fixes

* get rid of multi-package config ([bbd888b](https://github.com/matchdav/eigenhelm/commit/bbd888b00221f6d36b6546d0d2a647f043af00db))


### Documentation

* sweep 1 ([31008cc](https://github.com/matchdav/eigenhelm/commit/31008ccd47e2671d2ad6ae34c7a0e7c5bf1f4d31))
* sweep 2, make them pop ([0f1b558](https://github.com/matchdav/eigenhelm/commit/0f1b558e9a8ad9ff2db732858036826ebc59179e))
