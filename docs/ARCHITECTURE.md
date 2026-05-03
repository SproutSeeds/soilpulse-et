# Architecture

Last updated: 2026-04-10

SoilPulse-ET is a concept architecture for adaptive sensing and onboard
processing. It is not flight software.

## System Components

| component | location | responsibility |
| --- | --- | --- |
| User Need Model | ground | field priorities, program goals, risk thresholds |
| Observation Planner | ground / onboard | planned task list, revisit goals, resource windows |
| Sensor Task Queue | onboard | candidate observations and timing constraints |
| Feature Extractor | onboard | ET-proxy, vegetation delta, cloud fraction, confidence |
| Tile State Ledger | onboard / ground | latest priority, evidence quality, freshness, and uncertainty state per tile |
| Triage Policy | onboard | score candidate tiles and choose packet action |
| Packet Queue | onboard | bounded priority chips and feature summaries |
| Downlink Manager | onboard | schedule packets under contact and power limits |
| Ground Calibrator | ground | compare downlinked packets with ECOSTRESS / user context |
| User Delivery Layer | ground | analyst dashboard, alert, or worklist integration |

## Operating Modes

| mode | behavior |
| --- | --- |
| Nominal | high-scoring tiles can downlink priority chips; medium tiles get summaries |
| Summary-only | reduced downlink forces compact summaries for all selected tiles |
| Cloud-conservative | cloud threshold tightens after cloudy acquisitions |
| Low-power | processing and packet limits shrink; only highest scores survive |
| Recalibration | ground updates thresholds from ECOSTRESS and user feedback |
| Knowledge-gap | stale, obscured, or low-confidence tiles are flagged for future clean observations |

## Architecture Flow

1. Ground user priorities and recent history define candidate goals.
2. Observation planner converts goals into onboard task constraints.
3. Feature extractor summarizes each tile after acquisition.
4. Tile state ledger updates priority, evidence quality, and knowledge state.
5. Triage policy scores each candidate.
6. Packet queue accepts priority chips or feature summaries until budgets are
   exhausted.
7. Downlink manager transmits selected packets.
8. Ground calibrator compares results with ECOSTRESS-derived context.
9. User delivery layer turns selected events into scouting or planning work.

## JPL Scheduling Vocabulary

The architecture borrows planning language from JPL scheduling work such as
ASPEN, without claiming to use ASPEN.

| scheduling idea | SoilPulse-ET equivalent |
| --- | --- |
| goals | user-prioritized field observations |
| resources | energy, processing, memory, storage, downlink, packets |
| temporal constraints | contact windows, revisit age, acquisition timing |
| state update | cloud, confidence, freshness, stress score, evidence quality, resource usage |
| repair / replanning | downgrade chip to summary or defer candidate |

## Tile Knowledge States

The demo uses simple, auditable labels that can be shown to a judge or land
manager:

| state | meaning |
| --- | --- |
| `clear_recent` | the latest useful evidence is recent, clear, and reliable enough for normal scoring |
| `stale` | the tile has not had a recent useful observation, so revisit age raises attention |
| `partial_cloud` | clouds limit the observation but do not fully screen it out |
| `obscured` | cloud cover is high enough that the tile should not consume downlink this contact |
| `low_confidence` | uncertainty is high enough to warn against overinterpretation |

## Diagram Source

The current architecture diagram source lives at:

- `docs/diagrams/soilpulse_architecture.mmd`
- `docs/diagrams/soilpulse_architecture.svg`

Render this to SVG or PNG for paper use after final wording is stable.
