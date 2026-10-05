#pragma once
/**
 * @file types.hpp
 * @brief Core data types for the GeoSeg image processing library.
 *
 * Demonstrates: Templates, Operator Overloading, Encapsulation.
 */

#include <vector>
#include <string>
#include <stdexcept>
#include <cmath>
#include <iostream>
#include <algorithm>
#include <cassert>
#include <typeinfo>
#include <type_traits>

namespace geoseg {

// ─── Pixel Types ────────────────────────────────────────────────────────────────

using PixelU16  = uint16_t;   // Raw Sentinel-2 reflectance (0–10000)
using PixelF32  = float;      // Normalized reflectance (0–1)
using PixelU8   = uint8_t;    // Classification output (class indices)

// ─── BoundingBox ────────────────────────────────────────────────────────────────

/**
 * @brief Geographic bounding box in WGS84 coordinates.
 */
struct BoundingBox {
    double west;
    double south;
    double east;
    double north;

    BoundingBox() : west(0), south(0), east(0), north(0) {}
    BoundingBox(double w, double s, double e, double n)
        : west(w), south(s), east(e), north(n) {}

    double width()  const { return east - west; }
    double height() const { return north - south; }

    bool contains(double lon, double lat) const {
        return lon >= west && lon <= east && lat >= south && lat <= north;
    }

    friend std::ostream& operator<<(std::ostream& os, const BoundingBox& bb) {
        os << "BBox[" << bb.west << ", " << bb.south
           << " → " << bb.east << ", " << bb.north << "]";
        return os;
    }
};

// ─── Metadata ───────────────────────────────────────────────────────────────────

/**
 * @brief Raster metadata — CRS, geotransform, band names.
 */
struct RasterMetadata {
    int width     = 0;
    int height    = 0;
    int channels  = 0;
    std::string crs = "EPSG:4326";
    std::vector<double> geoTransform = {0, 1, 0, 0, 0, -1};  // GDAL-style
    std::vector<std::string> bandNames;

    std::string toString() const {
        return "Raster[" + std::to_string(width) + "×" +
               std::to_string(height) + " (" +
               std::to_string(channels) + " bands), " + crs + "]";
    }
};

// ─── Image<T> Template ──────────────────────────────────────────────────────────

/**
 * @brief Multi-band image container with element-wise arithmetic.
 *
 * Stores pixel data as a flat vector in CHW (channels × height × width) order.
 * Supports operator overloading for band math operations.
 *
 * @tparam T Pixel data type (uint16_t, float, uint8_t).
 */
template <typename T>
class Image {
private:
    int channels_;
    int height_;
    int width_;
    std::vector<T> data_;  // Flat CHW layout

public:
    // ─── Constructors ───────────────────────────────────────────────────────

    Image() : channels_(0), height_(0), width_(0) {}

    Image(int channels, int height, int width)
        : channels_(channels), height_(height), width_(width),
          data_(static_cast<size_t>(channels) * height * width, T{0}) {}

    Image(int channels, int height, int width, const std::vector<T>& data)
        : channels_(channels), height_(height), width_(width), data_(data) {
        if (data_.size() != static_cast<size_t>(channels) * height * width) {
            throw std::invalid_argument(
                "Data size mismatch: expected " +
                std::to_string(static_cast<size_t>(channels) * height * width) +
                ", got " + std::to_string(data_.size())
            );
        }
    }

    // ─── Accessors (Encapsulation) ──────────────────────────────────────────

    int channels() const { return channels_; }
    int height()   const { return height_; }
    int width()    const { return width_; }
    size_t size()  const { return data_.size(); }
    bool empty()   const { return data_.empty(); }

    const std::vector<T>& data() const { return data_; }
    std::vector<T>& data() { return data_; }

    // ─── Element Access ─────────────────────────────────────────────────────

    /** @brief Access pixel at (channel, row, col). */
    T& at(int c, int y, int x) {
        if (c < 0 || c >= channels_ || y < 0 || y >= height_ || x < 0 || x >= width_) {
            throw std::out_of_range("Image::at: index out of bounds");
        }
        return data_[static_cast<size_t>(c) * height_ * width_ + y * width_ + x];
    }

    const T& at(int c, int y, int x) const {
        if (c < 0 || c >= channels_ || y < 0 || y >= height_ || x < 0 || x >= width_) {
            throw std::out_of_range("Image::at: index out of bounds");
        }
        return data_[static_cast<size_t>(c) * height_ * width_ + y * width_ + x];
    }

    /** @brief Get a single band as a new single-channel Image. */
    Image<T> band(int c) const {
        Image<T> result(1, height_, width_);
        size_t offset = static_cast<size_t>(c) * height_ * width_;
        std::copy(data_.begin() + offset,
                  data_.begin() + offset + height_ * width_,
                  result.data().begin());
        return result;
    }

    // ─── Operator Overloading (Element-wise Band Math) ──────────────────────

    /** @brief Element-wise addition. */
    Image<T> operator+(const Image<T>& other) const {
        assertSameShape(other);
        Image<T> result(channels_, height_, width_);
        for (size_t i = 0; i < data_.size(); ++i) {
            result.data()[i] = data_[i] + other.data()[i];
        }
        return result;
    }

    /** @brief Element-wise subtraction. */
    Image<T> operator-(const Image<T>& other) const {
        assertSameShape(other);
        Image<T> result(channels_, height_, width_);
        for (size_t i = 0; i < data_.size(); ++i) {
            result.data()[i] = data_[i] - other.data()[i];
        }
        return result;
    }

    Image<T> operator*(const Image<T>& other) const {
        assertSameShape(other);
        Image<T> result(channels_, height_, width_);
        for (size_t i = 0; i < data_.size(); ++i) {
            result.data()[i] = data_[i] * other.data()[i];
        }
        return result;
    }

    /** @brief Element-wise division (with epsilon for safety). */
    Image<T> operator/(const Image<T>& other) const {
        assertSameShape(other);
        Image<T> result(channels_, height_, width_);
        if (std::is_floating_point<T>::value) {
            const T eps = static_cast<T>(1e-6);
            for (size_t i = 0; i < data_.size(); ++i) {
                result.data()[i] = data_[i] / (other.data()[i] + eps);
            }
        } else {
            for (size_t i = 0; i < data_.size(); ++i) {
                result.data()[i] = (other.data()[i] != 0) ? (data_[i] / other.data()[i]) : T{0};
            }
        }
        return result;
    }

    /** @brief Scalar multiplication. */
    Image<T> operator*(T scalar) const {
        Image<T> result(channels_, height_, width_);
        for (size_t i = 0; i < data_.size(); ++i) {
            result.data()[i] = data_[i] * scalar;
        }
        return result;
    }

    /** @brief Scalar division. */
    Image<T> operator/(T scalar) const {
        Image<T> result(channels_, height_, width_);
        for (size_t i = 0; i < data_.size(); ++i) {
            result.data()[i] = data_[i] / scalar;
        }
        return result;
    }

    // ─── Utility ────────────────────────────────────────────────────────────

    /** @brief Fill all pixels with a value. */
    void fill(T value) {
        std::fill(data_.begin(), data_.end(), value);
    }

    /** @brief Concatenate another image along the channel axis. */
    Image<T> concatenate(const Image<T>& other) const {
        if (height_ != other.height_ || width_ != other.width_) {
            throw std::invalid_argument("Spatial dimensions must match for concatenation");
        }
        Image<T> result(channels_ + other.channels_, height_, width_);
        std::copy(data_.begin(), data_.end(), result.data().begin());
        std::copy(other.data().begin(), other.data().end(),
                  result.data().begin() + data_.size());
        return result;
    }

    /** @brief Create a sub-image (crop). */
    Image<T> crop(int startY, int startX, int cropH, int cropW) const {
        if (startY + cropH > height_ || startX + cropW > width_ || startY < 0 || startX < 0) {
            throw std::out_of_range("Image::crop: crop region exceeds image bounds");
        }
        Image<T> result(channels_, cropH, cropW);
        for (int c = 0; c < channels_; ++c) {
            for (int y = 0; y < cropH; ++y) {
                for (int x = 0; x < cropW; ++x) {
                    result.at(c, y, x) = at(c, startY + y, startX + x);
                }
            }
        }
        return result;
    }

    /** @brief Pad the image with zeros to target dimensions. */
    Image<T> pad(int targetH, int targetW) const {
        Image<T> result(channels_, targetH, targetW);
        for (int c = 0; c < channels_; ++c) {
            for (int y = 0; y < std::min(height_, targetH); ++y) {
                for (int x = 0; x < std::min(width_, targetW); ++x) {
                    result.at(c, y, x) = at(c, y, x);
                }
            }
        }
        return result;
    }

    friend std::ostream& operator<<(std::ostream& os, const Image<T>& img) {
        os << "Image<" << typeid(T).name() << ">["
           << img.channels_ << "×" << img.height_ << "×" << img.width_ << "]";
        return os;
    }

private:
    void assertSameShape(const Image<T>& other) const {
        if (channels_ != other.channels_ || height_ != other.height_ || width_ != other.width_) {
            throw std::invalid_argument(
                "Shape mismatch: [" + std::to_string(channels_) + "," +
                std::to_string(height_) + "," + std::to_string(width_) + "] vs [" +
                std::to_string(other.channels_) + "," +
                std::to_string(other.height_) + "," + std::to_string(other.width_) + "]"
            );
        }
    }
};

// ─── Tile ───────────────────────────────────────────────────────────────────────

/**
 * @brief A tile extracted from a larger image, with position metadata.
 */
struct Tile {
    Image<PixelF32> data;
    int originX;       // Column offset in the source image
    int originY;       // Row offset in the source image
    int actualWidth;   // Original width before padding
    int actualHeight;  // Original height before padding

    Tile() : originX(0), originY(0), actualWidth(0), actualHeight(0) {}

    Tile(const Image<PixelF32>& d, int ox, int oy, int aw, int ah)
        : data(d), originX(ox), originY(oy), actualWidth(aw), actualHeight(ah) {}
};

// ─── Type Aliases ───────────────────────────────────────────────────────────────

using ImageF32 = Image<PixelF32>;
using ImageU16 = Image<PixelU16>;
using ImageU8  = Image<PixelU8>;

}  // namespace geoseg
