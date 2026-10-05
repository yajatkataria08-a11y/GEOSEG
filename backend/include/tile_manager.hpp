#pragma once
/**
 * @file tile_manager.hpp
 * @brief TileManager — sliding-window image tiling and stitching.
 *
 * Demonstrates: Inheritance, Encapsulation of tiling parameters,
 * container management for tiles.
 */

#include "image_processor.hpp"
#include "types.hpp"
#include <vector>
#include <algorithm>

namespace geoseg {

/**
 * @brief Manages splitting large images into overlapping tiles and stitching them back.
 *
 * Inherits from ImageProcessor. Used during inference to handle images
 * larger than the model's training patch size.
 *
 * Usage:
 * @code
 *     TileManager manager(512, 32);
 *     auto tiles = manager.splitIntoTiles(largeImage);
 *     // ... run inference on each tile ...
 *     ImageU8 result = manager.stitchTiles(predictedTiles, height, width);
 * @endcode
 */
class TileManager : public ImageProcessor {
private:
    int tileSize_;
    int overlap_;
    int stride_;

public:
    /**
     * @brief Construct a TileManager.
     *
     * @param tileSize Size of each square tile (pixels).
     * @param overlap Overlap between adjacent tiles (pixels).
     */
    TileManager(int tileSize = 512, int overlap = 32)
        : ImageProcessor("TileManager"),
          tileSize_(tileSize),
          overlap_(overlap),
          stride_(tileSize - overlap) {
        if (tileSize <= 0) throw std::invalid_argument("tileSize must be > 0");
        if (overlap < 0)   throw std::invalid_argument("overlap must be >= 0");
        if (overlap >= tileSize) throw std::invalid_argument("overlap must be < tileSize");
    }

    // ─── Tiling ─────────────────────────────────────────────────────────────

    /**
     * @brief Split an image into overlapping tiles.
     *
     * Edge tiles that are smaller than tileSize are zero-padded.
     * The original dimensions are stored in each Tile for unpadding.
     *
     * @param image Input image (C, H, W).
     * @return Vector of tiles with position metadata.
     */
    std::vector<Tile> splitIntoTiles(const ImageF32& image) const {
        int H = image.height();
        int W = image.width();
        std::vector<Tile> tiles;
        tiles.reserve(getTileCount(H, W));

        for (int y = 0; y < H; y += stride_) {
            for (int x = 0; x < W; x += stride_) {
                int tileH = std::min(tileSize_, H - y);
                int tileW = std::min(tileSize_, W - x);

                // Crop the tile from the source image
                ImageF32 tileData = image.crop(y, x, tileH, tileW);

                // Pad if smaller than tileSize
                if (tileH < tileSize_ || tileW < tileSize_) {
                    tileData = tileData.pad(tileSize_, tileSize_);
                }

                tiles.emplace_back(tileData, x, y, tileW, tileH);
            }
        }

        return tiles;
    }

    /**
     * @brief Stitch predicted tiles back into a full-size image.
     *
     * Uses simple overwrite strategy — each tile writes its prediction
     * at its recorded position, cropped to its actual (unpadded) size.
     *
     * @param tiles Vector of tiles with prediction data (1-channel class indices).
     * @param outputH Full image height.
     * @param outputW Full image width.
     * @return Stitched single-channel image.
     */
    ImageU8 stitchTiles(const std::vector<Tile>& tiles, int outputH, int outputW) const {
        ImageU8 result(1, outputH, outputW);

        for (const auto& tile : tiles) {
            for (int y = 0; y < tile.actualHeight; ++y) {
                for (int x = 0; x < tile.actualWidth; ++x) {
                    int globalY = tile.originY + y;
                    int globalX = tile.originX + x;
                    if (globalY < outputH && globalX < outputW) {
                        // Convert float prediction to uint8 class index
                        result.at(0, globalY, globalX) =
                            static_cast<PixelU8>(tile.data.at(0, y, x));
                    }
                }
            }
        }

        return result;
    }

    // ─── Queries ────────────────────────────────────────────────────────────

    /**
     * @brief Calculate how many tiles an image of given size will produce.
     */
    int getTileCount(int height, int width) const {
        int tilesY = (height + stride_ - 1) / stride_;
        int tilesX = (width  + stride_ - 1) / stride_;
        return tilesY * tilesX;
    }

    int getTileSize() const { return tileSize_; }
    int getOverlap()  const { return overlap_; }
    int getStride()   const { return stride_; }

    // ─── ImageProcessor Interface ───────────────────────────────────────────

    /**
     * @brief Process implementation — returns the first tile (for testing).
     *
     * In practice, use splitIntoTiles() and stitchTiles() directly.
     */
    ImageF32 process(const ImageF32& input) override {
        auto tiles = splitIntoTiles(input);
        if (tiles.empty()) return ImageF32();
        return tiles[0].data;
    }

    std::string getInfo() const override {
        return "TileManager[size=" + std::to_string(tileSize_) +
               ", overlap=" + std::to_string(overlap_) +
               ", stride=" + std::to_string(stride_) + "]";
    }
};

void printTileGridInfo(int width, int height, int tileSize, int overlap);

}  // namespace geoseg
