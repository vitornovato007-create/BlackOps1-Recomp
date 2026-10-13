
#include <jni.h>
#include <android/log.h>

#include <exception>
#include <new>

#define LOG_TAG "BlackOps1Android"

#define LOG_INFO(...) \
    __android_log_print(ANDROID_LOG_INFO, LOG_TAG, __VA_ARGS__)

#define LOG_WARN(...) \
    __android_log_print(ANDROID_LOG_WARN, LOG_TAG, __VA_ARGS__)

#define LOG_ERROR(...) \
    __android_log_print(ANDROID_LOG_ERROR, LOG_TAG, __VA_ARGS__)

namespace {

constexpr const char* STATUS_OK =
        "Biblioteca nativa ARM64 carregada com sucesso.\n"
        "JNI inicializado corretamente.\n"
        "Runtime ReXGlue ainda nao foi integrado.";

constexpr const char* STATUS_ERROR =
        "A biblioteca nativa foi carregada, mas ocorreu um erro.";

} // namespace

extern "C" {

/*
 * Retorna o estado atual da biblioteca nativa.
 *
 * Deve corresponder ao metodo declarado em MainActivity.java:
 * private native String getNativeStatus();
 */
JNIEXPORT jstring JNICALL
Java_com_blackops1_recomp_MainActivity_getNativeStatus(
        JNIEnv* env,
        jobject /* thiz */) {

    if (env == nullptr) {
        LOG_ERROR("JNIEnv nulo em getNativeStatus.");
        return nullptr;
    }

    LOG_INFO("Consulta do estado da biblioteca nativa.");

    return env->NewStringUTF(STATUS_OK);
}

/*
 * Verifica se a biblioteca nativa consegue responder
 * a uma chamada JNI.
 *
 * Retorna true se a chamada chegar corretamente.
 */
JNIEXPORT jboolean JNICALL
Java_com_blackops1_recomp_MainActivity_nativeSelfTest(
        JNIEnv* env,
        jobject /* thiz */) {

    if (env == nullptr) {
        LOG_ERROR("JNIEnv nulo no teste nativo.");
        return JNI_FALSE;
    }

    LOG_INFO("Teste JNI executado com sucesso.");

    return JNI_TRUE;
}

/*
 * Chamado automaticamente pela JVM/Android quando
 * a biblioteca e carregada por System.loadLibrary().
 */
JNIEXPORT jint JNICALL
JNI_OnLoad(JavaVM* vm, void* /* reserved */) {

    if (vm == nullptr) {
        LOG_ERROR("JavaVM nulo durante JNI_OnLoad.");
        return JNI_ERR;
    }

    JNIEnv* env = nullptr;

    const jint result = vm->GetEnv(
            reinterpret_cast<void**>(&env),
            JNI_VERSION_1_6
    );

    if (result != JNI_OK || env == nullptr) {
        LOG_ERROR("Falha ao inicializar JNI.");
        return JNI_ERR;
    }

    LOG_INFO("Biblioteca BlackOps1Android inicializada.");

    return JNI_VERSION_1_6;
}

} // extern "C"
