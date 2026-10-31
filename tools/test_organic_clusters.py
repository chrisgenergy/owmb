import os, json, math, time

db_path = os.path.expandvars(r"%APPDATA%\OpenWav\library_index.json")
with open(db_path, "r", encoding="utf-8") as f:
    data = json.load(f)

items = data.get("items", [])

def get_canonical_category(raw_tag):
    t = raw_tag.strip().lower()
    if t.startswith("#"): t = t[1:]
    if not t or t == "untagged": return "other"
    if t in ["subkick", "kick"]: return "kick"
    if t == "snare": return "snare"
    if t in ["rimshot", "rim", "clave"]: return "clave/rim"
    if t == "clap": return "clap"
    if t == "snap": return "snap"
    if t in ["closedhat", "closed_hat", "closed-hat"]: return "hihat closed"
    if t in ["openhat", "open_hat", "open-hat"]: return "hihat open"
    if t in ["hihat", "hat"]: return "hihat"
    if t == "tom": return "tom"
    if t in ["crash", "ride", "cymbal"]: return "cymbal"
    if t in ["shaker", "tambourine", "tamb"]: return "tambourine shaker"
    if t == "cowbell": return "cowbell"
    if t in ["conga", "bongo"]: return "bongo/conga"
    if t in ["percussion", "perc", "percloop", "toploop"]: return "percussion"
    if t in ["subbass", "synthbass", "reesebass", "slapbass", "808bass", "bass", "bassloop", "808"]: return "bass"
    if t in ["piano", "rhodes", "organ", "keys", "chord", "chords"]: return "keys"
    if t in ["acousticguitar", "electricguitar", "guitar", "gtr"]: return "guitar"
    if t in ["violin", "viola", "cello", "contrabass", "strings", "string"]: return "strings"
    if t in ["frenchhorn", "trumpet", "trombone", "tuba", "brass", "horn"]: return "brass"
    if t in ["piccolo", "flute", "oboe", "englishhorn", "clarinet", "bassoon", "sax", "woodwinds", "woodwind"]: return "woodwinds"
    if t in ["timpani", "tubularbells", "glockenspiel", "xylophone", "marimba", "bell", "gong", "harp", "ensemble", "orchestral"]: return "orchestral"
    if t in ["acapella", "vocalchop", "chant", "speech", "vocal", "vox", "vocalloop", "choir"]: return "vocal"
    if t in ["lead", "pad", "pluck", "arp", "synth", "melodicloop"]: return "synth"
    if t in ["subdrop", "impact", "riser", "downlifter", "sweep", "glitch", "vinyl", "foley", "atmosphere", "texture", "fx", "sfx"]: return "fx"
    if t in ["drumloop", "loop", "909", "beat", "beats", "drumkit", "kit", "kits", "breakbeat", "groove"]: return "loop"
    return "other"

# Group items
clusters_items = {}
for it in items:
    cat = "other"
    for t in it.get("tags", []):
        c = get_canonical_category(t)
        if c != "other":
            cat = c
            break
    if cat not in clusters_items: clusters_items[cat] = []
    clusters_items[cat].append(it)

print(f"Categories: {len(clusters_items)}")
for cat, itms in sorted(clusters_items.items(), key=lambda x: -len(x[1]))[:8]:
    print(f"  {cat:15s}: {len(itms)}")

