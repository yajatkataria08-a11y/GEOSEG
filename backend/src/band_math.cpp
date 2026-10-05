/**
 * @file band_math.cpp
 * @brief BandMathEngine implementation.
 *
 * The main logic is header-only. This file provides standalone
 * utility functions for band math.
 */

#include "../include/band_math.hpp"
#include <iostream>

namespace geoseg {

/**
 * @brief Normalize raw Sentinel-2 reflectance values to [0, 1].
 *
 * @param input Raw reflectance image (values typically 0–10000).
 * @param scale Reflectance scale factor (default 10000).
 * @return Normalized image.
 */
ImageF32 normalizeReflectance(const ImageF32& input, float scale) {
    return input / scale;
}

/**
 * @brief Validate that required bands exist in the band order.
 *
 * @param bandOrder Current band ordering.
 * @param required Required band names.
 * @return True if all required bands are present.
 */
bool validateBandOrder(
    const std::vector<std::string>& bandOrder,
    const std::vector<std::string>& required
) {
    std::map<std::string, bool> present;
    for (const auto& band : bandOrder) {
        present[band] = true;
    }

    bool allPresent = true;
    for (const auto& req : required) {
        if (present.find(req) == present.end()) {
            std::cerr << "[BandMath] Missing required band: " << req << std::endl;
            allPresent = false;
        }
    }

    return allPresent;
}

}  // namespace geoseg
