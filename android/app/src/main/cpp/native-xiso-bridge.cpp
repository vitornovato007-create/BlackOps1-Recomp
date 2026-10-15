#include <jni.h>
#include <android/log.h>
#include <string>

#define XISO_TAG "BlackOps1XISO"

// extract-xiso is compiled with main renamed to blackops_extract_xiso_main.
// Its command-line implementation uses process-global state and changes the current
// working directory, so this bridge intentionally serializes calls (the Java manager
// already uses a single-thread executor).
extern "C" int blackops_extract_xiso_main(int argc, char **argv);

extern "C" JNIEXPORT jboolean JNICALL
Java_com_blackops1_recomp_importer_NativeXisoBridge_isAvailable(JNIEnv *, jclass) {
    return JNI_TRUE;
}

extern "C" JNIEXPORT jint JNICALL
Java_com_blackops1_recomp_importer_NativeXisoBridge_extract(JNIEnv *env, jclass,
                                                            jstring isoPath,
                                                            jstring outputDirectory,
                                                            jboolean skipSystemUpdate) {
    if (!isoPath || !outputDirectory) return -1;
    const char *iso = env->GetStringUTFChars(isoPath, nullptr);
    const char *out = env->GetStringUTFChars(outputDirectory, nullptr);
    if (!iso || !out) {
        if (iso) env->ReleaseStringUTFChars(isoPath, iso);
        if (out) env->ReleaseStringUTFChars(outputDirectory, out);
        return -2;
    }

    std::string isoArg(iso);
    std::string outArg(out);
    env->ReleaseStringUTFChars(isoPath, iso);
    env->ReleaseStringUTFChars(outputDirectory, out);

    // argv strings must be mutable for the C command-line parser.
    std::string arg0 = "extract-xiso";
    std::string argD = "-d";
    std::string argS = "-s";
    std::string argX = "-x";
    char *argv[7];
    int argc = 0;
    argv[argc++] = arg0.data();
    argv[argc++] = argD.data();
    argv[argc++] = outArg.data();
    if (skipSystemUpdate == JNI_TRUE) argv[argc++] = argS.data();
    argv[argc++] = argX.data();
    argv[argc++] = isoArg.data();
    argv[argc] = nullptr;

    __android_log_print(ANDROID_LOG_INFO, XISO_TAG, "Iniciando extração XISO");
    int result = blackops_extract_xiso_main(argc, argv);
    __android_log_print(ANDROID_LOG_INFO, XISO_TAG, "Extração XISO terminou: %d", result);
    return result;
}
