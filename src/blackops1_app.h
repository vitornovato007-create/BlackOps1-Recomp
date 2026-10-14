    #pragma once
    #include <filesystem>
    #include <memory>
    #include <string_view>
    #include <SDL3/SDL.h>
    #include <rex/rex_app.h>
    #include <rex/ui/windowed_app.h>
    #include "blackops1_init.h"

    extern const rex::PPCImageInfo PPCImageConfig;

    class BlackOps1App final : public rex::ReXApp {
     public:
      static std::unique_ptr<rex::ui::WindowedApp> Create(rex::ui::WindowedAppContext& ctx) {
        return std::unique_ptr<rex::ui::WindowedApp>(new BlackOps1App(ctx));
      }
     private:
      explicit BlackOps1App(rex::ui::WindowedAppContext& ctx)
          : rex::ReXApp(ctx, "blackops1", PPCImageConfig) {}
      void OnConfigurePaths(rex::PathConfig& paths) override {
        const char* internal = SDL_GetAndroidInternalStoragePath();
        if (internal && *internal) {
          paths.game_data_root = std::filesystem::path(internal) / "blackops1";
        }
        const char* pref = SDL_GetPrefPath("BlackOps1", "BlackOps1Recomp");
        if (pref && *pref) {
          paths.user_data_root = std::filesystem::path(pref) / "user";
          paths.cache_root = std::filesystem::path(pref) / "cache";
          paths.config_path = std::filesystem::path(pref) / "config.toml";
        }
      }
      void OnPreSetup(rex::RuntimeConfig& config) override {
        // Ask ReXGlue to load its Xenos GPU plugin. If Vulkan/device support is
        // insufficient, initialization should fail visibly in the log.
        config.gpu_plugin = "xenos";
      }
    };
