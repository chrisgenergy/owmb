# OWMB Sample Map (Cloud View) Technical & Behavioral Specification

This document provides a comprehensive technical reference and behavioral specification for the **Sample Map (`SampleCloudComponent`)** in OWMB (OpenWav). It details the semantic categorization engine, acoustic spatial layout physics, interactive auditioning behaviors, caching architecture, and edge-case handling.

---

## 1. System Overview & Philosophy

The **Sample Map** (also referred to as the **Cloud View** or **Galaxy View**) transforms a user's local sample library into an interactive, multi-dimensional acoustic constellation. Rather than displaying samples in traditional hierarchical file trees or tabular lists, the map organizes audio samples organically based on **musical semantics** (instrument categories) and **DSP acoustic features** (spectral brightness, decay time, crest factor / dynamic punch).

### Core Goals:
1. **Immediate Acoustic Discovery**: Users can navigate directly to sound types by location (e.g. kicks on the bottom-left, snares upper-left, basses bottom-right, synths upper-right, loops in the center).
2. **Organic Spacing Without Overlap**: Clusters expand dynamically so that individual sample nodes remain distinct and clickable, regardless of library density.
3. **Multi-Scale Timbre Navigation**: Within any category cluster, sounds transition smoothly from dark/subby to crisp/bright along the cluster axis, and from tight/punchy to long/reverberant across the cluster.
4. **Instant Recall via Persistent Caching**: Layout coordinates are computed once on a background worker thread and cached in a binary disk format, achieving 1–2 millisecond load times on subsequent launches.

```
                         [ HI-HATS ]
                              │
       [ SNARES / CLAPS ]     │      [ SYNTHS / LEADS ]
                 \            │            /
                  \           │           /
                   \      [ LOOPS ]      /
   [ TOMS ]         \         │         /        [ KEYS / GUITARS ]
          \          \        │        /        /
           \          ──────┼──────           /
            \                 │                 /
        [ KICKS ]             │             [ BASS ]
                              │
                    [ ACOUSTIC / ORCHESTRAL ]
```

---

## 2. Categorization & Routing Engine

The map relies on the **Single Source of Truth (SSoT)** engine defined in `TagDatabaseManager`. Every item in the cloud is routed through `TagDatabaseManager::getCanonicalCategoryForItem(item)`.

### 2.1 The 3-Tier Resolution Pipeline
When determining the canonical category for a sample node, the engine executes three sequential tiers:

1. **Tier 1: Explicit Database Tags (`item.tags`)**
   - Evaluates the sample's tag set using the strict `priorityList` via `TagDatabaseManager::getPrimaryCategoryTag`.
   - Never iterates alphabetically; priority determines precedence.
   - If a valid primary tag is found, its canonical category is retrieved via `TagDatabaseManager::getCanonicalCategory(primary)`.
   - Applies the **Misclassified Beat Safeguard** (see Section 2.3).
2. **Tier 2: Word-Boundary Path Inference (`TagDatabaseManager::inferTagsFromPath`)**
   - Engaged if the item had no category tags or was previously untagged.
   - Traverses directory names up to 3 levels deep and parses the filename against keyword rules using strict word-boundary matching (`isKeywordMatch`).
   - Suffixes/prefixes are isolated (e.g. `CL_Hat` matches closed hat, but `FL_Studio` does not match flute).
3. **Tier 3: DSP Feature Extraction Fallback (`TagDatabaseManager::classifyFromAudioFeatures`)**
   - Engaged if tags and path inference yielded no category.
   - Evaluates spectral centroid / high-frequency ratio (`highFreqRatio`), zero-crossing rate (`zcr`), crest factor, and envelope decay ratio (`decayRatio`).
   - Classifies unlabelled files into their natural acoustic group.

---

### 2.2 Strict Priority Hierarchy (`priorityList`)

When a sample carries multiple tags (e.g. `#Kick`, `#808`, `#Short`, `#Wav`), tags are resolved according to the following strict hierarchy:

| Priority Rank | Category Group | Specific Tags (Evaluated Left-to-Right) | Canonical Category |
| :--- | :--- | :--- | :--- |
| **1. Drums & Percussion** | Single-instrument drum one-shots | `#SubKick`, `#Kick`, `#Rimshot`, `#Snare`, `#Clap`, `#Snap`, `#OpenHat`, `#ClosedHat`, `#HiHat`, `#Tom`, `#Crash`, `#Ride`, `#Cymbal`, `#Cowbell`, `#Conga`, `#Bongo`, `#Shaker`, `#Tambourine`, `#Percussion` | `kick`, `snare`, `clave/rim`, `clap`, `snap`, `hihat open`, `hihat closed`, `hihat`, `tom`, `crash`, `ride`, `cymbal`, `cowbell`, `bongo/conga`, `tambourine shaker`, `percussion` |
| **2. Bass** | Low-end melodic instruments | `#SubBass`, `#ReeseBass`, `#SlapBass`, `#SynthBass`, `#808Bass`, `#Bass` | `bass` |
| **3. Keys & Guitars** | Chords, keyboards, guitars | `#Piano`, `#Rhodes`, `#Organ`, `#Keys`, `#AcousticGuitar`, `#ElectricGuitar`, `#Guitar` | `keys`, `guitar` |
| **4. Orchestral & Acoustic** | Strings, brass, woodwinds, orchestral percussion, choir | `#Violin`, `#Viola`, `#Cello`, `#Contrabass`, `#Strings`, `#FrenchHorn`, `#Trumpet`, `#Trombone`, `#Tuba`, `#Brass`, `#Piccolo`, `#Flute`, `#Oboe`, `#EnglishHorn`, `#Clarinet`, `#Bassoon`, `#Sax`, `#Woodwinds`, `#Timpani`, `#TubularBells`, `#Glockenspiel`, `#Xylophone`, `#Marimba`, `#Bell`, `#Gong`, `#Harp`, `#Choir`, `#Ensemble`, `#Orchestral` | `strings`, `brass`, `woodwinds`, `orchestral` |
| **5. Vocals** | Voices, vocal chops, acapellas | `#Acapella`, `#VocalChop`, `#Chant`, `#Speech`, `#Vocal` | `vocal` |
| **6. Synths** | Synthesizer textures and leads | `#Lead`, `#Pluck`, `#Arp`, `#Pad`, `#Synth` | `synth` |
| **7. FX & Textures** | Transitions and sound design | `#SubDrop`, `#Impact`, `#Riser`, `#Downlifter`, `#Sweep`, `#Glitch`, `#Vinyl`, `#Foley`, `#Atmosphere`, `#Texture`, `#FX` | `fx` |
| **8. Typed & Generic Loops** | Multi-instrument loops & rhythm beds | `#DrumLoop`, `#TopLoop`, `#PercLoop`, `#BassLoop`, `#VocalLoop`, `#MelodicLoop`, `#Loop` | `loop` |
| **9. Structural Fallbacks** | Modifiers & technical tags | `#808`, `#909`, `#OneShot`, `Untagged` | `bass` (for #808), `other` |

> [!IMPORTANT]
> **Drum One-Shot Inviolability**: Drum one-shots (`#Kick`, `#Snare`, `#Tom`, etc.) sit at **Priority Rank 1**. A sample with a `#Kick` tag will **never** be pulled into the `loop` cluster, even if it resides inside a folder named `Drums` or has a long decay tail.

---

### 2.3 Misclassified Beat Safeguard (`isMisclassifiedBeat`)

Full drum loops, drum rack previews, and rhythm beds often have prominent sub frequencies (heavy kick transients and 808 sub tails). Standard DSP analysis can misidentify these as `#Bass` or `#Synth`.

To resolve this without corrupting drum one-shots, the engine implements a dedicated predicate:
```cpp
auto isMisclassifiedBeat = [&](const juce::String& cat) -> bool
{
    if (cat == "loop")
        return false;

    const juce::String fn = item.fileName.toLowerCase();
    // Keep bass if filename explicitly mentions bass (excluding "bass drum")
    if (fn.contains("bass") && !fn.contains("bass drum") && !fn.contains("bassdrum") && !fn.contains("bass_drum"))
        return false;

    // Word-boundary drum beat indicators: "beat", "beats", "drumkit", "breakbeat", "drum loop"
    bool hasBeatKeyword = isKeywordMatch(fn, "beat") || isKeywordMatch(fn, "beats") ||
                          fn.contains("breakbeat") || fn.contains("drumkit") ||
                          fn.contains("drumloop") || fn.contains("drum loop") ||
                          (isKeywordMatch(fn, "groove") && !cat.contains("keys") && !cat.contains("synth"));

    if (hasBeatKeyword && item.durationSeconds >= 1.2)
        return true;

    // Folder is explicitly a drum loop folder or groove preview (with duration >= 1.2s)
    const juce::String fp = item.filePath.toLowerCase().replaceCharacter('/', '\\');
    if (item.durationSeconds >= 1.2)
    {
        if (fp.contains("\\midi clips\\drums\\") ||
            fp.contains("\\loops\\drums\\full\\") ||
            fp.contains("\\drum racks\\") ||
            fp.contains("\\grooves\\"))
            return true;

        if (fp.contains("\\loops\\drums\\") && (hasBeatKeyword || fp.contains("full") || fp.contains("mix")))
            return true;
    }

    return false;
};
```

**Expected Routing Behavior:**
* `Straight EDM Beat 128 bpm.wav` (duration 3.75s, deep low end) $\rightarrow$ **`loop`** (intercepted from `bass`).
* `Hot Rod Kit.adg.ogg` (Ableton Drum Rack preview, duration 4.0s) $\rightarrow$ **`loop`** (intercepted from `synth`).
* `King Bass.adv.ogg` (bass synthesizer patch) $\rightarrow$ **`bass`** (preserved because `"bass"` is in the filename).
* `Kick Foot Late Nite.aif` (0.3s kick inside `Drums\Kick`) $\rightarrow$ **`kick`** (category is `"kick"`, never touches `isMisclassifiedBeat`).

---

### 2.4 Tag Sanitization Rules (`TagDatabaseManager::sanitizeTags`)

During database operations and library scanning, tag sets are kept clean and mutually exclusive:
1. **Channel / Length Hygiene**: A sample cannot be `#Stereo` and `#Mono` simultaneously (stereo takes priority); `#Short` and `#Long` are mutually exclusive.
2. **SubKick vs. SubBass**: If `#SubKick` is detected (e.g. `Sub_Kick_01.wav`), false `#SubBass` tags are stripped.
3. **Keys vs. Bass**: If keyboard tags (`#Piano`, `#Rhodes`, `#Keys`) collide with generic `#Bass` (without explicit sub/808/reese tags), Keys takes precedence.
4. **Drum Isolation**: A `#Kick` sample will have conflicting drum tags (`#Snare`, `#HiHat`, `#Tom`, `#Clap`) purged to ensure single-instrument cluster purity.
5. **Multi-Drum Loops**: If a sample has `#Loop` (or duration $\ge 1.5$s) and contains multiple drum instrument tags (e.g. `#Kick` and `#Snare`), individual drum tags are removed and replaced with `#DrumLoop`.
6. **Silent & Dummy Files**: Samples with duration $< 5$ ms, flatline amplitude, or filenames matching `silent.aif`/`silent.wav` receive `#Silent` and are strictly categorized as `"other"`.

---

## 3. Spatial Layout & Physics Engine

The 2D and 3D spatial layout is calculated by `SampleCloudComponent::calculateClusterLayoutInternal`.

### 3.1 Macro Geography (Hemispheric Constellation)

Clusters are positioned around the canvas in a balanced, acoustically coherent arrangement:
* **Western (Left) Hemisphere — Rhythm & Impact**:
  - `kick` (South-West)
  - `snare`, `clap`, `snap` (North-West)
  - `hihat`, `hihat closed`, `hihat open` (North-North-West)
  - `tom` (West)
  - `percussion`, `bongo/conga`, `tambourine shaker`, `cowbell`, `clave/rim` (North-West to North)
  - `crash`, `ride`, `cymbal` (West to North-West)
* **Center / Equatorial Belt — Grooves**:
  - `loop` (Central hub, separating percussive hits from tonal instruments)
* **Eastern (Right) Hemisphere — Harmony, Melody & Texture**:
  - `bass` (South-East)
  - `keys`, `guitar` (East)
  - `synth` (North-East)
  - `vocal` (North-East)
  - `strings`, `brass`, `woodwinds`, `orchestral` (East to South-East)
  - `fx` (Far North-East)
* **Outskirts / Peripheral**:
  - `other` (Utility files, silent dummies, unclassifiable sounds placed far outside active clusters).

---

### 3.2 Intra-Cluster Physics & Timbral Mapping

Each category forms an elliptical nebula whose local coordinate system maps directly to acoustic audio features:

```
                  Crisp / Bright (+X: High Spectral Centroid)
                                    ▲
                                    │
                                    │      * (Long, bright cymbal)
                                    │
    Tight / Punchy                  │                  Long Decay / Ambient
    (-Y: Low Decay Ratio) ──────────┼────────── (+Y: High Decay Ratio)
                                    │
                 * (Dry, subby kick)│
                                    │
                                    ▼
                  Dark / Subby (-X: Low Spectral Centroid)
```

1. **Long Axis ($X_{\text{local}}$, 78% weight)**: **Harmonic Brightness / Spectral Centroid**
   - Dark, sub-heavy, warm samples settle toward the negative pole.
   - Bright, sizzly, high-frequency-rich samples settle toward the positive pole.
2. **Cross Axis ($Y_{\text{local}}$, 55% weight)**: **Envelope Decay Time / Duration**
   - Punchy, transient, gated one-shots settle toward the inner core.
   - Sustained, reverberant, long-decay samples settle toward the outer edge.
3. **Depth Axis ($Z$, 3D Mode)**: **Crest Factor (Dynamic Punch)**
   - High Peak-to-RMS ratio (raw, punchy acoustic hits, dynamic acoustic kicks) $\rightarrow$ positions forward ($+Z$).
   - Low Peak-to-RMS ratio (heavily limited, compressed, saturated, dense synths/basses) $\rightarrow$ positions deeper into the background ($-Z$).

---

### 3.3 Collision Avoidance & Physics Relaxation

To ensure that nodes in dense categories (e.g. 500+ kicks or snares) do not visually overlap:
* **Dynamic Cluster Expansion**: Cluster radii are scaled by $\sqrt{N}$ where $N$ is the sample count in that cluster.
* **12-Iteration Pairwise Repulsion Pass**:
  - Within each cluster, points closer than the minimum clearance distance ($2 \times \text{radius} + \text{padding}$) exert inverse-square repulsive forces on each other.
  - Dampened over 12 iterations so points relax into a uniform Voronoi-like spacing while preserving their timbral position relative to the nebula axes.
* **Micro-Gravitational Semantic Pulls**:
  - Points with secondary semantic tags receive subtle attraction vectors toward neighboring categories (e.g., an `#808Kick` receives a subtle pull toward the `bass` cluster; a `#Rimshot` pulls slightly toward `clave/rim`).
  - This groups hybrid sounds along cluster borders without adding extra text labels to the map.

---

## 4. Interactive Controls & User Experience

### 4.1 Viewing Modes (2D vs. 3D)
* **2D Mode**: Orthographic top-down projection. Best for fast geometric scanning across categories. Left-drag pans the canvas; scroll wheel zooms toward the cursor.
* **3D Mode**: Perspective projection with pitch and yaw orbital rotation.
  - Left-drag rotates the galaxy in 3D space.
  - Middle-drag or Shift-left-drag pans the camera.
  - **Auto-Spin**: Toggleable via the `Spin` / `Stop Spin` button in the HUD. Gently orbits the camera when idle.
  - **Trackpad / Magic Mouse Support**: On macOS, horizontal two-finger swipes smoothly rotate the view around the selected node.

---

### 4.2 Auditioning & Selection
* **Mouseover Auditioning ("Mouseover: On/Off")**:
  - Toggle button in the top-left overlay.
  - When enabled, moving the mouse over any sample node immediately triggers audio playback without clicking.
  - Uses an expanded trigger radius with hysteresis to guarantee responsive playback during fast cursor sweeps while preventing duplicate re-triggers.
* **Click-to-Play**:
  - Left-clicking any sample node triggers playback.
  - Re-clicking an already playing node stops and restarts playback immediately from the start (voice re-triggering, no audio overlapping).
* **Active Node Halo**:
  - The currently auditioned sample pulses with an animated concentric ring halo in the category's theme color.
* **Audio Info Card (HUD)**:
  - Displays filename, primary category badge, audio duration, sample rate, and bit depth.

---

### 4.3 Category Filter Pills
* Located along the bottom toolbar.
* Each pill corresponds to an active category in the library, styled with its unique cluster color.
* **Left-Click**: Focuses and smoothly animates the camera to frame that cluster.
* **Visibility**: If a category has 0 samples in the user's library, its pill is automatically hidden.

---

### 4.4 In-Constellation Category Labels & 360° Dark Halo
* **High-Contrast Omnidirectional 360° Dark Halo**:
  - Each cluster label is rendered with an 8-way dark charcoal/black outline (`#08090C` at 92% alpha) and a subtle downward grounding shadow directly beneath the crisp white typography.
  - Solves white-on-bright luminance collision on yellow (Hi-Hat), cyan (Cymbal/Ride), and green (Shaker) clusters without introducing rectangular bounding boxes, vignettes, or visual canvas clutter.
  - Keeps the typography floating freely and permanently legible from any distance or camera angle.
* **Zero Performance Overhead**:
  - Leverages hardware-accelerated font glyph caching without CPU-intensive software radial gradient rasterization, ensuring silky smooth, lag-free 60–144+ FPS cursor responsiveness across the entire canvas.

---

## 5. Performance, Threading & Caching Architecture

Computing physics layouts across libraries with 5,000–50,000+ samples involves hundreds of thousands of distance calculations. To ensure a 60 FPS user interface, the layout system is completely decoupled from the main thread.

```
[ User loads Library or applies Filter ]
                 │
                 ▼
     Check Binary Disk Cache
    (%APPDATA%/OpenWav/CloudCache)
    ┌────────────┴────────────┐
    │                         │
[ Cache Hit ]             [ Cache Miss ]
    │                         │
    │ (1-2 ms)                ▼
    │               Spawn layoutThread (Worker)
    │               Show Animated Loading HUD (60 FPS)
    │                         │
    │               Run calculateClusterLayoutInternal()
    │               - Cancellation checks every 128 items
    │               - Multi-phase repulsion relaxation
    │                         │
    │               Write binary cache (.bin) to disk
    │               Auto-prune old versions (< v13)
    │                         │
    │               Dispatch to MessageManager::callAsync
    ▼                         ▼
  [ Instantly Render Galaxy on Screen ]
```

### 5.1 Asynchronous Background Thread (`layoutThread`)
* When filters change or a new library is loaded, layout calculations run entirely inside `layoutThread`.
* **Microsecond Cancellation**:
  ```cpp
  if ((i & 127) == 0 && !layoutActive.load())
      return; // Immediate abort on user filter switch
  ```
  If the user quickly switches views or adjusts search filters, the running thread aborts in $< 1$ ms without wasting CPU cycles.
* Results are marshaled back to the UI thread safely using `juce::MessageManager::callAsync`.

---

### 5.2 Binary Cache Format (`cloud_layout_<hash>.bin`)
* Located in `%APPDATA%\OpenWav\CloudCache\` (Windows) or `~/Library/Application Support/OpenWav/CloudCache/` (macOS).
* **Format Specification**:
  - Magic Header: `0x4F57434C` (`'OWCL'`)
  - Format Version: `13` (Integer, auto-invalidates on layout algorithm revisions)
  - 64-bit Hash: MurmurHash/XXHash of all item IDs, file paths, and timestamps.
  - Node Count, Cluster Count, Edge Count.
  - Binary packed `x, y, z` coordinates for 2D and 3D nodes.
* **Cache Auto-Pruning**:
  - Any cache files from older layout versions (versions $< 13$) or temporary `.tmp` files are purged on launch.
  - LRU cap maintains a maximum of 10 library configurations ($\approx 5$ MB total disk footprint).

---

## 6. Category Color Palette Reference

Every category is assigned a persistent, high-contrast hue used across node rendering, constellation halos, HUD badges, and bottom filter pills:

| Category | Hex Color | Visual Tone | Acoustic Association |
| :--- | :--- | :--- | :--- |
| **`kick`** | `#FF2A85` | Neon Magenta / Hot Pink | Punchy low-end impact |
| **`snare`** | `#FF6B35` | Vibrant Orange | Sharp mid-range crack |
| **`hihat`** | `#FFD23F` | Golden Yellow | Sizzling high frequencies |
| **`hihat closed`** | `#E5C030` | Muted Gold | Short, tight metallic sizzle |
| **`hihat open`** | `#FFF066` | Bright Yellow | Extended metallic decay |
| **`tom`** | `#E056FD` | Purple Pink | Resonant acoustic body |
| **`clap`** | `#FF8A5B` | Coral Peach | Layered transient spread |
| **`clave/rim`** | `#FFA07A` | Light Salmon | High-transient wood/metal click |
| **`crash`** | `#FFD97D` | Warm Sun Yellow | Explosive metallic splash |
| **`ride`** | `#F4E04D` | Pale Gold | Sustained bell and ping |
| **`cymbal`** | `#FFE066` | Bright Cymbal Yellow | Metallic overhead washes |
| **`cowbell`** | `#EE964B` | Ochre Amber | Harmonic percussive metal |
| **`bongo/conga`** | `#98D8AA` | Warm Pistachio | Organic skin and hand drums |
| **`tambourine shaker`**| `#7CD97D`| Mint Spring Green | Granular high-frequency shaking |
| **`percussion`** | `#2ECC71` | Vibrant Green | General percussive elements |
| **`loop`** | `#20B2AA` | Light Sea Green / Cyan | Rhythmic grooves & drum kits |
| **`bass`** | `#9B5DE5` | Deep Purple | Low-frequency melodic foundation |
| **`synth`** | `#F15BB5` | Electronic Orchid | Synthesizers, pads, leads |
| **`keys`** | `#00BBF9` | Sky Cyan | Pianos, Rhodes, electric keys |
| **`guitar`** | `#00F5D4` | Bright Turquoise | Acoustic and electric guitars |
| **`strings`** | `#F72585` | Deep Rose | Orchestral string ensembles |
| **`brass`** | `#F77F00` | Brass Gold | Trumpets, horns, trombones |
| **`woodwinds`** | `#48CAE4` | Wind Blue | Flutes, clarinets, saxophones |
| **`orchestral`** | `#7209B7` | Regal Violet | Full symphonic and mallet percussion|
| **`vocal`** | `#FF4D6D` | Crimson Pink | Human voice, chops, chants |
| **`fx`** | `#4CC9F0` | Electric Azure | Risers, sweeps, textures |
| **`other`** | `#6C757D` | Slate Grey | Unclassified / utility files |

---

## 7. Edge Cases & Verification Guide

When testing or troubleshooting the map, verify against these key edge-case behaviors:

1. **Short vs. Long Kicks**:
   - *Expected*: A short acoustic kick (e.g. 0.2s) and an 808 kick with a 2.5s decaying sub tail must **both** land in the `kick` cluster. The 808 kick will naturally position toward the decay axis and slightly gravitate toward the `bass` cluster, but will never leave `kick`.
2. **Drum Beats with Low-End Energy**:
   - *Expected*: Files like `Straight EDM Beat 128 bpm.wav` contain massive low-end content from kicks and basslines. They must land in the **`loop`** cluster, never in `bass`.
3. **Drum Rack Kit Previews**:
   - *Expected*: Ableton drum rack presets (e.g. `Hot Rod Kit.adg.ogg`) must land in **`loop`**, never in `synth`.
4. **Bass Synthesizers with Percussive Attacks**:
   - *Expected*: Plucky basslines with sharp transient crest factors (e.g. `Growl Bass.adv.ogg`) must remain in **`bass`** and must not be hijacked into `kick`.
5. **Silent & Utility Files**:
   - *Expected*: Dummy files like `Silent.aif` or samples under 5 ms must land in **`other`** and are placed far in the periphery, never inside the active `loop` or `kick` nebulas.
6. **High Sample Density (1,000+ samples per category)**:
   - *Expected*: The cluster boundary expands automatically. Nodes maintain a visible gap and do not stack or clip on top of one another.

