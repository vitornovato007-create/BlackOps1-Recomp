// Entrada nativa Android para o runtime Black Ops 1 Recomp.
#include <SDL3/SDL_hints.h>
#include <SDL3/SDL_system.h>
#include <vulkan/vulkan.h>

#include <android/log.h>
#include <jni.h>

#include <cstdlib>
#include <map>
#include <string>
#include <utility>

#include <rex/cvar.h>
#include <rex/filesystem.h>
#include <rex/logging.h>
#include <rex/memory.h>
#include <rex/thread.h>
#include <rex/ui/windowed_app.h>
#include <rex/ui/windowed_app_context_sdl.h>

#include "blackops1_app.h"

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
        if (initialized) {
          BO1LogStage("[BO1-STAGE] RunMainMessageLoop starting");
          result = app_context.RunMainMessageLoop();
          BO1LogStage("[BO1-STAGE] RunMainMessageLoop returned=%d", result);
        } else {
          result = EXIT_FAILURE;
        }
        app->InvokeOnDestroy();
      }
    }
  }

  ShutdownAndroidReXGlue();
  BO1_LOGI("[BO1-STAGE] SDL_main encerrando com codigo %d.", result);
  return result;
}
