# Same ARM64 upstream runtime as images/llamacpp; models mounted, not baked in.
FROM ghcr.io/ggml-org/llama.cpp:server-b8576
COPY embedding-entrypoint.sh /opt/embedding-entrypoint.sh
ENTRYPOINT ["/bin/sh", "/opt/embedding-entrypoint.sh"]
