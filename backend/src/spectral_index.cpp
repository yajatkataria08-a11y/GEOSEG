/**
 * @file spectral_index.cpp
 * @brief Implementation details for spectral index utilities.
 *
 * The core compute() logic is in the header (inline in each class).
 * This file provides additional utility functions.
 */

#include "../include/spectral_index.hpp"
#include <iostream>
#include <vector>

namespace geoseg {

/**
 * @brief Print info about all available spectral indices.
 */
void printAvailableIndices() {
    std::vector<std::string> indexNames = {"NDVI", "NDWI", "NDBI"};

    std::cout << "Available Spectral Indices:" << std::endl;
    std::cout << "─────────────────────────────────────────────" << std::endl;

    for (const auto& name : indexNames) {
        auto index = createIndex(name);
        std::cout << "  " << index->getDescription() << std::endl;
    }

    std::cout << "─────────────────────────────────────────────" << std::endl;
}

}  // namespace geoseg
