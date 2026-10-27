// Entrada nativa Android para o runtime Black Ops 1 Recomp.
#include <SDL3/SDL_hints.h>
#include <SDL3/SDL_system.h>

#include <android/log.h>
#include <jni.h>

#include <cstdlib>
#include <map>
#include <utility>

#include <rex/cvar.h>
#include <rex/filesystem.h>
#include <rex/logging.h>
#include <rex/memory.h>
#include <rex/thread.h>
#include <rex/ui/windowed_app.h>
#include <rex/ui/windowed_app_context_sdl.h>

#define BO1_TAG "BlackOps1Android"
#define BO1_LOGI(...) __android_log_print(ANDROID_LOG_INFO, BO1_TAG, __VA_ARGS__)
#define BO1_LOGE(...) __android_log_print(ANDROID_LOG_ERROR, BO1_TAG, __VA_ARGS__)

namespace {

bool InitializeAndroidReXGlue() {
  auto* env = static_cast<JNIEnv*>(SDL_GetAndroidJNIEnv());
  auto activity = static_cast<jobject>(SDL_GetAndroidActivity());
  if (!env || !activity) {
    BO1_LOGE("SDL nao forneceu JNIEnv/Activity; abortando antes de iniciar ReXGlue.");
    return false;
  }

  // A Activity ja foi entregue ao SDL. Inicializamos apenas os
  // subsistemas Android declarados por este checkout do ReXGlue.
  env->DeleteLocalRef(activity);

  rex::memory::AndroidInitialize();
  rex::thread::AndroidInitialize();
  rex::filesystem::AndroidInitialize();

  BO1_LOGI("Subsistemas Android do ReXGlue inicializados.");
  return true;
}

void ShutdownAndroidReXGlue() {
  rex::filesystem::AndroidShutdown();
  rex::thread::AndroidShutdown();
  rex::memory::AndroidShutdown();
}

}  // namespace

extern "C" __attribute__((visibility("default"))) int SDL_main(int argc, char* argv[]) {
  BO1_LOGI("[BO1-STAGE] SDL_main entrou; argc=%d", argc);

  if (!InitializeAndroidReXGlue()) {
    BO1_LOGE("[BO1-STAGE] Falha ao inicializar contexto Android/ReXGlue.");
    return EXIT_FAILURE;
  }

  int result = EXIT_FAILURE;
  {
    auto remaining = rex::cvar::Init(argc, argv);
    rex::cvar::ApplyEnvironment();
    rex::InitLoggingEarly();

    SDL_SetHint(SDL_HINT_ORIENTATIONS, "LandscapeLeft LandscapeRight");

    rex::ui::SDLWindowedAppContext app_context;
    if (!app_context.Initialize()) {
      BO1_LOGE("[BO1-STAGE] SDLWindowedAppContext::Initialize falhou.");
    } else {
      auto creator = rex::ui::WindowedApp::GetCreator("blackops1");
      if (!creator) {
        BO1_LOGE("[BO1-STAGE] App 'blackops1' nao registrada; confira REX_DEFINE_APP.");
      } else {
        auto app = creator(app_context);
        const auto& positional_names = app->GetPositionalOptions();
        const size_t count = remaining.size() < positional_names.size()
                                 ? remaining.size()
                                 : positional_names.size();
        std::map<std::string, std::string> parsed;
        for (size_t i = 0; i < count; ++i) {
          parsed[positional_names[i]] = remaining[i];
        }
        app->SetParsedArguments(std::move(parsed));

        BO1_LOGI("[BO1-STAGE] Inicializando BlackOps1App.");
        const bool initialized = app->OnInitialize();
        BO1_LOGI("[BO1-STAGE] BlackOps1App::OnInitialize retornou %s.",
                 initialized ? "true" : "false");
        result = initialized ? app_context.RunMainMessageLoop() : EXIT_FAILURE;
        app->InvokeOnDestroy();
      }
    }
  }

  ShutdownAndroidReXGlue();
  BO1_LOGI("[BO1-STAGE] SDL_main encerrando com codigo %d.", result);
  return result;
}
