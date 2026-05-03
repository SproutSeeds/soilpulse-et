# Market And Impact

Last updated: 2026-04-22

SoilPulse-ET should sell its value through measurable technical impact first,
then business relevance.

## First Adopter

Primary adopter: irrigation district, groundwater sustainability agency, or
conservation planner responsible for water-efficiency, soil-cover, habitat, or
restoration programs across many fields.

Buyer / user examples:

- irrigation district analyst
- groundwater sustainability agency / water-program analyst
- conservation technical-service provider
- regenerative agriculture program manager
- water-risk analytics partner

## First Category To Win

The Phase 1 center should be **water-stress triage for irrigated and
regenerative agriculture in groundwater-constrained basins**.

This category is the cleanest because ET connects directly to water use,
irrigation stress, conservation targeting, and institutional water-management
workflows. California SGMA context makes local groundwater agencies and
district-scale analysts plausible early users, while NASA agriculture and OpenET
context support the broader claim that satellite ET can inform water-management
decisions.

## Workflow Pain

The user needs to decide where to send scarce attention after fast-changing
heat, drought, cloud, or vegetation-stress conditions. Traditional satellite
workflows can deliver too much low-value data and not enough rapid evidence for
priority fields.

## Value Proposition

SoilPulse-ET helps the mission spend onboard compute and downlink on the field
observations most likely to support timely water-stress follow-up.

## Measurable Technical Impact

| metric | meaning | evidence path |
| --- | --- | --- |
| downlink saved | selected packet size versus full-chip baseline | demo metrics |
| high-stress retention | high-scoring tiles retained under constrained budget | demo metrics |
| cloud-waste avoided | cloudy candidates deferred | demo metrics |
| budget utilization | downlink, packet, compute, energy used | demo output |
| response focus | selected packets become a smaller analyst worklist | paper scenario |

## Business Model Hypothesis

Initial product shape: analytics and tasking layer for Earth-observation
operators or agricultural decision-support providers.

Potential channels:

- irrigation district pilots
- conservation program analytics
- satellite-operator onboard software partnerships
- technical-service provider integrations
- government or research pilots

Potential revenue models:

- pilot services
- data-product subscription
- onboard policy licensing
- integration services for satellite operators

## NASA Harvest Context

NASA Harvest supports agriculture-monitoring work involving national, regional,
and policy users. Use this to frame the market as institutional decision
support, not a single-farm phone app.

## OpenET Context

OpenET context is useful because field-scale ET data supports water budgets,
groundwater management, water trading, and ET-based irrigation practices. Use it
carefully: OpenET itself says it is not a new irrigation scheduling tool. That
boundary helps SoilPulse-ET stay in decision-support territory.

## Generalization Beyond Agriculture

| market | transfer path |
| --- | --- |
| forestry drought stress | same chip/summary/defer triage with canopy stress features |
| restoration monitoring | prioritize riparian buffers, wetlands, and revegetation sites |
| post-fire recovery | use burn / vegetation recovery indicators and cloud/smoke screens |
| water-resource risk | summarize ET and vegetation stress for risk analytics |

## MVP Roadmap

| stage | deliverable |
| --- | --- |
| Phase 1 submission | concept paper, policy demo, resource budget |
| MVP pilot | ECOSTRESS-derived event-hunt table, user thresholds, dashboard mock |
| Phase 2 prototype | onboard-policy simulator with scheduling and resource sensitivity |
| Partner pilot | irrigation district or conservation-service workflow test |
| Commercial path | operator integration or analytics-service offering |
