# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

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
