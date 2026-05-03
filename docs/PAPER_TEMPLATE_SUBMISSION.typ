#set page(
  paper: "us-letter",
  margin: 1in,
  footer: context align(right)[#counter(page).display()],
)
#set text(font: "Arial", size: 11pt)
#set par(justify: false, leading: 0.57em, spacing: 0.42em)
#set heading(numbering: none)
#let navy = rgb("#1f4e79")
#let gold = rgb("#c58a00")
#let soft = rgb("#eef4fa")
#let line_gray = rgb("#9aa8b5")

#show heading.where(level: 1): it => {
  set text(size: 13.5pt, weight: "bold", fill: navy)
  block(above: 0.18in, below: 0.08in)[
    #it
    #v(2pt)
    #line(length: 100%, stroke: (paint: gold, thickness: 0.8pt))
  ]
}
#show heading.where(level: 2): it => {
  set text(size: 11pt, weight: "bold", fill: navy)
  block(above: 0.08in, below: 0.02in)[#it]
}

#let field(label, value) = [
  #text(weight: "bold")[#label:] #value
]

#let info_row(label, value) = [
  #text(weight: "bold", fill: navy)[#label:] #value
]

#let table_style = (
  stroke: (x, y) => if y == 0 { (paint: navy, thickness: 0.8pt) } else { (paint: line_gray, thickness: 0.45pt) },
  fill: (x, y) => if y == 0 { soft } else { none },
)

#let callout(body) = box(
  width: 100%,
  inset: 8pt,
  fill: soft,
  stroke: (paint: navy, thickness: 0.6pt),
  radius: 3pt,
)[#body]

#align(center)[
  #text(size: 17pt, weight: "bold", fill: navy)[SoilPulse-ET]
  #v(2pt)
  #text(size: 12pt, weight: "bold")[SmallSat Onboard Triage for Regenerative Agriculture Water-Stress Follow-Up]
  #v(5pt)
  #line(length: 4.7in, stroke: (paint: gold, thickness: 1pt))
]

#v(0.13in)

#box(width: 100%, inset: 9pt, fill: soft, stroke: (paint: navy, thickness: 0.7pt), radius: 3pt)[
  #text(size: 11.5pt, weight: "bold", fill: navy)[Participant Information]
  #v(4pt)
  #info_row("Participant Name", "Cody Mitchell")

  #info_row("Team Name", "Fractal Research Group / SoilPulse-ET")

  #info_row("NASA Data Set Used", "ECOSTRESS Tiled Evapotranspiration Instantaneous and Daytime L3 Global 70 m V002")

  #info_row("DOI", "10.5067/ECOSTRESS/ECO_L3T_JET.002")
]

#v(0.08in)

= 1. Introduction

== A. Brief overview of the proposed solution and description of your team/organization.

SoilPulse-ET is a SmallSat onboard triage concept for regenerative agriculture water-stress follow-up. The proposed system keeps a tile-level knowledge ledger, scores event priority and evidence quality, then decides whether each candidate land tile should be sent as a priority image chip, compressed into a feature summary, or deferred during a constrained contact. The submission is prepared by Cody Mitchell as an independent researcher affiliated with Fractal Research Group / SoilPulse-ET. The Phase 1 artifact is a concept and policy demonstrator, not flight software and not a validated crop-stress model.

== B. Condensed summary of how the solution addresses all 5 Judge Criteria concepts.

- Creativity: SoilPulse-ET moves beyond a ground-only dashboard by putting a chip / summary / defer policy onboard the spacecraft planning loop.
- Technical feasibility: the concept is anchored to a conservative 6U CubeSat planning envelope and explicit downlink, packet, processing-time, and energy budgets.
- Potential impact: the current hybrid demo uses 224 KiB versus a 784 KiB full-chip baseline, saving 560 KiB / 71.43% while retaining 2/2 high-stress candidates and deferring 1/1 cloudy candidates.
- Business and market evaluation: the first users are irrigation districts, groundwater agencies, conservation planners, and regenerative agriculture technical-service providers.
- Presentation and reproducibility: the public artifact repository provides code, fixtures, tests, paper, and documentation aligned around the same NASA data anchor and evidence boundary.

#pagebreak()

= 2. Proposed Solution Details

== A. Explanation of proposed adaptive sensing or onboard processing approach to regenerative agriculture or forestry, or a similar land resilience objective.

SoilPulse-ET supports water-stress triage for regenerative agriculture and related land-resilience workflows. A ground planner nominates candidate field tiles based on user priorities, recent field history, and revisit needs. Onboard processing converts observations into compact features: evapotranspiration anomaly proxy, vegetation-change signal, cloud fraction, days since last useful observation, user priority, confidence, and resource cost. The policy then selects one action per tile: `priority_chip`, `feature_summary`, or `defer`.

== B. Problem statement for the solution.

Land managers and SmallSats both face scarcity. On the ground, field teams have limited attention and must decide which water-stress signals deserve follow-up. In orbit, SmallSats have limited power, compute, storage, contact time, and downlink. The problem is not simply observing more land; it is deciding what is worth processing and returning first under constrained mission resources.

== I. Selected land use algorithm(s) and small satellite technical requirements.

The first NASA data anchor is ECOSTRESS L3T JET V002. ECOSTRESS supports evapotranspiration logic and future calibration. The current software maps NASA and mission signals into transparent feature fields: ET anomaly proxy, confidence, cloud fraction, revisit age, user priority, and packet-size estimates. The planning envelope is a conservative 6U CubeSat body, with representative onboard processing using a radiation-tolerant CPU for policy execution and optional acceleration for feature extraction.

== II. Mission requirements aligned with onboard constraints.

#table(
  columns: (1.15in, 4.6in),
  stroke: table_style.stroke,
  fill: table_style.fill,
  [Constraint], [SoilPulse-ET design response],
  [Downlink], [Do not send every full chip. Select priority chips, send summaries, and defer low-value tiles.],
  [Compute], [Use compact per-tile features and a deterministic policy before downlink.],
  [Energy], [Track per-tile processing and packet costs under a mission budget.],
  [Storage], [Keep a tile-level ledger and return compact evidence when full imagery is not justified.],
  [Contact time], [Prioritize packets that create the highest-value analyst worklist.],
)

== III. Solution design integration into a current commercial market full-stack implementation system.

The concept fits as an onboard policy layer for Earth-observation operators and as a downstream decision-support feed for agricultural analytics providers. A practical full-stack path is: user priorities on the ground, spacecraft tasking, onboard feature extraction and triage, downlink of selected packets, and a district or conservation-provider worklist for follow-up.

#pagebreak()

= 3. Potential Impact

== A. Benefits and impact of the proposed solution.

The benefit is selective attention. SoilPulse-ET is designed to reduce wasted downlink, avoid returning cloudy or low-confidence observations during scarce contacts, and focus land-resilience analysts on the tiles most likely to need timely follow-up.

== I. How this solution builds upon current research and market capabilities.

The project builds on NASA evapotranspiration data, operational interest in satellite-driven agriculture monitoring, and market examples such as ET-informed water budgets and district-scale analytics. Its contribution is not a new agronomic truth claim. It is a systems layer that asks how a SmallSat can decide what to sense, summarize, downlink, or defer before data reaches the ground.

== II. Effect on technical variables compared to traditional methods.

#table(
  columns: (1.65in, 1.45in, 2.55in),
  stroke: table_style.stroke,
  fill: table_style.fill,
  [Variable], [Hybrid demo result], [Interpretation],
  [Downlink], [224 KiB vs. 784 KiB], [560 KiB / 71.43% byte savings versus sending all full chips.],
  [Packet count], [4 selected packets], [Two full chips plus two compact summaries.],
  [Cloud waste], [1/1 cloudy deferred], [Cloudy evidence is held back instead of consuming downlink.],
  [Stress retention], [2/2 retained], [The highest-stress candidates remain selected in the fixture.],
  [Energy/processing], [38.10% / 48.00%], [The policy stays within concept planning budgets.],
)

#callout([The 71.43% savings is byte savings, not the percentage of tiles deferred. Four of eight tiles are deferred, but two selected tiles are compact summaries rather than full chips.])

== III. Concrete examples, outperformance scenarios, and limitations.

Example scenario: after a hot and dry week, an irrigation district analyst may need to compare cover-cropped orchards, deficit-irrigated vineyards, rotational pastures, riparian buffers, and managed fallow trials. A traditional full-return workflow can spend downlink on every candidate. SoilPulse-ET instead returns detailed chips for urgent tiles, compact summaries for useful but lower-cost evidence, and defers cloudy or low-confidence tiles. The limitation is explicit: the current hybrid fixture contains one ECOSTRESS-derived knowledge-gap row plus labeled synthetic mission-scenario rows. It demonstrates policy behavior and resource accounting, not field-validated crop stress or flight readiness.

#pagebreak()

= 4. Team Experience and Market Evaluation

== A. Qualifications and expertise of team members.

Cody Mitchell is submitting as an independent researcher affiliated with Fractal Research Group / SoilPulse-ET. The Phase 1 contribution is software systems design, reproducible artifact packaging, and evidence-bounded research operations. This submission does not claim flight qualification, agronomic validation, or NASA approval.

== B. Past projects or research relevant to the proposed solution.

Fractal Research Group is being used here as the public research umbrella for targeted, auditable research artifacts. SoilPulse-ET applies that operating style to land and water resilience: public code, explicit resource budgets, clear NASA data lineage, and careful claim boundaries.

== C. Analysis for how the proposed solution can eventually be scaled or integrated into future markets.

The initial product shape is an analytics and tasking layer for Earth-observation operators or agricultural decision-support providers. It can scale from a Phase 1 policy demo to a pilot workflow by adding more real ECOSTRESS windows, real HLS vegetation ingestion, user-calibrated thresholds, and more detailed contact-window models.

== I. Potential product users and how target users inform solution design criteria.

Potential users include irrigation district analysts, groundwater sustainability agencies, conservation technical-service providers, regenerative agriculture program managers, and water-risk analytics partners. Their needs drive the design criteria: explainable tile decisions, audit-friendly reason codes, lower analyst burden, cloud and confidence handling, and explicit degraded modes under scarce satellite resources.

== II. Potential market applications beyond agricultural or forestry purposes.

The same chip / summary / defer pattern can transfer to forestry drought stress, restoration monitoring, post-fire recovery, riparian-buffer monitoring, wetland resilience, and water-resource risk analytics. The common market need is not only imagery access; it is prioritized evidence under constrained observation and response capacity.

#pagebreak()

= 5. Expected Outcomes

== A. Development process from base concept to MVP based on market analysis and industry gaps.

The base concept is already demonstrated as a reproducible policy fixture. The MVP path is to harden the evidence base and user fit:

1. Expand ECOSTRESS event-hunt windows across hot, dry, and comparison periods.
2. Replace synthetic HLS and terrain support fixtures with real ingestion.
3. Calibrate chip / summary / defer thresholds with a pilot user persona.
4. Extend the resource model to raw scene sizes, memory, storage, contact windows, and downlink rates.
5. Package a reviewer-friendly dashboard or notebook view for tile decisions and resource budgets.

This process addresses the industry gap between abundant Earth-observation data and the operational need for selective, explainable, resource-aware follow-up.

== B. Next steps if selected as a Finalist.

If selected, the next phase is validation and mission hardening. SoilPulse-ET would test the policy against more real windows, record ambiguous and failed cases, tune thresholds against actual user priorities, and map the concept onto a specific 6U compute, power, thermal, storage, and downlink stack. The finalist target is not to claim flight readiness; it is to become a better-validated mission prototype.

= 6. Conclusion

== A. Review key points about the proposed adaptive sensing or onboard processing solution.

SoilPulse-ET gives a SmallSat a transparent way to prioritize scarce observation resources. It maintains a tile-level knowledge ledger, scores event priority and evidence quality, and chooses between priority chips, feature summaries, and deferral. The NASA anchor is ECOSTRESS L3T JET V002, DOI `10.5067/ECOSTRESS/ECO_L3T_JET.002`.

== B. Summarize strengths and potential impact.

The strength of SoilPulse-ET is disciplined selectivity. The current hybrid demo shows meaningful downlink savings while preserving high-stress candidates and deferring cloudy evidence. For regenerative agriculture and water-stress follow-up, this can help missions manage scarce satellite resources so land managers can respond faster to scarce water. The submission remains honest about its boundary: concept and policy demonstrator today; validation and mission hardening next.

#pagebreak()

= 7. References

- NASA Space to Soil Challenge. https://nasa-space-to-soil.org/
- Hook, Simon, and Gregory Halverson. ECOSTRESS Tiled Evapotranspiration Instantaneous and Daytime L3 Global 70 m V002. NASA Land Processes Distributed Active Archive Center, 2024. DOI: 10.5067/ECOSTRESS/ECO_L3T_JET.002.
- NASA Earthdata ECOSTRESS catalog. https://www.earthdata.nasa.gov/data/catalog/lpcloud-eco-l3t-jet-002
- NASA SmallSats and CubeSats. https://www.nasa.gov/what-are-smallsats-and-cubesats/
- CubeSat Design Specification Rev. 14.1. https://www.nasa.gov/wp-content/uploads/2018/01/cubesatdesignspecificationrev14_12022-02-09.pdf
- JPL Artificial Intelligence Group, ASPEN. https://ai.jpl.nasa.gov/public/projects/aspen/
- NASA Harvest. https://www.nasaharvest.org/
- OpenET FAQ. https://openetdata.org/faq/
