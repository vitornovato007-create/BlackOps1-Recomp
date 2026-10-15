#include <jni.h>
#include <android/log.h>
#include <string>

#define XISO_TAG "BlackOps1XISO"

// Nome definido no CMakeLists.txt:
// main=blackops_extract_xiso_main
extern "C" int blackops_extract_xiso_main(int argc, char **argv);

extern "C" JNIEXPORT jboolean JNICALL
Java_com_blackops1_recomp_importer_NativeXisoBridge_isAvailable(
        JNIEnv *, jclass) {
    return JNI_TRUE;
}

extern "C" JNIEXPORT jint JNICALL
Java_com_blackops1_recomp_importer_NativeXisoBridge_extract(
        JNIEnv *env,
        jclass,
        jstring isoPath,
        jstring outputDirectory,
        jboolean skipSystemUpdate) {

    if (isoPath == nullptr || outputDirectory == nullptr) {
        return -1;
    }

    const char *iso = env->GetStringUTFChars(isoPath, nullptr);
    const char *out = env->GetStringUTFChars(outputDirectory, nullptr);

    if (iso == nullptr || out == nullptr) {
        if (iso != nullptr) {
            env->ReleaseStringUTFChars(isoPath, iso);
        }

        if (out != nullptr) {
            env->ReleaseStringUTFChars(outputDirectory, out);
        }

        return -2;
    }

    std::string isoArg(iso);
    std::string outArg(out);

    env->ReleaseStringUTFChars(isoPath, iso);
    env->ReleaseStringUTFChars(outputDirectory, out);

    std::string arg0 = "extract-xiso";
    std::string argD = "-d";
    std::string argS = "-s";
    std::string argX = "-x";

    char *argv[7];
    int argc = 0;

    argv[argc++] = arg0.data();
    argv[argc++] = argD.data();
    argv[argc++] = outArg.data();

    if (skipSystemUpdate == JNI_TRUE) {
        argv[argc++] = argS.data();
    }

    argv[argc++] = argX.data();
    argv[argc++] = isoArg.data();
    argv[argc] = nullptr;

    __android_log_print(
            ANDROID_LOG_INFO,
            XISO_TAG,
            "Iniciando extracao XISO"
    );

    const int result = blackops_extract_xiso_main(argc, argv);

    __android_log_print(
            ANDROID_LOG_INFO,
            XISO_TAG,
            "Extracao XISO terminou: %d",
            result
    );

    return result;
}
