#pragma once
/**
 * @file spectral_index.hpp
 * @brief Spectral index computation hierarchy.
 *
 * Demonstrates: Polymorphism (virtual dispatch), inheritance, factory pattern.
 *
 * All spectral indices follow the normalized difference formula:
 *     index = (band1 - band2) / (band1 + band2 + epsilon)
 *
 * Concrete classes (NDVI, NDWI, NDBI) specify which physical bands to use.
 */

#include "types.hpp"
#include <string>
#include <memory>
#include <cmath>

namespace geoseg {

/**
 * @brief Abstract base class for normalized difference spectral indices.
 *
 * Each index operates on two spectral bands and produces a single-channel
 * output with values in [-1, 1].
 */
class SpectralIndex {
protected:
    std::string name_;        // e.g., "NDVI"
    std::string band1Name_;   // Numerator positive band (e.g., "B08" for NIR)
    std::string band2Name_;   // Numerator negative band (e.g., "B04" for Red)
    double epsilon_;          // Division-by-zero protection

public:
    SpectralIndex(const std::string& name,
                  const std::string& band1,
                  const std::string& band2,
                  double eps = 1e-6)
        : name_(name), band1Name_(band1), band2Name_(band2), epsilon_(eps) {}

    virtual ~SpectralIndex() = default;

    /**
     * @brief Compute the index from two single-band images.
     *
     * Pure virtual — each concrete index may add custom post-processing.
     *
     * @param band1 First band image (1, H, W).
     * @param band2 Second band image (1, H, W).
     * @return Single-channel index image (1, H, W), values in [-1, 1].
     */
    virtual ImageF32 compute(const ImageF32& band1, const ImageF32& band2) const = 0;

    /**
     * @brief Shared normalized difference formula computation across pixel grid.
     *
     * index = (band1 - band2) / (band1 + band2 + epsilon)
     */
    ImageF32 computeNormalizedDifference(const ImageF32& band1, const ImageF32& band2) const {
        int h = band1.height(), w = band1.width();
        ImageF32 result(1, h, w);
        float eps = static_cast<float>(epsilon_);

        for (int y = 0; y < h; ++y) {
            for (int x = 0; x < w; ++x) {
                float b1 = band1.at(0, y, x);
                float b2 = band2.at(0, y, x);
                result.at(0, y, x) = (b1 - b2) / (b1 + b2 + eps);
            }
        }
        return result;
    }

    // ─── Accessors ──────────────────────────────────────────────────────────

    const std::string& getName()      const { return name_; }
    const std::string& getBand1Name() const { return band1Name_; }
    const std::string& getBand2Name() const { return band2Name_; }

    virtual std::string getDescription() const {
        return name_ + " = (" + band1Name_ + " - " + band2Name_ +
               ") / (" + band1Name_ + " + " + band2Name_ + ")";
    }
};

// ─── Concrete Indices ───────────────────────────────────────────────────────────

/**
 * @brief Normalized Difference Vegetation Index.
 *
 * NDVI = (NIR - Red) / (NIR + Red + ε)
 * High values → dense vegetation, low/negative → bare soil/water.
 */
class NDVI : public SpectralIndex {
public:
    NDVI() : SpectralIndex("NDVI", "B08", "B04") {}

    ImageF32 compute(const ImageF32& nir, const ImageF32& red) const override {
        return computeNormalizedDifference(nir, red);
    }

    std::string getDescription() const override {
        return "NDVI (Vegetation): (NIR[B08] - Red[B04]) / (NIR + Red)";
    }
};

/**
 * @brief Normalized Difference Water Index.
 *
 * NDWI = (Green - NIR) / (Green + NIR + ε)
 * High values → water bodies, low → dry land.
 */
class NDWI : public SpectralIndex {
public:
    NDWI() : SpectralIndex("NDWI", "B03", "B08") {}

    ImageF32 compute(const ImageF32& green, const ImageF32& nir) const override {
        return computeNormalizedDifference(green, nir);
    }

    std::string getDescription() const override {
        return "NDWI (Water): (Green[B03] - NIR[B08]) / (Green + NIR)";
    }
};

/**
 * @brief Normalized Difference Built-up Index.
 *
 * NDBI = (SWIR1 - NIR) / (SWIR1 + NIR + ε)
 * High values → urban/built-up areas, low → vegetation.
 */
class NDBI : public SpectralIndex {
public:
    NDBI() : SpectralIndex("NDBI", "B11", "B08") {}

    ImageF32 compute(const ImageF32& swir1, const ImageF32& nir) const override {
        return computeNormalizedDifference(swir1, nir);
    }

    std::string getDescription() const override {
        return "NDBI (Built-up): (SWIR1[B11] - NIR[B08]) / (SWIR1 + NIR)";
    }
};

// ─── Factory ────────────────────────────────────────────────────────────────────

/**
 * @brief Factory function for creating spectral indices by name.
 *
 * Demonstrates: Factory Pattern + Polymorphism.
 *
 * @param name Index name ("NDVI", "NDWI", "NDBI").
 * @return Unique pointer to the created index.
 */
inline std::unique_ptr<SpectralIndex> createIndex(const std::string& name) {
    if (name == "NDVI") return std::make_unique<NDVI>();
    if (name == "NDWI") return std::make_unique<NDWI>();
    if (name == "NDBI") return std::make_unique<NDBI>();
    throw std::invalid_argument("Unknown spectral index: " + name);
}

void printAvailableIndices();

}  // namespace geoseg
