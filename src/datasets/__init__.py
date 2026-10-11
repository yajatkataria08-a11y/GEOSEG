"""Dataset wrappers for EuroSAT, DeepGlobe, custom AOI, and AID aerial scene dataset."""

try:
    from src.datasets.eurosat import get_eurosat_dataloaders
except Exception:
    get_eurosat_dataloaders = None

try:
    from src.datasets.deepglobe import DeepGlobeDataset
except Exception:
    DeepGlobeDataset = None

try:
    from src.datasets.aoi import AOITileDataset
except Exception:
    AOITileDataset = None

from src.datasets.aid import AIDDataset, AID_CLASSES

__all__ = ["get_eurosat_dataloaders", "DeepGlobeDataset", "AOITileDataset", "AIDDataset", "AID_CLASSES"]

