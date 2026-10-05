cmake_minimum_required(VERSION 3.16)
project(geoseg_backend VERSION 0.1.0 LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# ─── Options ─────────────────────────────────────────────────────────────────────
option(BUILD_PYTHON_BINDINGS "Build pybind11 Python bindings" OFF)
option(BUILD_TESTS           "Build unit tests"               OFF)

# ─── Source Files ────────────────────────────────────────────────────────────────
set(BACKEND_SOURCES
    src/image_processor.cpp
    src/spectral_index.cpp
    src/band_math.cpp
    src/tile_manager.cpp
    src/geotiff_handler.cpp
)

set(BACKEND_HEADERS
    include/types.hpp
    include/image_processor.hpp
    include/spectral_index.hpp
    include/band_math.hpp
    include/tile_manager.hpp
    include/geotiff_handler.hpp
)

# ─── Static Library ─────────────────────────────────────────────────────────────
add_library(geoseg_lib STATIC ${BACKEND_SOURCES} ${BACKEND_HEADERS})
target_include_directories(geoseg_lib PUBLIC ${CMAKE_CURRENT_SOURCE_DIR}/include)

# ─── Standalone CLI ──────────────────────────────────────────────────────────────
add_executable(geoseg_backend main.cpp)
target_link_libraries(geoseg_backend PRIVATE geoseg_lib)
target_include_directories(geoseg_backend PRIVATE ${CMAKE_CURRENT_SOURCE_DIR})

# ─── Python Bindings (optional) ──────────────────────────────────────────────────
if(BUILD_PYTHON_BINDINGS)
    find_package(pybind11 REQUIRED)

    pybind11_add_module(geoseg_cpp bindings/pybind_module.cpp ${BACKEND_SOURCES})
    target_include_directories(geoseg_cpp PRIVATE ${CMAKE_CURRENT_SOURCE_DIR}/include)
    target_compile_definitions(geoseg_cpp PRIVATE BUILD_PYTHON_BINDINGS)
endif()

# ─── Install ─────────────────────────────────────────────────────────────────────
install(TARGETS geoseg_backend DESTINATION bin)
install(TARGETS geoseg_lib DESTINATION lib)
install(DIRECTORY include/ DESTINATION include/geoseg)

# ─── Print Config ────────────────────────────────────────────────────────────────
message(STATUS "GeoSeg Backend Configuration:")
message(STATUS "  C++ Standard:       ${CMAKE_CXX_STANDARD}")
message(STATUS "  Python Bindings:    ${BUILD_PYTHON_BINDINGS}")
message(STATUS "  Build Tests:        ${BUILD_TESTS}")
