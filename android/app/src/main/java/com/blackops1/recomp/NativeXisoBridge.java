package com.blackops1.recomp.importer;

/** Ponte JNI para o extract-xiso embutido em uma biblioteca nativa isolada. */
public final class NativeXisoBridge {

    static {
        // Não carregar o runtime SDL3/ReXGlue só para extrair uma ISO.
        System.loadLibrary("blackops1_xiso");
    }

    private NativeXisoBridge() {
    }

    /** Informa se o extrator nativo está disponível. */
    public static native boolean isAvailable();

    /**
     * Extrai uma ISO XISO para um diretório existente.
     *
     * @param isoPath caminho local da ISO.
     * @param outputDir diretório de destino.
     * @param skipSystemUpdate ignora a partição de atualização do sistema.
     * @return 0 indica sucesso; outros valores indicam falha.
     */
    public static native int extract(
            String isoPath,
            String outputDir,
            boolean skipSystemUpdate
    );
}
