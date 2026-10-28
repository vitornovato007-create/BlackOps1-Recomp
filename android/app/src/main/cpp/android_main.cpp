// Entrada nativa Android para o runtime Black Ops 1 Recomp.
#include <SDL3/SDL_hints.h>
#include <SDL3/SDL_system.h>
#include <vulkan/vulkan.h>

#include <android/log.h>
#include <dlfcn.h>
#include <jni.h>

#include <cstdlib>
#include <exception>
#include <map>
#include <string>
#include <utility>
#include <vector>

#include <rex/cvar.h>
#include <rex/filesystem.h>
#include <rex/logging.h>
#include <rex/main_android.h>
#include <rex/memory.h>
#include <rex/system.h>
#include <rex/thread.h>
#include <rex/ui/windowed_app.h>
#include <rex/ui/windowed_app_context_sdl.h>

#include "blackops1_app.h"

#define BO1_TAG "BlackOps1Android"
#define BO1_LOGI(...) __android_log_print(ANDROID_LOG_INFO, BO1_TAG, __VA_ARGS__)
#define BO1_LOGE(...) __android_log_print(ANDROID_LOG_ERROR, BO1_TAG, __VA_ARGS__)

namespace {

std::string AndroidNativeLibraryDirectory() {
  Dl_info info{};
  if (dladdr(reinterpret_cast<void*>(&AndroidNativeLibraryDirectory), &info) &&
      info.dli_fname) {
    const std::string library_path(info.dli_fname);
    const size_t separator = library_path.find_last_of('/');
    if (separator != std::string::npos) {
      return library_path.substr(0, separator);
    }
  }
  return {};
}

bool InitializeAndroidReXGlue() {
  auto* env = static_cast<JNIEnv*>(SDL_GetAndroidJNIEnv());
  auto activity = static_cast<jobject>(SDL_GetAndroidActivity());
  if (!env || !activity) {
    BO1_LOGE("SDL nao forneceu JNIEnv/Activity; abortando antes de iniciar ReXGlue.");
    return false;
  }

  JavaVM* java_vm = nullptr;
  if (env->GetJavaVM(&java_vm) != JNI_OK || !java_vm) {
    env->DeleteLocalRef(activity);
    BO1_LOGE("JNIEnv::GetJavaVM falhou; ReXGlue nao sera inicializado.");
    return false;
  }

  const std::string native_library_directory = AndroidNativeLibraryDirectory();
  if (native_library_directory.empty()) {
    env->DeleteLocalRef(activity);
    BO1_LOGE("Nao foi possivel localizar o diretorio das bibliotecas nativas.");
    return false;
  }

  // O SDK cria uma referencia global da Activity; a referencia local do SDL
  // e liberada exatamente uma vez depois de entregar o contexto.
  rex::SetAndroidApplicationContext(
      java_vm, activity, native_library_directory.c_str());
  env->DeleteLocalRef(activity);

  // O SDK nao inicializa automaticamente estes subsistemas em Android.
  rex::memory::AndroidInitialize();
  rex::thread::AndroidInitialize();
  rex::filesystem::AndroidInitialize();

  if (!rex::InitializeAndroidSystemForApplicationContext()) {
    BO1_LOGE("InitializeAndroidSystemForApplicationContext retornou false.");
    rex::filesystem::AndroidShutdown();
    rex::thread::AndroidShutdown();
    rex::memory::AndroidShutdown();
    rex::ShutdownAndroidSystem();
    return false;
  }

  BO1LogStage("[BO1-ANDROID] Contexto Android ReXGlue inicializado; libs=%s",
              native_library_directory.c_str());
  BO1LogStage("[BO1-ANDROID] memory/thread/filesystem AndroidInitialize concluido");
  BO1_LOGI("Contexto Android e subsistemas do ReXGlue inicializados.");
  return true;
}
void LogVulkanDiagnostics() {
  BO1LogStage("[BO1-VULKAN] Preflight started; diagnostic only, it will not block game startup.");

  uint32_t loader_version = VK_API_VERSION_1_0;
  const auto enumerate_version =
      reinterpret_cast<PFN_vkEnumerateInstanceVersion>(
          vkGetInstanceProcAddr(VK_NULL_HANDLE, "vkEnumerateInstanceVersion"));
  if (enumerate_version != nullptr) {
    const VkResult version_result = enumerate_version(&loader_version);
    if (version_result != VK_SUCCESS) {
      BO1LogStage("[BO1-VULKAN] vkEnumerateInstanceVersion failed: %d",
                  static_cast<int>(version_result));
      loader_version = VK_API_VERSION_1_0;
    }
  }
  BO1LogStage("[BO1-VULKAN] Loader API version=%u.%u.%u",
              VK_VERSION_MAJOR(loader_version),
              VK_VERSION_MINOR(loader_version),
              VK_VERSION_PATCH(loader_version));

  VkApplicationInfo app_info{};
  app_info.sType = VK_STRUCTURE_TYPE_APPLICATION_INFO;
  app_info.pApplicationName = "BlackOps1-Recomp diagnostic";
  app_info.applicationVersion = VK_MAKE_API_VERSION(0, 0, 1, 0);
  app_info.pEngineName = "BlackOps1-Recomp";
  app_info.engineVersion = VK_MAKE_API_VERSION(0, 0, 1, 0);
  app_info.apiVersion = VK_API_VERSION_1_0;

  VkInstanceCreateInfo create_info{};
  create_info.sType = VK_STRUCTURE_TYPE_INSTANCE_CREATE_INFO;
  create_info.pApplicationInfo = &app_info;

  VkInstance instance = VK_NULL_HANDLE;
  VkResult result = vkCreateInstance(&create_info, nullptr, &instance);
  if (result != VK_SUCCESS) {
    BO1LogStage("[BO1-VULKAN] vkCreateInstance failed=%d; continuing to normal runtime initialization.",
                static_cast<int>(result));
    return;
  }

  uint32_t device_count = 0;
  result = vkEnumeratePhysicalDevices(instance, &device_count, nullptr);
  if (result != VK_SUCCESS || device_count == 0) {
    BO1LogStage("[BO1-VULKAN] No physical devices; result=%d count=%u. Continuing startup.",
                static_cast<int>(result), device_count);
    vkDestroyInstance(instance, nullptr);
    return;
  }

  std::vector<VkPhysicalDevice> devices(device_count);
  result = vkEnumeratePhysicalDevices(instance, &device_count, devices.data());
  if (result != VK_SUCCESS) {
    BO1LogStage("[BO1-VULKAN] Device enumeration failed=%d; continuing startup.",
                static_cast<int>(result));
    vkDestroyInstance(instance, nullptr);
    return;
  }

  for (uint32_t i = 0; i < device_count; ++i) {
    VkPhysicalDeviceProperties properties{};
    vkGetPhysicalDeviceProperties(devices[i], &properties);
    uint32_t extension_count = 0;
    const VkResult extension_result =
        vkEnumerateDeviceExtensionProperties(devices[i], nullptr, &extension_count, nullptr);
    BO1LogStage(
        "[BO1-VULKAN] GPU[%u] name=%s api=%u.%u.%u vendor=0x%04x device=0x%04x type=%u driver=%u extensions=%u ext_result=%d",
        i, properties.deviceName,
        VK_VERSION_MAJOR(properties.apiVersion),
        VK_VERSION_MINOR(properties.apiVersion),
        VK_VERSION_PATCH(properties.apiVersion),
        properties.vendorID, properties.deviceID,
        static_cast<unsigned int>(properties.deviceType),
        properties.driverVersion,
        extension_result == VK_SUCCESS ? extension_count : 0,
        static_cast<int>(extension_result));
  }

  vkDestroyInstance(instance, nullptr);
  BO1LogStage("[BO1-VULKAN] Preflight complete; continuing to ReXGlue.");
}

void ShutdownAndroidReXGlue() {
  rex::filesystem::AndroidShutdown();
  rex::thread::AndroidShutdown();
  rex::memory::AndroidShutdown();
  rex::ShutdownAndroidSystem();
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

    // Adapted diagnostic practice from NFSMW Android Evolved: record Vulkan
    // loader/device information without requiring NFS-specific renderer features.
    LogVulkanDiagnostics();

    SDL_SetHint(SDL_HINT_ORIENTATIONS, "LandscapeLeft LandscapeRight");

    BO1LogStage("[BO1-STAGE] Criando SDLWindowedAppContext");
    try {
      rex::ui::SDLWindowedAppContext app_context;
      BO1LogStage("[BO1-STAGE] Chamando SDLWindowedAppContext::Initialize");
      if (!app_context.Initialize()) {
        BO1LogStage("[BO1-ERROR] SDLWindowedAppContext::Initialize retornou false");
        BO1_LOGE("[BO1-STAGE] SDLWindowedAppContext::Initialize falhou.");
      } else {
        BO1LogStage("[BO1-STAGE] SDLWindowedAppContext::Initialize retornou true");
        BO1LogStage("[BO1-STAGE] Procurando app registrada: blackops1");
        auto creator = rex::ui::WindowedApp::GetCreator("blackops1");
        if (!creator) {
          BO1LogStage("[BO1-ERROR] App blackops1 nao registrada; confira REX_DEFINE_APP");
          BO1_LOGE("[BO1-STAGE] App 'blackops1' nao registrada; confira REX_DEFINE_APP.");
        } else {
          BO1LogStage("[BO1-STAGE] Criador da app encontrado; construindo BlackOps1App");
          auto app = creator(app_context);
          BO1LogStage("[BO1-STAGE] BlackOps1App criada; lendo argumentos posicionais");
          const auto& positional_names = app->GetPositionalOptions();
          const size_t count = remaining.size() < positional_names.size()
                                   ? remaining.size()
                                   : positional_names.size();
          std::map<std::string, std::string> parsed;
          for (size_t i = 0; i < count; ++i) {
            parsed[positional_names[i]] = remaining[i];
          }
          app->SetParsedArguments(std::move(parsed));

          BO1LogStage("[BO1-STAGE] Chamando BlackOps1App::OnInitialize");
          const bool initialized = app->OnInitialize();
          BO1LogStage("[BO1-STAGE] BlackOps1App::OnInitialize retornou %s",
                      initialized ? "true" : "false");
          if (initialized) {
            BO1LogStage("[BO1-STAGE] Chamando RunMainMessageLoop");
            result = app_context.RunMainMessageLoop();
            BO1LogStage("[BO1-STAGE] RunMainMessageLoop retornou codigo=%d", result);
          } else {
            result = EXIT_FAILURE;
            BO1LogStage("[BO1-ERROR] OnInitialize retornou false; loop principal nao iniciado");
          }
          BO1LogStage("[BO1-STAGE] Chamando BlackOps1App::InvokeOnDestroy");
          app->InvokeOnDestroy();
          BO1LogStage("[BO1-STAGE] BlackOps1App::InvokeOnDestroy terminou");
        }
      }
    } catch (const std::exception& error) {
      BO1LogStage("[BO1-EXCEPTION] std::exception durante inicializacao/loop: %s",
                  error.what());
      BO1_LOGE("[BO1-EXCEPTION] %s", error.what());
      result = EXIT_FAILURE;
    } catch (...) {
      BO1LogStage("[BO1-EXCEPTION] Excecao C++ desconhecida durante inicializacao/loop");
      BO1_LOGE("[BO1-EXCEPTION] Excecao C++ desconhecida");
      result = EXIT_FAILURE;
    }
  }

  ShutdownAndroidReXGlue();
  BO1_LOGI("[BO1-STAGE] SDL_main encerrando com codigo %d.", result);
  return result;
}
