/*
 * Android ContentResolver-backed file descriptors for ReXGlue.
 * This source is copied into rexglue-sdk/src/core by the Android workflow.
 */
#include <rex/filesystem.h>

#include <SDL3/SDL_system.h>
#include <jni.h>

#include <string_view>

namespace rex::filesystem {
namespace {

bool HasPendingException(JNIEnv* env) {
  if (!env->ExceptionCheck()) return false;
  env->ExceptionDescribe();
  env->ExceptionClear();
  return true;
}

}  // namespace

void AndroidInitialize() {}

void AndroidShutdown() {}

bool IsAndroidContentUri(const std::string_view source) {
  constexpr std::string_view prefix = "content://";
  return source.size() >= prefix.size() &&
         source.substr(0, prefix.size()) == prefix;
}

int OpenAndroidContentFileDescriptor(const std::string_view uri,
                                     const char* mode) {
  if (!IsAndroidContentUri(uri) || mode == nullptr) return -1;

  auto* env = static_cast<JNIEnv*>(SDL_GetAndroidJNIEnv());
  auto activity = static_cast<jobject>(SDL_GetAndroidActivity());
  if (env == nullptr || activity == nullptr) return -1;

  int result = -1;
  jclass activity_class = env->GetObjectClass(activity);
  jclass context_class = env->FindClass("android/content/Context");
  jclass uri_class = env->FindClass("android/net/Uri");
  jclass resolver_class = env->FindClass("android/content/ContentResolver");
  jclass pfd_class = env->FindClass("android/os/ParcelFileDescriptor");

  if (activity_class == nullptr || context_class == nullptr ||
      uri_class == nullptr || resolver_class == nullptr ||
      pfd_class == nullptr || HasPendingException(env)) {
    goto cleanup;
  }

  {
    const jmethodID get_resolver =
        env->GetMethodID(context_class, "getContentResolver",
                         "()Landroid/content/ContentResolver;");
    const jmethodID parse =
        env->GetStaticMethodID(uri_class, "parse",
                               "(Ljava/lang/String;)Landroid/net/Uri;");
    const jmethodID open_fd =
        env->GetMethodID(resolver_class, "openFileDescriptor",
                         "(Landroid/net/Uri;Ljava/lang/String;)"
                         "Landroid/os/ParcelFileDescriptor;");
    const jmethodID detach_fd =
        env->GetMethodID(pfd_class, "detachFd", "()I");

    if (get_resolver == nullptr || parse == nullptr || open_fd == nullptr ||
        detach_fd == nullptr || HasPendingException(env)) {
      goto cleanup;
    }

    {
      const std::string uri_string(uri);
      jstring j_uri_string =
          env->NewStringUTF(uri_string.c_str());
      jstring j_mode = env->NewStringUTF(mode);
      if (j_uri_string == nullptr || j_mode == nullptr ||
          HasPendingException(env)) {
        if (j_uri_string != nullptr) env->DeleteLocalRef(j_uri_string);
        if (j_mode != nullptr) env->DeleteLocalRef(j_mode);
        goto cleanup;
      }

      jobject java_uri =
          env->CallStaticObjectMethod(uri_class, parse, j_uri_string);
      jobject resolver = env->CallObjectMethod(activity, get_resolver);
      if (!HasPendingException(env) && java_uri != nullptr &&
          resolver != nullptr) {
        jobject pfd =
            env->CallObjectMethod(resolver, open_fd, java_uri, j_mode);
        if (!HasPendingException(env) && pfd != nullptr) {
          result = env->CallIntMethod(pfd, detach_fd);
          if (HasPendingException(env)) result = -1;
          env->DeleteLocalRef(pfd);
        }
      }

      if (java_uri != nullptr) env->DeleteLocalRef(java_uri);
      if (resolver != nullptr) env->DeleteLocalRef(resolver);
      env->DeleteLocalRef(j_uri_string);
      env->DeleteLocalRef(j_mode);
    }
  }

cleanup:
  if (pfd_class != nullptr) env->DeleteLocalRef(pfd_class);
  if (resolver_class != nullptr) env->DeleteLocalRef(resolver_class);
  if (uri_class != nullptr) env->DeleteLocalRef(uri_class);
  if (context_class != nullptr) env->DeleteLocalRef(context_class);
  if (activity_class != nullptr) env->DeleteLocalRef(activity);
  if (activity_class != nullptr) env->DeleteLocalRef(activity_class);
  return result;
}

}  // namespace rex::filesystem
