package com.blackops1.recomp.importer;

/** JNI bridge for the XboxDev extract-xiso engine. */
public final class NativeXisoBridge {
    private NativeXisoBridge() {}

    public static native boolean isAvailable();
    /** Returns 0 on success; non-zero means extraction failed. */
    public static native int extract(String isoPath, String outputDirectory, boolean skipSystemUpdate);
}
