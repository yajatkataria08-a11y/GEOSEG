/**
 * @file main.cpp
 * @brief Standalone CLI demonstrating all OOP classes.
 *
 * Creates synthetic multi-band data, computes spectral indices,
 * tiles/stitches, and demonstrates polymorphism.
 */

#include "include/types.hpp"
#include "include/image_processor.hpp"
#include "include/spectral_index.hpp"
#include "include/band_math.hpp"
#include "include/tile_manager.hpp"
#include "include/geotiff_handler.hpp"

#include <iostream>
#include <vector>
#include <memory>
#include <cmath>

using namespace geoseg;

/**
 * @brief Create a synthetic Sentinel-2 image for testing.
 *
 * Generates a 12-band image with realistic-ish patterns:
 * - Vegetation patch (high NIR, low Red)
 * - Water patch (high Green, low NIR)
 * - Urban patch (high SWIR, moderate NIR)
 */
ImageF32 createSyntheticImage(int height, int width) {
    // 12 bands: B02-B12 (without B01 Coastal)
    ImageF32 image(12, height, width);

    for (int y = 0; y < height; ++y) {
        for (int x = 0; x < width; ++x) {
            // Determine land cover type based on position
            float region = 3.0f * y / height;

            float blue, green, red, nir, swir1;

            if (region < 1.0f) {
                // Vegetation: high NIR, low visible
                blue  = 0.03f; green = 0.06f; red = 0.04f;
                nir   = 0.45f; swir1 = 0.15f;
            } else if (region < 2.0f) {
                // Water: high blue/green, very low NIR
                blue  = 0.10f; green = 0.12f; red = 0.08f;
                nir   = 0.02f; swir1 = 0.01f;
            } else {
                // Urban: moderate all, high SWIR
                blue  = 0.12f; green = 0.12f; red = 0.14f;
                nir   = 0.20f; swir1 = 0.30f;
            }

            // Add some noise
            float noise = 0.01f * sinf(x * 0.1f + y * 0.1f);

            // Set bands: B02=Blue, B03=Green, B04=Red, ... B08=NIR, ... B11=SWIR1
            image.at(0,  y, x) = blue + noise;     // B02 Blue
            image.at(1,  y, x) = green + noise;    // B03 Green
            image.at(2,  y, x) = red + noise;      // B04 Red
            image.at(3,  y, x) = 0.10f + noise;    // B05 Red Edge 1
            image.at(4,  y, x) = 0.15f + noise;    // B06 Red Edge 2
            image.at(5,  y, x) = 0.20f + noise;    // B07 Red Edge 3
            image.at(6,  y, x) = nir + noise;      // B08 NIR
            image.at(7,  y, x) = nir * 0.9f;       // B8A Narrow NIR
            image.at(8,  y, x) = 0.01f;            // B09 Water Vapor
            image.at(9,  y, x) = 0.001f;           // B10 Cirrus
            image.at(10, y, x) = swir1 + noise;    // B11 SWIR1
            image.at(11, y, x) = swir1 * 0.8f;     // B12 SWIR2
        }
    }

    return image;
}

int main() {
    std::cout << "═══════════════════════════════════════════════════════" << std::endl;
    std::cout << "  GeoSeg C++ Backend — OOP Demonstration" << std::endl;
    std::cout << "═══════════════════════════════════════════════════════" << std::endl;

    // ─── 1. Demonstrate Templates & Operator Overloading ────────────────
    std::cout << "\n── 1. Image<T> Template & Operators ──\n" << std::endl;

    ImageF32 img1(3, 4, 4);
    img1.fill(1.0f);
    std::cout << "img1: " << img1 << std::endl;

    ImageF32 img2(3, 4, 4);
    img2.fill(2.0f);
    std::cout << "img2: " << img2 << std::endl;

    ImageF32 sum = img1 + img2;
    std::cout << "img1 + img2: pixel[0,0,0] = " << sum.at(0, 0, 0) << std::endl;

    ImageF32 diff = img2 - img1;
    std::cout << "img2 - img1: pixel[0,0,0] = " << diff.at(0, 0, 0) << std::endl;

    ImageF32 scaled = img1 * 3.0f;
    std::cout << "img1 * 3.0: pixel[0,0,0] = " << scaled.at(0, 0, 0) << std::endl;

    // ─── 2. Demonstrate Polymorphism (SpectralIndex hierarchy) ──────────
    std::cout << "\n── 2. Polymorphism — SpectralIndex ──\n" << std::endl;

    // Factory creates different concrete types through the same interface
    std::vector<std::unique_ptr<SpectralIndex>> indices;
    indices.push_back(createIndex("NDVI"));
    indices.push_back(createIndex("NDWI"));
    indices.push_back(createIndex("NDBI"));

    for (const auto& idx : indices) {
        std::cout << "  " << idx->getDescription() << std::endl;
    }

    // Create synthetic bands for testing
    ImageF32 nir(1, 4, 4);   nir.fill(0.45f);   // High NIR = vegetation
    ImageF32 red(1, 4, 4);   red.fill(0.04f);   // Low Red = vegetation
    ImageF32 green(1, 4, 4); green.fill(0.06f);
    ImageF32 swir(1, 4, 4);  swir.fill(0.15f);

    // Polymorphic compute — same interface, different implementations
    ImageF32 ndvi_result = indices[0]->compute(nir, red);
    ImageF32 ndwi_result = indices[1]->compute(green, nir);
    ImageF32 ndbi_result = indices[2]->compute(swir, nir);

    std::cout << "\n  NDVI (vegetation pixel): " << ndvi_result.at(0, 0, 0)
              << "  (expected ~0.84)" << std::endl;
    std::cout << "  NDWI (vegetation pixel): " << ndwi_result.at(0, 0, 0)
              << "  (expected ~-0.76)" << std::endl;
    std::cout << "  NDBI (vegetation pixel): " << ndbi_result.at(0, 0, 0)
              << "  (expected ~-0.50)" << std::endl;

    // ─── 3. Demonstrate Inheritance & Encapsulation (BandMathEngine) ────
    std::cout << "\n── 3. Inheritance & Encapsulation — BandMathEngine ──\n" << std::endl;

    std::vector<std::string> bandOrder = {
        "B02", "B03", "B04", "B05", "B06", "B07",
        "B08", "B8A", "B09", "B10", "B11", "B12"
    };

    BandMathEngine engine(bandOrder);
    std::cout << engine.getInfo() << std::endl;

    // Create synthetic Sentinel-2 image
    ImageF32 s2Image = createSyntheticImage(64, 64);
    std::cout << "Input: " << s2Image << std::endl;

    // Compute all indices
    ImageF32 allIndices = engine.computeAllIndices(s2Image);
    std::cout << "Indices: " << allIndices << " (NDVI, NDWI, NDBI)" << std::endl;

    // Build full multispectral input (12 bands + 3 indices = 15 channels)
    ImageF32 fullInput = engine.buildMultispectralInput(s2Image);
    std::cout << "Full input: " << fullInput << " (12 bands + 3 indices)" << std::endl;

    // Sample values from different regions
    std::cout << "\n  Vegetation region (y=5):" << std::endl;
    std::cout << "    NDVI=" << allIndices.at(0, 5, 5)
              << "  NDWI=" << allIndices.at(1, 5, 5)
              << "  NDBI=" << allIndices.at(2, 5, 5) << std::endl;

    std::cout << "  Water region (y=32):" << std::endl;
    std::cout << "    NDVI=" << allIndices.at(0, 32, 5)
              << "  NDWI=" << allIndices.at(1, 32, 5)
              << "  NDBI=" << allIndices.at(2, 32, 5) << std::endl;

    std::cout << "  Urban region (y=55):" << std::endl;
    std::cout << "    NDVI=" << allIndices.at(0, 55, 5)
              << "  NDWI=" << allIndices.at(1, 55, 5)
              << "  NDBI=" << allIndices.at(2, 55, 5) << std::endl;

    // ─── 4. Demonstrate Tiling (TileManager) ────────────────────────────
    std::cout << "\n── 4. TileManager — Tiling & Stitching ──\n" << std::endl;

    TileManager tiler(32, 4);  // 32×32 tiles, 4px overlap
    std::cout << tiler.getInfo() << std::endl;

    auto tiles = tiler.splitIntoTiles(s2Image);
    std::cout << "Split " << s2Image << " into " << tiles.size() << " tiles" << std::endl;

    for (size_t i = 0; i < std::min(tiles.size(), size_t(3)); ++i) {
        std::cout << "  Tile " << i << ": origin=("
                  << tiles[i].originX << "," << tiles[i].originY
                  << ") actual=" << tiles[i].actualWidth << "×" << tiles[i].actualHeight
                  << std::endl;
    }
    if (tiles.size() > 3) std::cout << "  ... (" << tiles.size() - 3 << " more)" << std::endl;

    // ─── 5. Demonstrate Abstraction (Polymorphic processor vector) ──────
    std::cout << "\n── 5. Abstraction — Polymorphic Processors ──\n" << std::endl;

    std::vector<ProcessorPtr> processors;
    processors.push_back(std::make_unique<BandMathEngine>(bandOrder));
    processors.push_back(std::make_unique<TileManager>(32, 4));

    for (const auto& proc : processors) {
        std::cout << "  Processor: " << proc->getInfo() << std::endl;
        // Can call process() on any processor without knowing the concrete type
    }

    // ─── 6. Demonstrate RAII (GeoTIFFHandler) ───────────────────────────
    std::cout << "\n── 6. RAII — GeoTIFFHandler ──\n" << std::endl;

    {
        GeoTIFFHandler handler("test_output.bin");
        std::cout << handler.getInfo() << std::endl;

        // Set metadata
        RasterMetadata meta;
        meta.width = 64;
        meta.height = 64;
        meta.channels = 12;
        meta.crs = "EPSG:32643";
        handler.setMetadata(meta);

        // Write the synthetic image
        handler.write(s2Image, "test_output.bin");
        std::cout << "  Metadata: " << meta.toString() << std::endl;

        // Handler destructor will close automatically (RAII)
    }
    std::cout << "  GeoTIFFHandler destroyed — RAII cleanup complete." << std::endl;

    // ─── Summary ────────────────────────────────────────────────────────
    std::cout << "\n═══════════════════════════════════════════════════════" << std::endl;
    std::cout << "  OOP Concepts Demonstrated:" << std::endl;
    std::cout << "    ✓ Templates       (Image<T>)" << std::endl;
    std::cout << "    ✓ Operator Overload (+, -, /, *)" << std::endl;
    std::cout << "    ✓ Abstraction     (ImageProcessor pure virtual)" << std::endl;
    std::cout << "    ✓ Inheritance     (BandMathEngine, TileManager)" << std::endl;
    std::cout << "    ✓ Polymorphism    (SpectralIndex factory)" << std::endl;
    std::cout << "    ✓ Encapsulation   (private data, public interface)" << std::endl;
    std::cout << "    ✓ RAII            (GeoTIFFHandler)" << std::endl;
    std::cout << "═══════════════════════════════════════════════════════" << std::endl;

    return 0;
}
