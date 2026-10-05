"""Dataset wrappers for EuroSAT, DeepGlobe, custom AOI, and AID aerial scene dataset."""

from src.datasets.eurosat import get_eurosat_dataloaders
from src.datasets.deepglobe import DeepGlobeDataset
from src.datasets.aoi import AOITileDataset
from src.datasets.aid import AIDDataset, AID_CLASSES

__all__ = ["get_eurosat_dataloaders", "DeepGlobeDataset", "AOITileDataset", "AIDDataset", "AID_CLASSES"]

