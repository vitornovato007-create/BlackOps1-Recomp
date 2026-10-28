#!/usr/bin/env python3
"""Resolve o plugin GPU pelo nativeLibraryDir real no Android."""
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "rexglue-sdk/src/system/gpu_plugin_loader.cpp"

HELPER = r'''
#if defined(__ANDROID__)
std::filesystem::path AndroidNativeLibraryPath(std::string_view filename) {
  JNIEnv* env = static_cast<JNIEnv*>(SDL_GetAndroidJNIEnv());
  jobject activity = static_cast<jobject>(SDL_GetAndroidActivity());
  if (!env || !activity) {
    REXSYS_ERROR("Android GPU plugin: SDL JNI environment/activity unavailable");
    return {};
  }

  jclass activity_class = env->GetObjectClass(activity);
  jmethodID get_application_info =
      activity_class ? env->GetMethodID(activity_class, "getApplicationInfo",
                                        "()Landroid/content/pm/ApplicationInfo;") : nullptr;
  jobject app_info = get_application_info
      ? env->CallObjectMethod(activity, get_application_info) : nullptr;
  if (env->ExceptionCheck()) {
    env->ExceptionDescribe();
    env->ExceptionClear();
    app_info = nullptr;
  }

  jclass info_class = app_info ? env->GetObjectClass(app_info) : nullptr;
  jfieldID native_library_dir_field =
      info_class ? env->GetFieldID(info_class, "nativeLibraryDir", "Ljava/lang/String;") : nullptr;
  auto native_dir = native_library_dir_field
      ? static_cast<jstring>(env->GetObjectField(app_info, native_library_dir_field)) : nullptr;

  std::filesystem::path result;
  if (native_dir) {
    const char* chars = env->GetStringUTFChars(native_dir, nullptr);
    if (chars) {
      result = std::filesystem::path(chars) / filename;
      env->ReleaseStringUTFChars(native_dir, chars);
    }
  }

  if (native_dir) env->DeleteLocalRef(native_dir);
  if (info_class) env->DeleteLocalRef(info_class);
  if (app_info) env->DeleteLocalRef(app_info);
  if (activity_class) env->DeleteLocalRef(activity_class);

  if (result.empty()) {
    REXSYS_ERROR("Android GPU plugin: could not resolve ApplicationInfo.nativeLibraryDir");
  }
  return result;
}
#endif
'''

def fail(message: str) -> None:
    print(f"::error::{message}", file=sys.stderr)
    raise SystemExit(1)

if not SOURCE.is_file():
    fail(f"GPU loader ausente: {SOURCE}")

text = SOURCE.read_text(encoding="utf-8")
if "AndroidNativeLibraryPath(" not in text:
    include_anchor = "#include <rex/system/gpu_plugin.h>"
    if include_anchor not in text:
        fail("Nao foi encontrado o include base do GPU loader.")
    if "#include <jni.h>" not in text:
        text = text.replace(include_anchor, include_anchor + "\n#if defined(__ANDROID__)\n#include <jni.h>\n#include <SDL3/SDL_system.h>\n#endif", 1)

    namespace_anchor = "}  // namespace\n\nstd::unique_ptr<IGraphicsSystem> LoadGpuPlugin"
    if namespace_anchor not in text:
        fail("Nao foi encontrado o fim do namespace anonimo do GPU loader.")
    text = text.replace(namespace_anchor, HELPER + "\n}  // namespace\n\nstd::unique_ptr<IGraphicsSystem> LoadGpuPlugin", 1)

old_path = "  auto path = rex::filesystem::GetExecutableFolder() / PluginFileName(name);"
new_path = """#if defined(__ANDROID__)
  // Android pode representar o caminho da biblioteca como base.apk!/lib/...
  // Isso nao e um caminho POSIX utilizavel por filesystem::exists/dlopen.
  // Consultar o diretorio nativo real fornecido pelo ApplicationInfo.
  auto path = AndroidNativeLibraryPath(PluginFileName(name));
  if (path.empty()) {
    GpuPluginStageLog("FAIL could not resolve Android nativeLibraryDir for %s", PluginFileName(name).c_str());
    return nullptr;
  }
#else
  auto path = rex::filesystem::GetExecutableFolder() / PluginFileName(name);
#endif"""
if old_path in text:
    text = text.replace(old_path, new_path, 1)
elif new_path not in text:
    fail("A linha original de resolucao do caminho mudou; patch abortado sem sobrescrever.")
if "AndroidNativeLibraryPath(PluginFileName(name))" not in text:
    fail("Validacao falhou: o loader nao usa nativeLibraryDir no Android.")
if "#include <SDL3/SDL_system.h>" not in text or "#include <jni.h>" not in text:
    fail("Validacao falhou: includes JNI/SDL ausentes.")
SOURCE.write_text(text, encoding="utf-8")
print("OK: GPU loader Android resolve o plugin em ApplicationInfo.nativeLibraryDir.")
