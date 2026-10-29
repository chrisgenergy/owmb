# OWMB Potential Performance Optimizations Roadmap

This document persists the agreed-upon performance enhancement opportunities identified during cloud map and scanner architecture analysis, reserved for future implementation.

---

### 1. Zero-Copy Incremental Rescan (`TagDatabaseManager`)
* **Current State**: Rescanning a library traverses folders and re-analyzes/re-reads audio items unless skipped.
* **Proposed Enhancement**:
  * Implement `TagDatabaseManager::isItemUnmodified(const juce::File& file)` checking `file.getLastModificationTime()` and `file.getSize()`.
  * If file size and timestamp match existing database records, skip audio decoding, spectral feature extraction, and re-tagging completely.
  * **Expected Gain**: Turns full library rescans for large collections (10,000+ samples) from tens of seconds into near-instant (< 1 second) passes.

---

### 2. Spatial Binning for Physics & Collision Avoidance (`SampleCloudComponent`)
* **Current State**:
  * Intra-cluster repulsion and inter-cluster constellation calculations run pairwise comparisons within clusters ($O(K \cdot N^2)$).
  * Fast enough for current libraries (~6,600 samples in ~150 ms offloaded to background thread).
* **Proposed Enhancement**:
  * Implement uniform 2D/3D spatial grid hashing (or coarse cell binning) for sample point repulsion passes.
  * Only check repulsion against points sharing adjacent spatial cells ($O(N)$ linear complexity).
  * **Expected Gain**: Scales effortlessly to massive 50,000+ sample libraries with sub-second background layout computation.

---

### 3. Tag & Path String Interning (`MediaItem` & `TagDatabaseManager`)
* **Current State**: Each `MediaItem` stores `std::set<juce::String>` and full path strings.
* **Proposed Enhancement**:
  * Shared tag dictionary (`juce::Identifier` or interned atom table) so identical tags (e.g., `#Kick`, `#Stereo`, `#Wav`) share pointer/integer IDs rather than duplicate string instances.
  * **Expected Gain**: Reduces memory footprint of the in-memory database by ~30–40% on massive libraries.

---

### 4. GPU Vertex Streaming Optimization (`SampleCloudComponent`)
* **Current State**: OpenGL and Metal buffers are updated via full VBO dynamic streaming buffers on layout load or filter change.
* **Proposed Enhancement**:
  * Partial VBO/SSBO subdata updates (`glBufferSubData`) for hover state/animation changes without rebuilding the full vertex array.
  * **Expected Gain**: Completely eliminates CPU-GPU bus overhead during active hover interaction.

