package com.blackops1.recomp;

/** Ponte JNI para o extract-xiso embutido na biblioteca nativa. */
public final class NativeXisoBridge {
    static {
        System.loadLibrary("blackops1_android");
    }

    private NativeXisoBridge() {}

    /**
     * Extrai uma ISO XISO para um diretório existente.
     * isoPath deve ser um caminho local acessível, não um content:// URI.
     * @return código de saída do extract-xiso (0 indica sucesso).
     */
    public static native int extractFile(String isoPath, String outputDir);
}
