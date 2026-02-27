/// <reference types="vite/client" />

interface ImportMetaEnv {
    readonly VITE_WS_URL?: string;
    readonly VITE_WS_BACKEND_URL?: string;
    readonly VITE_API_URL?: string;
    readonly VITE_API_KEY?: string;
    readonly VITE_API_BASE_URL?: string;
    readonly VITE_ENV_NAME?: string;
}

interface ImportMeta {
    readonly env: ImportMetaEnv;
}
