"""``python scripts/<tool>.py`` 时把仓库根目录加入 sys.path。"""

from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]


def install() -> Path:
    root = str(REPO_ROOT)
    if root not in sys.path:
        sys.path.insert(0, root)
    from shared.sklearn_warnings import configure_sklearn_pickle_warnings

    configure_sklearn_pickle_warnings()
    return REPO_ROOT
