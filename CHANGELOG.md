# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [2.1.0-beta.1](https://github.com/damacus/robovac/compare/v2.0.1-beta.1...v2.1.0-beta.1) (2026-02-11)


### Features

* **vaccum:** add support for Eufy X10 PRO (alias T2351) ([#281](https://github.com/damacus/robovac/issues/281)) ([bc9ecaf](https://github.com/damacus/robovac/commit/bc9ecaf162b4a3db6b26f47b3d9c62ce254e2a07))


### Bug Fixes

* add boolean START_PAUSE support and status mappings for 10 vacuum models ([#338](https://github.com/damacus/robovac/issues/338)) ([8ffef5e](https://github.com/damacus/robovac/commit/8ffef5e65f80c98d0da6fd4b9ce4cf79d4593a14))
* resolve issue [#300](https://github.com/damacus/robovac/issues/300) - X8 'Pure' fan speed not setting ([#315](https://github.com/damacus/robovac/issues/315)) ([b931726](https://github.com/damacus/robovac/commit/b93172628b40931c5dd2e7797a878707df5bce0c))

## [2.0.1-beta.1](https://github.com/damacus/robovac/compare/v2.0.0-beta.1...v2.0.1-beta.1) (2026-01-06)


### Documentation

* Update supported list of robovacs ([#292](https://github.com/damacus/robovac/issues/292)) ([f1a1652](https://github.com/damacus/robovac/commit/f1a1652cefa25c6dd548f4c8f8aec35a99a4ae30))

## [2.0.0-beta.1](https://github.com/damacus/robovac/compare/v1.5.0...v2.0.0-beta.1) (2026-01-06)


### Features

* Add docs site ([#287](https://github.com/damacus/robovac/issues/287)) ([6f4560b](https://github.com/damacus/robovac/commit/6f4560b5818b7c31ccc7e9507187b3aebfb3322f))
* Add Protocol 3.4 HMAC-SHA256 support and improve decryption error handling ([#286](https://github.com/damacus/robovac/issues/286)) ([8d0eb8d](https://github.com/damacus/robovac/commit/8d0eb8d7e684db7a877a428352d36970a5569ba2))
* add protocol version selection for Tuya devices ([#278](https://github.com/damacus/robovac/issues/278)) ([7b99613](https://github.com/damacus/robovac/commit/7b99613643837dd06056a4178992538174a0621f))
* Simplify README and point to docs site ([#291](https://github.com/damacus/robovac/issues/291)) ([5e82fe8](https://github.com/damacus/robovac/commit/5e82fe8fe06e05f27c53e0ba181e18a07a301e77))


### Bug Fixes

* correct markdown table formatting in archive docs ([c79507a](https://github.com/damacus/robovac/commit/c79507a170f73f7320f824005ab7a7cb2c5201ea))


### Documentation

* Document T2276 communication issues and investigation ([#238](https://github.com/damacus/robovac/issues/238)) ([933ed71](https://github.com/damacus/robovac/commit/933ed710eb6e0d1583acd873dfd4cb4a48c450a4)), closes [#42](https://github.com/damacus/robovac/issues/42)

## [1.5.0](https://github.com/damacus/robovac/compare/v1.4.0...v1.5.0) (2025-10-22)


### Features

* **T2080:** add MOP_LEVEL command support for Eufy Clean S1 ([#236](https://github.com/damacus/robovac/issues/236)) ([a11198c](https://github.com/damacus/robovac/commit/a11198cfeb2424ee2bccb554360fea2689910629))


### Bug Fixes

* **2280:** Add stub for 2280 vacuum cleaner ([#234](https://github.com/damacus/robovac/issues/234)) ([a173e16](https://github.com/damacus/robovac/commit/a173e1671e995ecbcf6c276f315c797c6aa02e66))

## [1.4.0](https://github.com/damacus/robovac/compare/v1.3.4...v1.4.0) (2025-10-22)


### Features

* add case-insensitive value lookup utility ([ff93578](https://github.com/damacus/robovac/commit/ff935781b87d55b47673b6679b49596d2f33b379))
* add command mapping tests for seven vacuum models ([ff93578](https://github.com/damacus/robovac/commit/ff935781b87d55b47673b6679b49596d2f33b379))
* **battery:** Fix battery deprecation notice ([#231](https://github.com/damacus/robovac/issues/231)) ([4efd321](https://github.com/damacus/robovac/commit/4efd321a9179a886f1dd31b1cd07ebc248e5164e))
* standardise vacuum model command mappings ([ff93578](https://github.com/damacus/robovac/commit/ff935781b87d55b47673b6679b49596d2f33b379))


### Bug Fixes

* **codes:** Stop duplicating codes in config ([#222](https://github.com/damacus/robovac/issues/222)) ([ff93578](https://github.com/damacus/robovac/commit/ff935781b87d55b47673b6679b49596d2f33b379))
* improve logging strategy for value lookups ([ff93578](https://github.com/damacus/robovac/commit/ff935781b87d55b47673b6679b49596d2f33b379))
* **python:** Drop down to python 3.13.1 to match home assistant ([#232](https://github.com/damacus/robovac/issues/232)) ([1321d46](https://github.com/damacus/robovac/commit/1321d46e7b0a760a0720fdff822825061feff395))


### Documentation

* add development guide and update README ([ff93578](https://github.com/damacus/robovac/commit/ff935781b87d55b47673b6679b49596d2f33b379))

## [1.3.4](https://github.com/damacus/robovac/compare/v1.3.3...v1.3.4) (2025-10-13)


### Documentation

* add GitHub labels system documentation ([68e1cbe](https://github.com/damacus/robovac/commit/68e1cbe33b73e9f50788a07a2c2aa9e05400f05a))

## [1.3.3](https://github.com/damacus/robovac/compare/v1.3.2...v1.3.3) (2025-10-13)


### Bug Fixes

* L60 commands ([#197](https://github.com/damacus/robovac/issues/197)) ([2fd0e9a](https://github.com/damacus/robovac/commit/2fd0e9a935100de0cba03ca6f62b0d412318e3a0))
* **logs:** Limit logging ([#215](https://github.com/damacus/robovac/issues/215)) ([9936867](https://github.com/damacus/robovac/commit/9936867910097d06d5d5bc718e6835cc3c54672c))
* **T2080:** Mapping more statuses for T2080 ([#208](https://github.com/damacus/robovac/issues/208)) ([67aaeb3](https://github.com/damacus/robovac/commit/67aaeb39068479bf32d0f3b2a3bece9ac1c8316a))
* **test:** add missing BATTERY feature to T2118 test expectations ([#220](https://github.com/damacus/robovac/issues/220)) ([f3fa3ff](https://github.com/damacus/robovac/commit/f3fa3ff4e6141839dd4be6e1f7ba94648ac70ba2))

## [1.3.2](https://github.com/damacus/robovac/compare/v1.3.1...v1.3.2) (2025-08-26)


### Bug Fixes

* correct autoReturn toggle logic and mode mappings ([#180](https://github.com/damacus/robovac/issues/180)) ([6dfd10d](https://github.com/damacus/robovac/commit/6dfd10d65951a3f4285d899718cbe667001c7f25))
* Update how codes are looked up ([#149](https://github.com/damacus/robovac/issues/149)) ([e06aed0](https://github.com/damacus/robovac/commit/e06aed02a02df3dd2075aaee393cf18593250d20))

## [1.3.1](https://github.com/damacus/robovac/compare/v1.3.0...v1.3.1) (2025-07-05)


### Bug Fixes

* (refactor) replace TUYA_CODES references with TuyaCodes class ([#141](https://github.com/damacus/robovac/issues/141)) ([5eabac6](https://github.com/damacus/robovac/commit/5eabac65ddf1a0d35ce5eb018c12e861e077b1b8))
* use model-specific code for start commands ([#139](https://github.com/damacus/robovac/issues/139)) ([f83f29e](https://github.com/damacus/robovac/commit/f83f29eb194158a478b421abbeb217420037c1cb))

## [1.3.0](https://github.com/damacus/robovac/compare/v1.2.5...v1.3.0) (2025-07-02)


### Features

* update node.js to v22.17.0 ([#132](https://github.com/damacus/robovac/issues/132)) ([e1b81fa](https://github.com/damacus/robovac/commit/e1b81fa84939310e693f5ea094b651330c8f51d9))

## [1.2.5](https://github.com/damacus/robovac/compare/v1.2.4...v1.2.5) (2025-06-24)


### Bug Fixes

* Refactor DPS codes ([#106](https://github.com/damacus/robovac/issues/106)) ([f96fef0](https://github.com/damacus/robovac/commit/f96fef0d09f78b41936c7581dce229182db6feb8))

## [1.2.4](https://github.com/damacus/robovac/compare/v1.2.3...v1.2.4) (2025-05-21)


### Bug Fixes

* fan speed list for T2181 ([#87](https://github.com/damacus/robovac/issues/87)) ([0f64f72](https://github.com/damacus/robovac/commit/0f64f7234f03a81593e928e55f15c49a56d7b206))

## [1.2.3](https://github.com/damacus/robovac/compare/v1.2.2...v1.2.3) (2025-05-13)


### Bug Fixes

* Add friendly heredocs to files so that we can all find models easier ([#86](https://github.com/damacus/robovac/issues/86)) ([604c403](https://github.com/damacus/robovac/commit/604c40394f2fab5920398ddca51caa61aa6c8537))
* Add T2267 and T2268 (L60 and L60 Hybrid) ([#81](https://github.com/damacus/robovac/issues/81)) ([aad9330](https://github.com/damacus/robovac/commit/aad93304934fba988117a8bab0f6d87b19aecc9d))

## [1.2.2](https://github.com/damacus/robovac/compare/v1.2.1...v1.2.2) (2025-05-07)


### Bug Fixes

* Fix init arguments in robovac ([#77](https://github.com/damacus/robovac/issues/77)) ([7d3c5df](https://github.com/damacus/robovac/commit/7d3c5df81cb543308483516c91cf0d1cb23ddc80))

## [1.2.1](https://github.com/damacus/robovac/compare/v1.2.0...v1.2.1) (2025-05-07)


### Bug Fixes

* Also bump the version in manifest.json ([#71](https://github.com/damacus/robovac/issues/71)) ([64b1f6b](https://github.com/damacus/robovac/commit/64b1f6ba8b0d6f1f31171d37eb9402fc2cd2b1d0))
* Fix return types from RoboVac ([#72](https://github.com/damacus/robovac/issues/72)) ([f9fb413](https://github.com/damacus/robovac/commit/f9fb413a474048ff4d1528c74586ab8e5ff65063))

## [1.2.0](https://github.com/damacus/robovac/compare/v1.1.0...v1.2.0) (2025-05-07)


### Features

* Migrate to v2 API ([#68](https://github.com/damacus/robovac/issues/68)) ([1b909cc](https://github.com/damacus/robovac/commit/1b909cc910a59290e1fba8814c194626c82cc377))

## [1.1.0](https://github.com/damacus/robovac/compare/v1.0.2...v1.1.0) (2025-05-07)


### Features

* Update workflows ([#56](https://github.com/damacus/robovac/issues/56)) ([04a855e](https://github.com/damacus/robovac/commit/04a855eb65c6858ec451e3e4e7c753f227c5adb0))


### Bug Fixes

* Add custom vaccums ([#53](https://github.com/damacus/robovac/issues/53)) ([4753e4d](https://github.com/damacus/robovac/commit/4753e4d6101bc67f9787afd285a0b14c3ab88ab4))
* Allow 2 blank lines in markdown ([#62](https://github.com/damacus/robovac/issues/62)) ([3ec9117](https://github.com/damacus/robovac/commit/3ec9117d2dcf155dcbd7dc0f20936b76bee1de0e))
* Codecov ([#65](https://github.com/damacus/robovac/issues/65)) ([10ccbda](https://github.com/damacus/robovac/commit/10ccbdaa85a7839edd21d00595c9bd249736aa35))

## [Unreleased]
