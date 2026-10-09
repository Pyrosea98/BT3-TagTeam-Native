#include "runtime/ps2_ui_glyph_atlas.h"
#include <array>
#include <cassert>
#include <cmath>
#include <fstream>
#include <iterator>
#include <cstdio>
int main(int argc, char** argv) {
    if (argc != 2) return 2;
    std::ifstream in(argv[1], std::ios::binary);
    std::vector<uint8_t> bytes((std::istreambuf_iterator<char>(in)), {});
    ps2x::ui::GlyphAtlas atlas;
    assert(atlas.load(bytes));
    std::array<ps2x::ui::GlyphQuad, 32> quads;
    auto full = atlas.layout("AV", 12, 24, quads);
    assert(full.written == 2 && !full.capacityExceeded);
    assert(full.advance == atlas.measure("AV"));
    auto half = atlas.layout("AV", 12, 24, quads, 0.75f);
    assert(std::abs(half.advance - full.advance * 0.75f) < 0.001f);
    assert(quads[0].scale == 0.75f);
    auto bounded = atlas.layout("ABC", 0, 0, std::span(quads).first(1));
    assert(bounded.written == 1 && bounded.capacityExceeded);
    assert(bounded.advance == atlas.measure("ABC"));
    assert(atlas.measure("\xF0\x9F\x98\x80") == atlas.measure("\xef\xbf\xbd")); // unsupported emoji
    assert(atlas.measure("\xff") == atlas.measure("\xef\xbf\xbd"));
    assert(atlas.measure("\xc0\xaf") == atlas.measure("\xef\xbf\xbd\xef\xbf\xbd")); // invalid overlong UTF-8
    auto accents = atlas.layout("\xc3\x91\xc3\xa9\xc2\xbf", 0, 0, quads);
    assert(accents.written == 3);
    assert(atlas.measure("") == 0);
    assert(atlas.measure("AV", -1) == 0);
    auto bad = bytes; bad[4] = 2; assert(!atlas.load(bad)); assert(atlas.measure("AV") == 0);
    assert(!atlas.load(std::span(bytes).first(bytes.size() - 1)));
    bad = bytes; bad[32] = 0xff; bad[33] = 0xff; assert(!atlas.load(bad)); // invalid page
    assert(atlas.load(bytes));
    std::printf("PASS %s pages=%u AV=%.6f line=%.3f baseline=%.3f\n", argv[1], atlas.pages(),
                atlas.measure("AV"), atlas.lineHeight(), atlas.baseline());
}
