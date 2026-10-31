"""Spatial-msiPL research implementation.

The convenience exports are loaded only when requested so summary scripts can import
lightweight submodules without requiring the HDF5 training dependencies.
"""

__all__ = ["H5SpatialContextDataset", "tic_normalize"]


def __getattr__(name):
    if name in __all__:
        from . import preprocessing

        return getattr(preprocessing, name)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
