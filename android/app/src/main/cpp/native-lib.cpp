#include <jni.h>
#include <android/log.h>

#define LOG_TAG "BlackOps1Android"

#define LOG_INFO(...) 
__android_log_print(ANDROID_LOG_INFO, LOG_TAG, **VA_ARGS**)

extern "C"
JNIEXPORT jstring JNICALL
Java_com_blackops1_recomp_MainActivity_getNativeStatus(
JNIEnv* env,
jobject /* thiz */) {


LOG_INFO("Biblioteca nativa carregada.");

return env->NewStringUTF(
    "Biblioteca C++ ARM64 carregada com sucesso.\n"
    "ReXGlue ainda nao foi integrado."
);


}
