#!/usr/bin/env python3
"""Create Computational_Model_legacy.py inside a msiPL clone at commit 1e8d5cf.

The legacy model is upstream Computational_Model.py with three Keras-compatibility edits
(ReLU() -> Activation("relu"), as in computational_model_legacy.patch), so that it runs
with Keras 2.1.5 / TensorFlow 1.8.0. The upstream file is not redistributed here; this
script reads it from your clone, applies the edits and checks the result's SHA-256.

Usage: python baselines/msipl/make_legacy_model.py [MSIPL_REPO]
(default: $MSIPL_REPO, else baselines/msipl/msiPL)
"""

import hashlib
import os
import sys
from pathlib import Path

UPSTREAM_SHA256 = "24d717b26296199643631b40cc0cdc7baefe9018321809e03e8b0620e51377cb"   # LF endings
LEGACY_SHA256 = "27236d8283612dfe91c42750694d7e2cc5ff56222b2473e5ff9460bd70cdbe48"
EDITS = [
    ("from keras.layers import Lambda, Input, Dense, ReLU, BatchNormalization",
     "from keras.layers import Lambda, Input, Dense, Activation, BatchNormalization"),
    ("        h = ReLU()(h)", '        h = Activation("relu")(h)'),
    ("        hdec = ReLU()(hdec)", '        hdec = Activation("relu")(hdec)'),
]


def digest(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    default = os.environ.get("MSIPL_REPO", Path(__file__).resolve().parent / "msiPL")
    repo = Path(argv[0] if argv else default)
    source = (repo / "Computational_Model.py").read_bytes().decode("utf-8").replace("\r\n", "\n")
    if digest(source) != UPSTREAM_SHA256:
        sys.exit(f"{repo}/Computational_Model.py is not msiPL commit 1e8d5cf")
    for old, new in EDITS:
        if source.count(old) != 1:
            sys.exit(f"edit does not apply once: {old!r}")
        source = source.replace(old, new)
    if digest(source) != LEGACY_SHA256:
        sys.exit("result differs from the legacy model used for the paper")
    target = repo / "Computational_Model_legacy.py"
    if target.exists():
        sys.exit(f"exists: {target}")
    target.write_bytes(source.encode("utf-8"))
    print(f"wrote {target}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
