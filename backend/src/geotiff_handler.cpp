/**
 * @file geotiff_handler.cpp
 * @brief GeoTIFFHandler implementation.
 *
 * The core logic is header-only. This file provides standalone
 * utility functions for GeoTIFF operations.
 */

#include "../include/geotiff_handler.hpp"
#include <iostream>
#include <fstream>

namespace geoseg {

/**
 * @brief Check if a file exists and is readable.
 */
bool fileExists(const std::string& path) {
    std::ifstream f(path.c_str());
    return f.good();
}

/**
 * @brief Get file size in bytes.
 */
size_t getFileSize(const std::string& path) {
    std::ifstream f(path.c_str(), std::ios::binary | std::ios::ate);
    if (!f.is_open()) return 0;
    return static_cast<size_t>(f.tellg());
}

/**
 * @brief Print metadata about a GeoTIFF file.
 */
void printGeoTIFFInfo(const std::string& path) {
    if (!fileExists(path)) {
        std::cerr << "File not found: " << path << std::endl;
        return;
    }

    size_t size = getFileSize(path);
    std::cout << "GeoTIFF Info:" << std::endl;
    std::cout << "  Path: " << path << std::endl;
    std::cout << "  Size: " << size << " bytes ("
              << (size / 1024 / 1024) << " MB)" << std::endl;
}

}  // namespace geoseg
