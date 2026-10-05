/**
 * @file tile_manager.cpp
 * @brief TileManager implementation.
 *
 * The core logic is header-only. This file provides standalone
 * utility functions for tiling operations.
 */

#include "../include/tile_manager.hpp"
#include <iostream>

namespace geoseg {

/**
 * @brief Print tile grid info for a given image size and tile config.
 */
void printTileGridInfo(int imageH, int imageW, int tileSize, int overlap) {
    TileManager manager(tileSize, overlap);
    int count = manager.getTileCount(imageH, imageW);

    std::cout << "Tile Grid Info:" << std::endl;
    std::cout << "  Image:    " << imageW << " × " << imageH << std::endl;
    std::cout << "  Tile:     " << tileSize << " × " << tileSize << std::endl;
    std::cout << "  Overlap:  " << overlap << " px" << std::endl;
    std::cout << "  Stride:   " << manager.getStride() << " px" << std::endl;
    std::cout << "  Tiles:    " << count << std::endl;
}

}  // namespace geoseg
