#pragma once
/**
 * @file band_math.hpp
 * @brief BandMathEngine — computes spectral indices from multi-band images.
 *
 * Demonstrates: Inheritance from ImageProcessor, Encapsulation of band ordering,
 * polymorphic usage of SpectralIndex objects.
 */

#include "image_processor.hpp"
#include "spectral_index.hpp"
#include <vector>
#include <string>
#include <map>
#include <memory>

namespace geoseg {

/**
 * @brief Engine for computing spectral indices from Sentinel-2 imagery.
 *
 * Inherits from ImageProcessor. Encapsulates band ordering to prevent the
 * #1 silent bug in multispectral pipelines — band order mismatches.
 *
 * Usage:
 * @code
 *     BandMathEngine engine({"B02","B03","B04","B05","B06","B07","B08","B8A","B09","B10","B11","B12"});
 *     ImageF32 indices = engine.computeAllIndices(multibandImage);
 *     // indices has 3 channels: [NDVI, NDWI, NDBI]
 * @endcode
 */
class BandMathEngine : public ImageProcessor {
private:
    std::vector<std::string> bandOrder_;
    std::map<std::string, int> bandIndex_;
    std::vector<std::unique_ptr<SpectralIndex>> indices_;

    /** @brief Build the band name → channel index lookup map. */
    void buildBandIndex() {
        bandIndex_.clear();
        for (size_t i = 0; i < bandOrder_.size(); ++i) {
            bandIndex_[bandOrder_[i]] = static_cast<int>(i);
        }
    }

    /** @brief Look up the channel index for a band name. */
    int getBandChannel(const std::string& bandName) const {
        auto it = bandIndex_.find(bandName);
        if (it == bandIndex_.end()) {
            throw std::invalid_argument(
                "Band '" + bandName + "' not found in band order. "
                "Available: " + getBandOrderString()
            );
        }
        return it->second;
    }

    std::string getBandOrderString() const {
        std::string result = "[";
        for (size_t i = 0; i < bandOrder_.size(); ++i) {
            if (i > 0) result += ", ";
            result += bandOrder_[i];
        }
        return result + "]";
    }

public:
    /**
     * @brief Construct a BandMathEngine with explicit band ordering.
     *
     * @param bandOrder Ordered list of Sentinel-2 band names matching the
     *                  channel order of input images. MUST match exactly.
     */
    explicit BandMathEngine(const std::vector<std::string>& bandOrder)
        : ImageProcessor("BandMathEngine", static_cast<int>(bandOrder.size())),
          bandOrder_(bandOrder) {
        buildBandIndex();

        // Register all supported indices
        indices_.push_back(std::make_unique<NDVI>());
        indices_.push_back(std::make_unique<NDWI>());
        indices_.push_back(std::make_unique<NDBI>());
    }

    /**
     * @brief Compute a single spectral index by name.
     *
     * @param input Multi-band image (C, H, W).
     * @param indexName One of "NDVI", "NDWI", "NDBI".
     * @return Single-channel index image (1, H, W).
     */
    ImageF32 computeIndex(const ImageF32& input, const std::string& indexName) const {
        for (const auto& idx : indices_) {
            if (idx->getName() == indexName) {
                int ch1 = getBandChannel(idx->getBand1Name());
                int ch2 = getBandChannel(idx->getBand2Name());
                return idx->compute(input.band(ch1), input.band(ch2));
            }
        }
        throw std::invalid_argument("Unknown spectral index: " + indexName);
    }

    /**
     * @brief Compute NDVI from the multi-band image.
     * @param input Multi-band image (C, H, W) with bands matching bandOrder.
     * @return Single-channel NDVI (1, H, W).
     */
    ImageF32 computeNDVI(const ImageF32& input) const {
        return computeIndex(input, "NDVI");
    }

    /**
     * @brief Compute NDWI from the multi-band image.
     */
    ImageF32 computeNDWI(const ImageF32& input) const {
        return computeIndex(input, "NDWI");
    }

    /**
     * @brief Compute NDBI from the multi-band image.
     */
    ImageF32 computeNDBI(const ImageF32& input) const {
        return computeIndex(input, "NDBI");
    }

    /**
     * @brief Compute all spectral indices and stack them.
     *
     * @param input Multi-band image (C, H, W).
     * @return 3-channel image (3, H, W): [NDVI, NDWI, NDBI].
     */
    ImageF32 computeAllIndices(const ImageF32& input) const {
        ImageF32 ndvi = computeNDVI(input);
        ImageF32 ndwi = computeNDWI(input);
        ImageF32 ndbi = computeNDBI(input);

        // Stack: concatenate along channel axis
        return ndvi.concatenate(ndwi).concatenate(ndbi);
    }

    /**
     * @brief Build a full multispectral input: raw bands + indices.
     *
     * @param input Multi-band image (C, H, W).
     * @return Image with (C+3, H, W): original bands + [NDVI, NDWI, NDBI].
     */
    ImageF32 buildMultispectralInput(const ImageF32& input) const {
        ImageF32 indices = computeAllIndices(input);
        return input.concatenate(indices);
    }

    /**
     * @brief Implements ImageProcessor::process().
     *
     * Default behavior: compute all indices and concatenate with input.
     */
    ImageF32 process(const ImageF32& input) override {
        if (!validate(input)) {
            throw std::invalid_argument("Input validation failed for BandMathEngine");
        }
        return buildMultispectralInput(input);
    }

    std::string getInfo() const override {
        return "BandMathEngine[bands=" + getBandOrderString() +
               ", indices=NDVI,NDWI,NDBI]";
    }

    /** @brief Get the current band order. */
    const std::vector<std::string>& getBandOrder() const { return bandOrder_; }

    /** @brief Get the number of registered indices. */
    size_t getIndexCount() const { return indices_.size(); }
};

/**
 * @brief Normalize raw Sentinel-2 reflectance values to [0, 1].
 */
ImageF32 normalizeReflectance(const ImageF32& input, float scale = 10000.0f);

/**
 * @brief Validate that required bands exist in the band order.
 */
bool validateBandOrder(
    const std::vector<std::string>& bandOrder,
    const std::vector<std::string>& required
);

}  // namespace geoseg
