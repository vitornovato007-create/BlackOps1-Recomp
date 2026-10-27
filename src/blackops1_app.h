    #pragma once
    #include <filesystem>
    #include <fstream>
    #include <string>
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
          : rex::ReXApp(ctx, "blackops1", PPCImageConfig) {
        SDL_Log("[BO1-STAGE] BlackOps1App constructor entered");
      }
      void OnConfigurePaths(rex::PathConfig& paths) override {
        SDL_Log("[BO1-STAGE] OnConfigurePaths entered");
        const char* internal = SDL_GetAndroidInternalStoragePath();
        SDL_Log("[BO1-STAGE] SDL_GetAndroidInternalStoragePath=%s",
                internal && *internal ? internal : "(null/empty)");
        if (internal && *internal) {
          const std::filesystem::path internal_root(internal);
          const std::filesystem::path selected_root_file = internal_root / "runtime-game-root.txt";
          SDL_Log("[BO1-STAGE] Runtime root config file=%s",
                  selected_root_file.string().c_str());
          std::ifstream selected_root_stream(selected_root_file);
          std::string selected_root;
          if (selected_root_stream && std::getline(selected_root_stream, selected_root)
              && !selected_root.empty()) {
            SDL_Log("[BO1-STAGE] Runtime root read from config=%s", selected_root.c_str());
            const std::filesystem::path candidate(selected_root);
            std::error_code ec;
            const auto executable = candidate / "default.xex";
            if (std::filesystem::is_directory(candidate, ec) && !ec
                && std::filesystem::is_regular_file(executable, ec) && !ec
                && std::filesystem::file_size(executable, ec) > 0 && !ec) {
              paths.game_data_root = candidate;
              SDL_Log("[BO1-STAGE] game_data_root accepted=%s",
                      paths.game_data_root.string().c_str());
            } else {
              SDL_Log("[BO1-STAGE] Selected root rejected; using internal fallback. error=%s",
                      ec.message().c_str());
              paths.game_data_root = internal_root / "blackops1";
              SDL_Log("[BO1-STAGE] game_data_root fallback=%s",
                      paths.game_data_root.string().c_str());
            }
          } else {
            SDL_Log("[BO1-STAGE] Runtime root config missing/empty; using internal fallback");
            paths.game_data_root = internal_root / "blackops1";
            SDL_Log("[BO1-STAGE] game_data_root fallback=%s",
                    paths.game_data_root.string().c_str());
          }
        }
        SDL_Log("[BO1-STAGE] OnConfigurePaths game root setup complete");
        const char* pref = SDL_GetPrefPath("BlackOps1", "BlackOps1Recomp");
        if (pref && *pref) {
          paths.user_data_root = std::filesystem::path(pref) / "user";
          paths.cache_root = std::filesystem::path(pref) / "cache";
          paths.config_path = std::filesystem::path(pref) / "config.toml";
          SDL_Log("[BO1-STAGE] user_data_root=%s", paths.user_data_root.string().c_str());
          SDL_Log("[BO1-STAGE] cache_root=%s", paths.cache_root.string().c_str());
          SDL_Log("[BO1-STAGE] config_path=%s", paths.config_path.string().c_str());
        }
      }
      void OnPreSetup(rex::RuntimeConfig& config) override {
        SDL_Log("[BO1-STAGE] OnPreSetup entered");
        // Ask ReXGlue to load its Xenos GPU plugin. If Vulkan/device support is
        // insufficient, initialization should fail visibly in the log.
        config.gpu_plugin = "xenos";
        SDL_Log("[BO1-STAGE] GPU plugin configured: xenos");
        SDL_Log("[BO1-STAGE] OnPreSetup complete");
      }
    };
