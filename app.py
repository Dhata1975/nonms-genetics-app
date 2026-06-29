from __future__ import annotations

import sys
from pathlib import Path

# Keep Streamlit Cloud pointed at the volunteer app.
cloud_dir = Path(__file__).resolve().parent / "cloud_app"
sys.path.insert(0, str(cloud_dir))

from app import main  # noqa: E402

if __name__ == "__main__":
    main()
