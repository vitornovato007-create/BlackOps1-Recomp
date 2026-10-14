#include <jni.h>
#include <android/log.h>
#include <atomic>
#include <mutex>
#include <string>

#define TAG "BlackOps1Android"

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
