#pragma once

#include <expected>
#include <vector>
#include <string>
#include <string_view>
#include <filesystem>
#include <rex/system/map_parser_types.h>

namespace rex::runtime {

/**
 * @brief Parse an nm-style map file from disk.
 * 
 * This is the format produced by nm on Unix:
 *     00000000 t test_add1
 *     00000010 T test_sub1
 * 
 * Symbol types:
 *     T/t = text (code)
 *     D/d = data
 *     B/b = bss
 *     U = undefined
 * 
 * @param map_path Path to the .map file
 * @param options  Parsing options (base address, etc.)
 * @return Vector of parsed symbols or a MapParseError on failure
 */
std::expected<std::vector<BinarySymbol>, MapParseError> ParseNmMap(
    const std::filesystem::path& map_path, 
    MapParseOptions options = {}
);

/**
 * @brief Parse nm-style map data from a string.
 * 
 * @param map_data Map file contents as a string view
 * @param options  Parsing options
 * @return Vector of parsed symbols or a MapParseError on failure
 */
std::expected<std::vector<BinarySymbol>, MapParseError> ParseNmMapString(
    std::string_view map_data, 
    MapParseOptions options = {}
);

} // namespace rex::runtime
