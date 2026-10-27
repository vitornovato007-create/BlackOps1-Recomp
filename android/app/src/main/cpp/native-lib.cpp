#include <jni.h>
#include <android/log.h>
#include <atomic>
#include <filesystem>
#include <fstream>
#include <mutex>
#include <string>
#include <SDL3/SDL.h>

#define TAG "BlackOps1Android"

extern "C" JNIEXPORT jint JNICALL JNI_OnLoad(JavaVM*, void*) {
    __android_log_print(ANDROID_LOG_INFO, TAG, "[BO1-STAGE] JNI_OnLoad: blackops1_android carregada");
    const char* internal = SDL_GetAndroidInternalStoragePath();
    if (internal && *internal) {
        std::error_code ec;
        const auto log_dir = std::filesystem::path(internal) / "logs";
        std::filesystem::create_directories(log_dir, ec);
        if (!ec) {
            std::ofstream output(log_dir / "blackops1-diagnostics.txt", std::ios::out | std::ios::app);
            if (output) {
                output << "[NATIVE-STAGE] [BO1-STAGE] JNI_OnLoad: blackops1_android carregada\n";
                output.flush();
            }
        }
    }
    return JNI_VERSION_1_6;
}

namespace {
std::mutex status_mutex;
std::string status =
    "Biblioteca nativa carregada. O runtime SDL/ReXGlue inicia pelo ponto de entrada nativo; "
    "esta mensagem so confirma o carregamento da biblioteca.";
}

extern "C" JNIEXPORT jstring JNICALL
Java_com_blackops1_recomp_MainActivity_getNativeStatus(JNIEnv* env, jobject) {
    std::lock_guard<std::mutex> lock(status_mutex);
    return env->NewStringUTF(status.c_str());
}

extern "C" JNIEXPORT void JNICALL
Java_com_blackops1_recomp_MainActivity_nativeSetRuntimeStatus(JNIEnv* env, jobject,
                                                               jstring message) {
    if (!message) return;
    const char* chars = env->GetStringUTFChars(message, nullptr);
    if (!chars) return;
    {
        std::lock_guard<std::mutex> lock(status_mutex);
        status.assign(chars);
    }
    __android_log_print(ANDROID_LOG_INFO, TAG, "%s", chars);
    env->ReleaseStringUTFChars(message, chars);
}
