#pragma once
/**
 * @file geotiff_handler.hpp
 * @brief GeoTIFFHandler — read/write GeoTIFF files with RAII.
 *
 * Demonstrates: RAII (resource acquisition is initialization),
 * Inheritance from ImageProcessor, Encapsulation of file state.
 *
 * Note: This is a simplified implementation. Full GDAL integration
 * requires linking against the GDAL library. This version provides
 * the OOP structure and can work with raw binary files for demonstration.
 */

#include "image_processor.hpp"
#include "types.hpp"
#include <string>
#include <fstream>
#include <iostream>
#include <stdexcept>

namespace geoseg {

/**
 * @brief GeoTIFF file handler with RAII resource management.
 *
 * Inherits from ImageProcessor. Manages file handles via
 * constructor/destructor (RAII pattern).
 *
 * When compiled with GDAL support, uses the GDAL C++ API.
 * Without GDAL, provides a simplified binary read/write for demonstration.
 */
class GeoTIFFHandler : public ImageProcessor {
private:
    std::string filePath_;
    RasterMetadata metadata_;
    bool isOpen_;

    // RAII: file handle would be managed here
    // With full GDAL: GDALDataset* dataset_;

public:
    /**
     * @brief Construct a handler for a specific file path.
     *
     * RAII: the constructor acquires the resource (opens the file),
     * the destructor releases it (closes the file).
     *
     * @param filePath Path to the GeoTIFF file.
     */
    explicit GeoTIFFHandler(const std::string& filePath)
        : ImageProcessor("GeoTIFFHandler"),
          filePath_(filePath),
          isOpen_(false) {}

    /**
     * @brief RAII destructor — ensures file handles are closed.
     */
    ~GeoTIFFHandler() override {
        close();
    }

    // Delete copy (RAII — no sharing of file handles)
    GeoTIFFHandler(const GeoTIFFHandler&) = delete;
    GeoTIFFHandler& operator=(const GeoTIFFHandler&) = delete;

    // ─── File Operations ────────────────────────────────────────────────────

    /**
     * @brief Open the GeoTIFF file and read metadata.
     *
     * In a full implementation, this would call GDALOpen().
     * Here we demonstrate the RAII pattern and metadata extraction.
     */
    bool open() {
        if (isOpen_) return true;

        std::ifstream file(filePath_, std::ios::binary);
        if (!file.is_open()) {
            std::cerr << "[GeoTIFFHandler] Cannot open: " << filePath_ << std::endl;
            return false;
        }

        // Read basic file info (simplified — full GDAL would parse the TIFF structure)
        file.seekg(0, std::ios::end);
        size_t fileSize = file.tellg();
        file.close();

        if (fileSize == 0) {
            std::cerr << "[GeoTIFFHandler] Empty file: " << filePath_ << std::endl;
            return false;
        }

        isOpen_ = true;
        std::cout << "[GeoTIFFHandler] Opened: " << filePath_
                  << " (" << fileSize << " bytes)" << std::endl;

        return true;
    }

    /**
     * @brief Close the file handle (RAII cleanup).
     */
    void close() {
        if (isOpen_) {
            isOpen_ = false;
            // With GDAL: GDALClose(dataset_);
        }
    }

    /**
     * @brief Read the raster data into an Image.
     *
     * @return Multi-band image (C, H, W).
     */
    ImageF32 read() {
        if (!isOpen_ && !open()) {
            throw std::runtime_error("Cannot read: file not open");
        }

        // Simplified: create a placeholder image
        // Full GDAL implementation would use GDALRasterBand::RasterIO()
        std::cout << "[GeoTIFFHandler] Reading raster data from: "
                  << filePath_ << std::endl;

        // Return metadata-sized image (would be populated by GDAL)
        return ImageF32(
            metadata_.channels > 0 ? metadata_.channels : 1,
            metadata_.height > 0 ? metadata_.height : 1,
            metadata_.width > 0 ? metadata_.width : 1
        );
    }

    /**
     * @brief Write an image to a GeoTIFF file.
     *
     * Preserves CRS and geotransform from the metadata.
     *
     * @param image The image to write.
     * @param outputPath Output file path.
     */
    void write(const ImageF32& image, const std::string& outputPath) const {
        std::cout << "[GeoTIFFHandler] Writing " << image
                  << " to: " << outputPath << std::endl;

        // Full GDAL implementation:
        // GDALDriver* driver = GetGDALDriverManager()->GetDriverByName("GTiff");
        // GDALDataset* outDS = driver->Create(outputPath.c_str(), ...);
        // outDS->SetProjection(metadata_.crs);
        // outDS->SetGeoTransform(metadata_.geoTransform.data());
        // for each band: outDS->GetRasterBand(i)->RasterIO(GF_Write, ...);
        // GDALClose(outDS);

        // Simplified: write raw binary
        std::ofstream file(outputPath, std::ios::binary);
        if (!file.is_open()) {
            throw std::runtime_error("Cannot write to: " + outputPath);
        }

        const auto& data = image.data();
        file.write(reinterpret_cast<const char*>(data.data()),
                   data.size() * sizeof(PixelF32));
        file.close();

        std::cout << "[GeoTIFFHandler] Written successfully." << std::endl;
    }

    /**
     * @brief Write a uint8 classification result.
     */
    void writeClassification(const ImageU8& image, const std::string& outputPath) const {
        std::cout << "[GeoTIFFHandler] Writing classification " << image
                  << " to: " << outputPath << std::endl;

        std::ofstream file(outputPath, std::ios::binary);
        if (!file.is_open()) {
            throw std::runtime_error("Cannot write to: " + outputPath);
        }

        const auto& data = image.data();
        file.write(reinterpret_cast<const char*>(data.data()),
                   data.size() * sizeof(PixelU8));
        file.close();
    }

    // ─── Metadata ───────────────────────────────────────────────────────────

    /**
     * @brief Get raster metadata.
     */
    const RasterMetadata& getMetadata() const { return metadata_; }

    /**
     * @brief Set metadata (for creating new files).
     */
    void setMetadata(const RasterMetadata& meta) { metadata_ = meta; }

    bool isFileOpen() const { return isOpen_; }
    const std::string& getFilePath() const { return filePath_; }

    // ─── ImageProcessor Interface ───────────────────────────────────────────

    /**
     * @brief Process: reads the file and returns the image data.
     */
    ImageF32 process(const ImageF32& /*input*/) override {
        return read();
    }

    std::string getInfo() const override {
        return "GeoTIFFHandler[" + filePath_ + ", " +
               (isOpen_ ? "open" : "closed") + "]";
    }
};

bool fileExists(const std::string& path);
size_t getFileSize(const std::string& path);
void printGeoTIFFInfo(const std::string& path);

}  // namespace geoseg
