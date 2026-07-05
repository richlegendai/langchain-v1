from pathlib import Path
from typing import Final


PROJECT_ROOT: Final[Path] = Path(__file__).resolve().parents[2]
DATA_DIR: Final[Path] = PROJECT_ROOT / "data"
SOURCES_DIR: Final[Path] = DATA_DIR / "sources"
CHROMA_DIR: Final[Path] = DATA_DIR / "chroma_db"
SQLITE_PATH: Final[Path] = DATA_DIR / "app.sqlite"
OUTPUTS_DIR: Final[Path] = DATA_DIR / "outputs"
