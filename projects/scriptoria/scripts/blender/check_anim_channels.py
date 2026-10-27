"""Report which glTF animation channels actually vary (root motion / stray translation check).

Usage: blender -b --factory-startup --python scripts/blender/check_anim_channels.py -- <animated.glb> <out.json>
"""
import json, struct, sys
import numpy as np

path, out = sys.argv[sys.argv.index("--") + 1:]
data = open(path, "rb").read()
n = struct.unpack_from("<I", data, 12)[0]
d = json.loads(data[20:20 + n])
off = 20 + n
bn = struct.unpack_from("<I", data, off)[0]
b = data[off + 8: off + 8 + bn]


def arr(i):
    a = d["accessors"][i]
    bv = d["bufferViews"][a["bufferView"]]
    s = bv.get("byteOffset", 0) + a.get("byteOffset", 0)
    nc = {"SCALAR": 1, "VEC3": 3, "VEC4": 4}[a["type"]]
    return np.frombuffer(b[s:s + a["count"] * nc * 4], dtype=np.float32).reshape(a["count"], nc)


rest = {nd["name"]: nd for nd in d["nodes"] if "name" in nd}
report = {}
for an in d["animations"]:
    varying, nonrest_const = [], []
    for ch in an["channels"]:
        o = arr(an["samplers"][ch["sampler"]]["output"])
        name, p = d["nodes"][ch["target"]["node"]]["name"], ch["target"]["path"]
        if float(np.ptp(o, axis=0).max()) > 1e-5:
            varying.append([name, p, round(float(np.ptp(o, axis=0).max()), 4)])
        elif p != "rotation":
            default = {"translation": [0, 0, 0], "scale": [1, 1, 1]}[p]
            if np.abs(o[0] - np.array(rest[name].get(p, default))).max() > 1e-4:
                nonrest_const.append([name, p])
    report[an["name"]] = {
        "keys": d["accessors"][an["samplers"][0]["input"]]["count"],
        "varyingChannels": len(varying),
        "varyingNonRotation": [v for v in varying if v[1] != "rotation"],
        "rootVarying": [v for v in varying if v[0] == "root"],
        "constantChannelsDifferingFromRest": nonrest_const,
    }
json.dump(report, open(out, "w"), indent=1)
print("CHANNELS", json.dumps(report))
