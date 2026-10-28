#!/usr/bin/env python3
"""Persistente instrumentacao de runtime Android no checkout temporario do ReXGlue."""
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
REX_APP = ROOT / "rexglue-sdk/src/ui/rex_app.cpp"
GPU_LOADER = ROOT / "rexglue-sdk/src/system/gpu_plugin_loader.cpp"


def fail(message: str) -> None:
    print(f"::error::{message}", file=sys.stderr)
    raise SystemExit(1)


def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        fail(f"{label}: esperado exatamente 1 ponto de insercao, encontrados {count}.")
    return text.replace(old, new, 1)


def ensure_includes(text: str, includes: list[str]) -> str:
    anchor = "#include <rex/rex_app.h>" if "rex_app.h" in text else "#include <rex/system/gpu_plugin.h>"
    for item in includes:
        if item not in text:
            text = replace_once(text, anchor, anchor + "\n" + item, f"include {item}")
    return text


def app_log_helper() -> str:
    return r'''
namespace {
void ReXAppStageLog(const char* format, ...) {
  char message[2048];
  va_list args;
  va_start(args, format);
  std::vsnprintf(message, sizeof(message), format, args);
  va_end(args);
#if defined(__ANDROID__)
  SDL_Log("[REX-STAGE] %s", message);
  const char* internal = SDL_GetAndroidInternalStoragePath();
  if (!internal || !*internal) {
    SDL_Log("[REX-STAGE] ERRO: SDL_GetAndroidInternalStoragePath vazio; evento acima so foi enviado ao logcat.");
    return;
  }
  static std::mutex log_mutex;
  std::lock_guard<std::mutex> lock(log_mutex);
  std::error_code ec;
  const auto dir = std::filesystem::path(internal) / "logs";
  std::filesystem::create_directories(dir, ec);
  if (ec) {
    SDL_Log("[REX-STAGE] ERRO criando diretorio de log: %s (%s)", dir.string().c_str(), ec.message().c_str());
    return;
  }
  const auto file = dir / "blackops1-diagnostics.txt";
  std::ofstream out(file, std::ios::out | std::ios::app);
  if (!out) {
    SDL_Log("[REX-STAGE] ERRO abrindo arquivo de diagnostico: %s", file.string().c_str());
    return;
  }
  out << "[REX-STAGE] " << message << '\n';
  out.flush();
  if (!out) SDL_Log("[REX-STAGE] ERRO gravando arquivo de diagnostico: %s", file.string().c_str());
#else
  REXLOG_INFO("[REX-STAGE] {}", message);
#endif
}
}  // namespace
'''


def gpu_log_helper() -> str:
    return r'''
namespace {
void GpuPluginStageLog(const char* format, ...) {
  char message[2048];
  va_list args;
  va_start(args, format);
  std::vsnprintf(message, sizeof(message), format, args);
  va_end(args);
#if defined(__ANDROID__)
  SDL_Log("[BO1-GPU-PLUGIN] %s", message);
  const char* internal = SDL_GetAndroidInternalStoragePath();
  if (!internal || !*internal) return;
  static std::mutex log_mutex;
  std::lock_guard<std::mutex> lock(log_mutex);
  std::error_code ec;
  const auto dir = std::filesystem::path(internal) / "logs";
  std::filesystem::create_directories(dir, ec);
  if (ec) {
    SDL_Log("[BO1-GPU-PLUGIN] ERRO criando diretorio: %s", ec.message().c_str());
    return;
  }
  const auto file = dir / "blackops1-diagnostics.txt";
  std::ofstream out(file, std::ios::out | std::ios::app);
  if (!out) {
    SDL_Log("[BO1-GPU-PLUGIN] ERRO abrindo arquivo: %s", file.string().c_str());
    return;
  }
  out << "[BO1-GPU-PLUGIN] " << message << '\n';
  out.flush();
  if (!out) SDL_Log("[BO1-GPU-PLUGIN] ERRO gravando arquivo: %s", file.string().c_str());
#else
  REXSYS_INFO("[BO1-GPU-PLUGIN] {}", message);
#endif
}
}  // namespace
'''


def patch_app() -> None:
    if not REX_APP.is_file():
        fail(f"Fonte ReXApp ausente: {REX_APP}")
    text = REX_APP.read_text(encoding="utf-8")
    if "ReXAppStageLog(" not in text:
        text = ensure_includes(text, [
            "#include <cstdarg>", "#include <cstdio>", "#include <fstream>",
            "#include <mutex>", "#include <system_error>",
            "#if defined(__ANDROID__)\n#include <SDL3/SDL.h>\n#include <SDL3/SDL_system.h>\n#endif",
            "#include <filesystem>",
        ])
        text = replace_once(text, "// --- ReXApp ---", app_log_helper() + "\n// --- ReXApp ---", "helper ReXApp")
    # These stage markers are added to upstream source after each clean SDK checkout.
    additions = [
        ("bool ReXApp::OnInitialize() {", '  ReXAppStageLog("OnInitialize entered");\n'),
        ("bool ReXApp::SetupEnvironment() {", '  ReXAppStageLog("SetupEnvironment entered");\n'),
        ("bool ReXApp::SetupPresentation() {", '  ReXAppStageLog("SetupPresentation entered");\n'),
        ("  OnPreSetup(config_);", '  ReXAppStageLog("SetupPresentation: calling OnPreSetup");\n  OnPreSetup(config_);\n  ReXAppStageLog("SetupPresentation: OnPreSetup returned; gpu_plugin=%s; graphics_preconfigured=%s", config_.gpu_plugin.c_str(), config_.graphics ? "true" : "false");'),
        ("    config_.graphics = rex::system::LoadGpuPlugin(config_.gpu_plugin);", '    ReXAppStageLog("SetupPresentation: calling LoadGpuPlugin name=%s", config_.gpu_plugin.c_str());\n    config_.graphics = rex::system::LoadGpuPlugin(config_.gpu_plugin);\n    ReXAppStageLog("SetupPresentation: LoadGpuPlugin returned %s", config_.graphics ? "graphics object" : "null");'),
        ("    X_STATUS status = config_.graphics->SetupPresentation(&app_context());", '    ReXAppStageLog("SetupPresentation: calling graphics->SetupPresentation");\n    X_STATUS status = config_.graphics->SetupPresentation(&app_context());\n    ReXAppStageLog("SetupPresentation: graphics->SetupPresentation status=0x%08X", static_cast<unsigned int>(status));'),
        ("  window_ = rex::ui::Window::Create(app_context(), GetName(), 1280, 720);", '  ReXAppStageLog("SetupPresentation: calling Window::Create");\n  window_ = rex::ui::Window::Create(app_context(), GetName(), 1280, 720);\n  ReXAppStageLog("SetupPresentation: Window::Create returned %s", window_ ? "non-null" : "null");'),
        ("  auto status = runtime_->Setup(ppc_info_, std::move(config_));", '  ReXAppStageLog("ConstructRuntime: calling Runtime::Setup");\n  auto status = runtime_->Setup(ppc_info_, std::move(config_));\n  ReXAppStageLog("ConstructRuntime: Runtime::Setup status=0x%08X", static_cast<unsigned int>(status));'),
        ('  status = runtime_->LoadXexImage(xex_image);', '  ReXAppStageLog("ConstructRuntime: calling LoadXexImage path=%s", xex_image.c_str());\n  status = runtime_->LoadXexImage(xex_image);\n  ReXAppStageLog("ConstructRuntime: LoadXexImage status=0x%08X", static_cast<unsigned int>(status));'),
    ]
    for anchor, insertion in additions:
        marker = insertion.strip().splitlines()[-1].strip()
        if marker in text:
            continue
        if anchor not in text:
            fail(f"ReXApp: ponto de instrumentacao ausente: {anchor.strip()}")
        text = replace_once(text, anchor, insertion, f"instrumentacao ReXApp {anchor.strip()}")
    # Explicit false-path diagnostics, including paths before GPU setup.
    false_paths = [
        ("  if (!SetupEnvironment()) {", '  if (!SetupEnvironment()) {\n    ReXAppStageLog("FAIL OnInitialize: SetupEnvironment returned false");'),
        ("  if (!SetupPresentation()) {", '  if (!SetupPresentation()) {\n    ReXAppStageLog("FAIL OnInitialize: SetupPresentation returned false");'),
        ("  if (!ConstructRuntime(*paths)) {", '  if (!ConstructRuntime(*paths)) {\n    ReXAppStageLog("FAIL OnInitialize: ConstructRuntime returned false");'),
        ("  if (!std::filesystem::is_directory(paths.game_data_root)) {", '  if (!std::filesystem::is_directory(paths.game_data_root)) {\n    ReXAppStageLog("FAIL ConstructRuntime: game_data_root is not a directory: %s", paths.game_data_root.string().c_str());'),
    ]
    for anchor, replacement in false_paths:
        if replacement not in text:
            if anchor not in text:
                fail(f"ReXApp: caminho de falha ausente: {anchor.strip()}")
            text = replace_once(text, anchor, replacement, "diagnostico de falha ReXApp")
    REX_APP.write_text(text, encoding="utf-8")
    for marker in ("OnInitialize entered", "calling LoadGpuPlugin", "LoadXexImage status"):
        if marker not in text:
            fail(f"Validacao ReXApp falhou; marcador ausente: {marker}")
    print("OK: ReXApp instrumentada com etapas de inicializacao, renderer e XEX.")


def patch_gpu_loader() -> None:
    if not GPU_LOADER.is_file():
        fail(f"Loader GPU ausente: {GPU_LOADER}")
    text = GPU_LOADER.read_text(encoding="utf-8")
    if "GpuPluginStageLog(" not in text:
        text = ensure_includes(text, [
            "#include <cstdarg>", "#include <cstdio>", "#include <fstream>",
            "#include <mutex>", "#include <system_error>",
            "#if defined(__ANDROID__)\n#include <SDL3/SDL.h>\n#include <SDL3/SDL_system.h>\n#endif",
            "#include <filesystem>",
        ])
        text = replace_once(text, "}  // namespace\n\nstd::unique_ptr<IGraphicsSystem> LoadGpuPlugin",
                            gpu_log_helper() + "\n}  // namespace\n\nstd::unique_ptr<IGraphicsSystem> LoadGpuPlugin",
                            "helper GPU plugin")
    additions = [
        ("std::unique_ptr<IGraphicsSystem> LoadGpuPlugin(std::string_view name, std::string_view backend) {",
         '  GpuPluginStageLog("begin name=%.*s backend=%.*s", static_cast<int>(name.size()), name.data(), static_cast<int>(backend.size()), backend.data());\n'),
        ("  auto path = rex::filesystem::GetExecutableFolder() / PluginFileName(name);",
         '  auto path = rex::filesystem::GetExecutableFolder() / PluginFileName(name);\n  GpuPluginStageLog("resolved path=%s config=%s", path.string().c_str(), std::string(REXGLUE_BUILD_CONFIG).c_str());'),
        ("  platform::DynamicLibrary library;",
         '  GpuPluginStageLog("plugin file exists=true; attempting dlopen/Load");\n  platform::DynamicLibrary library;'),
        ("  if (!library.Load(path, platform::SymbolResolution::kImmediate)) {",
         '  GpuPluginStageLog("DynamicLibrary::Load begin path=%s", path.string().c_str());\n  if (!library.Load(path, platform::SymbolResolution::kImmediate)) {\n    GpuPluginStageLog("FAIL DynamicLibrary::Load; inspect linker dependencies/undefined symbols in logcat");'),
        ("  if (!abi_version_fn || !create_fn) {",
         '  GpuPluginStageLog("exports abi_version=%s create=%s", abi_version_fn ? "found" : "missing", create_fn ? "found" : "missing");\n  if (!abi_version_fn || !create_fn) {\n    GpuPluginStageLog("FAIL required GPU plugin ABI exports missing");'),
        ("  uint32_t plugin_abi = abi_version_fn();",
         '  uint32_t plugin_abi = abi_version_fn();\n  GpuPluginStageLog("ABI plugin=%u expected=%u", plugin_abi, kGpuPluginAbiVersion);'),
        ("  IGraphicsSystem* graphics_system = create_fn(kGpuPluginAbiVersion, &info);",
         '  GpuPluginStageLog("calling factory backend=%s struct_size=%u", backend_str.c_str(), info.struct_size);\n  IGraphicsSystem* graphics_system = create_fn(kGpuPluginAbiVersion, &info);\n  GpuPluginStageLog("factory returned %s", graphics_system ? "non-null graphics system" : "null");'),
        ("  LoadedPlugins().push_back(std::move(library));",
         '  GpuPluginStageLog("SUCCESS plugin loaded; filename=%s", path.filename().string().c_str());\n  LoadedPlugins().push_back(std::move(library));'),
    ]
    for anchor, insertion in additions:
        marker = insertion.strip().splitlines()[-1].strip()
        if marker in text:
            continue
        if anchor not in text:
            fail(f"GPU loader: ponto de instrumentacao ausente: {anchor.strip()}")
        text = replace_once(text, anchor, insertion, f"instrumentacao GPU {anchor.strip()}")
    # Missing-file and ABI-mismatch paths need their own explicit final markers.
    if 'GpuPluginStageLog("FAIL plugin file does not exist:' not in text:
        text = text.replace(
            '  if (!std::filesystem::exists(path)) {\n',
            '  if (!std::filesystem::exists(path)) {\n    GpuPluginStageLog("FAIL plugin file does not exist: %s", path.string().c_str());\n',
            1,
        )
    if 'GpuPluginStageLog("FAIL ABI mismatch' not in text:
        text = text.replace(
            '  if (plugin_abi != kGpuPluginAbiVersion) {\n',
            '  if (plugin_abi != kGpuPluginAbiVersion) {\n    GpuPluginStageLog("FAIL ABI mismatch plugin=%u expected=%u", plugin_abi, kGpuPluginAbiVersion);\n',
            1,
        )
    if 'GpuPluginStageLog("FAIL factory returned null' not in text:
        text = text.replace(
            '  if (!graphics_system) {\n',
            '  if (!graphics_system) {\n    GpuPluginStageLog("FAIL factory returned null backend=%s", backend_str.c_str());\n',
            1,
        )
    GPU_LOADER.write_text(text, encoding="utf-8")
    for marker in ("resolved path=", "exports abi_version=", "ABI plugin=", "factory returned"):
        if marker not in text:
            fail(f"Validacao GPU loader falhou; marcador ausente: {marker}")
    print("OK: loader GPU instrumentado com caminho, dlopen, ABI e factory.")


patch_app()
patch_gpu_loader()
print("Instrumentacao diagnostica real aplicada ao SDK temporario.")
