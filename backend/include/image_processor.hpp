#pragma once
/**
 * @file image_processor.hpp
 * @brief Abstract base class for all image processing operations.
 *
 * Demonstrates: Abstraction (pure virtual methods), virtual destructor,
 * protected members, and interface design.
 */

#include "types.hpp"
#include <string>
#include <memory>

namespace geoseg {

/**
 * @brief Abstract base class for image processors.
 *
 * All image processing operations (band math, tiling, I/O) inherit from
 * this class and implement the `process()` method. This enables polymorphic
 * usage — you can store different processors in a container and call
 * process() without knowing the concrete type.
 */
class ImageProcessor {
protected:
    std::string name_;
    int expectedChannels_;

    /**
     * @brief Validate input image dimensions.
     * @param input The image to validate.
     * @return True if the input is valid for this processor.
     */
    virtual bool validate(const ImageF32& input) const {
        if (input.empty()) {
            std::cerr << "[" << name_ << "] Error: empty input image" << std::endl;
            return false;
        }
        if (expectedChannels_ > 0 && input.channels() != expectedChannels_) {
            std::cerr << "[" << name_ << "] Error: expected " << expectedChannels_
                      << " channels, got " << input.channels() << std::endl;
            return false;
        }
        return true;
    }

public:
    /**
     * @brief Construct a named processor.
     * @param name Human-readable processor name.
     * @param expectedChannels Expected input channel count (0 = any).
     */
    ImageProcessor(const std::string& name, int expectedChannels = 0)
        : name_(name), expectedChannels_(expectedChannels) {}

    /** @brief Virtual destructor for proper cleanup in derived classes. */
    virtual ~ImageProcessor() = default;

    // Delete copy to prevent slicing
    ImageProcessor(const ImageProcessor&) = delete;
    ImageProcessor& operator=(const ImageProcessor&) = delete;

    // Allow move
    ImageProcessor(ImageProcessor&&) = default;
    ImageProcessor& operator=(ImageProcessor&&) = default;

    /**
     * @brief Process an image — pure virtual, must be overridden.
     *
     * Each derived class implements this differently:
     * - BandMathEngine: computes spectral indices
     * - TileManager: splits into tiles
     * - GeoTIFFHandler: reads/writes files
     *
     * @param input The input image to process.
     * @return Processed output image.
     */
    virtual ImageF32 process(const ImageF32& input) = 0;

    /**
     * @brief Get a human-readable description of this processor.
     * @return Info string.
     */
    virtual std::string getInfo() const {
        return name_ + " (channels=" + std::to_string(expectedChannels_) + ")";
    }

    /** @brief Get the processor name. */
    const std::string& getName() const { return name_; }
};

// Type alias for polymorphic ownership
using ProcessorPtr = std::unique_ptr<ImageProcessor>;

}  // namespace geoseg
