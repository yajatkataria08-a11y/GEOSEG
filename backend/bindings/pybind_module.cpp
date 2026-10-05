/**
 * @file pybind_module.cpp
 * @brief Python bindings for the GeoSeg C++ backend via pybind11.
 *
 * Exposes the OOP class hierarchy to Python:
 *   import geoseg_cpp
 *   engine = geoseg_cpp.BandMathEngine(["B02", "B03", ...])
 *   indices = engine.compute_all_indices(image_array)
 *
 * Build with: cmake -DBUILD_PYTHON_BINDINGS=ON ..
 */

#include <pybind11/pybind11.h>
#include <pybind11/stl.h>
#include <pybind11/numpy.h>

#include "../include/types.hpp"
#include "../include/spectral_index.hpp"
#include "../include/band_math.hpp"
#include "../include/tile_manager.hpp"
#include "../include/geotiff_handler.hpp"

namespace py = pybind11;
using namespace geoseg;

// ─── NumPy ↔ Image Conversion ──────────────────────────────────────────────────

/**
 * @brief Convert a NumPy array (C, H, W) to an ImageF32.
 */
ImageF32 numpy_to_image(py::array_t<float> arr) {
    auto buf = arr.request();
    if (buf.ndim != 3) {
        throw std::runtime_error("Expected 3D array (C, H, W), got " +
                                 std::to_string(buf.ndim) + "D");
    }

    int channels = buf.shape[0];
    int height   = buf.shape[1];
    int width    = buf.shape[2];

    std::vector<float> data(static_cast<float*>(buf.ptr),
                            static_cast<float*>(buf.ptr) + buf.size);

    return ImageF32(channels, height, width, data);
}

/**
 * @brief Convert an ImageF32 to a NumPy array (C, H, W).
 */
py::array_t<float> image_to_numpy(const ImageF32& img) {
    py::array_t<float> result({img.channels(), img.height(), img.width()});
    auto buf = result.request();
    float* ptr = static_cast<float*>(buf.ptr);
    std::copy(img.data().begin(), img.data().end(), ptr);
    return result;
}

// ─── Module Definition ──────────────────────────────────────────────────────────

PYBIND11_MODULE(geoseg_cpp, m) {
    m.doc() = "GeoSeg C++ Backend — Image processing for satellite land cover segmentation";

    // ─── BoundingBox ────────────────────────────────────────────────────
    py::class_<BoundingBox>(m, "BoundingBox")
        .def(py::init<double, double, double, double>(),
             py::arg("west"), py::arg("south"), py::arg("east"), py::arg("north"))
        .def_readwrite("west",  &BoundingBox::west)
        .def_readwrite("south", &BoundingBox::south)
        .def_readwrite("east",  &BoundingBox::east)
        .def_readwrite("north", &BoundingBox::north)
        .def("width",    &BoundingBox::width)
        .def("height",   &BoundingBox::height)
        .def("contains", &BoundingBox::contains)
        .def("__repr__", [](const BoundingBox& bb) {
            return "BBox(" + std::to_string(bb.west) + ", " +
                   std::to_string(bb.south) + " → " +
                   std::to_string(bb.east) + ", " +
                   std::to_string(bb.north) + ")";
        });

    // ─── BandMathEngine ─────────────────────────────────────────────────
    py::class_<BandMathEngine>(m, "BandMathEngine")
        .def(py::init<const std::vector<std::string>&>(), py::arg("band_order"))
        .def("compute_ndvi", [](const BandMathEngine& self, py::array_t<float> input) {
            return image_to_numpy(self.computeNDVI(numpy_to_image(input)));
        }, py::arg("input"))
        .def("compute_ndwi", [](const BandMathEngine& self, py::array_t<float> input) {
            return image_to_numpy(self.computeNDWI(numpy_to_image(input)));
        }, py::arg("input"))
        .def("compute_ndbi", [](const BandMathEngine& self, py::array_t<float> input) {
            return image_to_numpy(self.computeNDBI(numpy_to_image(input)));
        }, py::arg("input"))
        .def("compute_all_indices", [](const BandMathEngine& self, py::array_t<float> input) {
            return image_to_numpy(self.computeAllIndices(numpy_to_image(input)));
        }, py::arg("input"))
        .def("build_multispectral_input", [](const BandMathEngine& self, py::array_t<float> input) {
            return image_to_numpy(self.buildMultispectralInput(numpy_to_image(input)));
        }, py::arg("input"))
        .def("get_info",       &BandMathEngine::getInfo)
        .def("get_band_order", &BandMathEngine::getBandOrder)
        .def("__repr__",       &BandMathEngine::getInfo);

    // ─── TileManager ────────────────────────────────────────────────────
    py::class_<TileManager>(m, "TileManager")
        .def(py::init<int, int>(),
             py::arg("tile_size") = 512, py::arg("overlap") = 32)
        .def("get_tile_count", &TileManager::getTileCount,
             py::arg("height"), py::arg("width"))
        .def("get_tile_size",  &TileManager::getTileSize)
        .def("get_overlap",    &TileManager::getOverlap)
        .def("get_stride",     &TileManager::getStride)
        .def("get_info",       &TileManager::getInfo)
        .def("__repr__",       &TileManager::getInfo);

    // ─── SpectralIndex (polymorphic) ────────────────────────────────────
    py::class_<SpectralIndex>(m, "SpectralIndex")
        .def("get_name",        &SpectralIndex::getName)
        .def("get_description", &SpectralIndex::getDescription)
        .def("compute", [](const SpectralIndex& self,
                           py::array_t<float> band1,
                           py::array_t<float> band2) {
            return image_to_numpy(self.compute(numpy_to_image(band1), numpy_to_image(band2)));
        }, py::arg("band1"), py::arg("band2"));

    // Factory
    m.def("create_index", [](const std::string& name) -> std::unique_ptr<SpectralIndex> {
        return createIndex(name);
    }, py::arg("name"), "Create a spectral index by name (NDVI, NDWI, NDBI)");

    // ─── Utility Functions ──────────────────────────────────────────────
    m.def("normalize_reflectance", [](py::array_t<float> input, float scale) {
        auto img = numpy_to_image(input);
        return image_to_numpy(img / scale);
    }, py::arg("input"), py::arg("scale") = 10000.0f,
       "Normalize Sentinel-2 reflectance values");
}


