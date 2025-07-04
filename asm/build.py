import re
import os
from collections import defaultdict


def main():
    sym_patches = defaultdict(list)
    with open("build/sym.txt") as f:
        for line in f:
            sym = re.match(r"([ABCDEF\d]{8})\s(\w+),([ABCDEF\d]{8})", line)
            if sym:
                addr = int(sym.group(1), 16) - 0xFF000
                name = sym.group(2)
                size = int(sym.group(3), 16)
                patch_type = name.split("_")[0]
                data = {"addr": addr, "name": name, "size": size}
                sym_patches[patch_type].append(data)

    for sym_type, sym_data in sym_patches.items():
        path = os.path.join("../patches/", sym_type.lower() + ".txt")
        with open(path, "w") as f, open("out/SLUS_209.11", "rb") as binary:
            for d in sym_data:
                f.write("; " + d["name"] + "\n")

                binary.seek(d["addr"])
                for i in range(d["size"]):
                    data = ord(binary.read(1))
                    f.write(str(d["addr"] + i) + "," + str(data) + "\n")


if __name__ == "__main__":
    main()
