import os, json, math

def get_canonical_category(raw_tag):
    t = raw_tag.strip().lower()
    if t.startswith("#"): t = t[1:]
    if any(k in t for k in ["synth", "lead", "pad", "pluck", "arp"]): return "synth"
    return "other"

db_path = os.path.expandvars(r"%APPDATA%\OpenWav\library_index.json")
with open(db_path, "r", encoding="utf-8") as f:
    data = json.load(f)

synth_items = []
for item in data.get("items", []):
    for t in item.get("tags", []):
        if get_canonical_category(t) == "synth":
            synth_items.append(item)
            break

print(f"Total synth items: {len(synth_items)}")

# Let's inspect properties of synth items: highFreqRatio, zcr, decayRatio, crestFactor
hfr_zero = sum(1 for it in synth_items if it.get("highFreqRatio", 0) == 0)
zcr_zero = sum(1 for it in synth_items if it.get("zcr", 0) == 0)
decay_zero = sum(1 for it in synth_items if it.get("decayRatio", 0) == 0)
crest_zero = sum(1 for it in synth_items if it.get("crestFactor", 0) == 0)
print(f"hfr_zero: {hfr_zero}, zcr_zero: {zcr_zero}, decay_zero: {decay_zero}, crest_zero: {crest_zero}")

# Let's check distribution of compound brightness
brights = [it.get("highFreqRatio", 0) * 0.45 + it.get("zcr", 0) * 2.2 for it in synth_items]
unique_brights = len(set(round(b, 6) for b in brights))
print(f"Unique brightness values: {unique_brights} out of {len(synth_items)}")

