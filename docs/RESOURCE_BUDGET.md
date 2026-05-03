# Resource Budget

Last updated: 2026-04-22

This file records the working SmallSat-style resource assumptions for the Phase
1 software demo. These are concept-planning values, not flight-qualified claims.

## CubeSat Planning Anchor

The demo budget is now anchored to a conservative `6U` rail-based CubeSat
baseline from CubeSat Design Specification Rev. `14.1`, rather than an abstract
"small satellite" placeholder.

| hardware planning item | current planning anchor |
| --- | --- |
| form factor | `6U` rail-based CubeSat |
| body envelope | `100.0 x 226.3 x 366.0 mm` |
| typical maximum mass | `12.00 kg` |
| center of gravity range | `X +/- 4.5 cm`, `Y +/- 2 cm`, `Z +/- 7 cm` from geometric center |
| constrained-face protrusion | `6.5 mm max` from the plane of the rail |
| rail clearance | `8.5 mm min` from rail edge to first protrusion |
| structure / rails | aluminum-alloy structure preferred; external rail-contact surfaces hard anodized |
| prelaunch power state | powered off from delivery through dispenser deployment |
| required safety devices | deployment switch plus RBF pin |
| inhibit stance | `3` independent RF inhibits; `3` deployable inhibits if deployables are used |

This baseline intentionally avoids optional extra volume, propulsion, and any
required deployable mechanisms in the current Phase 1 story.

## Demo Cycle Budget

| resource | value | purpose |
| --- | ---: | --- |
| downlink | `384 KiB` | one short planning contact allocation for selected packets |
| packets | `6` | maximum selected chips or summaries in one demo cycle |
| processing | `1500 ms` | bounded onboard triage compute window |
| energy | `42 J` | bounded triage-cycle energy allocation |
| memory | `128 MiB` | planning envelope for feature buffers and packet queue |
| storage | `512 MiB` | planning envelope for temporary candidate chips and summaries |

## Packet Assumptions

| packet type | default size | intended content |
| --- | ---: | --- |
| priority chip | `96 KiB` | cropped image / feature chip for high-scoring event follow-up |
| larger priority chip | `112 KiB` | higher-entropy or slightly larger chip in demo fixture |
| feature summary | `8 KiB` | compact statistics, geolocation, uncertainty, freshness, knowledge state, and context metadata |
| deferred tile | `0 KiB` | no downlink in this contact |

## Current Demo Use

The synthetic triage run selects:

- two priority chips
- two feature summaries
- three deferred candidates

Used budget:

| resource | used | budget |
| --- | ---: | ---: |
| downlink | `224 KiB` | `384 KiB` |
| packets | `4` | `6` |
| processing | `720 ms` | `1500 ms` |
| energy | `16 J` | `42 J` |

Metrics versus a full-chip-all-candidates baseline:

| metric | value |
| --- | ---: |
| candidate count | `7` |
| selected packets | `4` |
| full-chip baseline | `688 KiB` |
| used downlink | `224 KiB` |
| downlink saved | `464 KiB` / `67.44%` |
| high-stress retention | `2/2` / `100%` |
| cloudy candidates deferred | `1/1` |
| cloud waste avoided | `96 KiB` |

## Budget Sensitivity

| downlink KiB | packets | used KiB | selected | saved % | high-stress retained |
| ---: | ---: | ---: | ---: | ---: | ---: |
| `64` | `3` | `24.0` | `3` | `96.51` | `100.00%` |
| `128` | `4` | `120.0` | `4` | `82.56` | `100.00%` |
| `384` | `6` | `224.0` | `4` | `67.44` | `100.00%` |

The smaller budgets force the policy toward compact summaries. This is useful
for showing graceful degradation, but the paper should explain that summary-only
behavior may reduce analyst confidence compared with downlinking full chips.

## Hybrid Demo Use

`make hybrid-demo` builds `tests/fixtures/candidate_tiles.hybrid.csv` and runs
the same triage policy. It keeps one real ECOSTRESS-derived knowledge-gap row
and synthetic mission-scenario rows for resource-constrained behavior.

Hybrid result:

| metric | value |
| --- | ---: |
| candidate count | `8` |
| selected packets | `4` |
| full-chip baseline | `784 KiB` |
| used downlink | `224 KiB` |
| downlink saved | `560 KiB` / `71.43%` |
| high-stress retention | `2/2` / `100%` |
| cloudy candidates deferred | `1/1` |
| cloud waste avoided | `96 KiB` |

This is the best current paper/video demo because it combines real NASA data
lineage with a complete chip / summary / defer mission behavior example.

## Representative Compute Stack

This is a concept stack, not selected flight hardware:

| layer | representative role |
| --- | --- |
| radiation-tolerant CPU | task control, packet queue, policy execution |
| small FPGA / NPU option | accelerated cloud screening or feature extraction |
| onboard memory | feature buffers, intermediate tile statistics |
| onboard storage | temporary chips, summaries, and retry queue |
| downlink manager | packet prioritization during contact windows |

## Baseline And Forward Path

### Current baseline

Use only the claims we can defend now:

- the software demo fits a disciplined `6U` CubeSat planning envelope
- no propulsion is assumed
- no deployables are required to explain the current Phase 1 concept
- no dispenser-specific access ports, extended body length, or extra volume are
  required
- the compute stack remains representative until a specific board-level design
  is selected

### Forward engineering path

Reserve these items for the forward roadmap:

- final board and bus component selection
- optional FPGA / NPU acceleration
- dispenser-specific access-port or extra-volume usage
- deployable power or antenna packaging if justified by the link budget
- launch-provider fit checks, vibration, thermal-vacuum, and protoflight or
  qualification testing
- licensing, debris, and remote-sensing compliance work

Some of these items may still be unclear at Phase 1. That is acceptable as long
as they are named honestly as future engineering work rather than implied as
resolved current capability.

## Operational Safety Constraints To Respect

Even though the current artifact is software-first, the concept plan should
respect these CDS Rev. `14.1` operational constraints:

- powered functions remain off from delivery through on-orbit deployment
- deployables must wait at least `30 minutes` after deployment-switch
  activation before release
- the spacecraft must not generate or transmit RF earlier than `45 minutes`
  after on-orbit deployment
- deployables must be constrained by the CubeSat, not by the dispenser

## Submission Framing

The resource table should be used to show method discipline:

- every onboard claim gets a compute, energy, storage, or bandwidth hook
- selected packets are explicitly smaller than sending every candidate as a
  full chip
- the code demonstrates policy behavior, while final SmallSat sizing remains a
  Phase 2 engineering task

## Next Evidence To Add

- estimate candidate raw scene sizes after choosing sensor assumptions
- separate always-on housekeeping energy from event-trigger compute energy
