#include "runtime/ps2_ui_text_draw.h"
#include <array>
#include <cassert>
#include <fstream>
#include <iterator>
#include <filesystem>
#include <cstdio>
using namespace ps2x::ui;
struct Sink final : TextSpriteSink {
    unsigned uploads = 0, releaseCount = 0, begins = 0, ends = 0, count = 0, failAt = 0;
    std::array<TextSprite, 512> sprites;
    std::array<bool, 128> alive{};
    Rect clip{};
    TextureHandle upload() {
        ++uploads;
        if (uploads == failAt) return 0;
        assert(uploads < alive.size()); alive[uploads] = true; return uploads;
    }
    TextureHandle uploadIndices(std::span<const uint8_t> bytes, uint16_t w, uint16_t h) override {
        assert(bytes.size() == size_t(w) * h); return upload();
    }
    TextureHandle uploadPalette(std::span<const uint8_t> bytes) override { assert(bytes.size() == 1024); return upload(); }
    void release(TextureHandle h) override { assert(alive[h]); alive[h] = false; ++releaseCount; }
    void begin(Rect r) override { assert(begins == ends); ++begins; count = 0; clip = r; }
    void sprite(const TextSprite& s) override {
        assert(alive[s.indices] && alive[s.palette]);
        assert(s.x0 >= clip.x && s.x1 <= clip.x + clip.width && s.x0 < s.x1);
        assert(s.y0 >= clip.y && s.y1 <= clip.y + clip.height && s.y0 < s.y1);
        assert(s.u0 >= 0 && s.u1 <= 1 && s.u0 < s.u1 && s.v0 >= 0 && s.v1 <= 1 && s.v0 < s.v1);
        assert(count < sprites.size()); sprites[count++] = s;
    }
    void end() override { ++ends; }
};
std::vector<uint8_t> read(const std::filesystem::path& file) {
    std::ifstream input(file, std::ios::binary); assert(input);
    return {(std::istreambuf_iterator<char>(input)), {}};
}
int main(int argc, char** argv) {
    if (argc != 2) return 2;
    std::filesystem::path metricsPath = argv[1]; auto root = metricsPath.parent_path();
    auto stem = metricsPath.stem().string(); auto metrics = read(metricsPath);
    GlyphAtlas parsed; assert(parsed.load(metrics));
    std::vector<std::vector<uint8_t>> pageData, paletteData;
    std::vector<std::span<const uint8_t>> pages, palettes;
    for (unsigned i = 0; i < parsed.pages(); ++i) pageData.push_back(read(root / (stem + "-" + std::to_string(i) + ".indices")));
    for (auto tag : {"gold", "white", "grey", "cyan", "yellow", "red", "green"}) paletteData.push_back(read(root / (stem + "-" + tag + ".rgba")));
    for (auto& p : pageData) pages.emplace_back(p);
    for (auto& p : paletteData) palettes.emplace_back(p);
    Localizer locale;
    assert(locale.tag() == "en" && locale.text(TextId::Ready) == "Ready");
    assert(locale.select("es-CO") && locale.tag() == "es" && locale.text(TextId::Ready) == "Listo");
    assert(!locale.select("fr") && locale.tag() == "es");
    assert(locale.text(TextId::Count).empty());
    for (unsigned language = 0; language < 2; ++language) {
        assert(locale.select(language == 0 ? "en" : "es"));
        for (size_t i = 0; i < size_t(TextId::Count); ++i)
            assert(!locale.text(TextId(i)).empty() && locale.text(TextId(i)) == kUiStrings[i][language]);
    }
    Sink sink;
    {
        NativeTextFont font; assert(font.load(sink, metrics, pages, palettes));
        const auto initialUploads = sink.uploads;
        assert(initialUploads == parsed.pages() + 7);
        std::array<GlyphQuad, 256> scratch;
        assert(!font.draw(locale, TextId::Count, Palette::White, 320, 64, {0, 0, 640, 448}, scratch).success);
        auto label = font.draw(locale, TextId::Ready, Palette::White, 320, 64, {0, 0, 640, 448}, scratch, TextAlign::Centre);
        assert(label.success && label.submitted > 0);
        float left = sink.sprites[0].x0;
        auto right = font.draw(locale, TextId::Ready, Palette::White, 320, 64, {0, 0, 640, 448}, scratch, TextAlign::Right);
        assert(right.success && sink.sprites[0].x0 < left);
        for (auto viewport : {Rect{0, 0, 320, 224}, Rect{320, 0, 320, 224}, Rect{0, 224, 320, 224}, Rect{320, 224, 320, 224}})
            assert(font.draw("100%", Palette::Yellow, -2, 20, viewport, scratch).success);
        // Completely clipped text is successful but submits no sprites.
        auto invisible = font.draw("100%", Palette::Red, -1000, -1000, {0, 0, 640, 448}, scratch);
        assert(invisible.success && invisible.submitted == 0);
        auto before = sink.begins;
        auto small = font.draw("100%", Palette::Green, 25, 25, {0, 0, 640, 448}, std::span(scratch).first(1));
        assert(!small.success && sink.begins == before);
        assert(!font.draw("100%", Palette::Count, 25, 25, {0, 0, 640, 448}, scratch).success);
        for (unsigned i = 0; i < 120; ++i)
            assert(font.draw("100%", Palette(i % 7), 25, 25, {0, 0, 640, 448}, scratch).success);
        assert(sink.uploads == initialUploads); // no per-frame or colour-switch uploads
    }
    assert(sink.releaseCount == sink.uploads && sink.begins == sink.ends);
    Sink failure; failure.failAt = parsed.pages() + 2;
    NativeTextFont failedFont;
    assert(!failedFont.load(failure, metrics, pages, palettes));
    assert(failure.releaseCount + 1 == failure.uploads);
    std::printf("PASS native draw %s pages=%u upload-once/120frames/cleanup/locale/clip\n", argv[1], parsed.pages());
}
