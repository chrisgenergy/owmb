import os, json

db_path = os.path.expandvars(r"%APPDATA%\OpenWav\library_index.json")
with open(db_path, "r", encoding="utf-8") as f:
    data = json.load(f)

for item in data.get("items", []):
    fp = item.get("filePath", "")
    if "808 Oracle" in fp:
        print(f"Path: {fp}")
        print(f"  tags: {item.get('tags')}")
        print(f"  hfr: {item.get('highFreqRatio')}, zcr: {item.get('zcr')}, decay: {item.get('decayRatio')}")

