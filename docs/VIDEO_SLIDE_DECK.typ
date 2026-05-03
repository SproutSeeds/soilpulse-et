#set page(width: 16in, height: 9in, margin: 0in, fill: rgb("#030711"))
#set text(font: "Arial", size: 25pt, fill: rgb("#f8fafc"))
#set par(leading: 0.72em)

#let accent = rgb("#93c5fd")
#let green = rgb("#34d399")
#let gold = rgb("#fbbf24")
#let muted = rgb("#cbd5e1")
#let panel = rgb("#0b1220")
#let border = rgb("#334155")
#let safe = 0.62in

#let bg = place(top + left, image("assets/starry_night_far.svg", width: 16in, height: 9in))

#let title_block(eyebrow, title) = [
  #text(size: 13pt, weight: "bold", fill: gold)[#upper(eyebrow)]
  #v(0.08in)
  #text(size: 50pt, weight: "bold", fill: accent)[#title]
  #v(0.12in)
  #line(length: 1.65in, stroke: (paint: gold, thickness: 2.5pt))
]

#let slide(eyebrow, title, body) = {
  rect(width: 100%, height: 100%, fill: none, inset: 0pt)[
    #bg
    #pad(left: safe, right: safe, top: safe, bottom: safe)[
      #title_block(eyebrow, title)
      #v(0.36in)
      #body
    ]
  ]
}

#let card(title, body, color: accent) = box(
  inset: 18pt,
  stroke: (paint: border, thickness: 1pt),
  radius: 8pt,
  fill: panel.lighten(4%),
)[
  #text(size: 23pt, weight: "bold", fill: color)[#title]
  #v(6pt)
  #text(size: 19pt, fill: muted)[#body]
]

#let metric(label, value, color: accent) = box(
  width: 3.3in,
  height: 1.38in,
  inset: 13pt,
  stroke: (paint: border, thickness: 1pt),
  radius: 8pt,
  fill: panel.lighten(5%),
)[
  #text(size: 14pt, fill: muted)[#label]
  #v(6pt)
  #text(size: 31pt, weight: "bold", fill: color)[#value]
]

#let metric_note(label, value, note, color: accent) = box(
  width: 3.3in,
  height: 1.48in,
  inset: 13pt,
  stroke: (paint: border, thickness: 1pt),
  radius: 8pt,
  fill: panel.lighten(5%),
)[
  #text(size: 12pt, fill: muted)[#label]
  #v(3pt)
  #text(size: 18pt, weight: "bold", fill: color)[#value]
  #v(2pt)
  #text(size: 10.5pt, fill: muted)[#note]
]

#let bullets(items) = [
  #set list(marker: [•], indent: 0.25in, body-indent: 0.16in)
  #text(size: 24pt)[#items]
]

#slide(
  [mission concept],
  [Fractal Research Group / SoilPulse-ET],
  [
    #v(0.15in)
    #text(size: 34pt, weight: "bold")[SmallSat onboard triage]
    #v(0.16in)
    #text(size: 30pt, fill: muted)[water-stress follow-up]
    #v(0.62in)
    #box(width: 11.5in, inset: 20pt, stroke: (paint: border, thickness: 1pt), radius: 8pt, fill: panel.lighten(4%))[
      #text(size: 24pt, fill: accent)[A compact satellite cannot downlink everything.]
      #v(7pt)
      #text(size: 20pt, fill: muted)[SoilPulse-ET decides what to sense, summarize, downlink, or defer.]
    ]
  ],
)

#pagebreak()

#slide(
  [phase 1 artifact],
  [What We Have Done],
  [
    #grid(
      columns: (1fr, 1fr),
      gutter: 0.34in,
      card([Use case], [Water-stress triage for regenerative agriculture and land-resilience users.], color: gold),
      card([NASA anchor], [ECOSTRESS evapotranspiration data grounds the first data path.], color: accent),
      card([Demo], [A reproducible policy chooses priority chip, feature summary, or defer.], color: green),
      card([Budgets], [The policy is constrained by downlink, packet count, processing time, and energy.], color: accent),
    )
  ],
)

#pagebreak()

#slide(
  [onboard decision loop],
  [How It Works],
  [
    #align(center)[
      #box(width: 13.6in, inset: 20pt, stroke: (paint: border, thickness: 1pt), radius: 8pt, fill: panel.lighten(4%))[
        #text(size: 28pt, weight: "bold")[NASA data -> tile state -> onboard packet choice]
      ]
    ]
    #v(0.42in)
    #text(size: 21pt, fill: muted)[A tile is one candidate land area. Each tile gets a priority score and an evidence-quality score.]
    #v(0.34in)
    #grid(
      columns: (1fr, 1fr, 1fr),
      gutter: 0.28in,
      card([priority chip], [Send a detailed observation when the tile looks urgent.], color: accent),
      card([feature summary], [Send compact features when a full chip is not needed.], color: green),
      card([defer], [Wait when the evidence is cloudy, stale, or low-confidence.], color: muted),
    )
  ],
)

#pagebreak()

#slide(
  [resource discipline],
  [What We Optimized],
  [
    #box(width: 13.5in, inset: 15pt, stroke: (paint: border, thickness: 1pt), radius: 8pt, fill: panel.lighten(4%))[
      #text(size: 21pt, fill: muted)[The 71.43% is byte savings, not the percent of tiles deferred.]
    ]
    #v(0.28in)
    #grid(
      columns: (1fr, 1fr, 1fr),
      gutter: 0.28in,
      metric_note([Baseline], [8 full chips], [full chip for every candidate], color: muted),
      metric_note([Selected], [2 chips + 2 summaries], [four packets, not four full chips], color: green),
      metric_note([Deferred], [4 tiles], [zero KiB this contact], color: gold),
    )
    #v(0.16in)
    #grid(
      columns: (1fr, 1fr, 1fr),
      gutter: 0.28in,
      metric_note([Baseline size], [784 KiB], [all eight as full chips], color: muted),
      metric_note([Used size], [224 KiB], [96 + 112 + 8 + 8 KiB], color: green),
      metric_note([Saved], [560 KiB / 71.43%], [bytes avoided, not tile count], color: green),
    )
  ],
)

#pagebreak()

#slide(
  [honest next questions],
  [Validation + Mission Hardening],
  [
    #grid(
      columns: (1fr, 1fr),
      gutter: 0.34in,
      card([Real data], [Expand ECOSTRESS windows and replace synthetic support fixtures with real HLS and terrain ingestion.], color: accent),
      card([Calibration], [Tune chip / summary / defer thresholds against irrigation and conservation user priorities.], color: green),
      card([Generalization], [Test across seasons, regions, water-stress windows, and land-cover types.], color: gold),
      card([Hardware], [Map the policy to a specific 6U compute, power, thermal, storage, and downlink stack.], color: accent),
    )
  ],
)

#pagebreak()

#slide(
  [why we are excited],
  [Why This Matters],
  [
    #bullets([
      - More selective SmallSats can return higher-value observations.
      - Onboard processing can reduce wasted downlink during constrained contacts.
      - Land managers can get faster signals during water-stress windows.
    ])
    #v(0.34in)
    #box(width: 12.3in, inset: 22pt, stroke: (paint: border, thickness: 1pt), radius: 8pt, fill: panel.lighten(4%))[
      #text(size: 30pt, weight: "bold", fill: accent)[SoilPulse-ET helps missions manage scarce satellite resources so land managers can respond faster to scarce water.]
    ]
  ],
)
