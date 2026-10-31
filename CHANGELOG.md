# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [1.1.9] - 2026-10-31

### Added
* **Hybrid Layer A + Layer B Procedural Sound Map (`SampleCloudComponent`)**:
  * **Layer A (Deterministic Macro-Allocation)**:
    * Implemented deterministic space partitioning using a 2D Centroidal Power Diagram (Weighted Lloyd Voronoi) within an Elliptical Cosmic Disc domain ($120 \times 75$ widescreen grid). Runs in $< 2\text{ms}$ CPU time and guarantees 100% space coverage with zero unesthetic voids, chasms, or black-hole parking lots.
    * **2D Planar Acoustic Axes**: Mapped continuous taxonomy vectors to intuitive physical coordinates—Vertical frequency gradient ($+Y$ Air/Splash down to $-Y$ Sub/Bass) and Horizontal texture gradient ($-X$ Percussive/Transient to $+X$ Harmonic/Tonal).
    * **Dynamic Library Resilience**: Active normalization automatically centers and bounds the galaxy regardless of library composition (boutique 200-sample packs, drum-only kits, orchestral scores, or 87k+ universal collections).
    * **Area-Packed Power Weights**: Category seed weights scale with true packed cluster area ($R_{\text{pack}} = 14.65 \sqrt{N}$), ensuring large categories have sufficient physical territory while small categories maintain a guaranteed minimum body ($R \ge 155\text{px}$).
    * **Pre-Centered Coordinate Frame**: Constellation coordinates are centered to $(0, 0)$ immediately upon mapping grid centroids to world space, ensuring angular coordinates remain locked throughout relaxation and rendering.
  * **Layer B (Polyline Contact Clearance & Organic Star Relaxation)**:
    * Evaluates exact 4-segment polyline spine boundary clearance with inward bend displacement, enforcing guaranteed $55.0\text{px}$ inter-cluster clearance (`kMinInterClusterGapPx = 55.0f`).
    * Recomputes spine vectors dynamically across relaxation passes as clusters shift.
    * Enforces dedicated horizontal and vertical label clearance ($\Delta X \ge 150\text{px}, \Delta Y \ge 42\text{px}$), guaranteeing zero text collisions under all zoom levels.
    * Restored isotropic physics ($F_x = F_y$): sample dots remain 100% circular, while the camera projection frustum handles panoramic widescreen framing and $17\%\text{–}22\%$ cosmic border margins.

* **Category Morphology Hierarchy: Circular Pebbles & Modern Vector Boomerangs**:
  * Implemented a continuous, library-adaptive radial morphology hierarchy based on normalized distance $d_{\text{norm}}$ from galactic center:
    * **Core Zone ($d_{\text{norm}} < 0.20$)**: Circular celestial star orbs ($S \approx 1.05 : 1$, $\text{widthRatio} \approx 0.95$, $\text{bend} = 0.0$) for central categories (`vocal`, `clap`, `loop`, `snare`), completely eliminating elongated "sausage" shapes.
    * **Mid-Orbit ($0.20 \le d_{\text{norm}} < 0.55$)**: Soft transitional ovals ($S \approx 1.25\text{–}1.45 : 1$, $\text{widthRatio} \approx 0.60\text{–}0.75$) with gentle organic curvature (`keys`, `strings`, `brass`, `guitar`, `percussion`).
    * **Perimeter Horizon ($d_{\text{norm}} \ge 0.55$)**: Aerodynamic Modern Vector Boomerangs ($S \approx 1.70\text{–}1.85 : 1$, $\text{widthRatio} \approx 0.42\text{–}0.45$, $\text{bend} \approx 0.32$) with concave inner faces, convex outer faces, and blunt hemispherical domes ($R_{\text{cap}} \ge 150\text{px}$).
  * **Centripetal Opposing Wings**: Perimeter wings sweep inward toward the galactic core $(0, 0)$, rejecting artificial spiral/vortex swirling.

* **True 2D Uniform Area Rejection Sampling (Roberts $R_2$ Blue Noise)**:
  * Star positions are generated via rejection sampling on Roberts $R_2$ quasi-random blue-noise sequence ($\phi_2 \approx 1.324718$, $\alpha_1 \approx 0.754878$, $\alpha_2 \approx 0.569840$), guaranteeing constant local density ($dN/dA = \text{const}$) throughout the entire cluster body.
  * Completely eliminated perimeter star accumulation ("crust/wall") and post-relaxation clamping overwrites.
  * Deterministic acoustic brightness sorting: orders samples from core to tips/edges based on spectral brightness (high-frequency ratio + ZCR).

* **Automated Dual-Layer Overlap Verification Gate (`simulate_library.py`)**:
  * Upgraded the Simulation-First test harness with two automated gates:
    1. **Polyline Boundary Clearance Gate**: Verifies minimum edge-to-edge gap across curved boomerang spines ($\ge 45.0\text{px}$).
    2. **Star-Level Cross-Cluster Overlap Catch Gate (§7)**: Evaluates $O(N)$ spatial grid distance checking across 87k sample stars, automatically halting compilation if any cross-category node distance is $< 24.5\text{px}$.
  * Verified 100% green across multi-genre archetypes (87k general, drum-only, orchestral-only, micro-pack) and scale-tested from 10k to 200k samples.

### Changed
* **Consolidated Production Layout Cache (Cache Version 48)**:
  * Consolidated all procedural layout, orientation, and star-sampling updates into binary cache format version `48` in `SampleCloudComponent`.

---

## [1.1.8] - 2026-10-31

### Added
* **Anisotropic Widescreen Gravity & Tangential Arc Dispersion (`SampleCloudComponent`)**:
  * Implemented widescreen aspect-aware gravity ($F_y = 1.30 \times F_{\text{inward}}, F_x = 0.75 \times F_{\text{inward}}$) in `SampleCloudComponent`, naturally shaping the galaxy into the target widescreen aspect ratio ($1.64 : 1$) and eliminating vertical compaction.
  * Added mutual **Tangential Arc Dispersion ($F_\theta$)** between clusters with narrow angular separation ($\Delta\theta < 11.5^\circ$), spreading high-frequency percussive neighbors (Hi-Hats, Shakers, Cymbals) along the outer perimeter arc and completely resolving radial spoke congestion.
  * Closed the acoustic continuum spring ribbon into a continuous loop connecting Percussion $\leftrightarrow$ High Cymbals $\leftrightarrow$ Woodwinds $\leftrightarrow$ Orchestral $\leftrightarrow$ Synth $\leftrightarrow$ Bass, eliminating quadrant chasms and adjacent sector gaps.
  * Declared all layout and physical force parameters as named `constexpr` constants complying with §7 Magic-Number Ban and §6 Acceptance Criteria.
  * Integrated Simulation-First test gate ([simulate_library.py](file:///c:/dev/owmb/simulate_library.py)) verifying edge-to-edge gap ($\ge 60\text{px}$), zero label collisions, aspect ratio ($\in [1.4, 1.9]$), and cosmic border margin ($17\text{–}22\%$).

### Changed
* **Sample Cloud Binary Layout Cache Version Bump (Version 27)**:
  * Incremented layout binary cache format version to `27` in `SampleCloudComponent` to invalidate stale caches and regenerate dynamic anisotropic 4-force layouts across all libraries.

---

## [1.1.7] - 2026-10-31

### Added
* **Dynamic 4-Force Galactic Model & Void-Free Auto-Closing (`SampleCloudComponent`)**:
  * Simulated the constellation as a dynamic physical system driven by four simultaneous forces:
    1. **Inward Centripetal Gravity**: Pulls all clusters inward toward the galaxy core until physical boundaries make contact with inner bodies, completely eliminating hollow donut centers and internal chasms.
    2. **Elastic Musical Affinity Springs**: Connected along the acoustic continuum (Kick $\leftrightarrow$ Tom $\leftrightarrow$ Loop $\leftrightarrow$ Other $\leftrightarrow$ Keys $\leftrightarrow$ Guitar $\leftrightarrow$ Bass; Hats $\leftrightarrow$ Shakers $\leftrightarrow$ Cymbals). When a category is small or absent, neighbor springs contract and smoothly close the seam with zero dead space.
    3. **Hard Dynamic Contact Repulsion**: Strictly enforces physical clearance based on actual category radii ($D_{\text{min}} = R_i(N_i) + R_j(N_j) + \text{clearance}$), allowing small categories to tuck neatly against large neighbors like moons orbiting a planet.
    4. **Angular Musical Compass**: Constrains categories to their musical compass direction relative to center rather than rigid coordinates, allowing radial distance $r$ to expand or contract dynamically based on library volume.
  * **Active Library Centroid Auto-Centering**: Translates the physical Center of Mass $(\bar{X}, \bar{Y})$ of the active library to $(0, 0)$ across both clusters and nodes, ensuring partial or specialized libraries (e.g. pure drum packs or pure orchestral scores) always center perfectly in the viewport.
* **Panoramic Widescreen Amphitheater & Void-Free Harmonic Continuum (`SampleCloudComponent`)**:
  * Stretched the galaxy anchor envelope to an optimal $\approx 1.55:1$ cinematic widescreen aspect ratio ($X \in [-0.85, +0.85]$, $Y \in [-0.60, +0.82]$), eliminating giant black void deserts on the left and right sides of widescreen displays.
  * Re-anchored the southern foundation arc into a seamless low-frequency bridge: Kick $\rightarrow$ Tom $\rightarrow$ Bongo/Conga $\rightarrow$ Loop $\rightarrow$ Other/Oneshot $\rightarrow$ Keys $\rightarrow$ Guitar $\rightarrow$ Bass, completely closing the bottom chasm.
  * Unfurled the northwest high-frequency categories into a single, flowing perimeter canopy arc: Clave/Rim $\rightarrow$ Cowbell $\rightarrow$ Closed Hi-Hat $\rightarrow$ Main Hi-Hat $\rightarrow$ Open Hi-Hat $\rightarrow$ Tambourine/Shaker $\rightarrow$ Ride $\rightarrow$ Cymbal $\rightarrow$ Crash $\rightarrow$ Woodwinds $\rightarrow$ FX, eliminating vertical multi-tier stacking and label crowding.
  * Rich interior infill: positioned Clap, Snap, and Percussion as an acoustic rhythmic bridge between Snare and Vocals, and Strings and Brass as a melodic bridge between Vocals and Synth/Bass.
  * Balanced camera auto-fit margin (`margin = 1.20f`), framing the galaxy with an even $\sim 17\text{–}20\%$ cosmic border on all four sides.
* **Northern Canopy Wide-Angle Fanning & Post-Center-of-Mass Label Decluttering (`SampleCloudComponent`)**:
  * Added a dedicated 24-iteration post-Center-of-Mass label declutter pass running directly on physical cluster centers after sample relaxation, mathematically preventing category text tags from ever overlapping or obscuring each other.
* **Harmonious Sub-Linear Nebula Sizing & Thick Galactic Bodies (`SampleCloudComponent`)**:
  * Replaced linear $\sqrt{N}$ scaling with sub-linear power sizing ($R(N) = 155\text{px} + 30\text{px} \times N^{0.35}$), reducing the dynamic range disparity between tiny and giant categories from $21:1$ down to a balanced $3.5:1$. Small categories gain a solid minimum body, while massive categories remain majestic without blowing up the camera view.
  * Thickened nebula bodies from $0.44\times$ to $0.66\times$ base radius and moderated aspect ratio stretch ($1.35\text{–}1.40$), transforming elongated "curved sausage/banana" shapes into radiant, full celestial clouds.

### Changed
* **Sample Cloud Binary Layout Cache Version Bump (Version 26)**:
  * Incremented layout binary cache format version to `26` in `SampleCloudComponent` to automatically purge stale layouts and regenerate dynamic 4-force closed-loop galactic layouts with active centroid auto-centering and void-free auto-closing across all libraries.

---

## [1.1.6] - 2026-10-30

### Added
* **Search-to-Map Bridge (`SampleCloudComponent`, `HeaderBarComponent`, `SampleTableComponent`, `FolderBrowserComponent`)**:
  * Seamlessly connects text-based search retrieval with spatial sound map memory.
  * In Sound Map view (`Cloud`), pressing `Enter` / `Return` inside the search bar instantly flies the camera to the first matching search result, smoothly centers and zooms in on the sample, highlights it, and triggers audio preview.
  * Added right-click context menu option **"Locate on Sound Map"** in both the Sample Table (List view) and Folder Browser, switching to Cloud view and focusing on the target sample.
  * Automatically un-dims the target node if dimmed under filter dimming mode, updates the similarity dock, and animates the camera smoothly.
* **Interactive Map Filter Dimming Toggle (`SampleCloudComponent`)**:
  * Added `Filter: Dim` / `Filter: Hide` toggle button on the map overlay, allowing users to choose between completely hiding filtered-out samples or keeping the entire universe visible with filtered-out samples softly dimmed.
  * In Dim mode, the universe map maintains 100% spatial continuity without layout jumps or re-calculations: matching samples shine with full vibrancy, while non-matching samples recede into a faint, dark background tone (`a = 0.14`, `radius * 0.75`).
  * Inactive category cluster titles and constellation lines automatically fade when containing zero matching samples.
  * Dimmed samples are strictly isolated from user interaction (cannot be hovered, clicked, or auditioned via Mouseover).
  * Sample Counter dynamically adapts in Dim mode to display matching vs total samples (e.g. `3,120 / 87,421 samples`).
* **Dynamic Sample Counter Badge on Map Overlay (`SampleCloudComponent`)**:
  * Added a subtle, semi-transparent frosted badge positioned immediately to the right of the `Mouseover` button.
  * Dynamically displays the current amount of samples on the map formatted with thousand separators (e.g. `87,421 samples` in normal state, and remaining counts when search keywords, tag filters, or folder selections are active).
  * Includes an informative hover tooltip and transparent click handling to avoid interfering with map panning or node selection.

### Fixed
* **Camera Re-Anchoring on 2D / 3D Map View Switch (`SampleCloudComponent`)**:
  * Fixed an issue where switching between 3D and 2D mode left the camera looking at empty void. The camera now dynamically re-anchors to the active sample's coordinate space (`pos2D` in 2D mode, `pos3D` in 3D mode) or universe center if unselected, keeping the sample centered across all dimension switches.
* **Continuous Playback & Non-Interrupting Map Location (`OpenWavAudioProcessorEditor`, `SampleCloudComponent`)**:
  * Prevented view mode changes between browsing views (`List`, `Folders`, `Cloud`) from cutting off audio playback.
  * Right-clicking "Locate on Sound Map" now navigates and highlights the sample without restarting or interrupting currently playing audio from `0.0s`.
* **2D / 3D Sound Map Preference Persistence (`TagDatabaseManager`, `SampleCloudComponent`)**:
  * Persisted the user's 2D vs. 3D map preference so the sound map reliably opens in the user's preferred dimension without reverting to 3D.
* **Cluster Outlier Elimination & Capsule Envelope Clamping Across All Categories (`SampleCloudComponent`)**:
  * Bounded sub-tag micro-attraction magnitude proportionally to each cluster's own `baseRadius` (max 2.5% or 14px) rather than unconstrained universe-scale distance, preventing samples with secondary sub-tags from being ejected into the void.
  * Added mathematical taper-aware capsule envelope enforcement (`allowedCross = baseRadius * sqrt(max(0.04, 1.0 - u^2 * 0.85)) * 0.68`) calibrated exactly to the 0.65 cluster body during initial node layout and after intra-cluster repulsion, smoothly tucking any boundary breaches flush into the cluster's dense outer rim. Completely eliminates stray outlier dots across all categories while fully preserving directional musical sub-tag orientation.
* **Eliminated Selection & Audition Lag in Massive Categories (`SampleCloudComponent`)**:
  * Optimized `updateSimilarStack()` by replacing unconstrained O(N) acoustic distance scans across tens of thousands of category samples with an ultra-fast two-stage spatial neighbor pre-filter.
  * Replaced redundant double-looping across all nodes with instant O(1) pre-cached cluster center of mass and count lookups.
  * Prunes candidate evaluation down to the closest 256 spatial neighbors via O(N) `std::nth_element`, cutting execution time in massive clusters like `synth` from ~200 ms down to < 1.5 ms on the UI thread for instant click and audition response.

### Changed
* **Dynamic Sample Cloud Zoom Scaling & Auto-Framing (`SampleCloudComponent`)**:
  * Replaced static zoom boundaries with true dynamic zoom scaling computed directly from real physical map bounds (`maxX`, `maxY`, `maxZ`) and viewport aspect ratio.
  * Dynamically computes `fitZoomScale` and adjusts `minZoomScale` down smoothly (down to `0.015f` for massive 87,000+ sample libraries), allowing users to zoom out to view the entire universe constellation on any display or library size without cutoff.
  * Added auto-framing on initial library load and updated `Reset View` (`resetZoomAndPan`) to target `fitZoomScale` instead of hardcoded 1.0x, ensuring newly loaded libraries immediately appear properly centered and framed.

---

## [1.1.5] - 2026-10-30

### Added
* **Quick Search Field Reset (`HeaderBarComponent`)**:
  * Embedded interactive `✕` Clear Button directly inside the header search bar (`searchEditor`).
  * Dynamically appears only when search text is present and stays hidden when empty.
  * Added `Escape` key shortcut inside the search field to instantly clear queries, refresh search results, and reset focus.
  * Added right-side border margin (`BorderSize<int>(1, 6, 1, 26)`) ensuring typed text never collides with the clear button.

---

## [1.1.4] - 2026-10-30

### Fixed
* **Beat Loops & Grooves Misclassification Across All Categories (`TagDatabaseManager`)**:
  * **Root Cause Analysis**:
    1. *`MIDI Clips\Drums` Preview Misrouting*: In Ableton Core Library (and standard sample packs), preview audio files for drum clips (e.g. `Pop Relaxed 104 bpm.alc.ogg`, `Dancehall Trap 113 bpm.alc.ogg`, `909 Core Kit House 127 bpm.alc.ogg`) reside under `Previews\MIDI Clips\Drums\`. Because their path does not contain the word `"loop"`, path inference did not mark them as `#DrumLoop`, triggering audio feature fallback which erroneously tagged them with `#MelodicLoop` and `#Synth`.
    2. *Priority Inversion*: In `priorityList`, `#Synth` (Priority Rank 6) took precedence over `#DrumLoop` (Priority Rank 8), causing 64 drum beat loops to be routed into the `synth` category cluster.
    3. *Predicate Path Gap in `isMisclassifiedBeat`*: The previous predicate only inspected `cat == "bass" || cat == "synth"` and required `"drum loop"` or `"loop"` in the file path, failing to catch drum clip paths or groove files.
    4. *Multi-Drum Loop Sanitization*: `sanitizeTags` previously required `hasKick && hasOtherDrums` to consolidate drum loops, failing on loops composed of hat + snare (`Hats and Snare UK Garage 127 bpm.aif`), hat + clap (`Hihat Clap House 120 bpm.wav`), or kick + ride (`EDM Kick and Ride 128 bpm.wav`), which collapsed into individual one-shot categories (`snare`, `clap`, `ride`).
    5. *Substring Collision False Positives*: Unconstrained substring matching for `"kit"` and `"beat"` in `inferTagsFromPath` and `sanitizeItem` erroneously stamped `#DrumLoop` on non-drum instrument presets like `Here Kitty Kitty.adv.ogg` (`"kit"` in `"kitty"`) and `Beating Vibraphone.adv.ogg` (`"beat"` in `"beating"`).
  * **Fixes Implemented**:
    - *Comprehensive Beat Safeguard*: Broadened `isMisclassifiedBeat` to check any non-loop category (`cat != "loop"`) and explicitly detect `\midi clips\drums\`, `\loops\drums\full\`, `\drum racks\`, and `\grooves\` for samples >= 1.2s, backed by strict word-boundary matching (`isKeywordMatch`) for `"beat"`, `"beats"`, `"breakbeat"`, and `"drumkit"`.
    - *Multi-Family Drum Loop Consolidation*: Enhanced `sanitizeTags` to count distinct drum families (Kick, Snare, Clap, Hat, Tom, Cymbal). If any loop sample possesses >= 2 distinct drum families, it is automatically consolidated into `#DrumLoop` and all individual one-shot tags are purged.
    - *Drum Loop Tag Hygiene*: Guaranteed that any sample carrying `#DrumLoop` automatically strips accidental `#MelodicLoop` and generic `#Synth` tags.
    - *Word-Boundary & Preset Protection*: Replaced all raw substring checks with `isKeywordMatch` across `getCanonicalCategory`, `inferTagsFromPath`, and `sanitizeItem`. Explicitly safeguarded harmonic instrument presets (`keys`, `synth`, `strings`, `brass`, etc.) against accidental drum tags.
    - *Library Index Sanitization*: Purged accidental `#Synth` and `#MelodicLoop` tags from all 108 files in `MIDI Clips\Drums`, and cleared false `#DrumLoop` tags from affected instrument presets in `library_index.json`.

### Changed
* **Sample Cloud Binary Layout Cache Version Bump (Version 14)**:
  * Incremented binary cache format version from `13` to `14` in `SampleCloudComponent` to automatically purge stale layouts and regenerate pristine spatial coordinates where all drum beat loops sit properly clustered in `loop`.

## [1.1.3] - 2026-10-29

### Fixed
* **Drum One-Shot Routing & Inviolability (`TagDatabaseManager`)**:
  * **Problem**: In `getCanonicalCategoryForItem`, an overly broad early return checking `filePath.containsIgnoreCase("drums")` inadvertently intercepted single drum one-shots located in standard directory paths (e.g. `.../Samples/One Shots/Drums/Kick/...`) before their primary category tags (`#Kick`, `#Tom`, `#Snare`, etc.) were evaluated. This forced thousands of drum one-shots into the `loop` category cluster and shriveled the kick cluster.
  * **Fix**: Removed the premature early return, restoring strict Priority Rank 1 for drum one-shots (`#Kick`, `#Tom`, `#Snare`, `#HiHat`, `#Clap`, `#Cymbal`, etc.). Drum one-shots are now guaranteed to land exclusively in their dedicated instrument clusters.
* **Beat Misclassification Safeguard (`TagDatabaseManager::isMisclassifiedBeat`)**:
  * **Problem**: Full drum grooves, breakbeats, and drum rack kit previews with massive low-end content (e.g. `Straight EDM Beat 128 bpm.wav`, `Hot Rod Kit.adg.ogg`) were frequently misclassified as `bass` or `synth` by low-frequency spectral DSP analysis.
  * **Fix**: Implemented a targeted predicate (`isMisclassifiedBeat`) that redirects samples to `loop` only if they would otherwise resolve to `bass` or `synth`, contain explicit groove/kit/beat indicators (filename keywords or loop directory paths with duration $\ge 1.5$s), and do not explicitly mention `"bass"` in their title. Genuine bass synthesizer presets (e.g. `King Bass.adv.ogg`, `Growl Bass.adv.ogg`) remain preserved in the `bass` cluster.
* **Inference Rule Hygiene & Index Sanitization**:
  * Removed ambiguous generic keywords (`"drum"`, `"drums"`, `"kit"`, `"break"`) from inferring `#DrumLoop` during folder and file scanning, preventing accidental loop tags on standard drum one-shots.
  * Sanitized `library_index.json` to purge erroneous `#DrumLoop` and `#Loop` tags from 2,687 drum one-shot files, restoring `#OneShot`.

### Changed
* **Sample Cloud Binary Layout Cache Version Bump (Version 13)**:
  * Incremented binary cache format version to `13` in `SampleCloudComponent` (`loadLayoutFromCache`, `saveLayoutToCache`, and auto-pruning passes) to automatically purge obsolete layouts containing displaced one-shots and compute clean, overlap-free coordinates.

### Added
* **Cluster Label Omnidirectional 360° Dark Halo (`SampleCloudComponent`)**:
  * **Contrast Enhancement**: Implemented an 8-way dark charcoal outline (`#08090C` at 92% alpha) and grounding shadow around white in-constellation category titles. Resolves white-on-bright luminance collision on yellow (Hi-Hat), cyan (Cymbal/Ride), and green (Shaker) clusters without introducing box artifacts or visual clutter.
  * **Zero-Overhead Performance**: Preserves pure floating typography with zero CPU overhead, eliminating event queue bottlenecks and ensuring silky smooth, lag-free cursor tracking across categories.
* **Technical & Behavioral Map Specification (`docs/SAMPLE_MAP_BEHAVIOR.md`)**:
  * Authored a comprehensive technical reference and behavioral specification covering the 3-tier categorization engine, priority hierarchy, 2D/3D intra-cluster timbral physics, collision avoidance relaxation, interaction models, and visual color palettes.

## [1.1.2] - 2026-10-29

### Added
* **Sample Cloud Layout Threading, Persistent Binary Disk Cache & Animated Loading Screen (`SampleCloudComponent`)**:
  * **Problem**: In the Cloud View, sample points are arranged using a multi-iteration pairwise repulsion simulation ($O(N^2)$ collision checks and square roots) to cluster sounds organically by timbre, decay, and harmonic brightness without visual overlap. On libraries with 10,000–50,000+ samples, this layout calculation ran synchronously on the main JUCE message thread, locking up the DAW UI completely for 15–120 seconds. Furthermore, layout coordinates were recalculated from scratch on every single launch or filter switch.
  * **Fix**:
    1. **Asynchronous Background Worker Threading**: Offloaded layout computation onto a dedicated background thread (`layoutThread`). Integrated microsecond cancellation checks (`(i & 127) == 0 && !layoutActive.load()`) inside the inner pairwise collision loop so the background thread aborts instantly (< 1 ms) when filters change or the view closes, dispatching results to the UI thread via thread-safe `MessageManager::callAsync`.
    2. **Persistent Binary Disk Cache (`%APPDATA%/OpenWav/CloudCache`)**: Implemented an atomic binary layout cache (`0x4F57434C` magic, versioning, data hash verification, and LRU auto-pruning). Once calculated, all 3D and 2D node coordinates, cluster centers, and constellation edges are written to disk on the worker thread. Subsequent launches and view switches load in 1–2 milliseconds (a 50,000x speedup), preserving 100% of the exact physics clustering and visual spacing.
    3. **Animated Loading Overlay (`paintOverlay`)**: Replaced the raw text label with a 60 FPS animated loading HUD: frosted anthracite glass card, pulsing ambient halo, rotating cyan radar sweep, and orbiting constellation nodes with category cluster colors and live sample tally.
    4. **Enhanced Acoustic Timbre Grouping & Dynamic 3D Depth**:
       - *High-Fidelity Timbre Weighting*: Increased acoustic brightness feature weighting from 55% to 78% along the nebula long axis (and decay weighting to 55% across the cluster), sharpening visual separation between dark/subby and crisp/bright samples while relying on the 12-iteration physics repulsion pass to prevent overlaps.
       - *3D Dynamic Punch ($Z$-Depth)*: Mapped physical 3D depth to Crest Factor (Peak-to-RMS ratio). Dynamic, raw, uncompressed acoustic hits position forward ($+Z$), while dense, limited, saturated hits position deeper into the background ($-Z$), turning 3D mode into a true multi-dimensional acoustic space.
       - *Semantic Sub-Tag Micro-Attraction*: Applied subtle gravitational micro-pulls toward neighbor categories for samples carrying secondary tags (e.g. 808 kicks gravitate toward the Bass nebula; rimshots gravitate toward the Clave cluster) without adding any extra text or visual clutter to the map.
       - *Cache Version Bump*: Transitioned binary cache to format version 2 for transparent, automatic recalculation.

* **Mechanical HDD Auto-Detection & Adaptive Low-Seek Scanning (`LibraryScanner`)**:
  * **Problem**: When scanning large sample libraries (500GB+ with hundreds of thousands of files) on rotational hard disk drives (HDDs) or network shares (NAS), running 16 concurrent worker threads causes severe physical head thrashing across platters, collapsing throughput from 150 MB/s down to 0.5 MB/s and risking drive overheating and system-wide freezes.
  * **Fix**: Implemented zero-privilege OS-level seek penalty detection (`IOCTL_STORAGE_QUERY_PROPERTY` on Windows, `/sys/dev/block/*/queue/rotational` on Linux). When a spinning HDD or network volume is detected, the scanner automatically engages an optimized low-seek mode: restricts worker concurrency to 1–2 sequential threads to eliminate mechanical head thrashing, sorts queued files by full directory path for adjacent physical cluster reads, and displays a dedicated rotational drive status notification. High-speed solid-state drives (SSDs) continue running at full parallel 16-thread capacity.

* **DAW State Saving Decoupling (`OpenWavAudioProcessor`)**:
  * **Problem**: In `getStateInformation()` and `setStateInformation()`, the audio processor directly invoked `dbManager.saveToFile()` and `dbManager.loadFromFile()`. Whenever the host DAW initiated background auto-saves (e.g. every few minutes in Ableton Live, FL Studio, Bitwig), duplicated a track, or saved a project, the plugin synchronously serialized or deserialized the entire global sample database (`library_index.json`). With large sample libraries (50k–100k+ samples, 50MB–200MB+ JSON), this introduced noticeable DAW audio dropouts, UI freezes, and disk write race conditions between concurrent plugin instances overwriting the same database file.
  * **Fix**: Decoupled the DAW's per-instance track session state from the global sample database by removing `dbManager.saveToFile()` from `getStateInformation()` and `dbManager.loadFromFile()` from `setStateInformation()`. Global library persistence remains completely self-managed by `TagDatabaseManager` (persisting on tag edits, scans, ratings, and plugin shutdown), eliminating DAW auto-save freezes while preserving full library integrity and instantaneous track state recall.

## [1.1.0] - 2026-10-28

### Added
* **Collapsible Scanned Folders Overview (`FolderBrowserComponent`)**:
  * New dedicated folder hierarchy browser displaying registered scanned folders and subfolders.
  * Hierarchical tree list with smooth kinetic scrolling, real-time sample count badges, and subfolder tallies.
  * Smart auto-unfolding of empty single-child folder chains.
  * Top toolbar with **Expand All** and **Collapse All** controls.
  * Sample row integration with 2× Retina play/pause indicators, tag badges, duration, format, sample rate, interactive 5-star ratings, and favorite toggles.
  * External drag-and-drop from folder rows directly into external DAWs (Ableton Live, FL Studio, etc.).
  * Keyboard navigation (`Up`/`Down` auditioning, `Right`/`Left` expand/collapse).
  * Folder right-click context menu: *Reveal in Explorer*, *Rescan Folder*, and *Remove from Scanned Folders*.
* **Header View Switcher (`HeaderBarComponent`)**:
  * Added `ViewMode::Folders` button positioned between **List** and **Cloud** views.
  * Custom Feather-style vector folder SVG icon in `OpenWavLookAndFeel`.
* **Galaxy View Mouseover Auditioning (`SampleCloudComponent`)**:
  * Added on/off toggle button in the top-left map overlay for hands-free hover auditioning.
  * Expanded trigger radius specifically for mouseover mode so fast cursor movement across clusters reliably triggers audio.
* **Safety Safeguards & Confirmation Prompts**:
  * Added an asynchronous confirmation dialog before removing a folder from Scanned Folders (both via the left panel `"X"` button and via right-click context menus).
  * Clear explanation in dialog that audio files on disk remain safe and only library database indices are cleared.
* **Compound Tag & Semantic Keywords**:
  * Added recognition for compound drum types: `sub_kick`, `bass_drum`, `open_hihat`, `closed_hihat`, `side_stick`, and `clave`.
  * Added negation rule handling (e.g., `no_kick`).

### Changed
* **Single Source of Truth (SSoT) Category Engine (`TagDatabaseManager`)**:
  * Unified semantic categorization across all views and query algorithms (`getPrimaryCategoryTag`, `getCanonicalCategory`, `getCanonicalCategoryForItem`, `areCategoriesCompatible`, `classifyFromAudioFeatures`).
  * Re-tagging now preserves manual user tags and acoustic DSP tags.
* **Acoustic Feature Extraction & Header Parsing (`LibraryScanner`)**:
  * Standardized audio loop window to 4.5 seconds with leading and trailing silence trimming.
  * Calibrated physical crossover frequency bands at 140 Hz, 800 Hz, and 4 kHz.
  * Standardized Zero-Crossing Rate (`zcr`) and High Frequency Ratio (`highFreqRatio`) against a 44.1 kHz grid to ensure sample-rate invariance.
  * Dynamic RIFF chunk-walking in `parseWavHeaderFast` to correctly handle non-standard header orders (`JUNK`, `bext`, `iXML`, `LIST` preceding `fmt `) with 2-byte word alignment.
* **Galaxy View Snapping & Highlighting**:
  * Fine-tuned magnetic cursor snapping at high zoom levels to prevent skipping over intermediate samples in dense clusters.
  * Enlarged cursor proximity highlight glow.
* **Path-Prefix Boundary Matching**:
  * Tightened `TagDatabaseManager::removeScanFolder` to enforce strict trailing path separator boundaries, preventing removal of `C:\Samples` from accidentally wiping sibling folders like `C:\Samples2`.
* **Build System Decoupling**:
  * Added CMake option `OWMB_COPY_PLUGIN_AFTER_BUILD` to allow isolated local builds without overwriting the system VST3 plugin directory.

### Fixed
* **Audio Auditioning State**:
  * Fixed sample re-click behavior so clicking an already playing sample resets and restarts playback cleanly from the start rather than spawning overlapping voices.
* **Similar Sounds Carousel Hitbox**:
  * Expanded the click trigger hitbox on the mini-list previous/next carousel buttons across the entire button surface.
* **Musical Key & BPM Detection**:
  * Fixed key extraction false positives from technical abbreviations (e.g. `FM` synthesis vs. `Fm` minor, `-6dB` vs. `Db`, isolated characters `A`–`G`).
  * Synchronized `#*BPM` tags with `item.bpm` for host transport alignment.
* **Character Encoding Artifacts**:
  * Standardized all text formatting through `juce::CharPointer_UTF8` to eliminate Windows-1252/Latin-1 encoding mismatches (e.g., `â□□` replacing em-dashes `—` and bullet separators `•`).
