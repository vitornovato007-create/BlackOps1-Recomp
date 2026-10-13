
#include <jni.h>
#include <atomic>
#include <mutex>
#include <string>

namespace {
    std::mutex runtime_mutex;
    std::atomic<bool> runtime_initialized{false};
    std::string runtime_status = "Runtime nativo carregado";
}

extern "C"
JNIEXPORT jstring JNICALL
Java_com_blackops1_recomp_MainActivity_nativeGetStatus(
        JNIEnv* env, jobject /* thiz */) {
    std::lock_guard<std::mutex> lock(runtime_mutex);
    return env->NewStringUTF(runtime_status.c_str());
}

extern "C"
JNIEXPORT jboolean JNICALL
Java_com_blackops1_recomp_MainActivity_nativeInitialize(
        JNIEnv* env, jobject /* thiz */) {
    std::lock_guard<std::mutex> lock(runtime_mutex);

    if (runtime_initialized.load()) {
        runtime_status = "Runtime já inicializado";
        return JNI_TRUE;
    }

    // A inicialização real do ReXGlue entra aqui.
    // Não declare o jogo iniciado antes de conectar
    // as funções geradas e as dependências do SDK.
    runtime_status =
        "Biblioteca carregada; integração do ReXGlue pendente";

    return JNI_FALSE;
}

extern "C"
JNIEXPORT void JNICALL
Java_com_blackops1_recomp_MainActivity_nativeShutdown(
        JNIEnv* /* env */, jobject /* thiz */) {
    std::lock_guard<std::mutex> lock(runtime_mutex);

    runtime_initialized.store(false);
    runtime_status = "Runtime encerrado";
}
