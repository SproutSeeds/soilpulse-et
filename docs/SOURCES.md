# Sources

Checked April 10, 2026.

Submission-critical challenge facts rechecked April 30, 2026 against the
official challenge website, NASA page, eligibility page, and USA.gov listing.
Final submission-page and deadline check performed May 3, 2026. No deadline,
artifact, DOI, video, or judging-category changes were found.

- Official challenge website:
  - https://nasa-space-to-soil.org/
  - rechecked `2026-04-30`
  - final handoff check `2026-05-03`
  - verified public facts:
    - open and free challenge
    - launched `2026-01-30`
    - submissions due `2026-05-04` at `8:00 PM ET`
    - finalists selected `2026-05-25`
    - prizes up to `$400,000`
    - Phase 1 requires a 5-page submission paper, 3-minute pitch video, and
      software code or hardware schematics
    - at least one NASA dataset or NASA-data-derived algorithm must be used
    - the dataset DOI citation must be included in the submission
    - video must be uploaded to YouTube or Vimeo and linked in the submission
    - AI-generated content is not allowed for video development
    - a team member should be visible throughout the video
    - code or schematics should be uploaded to a personal repository and linked
    - judging uses 5-point responses across Creativity, Technical Feasibility,
      Impact, Business Model Evaluation, and Presentation
- Official submission form:
  - https://nasa-space-to-soil.org/submission-form
  - rechecked `2026-05-03`
  - verified public facts:
    - page is titled `Submission Form`
    - page embeds an Airtable form at
      `https://airtable.com/embed/appUKh1juIUD8nKiN/pag0y2X5l5zo1n1pz/form`
- NASA page:
  - https://www.nasa.gov/directorates/stmd/prizes-challenges-crowdsourcing-program/center-of-excellence-for-collaborative-innovation-coeci/nasa-space-to-soil-challenge/
  - rechecked `2026-04-30`
  - verified public facts:
    - challenge is about SmallSat adaptive sensing and onboard processing
    - objective is computational and systems approaches, not new agriculture or
      forestry science
    - participants must work within onboard power, compute, and bandwidth
      constraints
    - submissions should not be post-hoc ground-based data fusion
    - full-stack data flow, interface definitions, operational modes, and
      degradation strategies are specifically called out as useful
    - Phase 1 finalists: up to `10` finalists receive `$5,000` each
    - Phase 2: up to `3` pitch event winners receive `$100,000` each and up to
      `2` runners-up receive `$25,000` each
    - Phase 3: pitch event winners join a `10-12` week incubator and are invited
      to IGARSS 2026 Demo Day
- USA.gov challenge listing:
  - https://www.usa.gov/challenges/nasa-space-to-soil
  - rechecked `2026-04-30`
  - verified public facts:
    - challenge supports regenerative agriculture, sustainable forestry, and
      resilient land management
    - challenge types include analytics, software, and technology demonstration
    - listing last updated `2026-03-12`
- Eligibility / participant agreement:
  - https://nasa-space-to-soil.org/nasa-eligibility-requirements
  - rechecked `2026-04-30`
  - verified public facts:
    - participants may enter as an individual, team, or entity
    - participants may not participate in more than one capacity simultaneously
    - submissions must not include malicious code, rights-violating content, or
      inappropriate content
    - FAQ says participants may submit only one entry per person or team
    - registration is separate from the submission process
- Selected NASA dataset anchor and implemented AppEEARS acquisition product:
  - ECOSTRESS Tiled Evapotranspiration Instantaneous and Daytime L3 Global
    70 m V002
  - NASA Earthdata catalog:
    https://www.earthdata.nasa.gov/data/catalog/lpcloud-eco-l3t-jet-002
  - DOI:
    https://doi.org/10.5067/ECOSTRESS/ECO_L3T_JET.002
  - citation from NASA Earthdata:
    Hook, Simon, and Gregory Halverson. ECOSTRESS Tiled Evapotranspiration
    Instantaneous and Daytime L3 Global 70 m v002. NASA Land Processes
    Distributed Active Archive Center, 2024,
    doi:10.5067/ECOSTRESS/ECO_L3T_JET.002.
  - useful facts:
    - available through AppEEARS
    - cloud-enabled dataset
    - Cloud Optimized GeoTIFF band distribution
    - global land, roughly 54 N to 54 S
    - 70 m spatial resolution
    - temporal extent begins `2018-07-09` and continues to present
    - includes ETdaily, instantaneous ET uncertainty, cloud mask, and water mask
  - AppEEARS API documentation:
    https://appeears.earthdatacloud.nasa.gov/api/
  - NASA AppEEARS overview:
    https://www.earthdata.nasa.gov/data/tools/appeears
  - AppEEARS supports spatial, temporal, and layer subsetting, including point
    coordinates and area-based vector polygons; this supports the repo's small
    grouped public point request for producing micro-tile feature rows without
    committing bulky rasters
  - NASA data release stating `ECO_L3T_JET.002` availability in AppEEARS:
    https://www.earthdata.nasa.gov/data/alerts-outages/ecostress-v2-level-3-et-level-4-esi-wue-tiled-data-now-available-appeears
- Candidate future NASA data layers for Phase 2:
  - Harmonized Landsat Sentinel-2 Vegetation Indices data products:
    https://www.earthdata.nasa.gov/data/alerts-outages/harmonized-landsat-sentinel-2-vegetation-indices-data-products-released
  - SMAP soil moisture Earthdata topic:
    https://www.earthdata.nasa.gov/topics/land-surface/soil-moisture-water-content
  - GPM IMERG:
    https://gpm.nasa.gov/data/imerg
  - NASADEM:
    https://www.earthdata.nasa.gov/data/catalog/lpcloud-nasadem-shhp-001
- Official Space to Soil helpful resources:
  - NASA Earthdata Login Registration Guide:
    https://drive.google.com/file/d/1M1bq8Z7CKMkLCuWTtWoHBhj287vjyfXh/view?usp=drive_link
  - NASA Earth Data:
    https://www.earthdata.nasa.gov/
  - NASA Agriculture overview:
    https://science.nasa.gov/earth/explore/agriculture/
  - NASA Earthdata Agriculture Production:
    https://www.earthdata.nasa.gov/topics/human-dimensions/agriculture
  - NASA Earthdata Land Surface:
    https://www.earthdata.nasa.gov/topics/land-surface
  - NASA Earthdata Wildfires:
    https://www.earthdata.nasa.gov/topics/human-dimensions/natural-hazards/wildfires
  - OpenET API / FARMS:
    https://openet.gitbook.io/
  - OpenET FAQ:
    https://etdata.org/faqs/
  - NASA Harvest:
    https://www.nasaharvest.org/
  - California Sustainable Groundwater Management Act:
    https://water.ca.gov/Programs/Groundwater-Management/SGMA-Groundwater-Management
  - NASA International Space Apps Challenge:
    https://www.spaceappschallenge.org/2025/challenges/
  - JPL Artificial Intelligence Group Scheduling Technology:
    https://ai.jpl.nasa.gov/public/projects/
  - JPL ASPEN:
    https://ai.jpl.nasa.gov/public/projects/aspen/
  - Tradespace Analysis Tool for Constellations:
    https://github.com/seakers/tatc
  - CubeSat Design Specification Rev 14.1:
    https://www.nasa.gov/wp-content/uploads/2018/01/cubesatdesignspecificationrev14_12022-02-09.pdf
  - NASA SmallSats and CubeSats:
    https://www.nasa.gov/what-are-smallsats-and-cubesats/
- Adjacent NASA challenge:
  - NASA Patent Remix Challenge NASA page:
    https://www.nasa.gov/directorates/stmd/prizes-challenges-crowdsourcing-program/center-of-excellence-for-collaborative-innovation-coeci/nasa-patent-remix-challenge/
  - NASA Patent Remix Challenge site:
    https://nasapatentremixchallenge.org/
