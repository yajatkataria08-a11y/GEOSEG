from setuptools import setup, find_packages

setup(
    name="geoseg",
    version="0.1.0",
    description="Satellite Land Cover Segmentation with Multispectral Sentinel-2 Imagery",
    author="Yajat",
    packages=find_packages(),
    python_requires=">=3.10",
    install_requires=[
        "torch>=2.1.0",
        "torchvision>=0.16.0",
        "torchgeo>=0.5.0",
        "segmentation-models-pytorch>=0.3.3",
        "torchmetrics>=1.2.0",
        "rasterio>=1.3.0",
        "kornia>=0.7.0",
        "pillow>=9.5.0",
        "fastapi>=0.100.0",
        "uvicorn[standard]>=0.20.0",
        "pydantic>=2.0.0",
        "python-multipart>=0.0.6",
        "tensorboard>=2.15.0",
        "matplotlib>=3.8.0",
        "pyyaml>=6.0",
        "numpy>=1.24.0,<2.0.0",
        "tqdm>=4.66.0",
    ],
    extras_require={
        "gee": ["earthengine-api>=0.1.380", "geemap>=0.30.0"],
    },
)
