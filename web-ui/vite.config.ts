import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import path from "path";

export default defineConfig({
    plugins: [react()],
    resolve: {
        alias: {
            "@": path.resolve(__dirname, "./src"),
            "@/components": path.resolve(__dirname, "./src/components"),
            "@/hooks": path.resolve(__dirname, "./src/hooks"),
            "@/api": path.resolve(__dirname, "./src/api"),
        },
    },
    server: {
        port: 3000,
        proxy: {
            "/v1": {
                target: "http://localhost:8000",
                changeOrigin: true,
                ws: true,
            },
            "/ws": {
                target: "http://localhost:8000",
                ws: true,
            },
        },
    },
    build: {
        outDir: "dist",
        sourcemap: true,
    },
});
