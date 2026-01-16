#!/usr/bin/env node

/**
 * Sync ForgeSyte UI plugins into web-ui/public/forgesyte-plugins
 *
 * Usage:
 *   node scripts/sync-plugins.js local /path/to/forgesyte-plugins
 *   node scripts/sync-plugins.js github https://github.com/user/repo.git
 *   node scripts/sync-plugins.js auto
 *
 * Auto mode: Clones from GitHub first (if FORGESYTE_PLUGINS_REPO set),
 * then overlays local plugins (if FORGESYTE_PLUGINS_PATH set).
 * Local plugins take priority over GitHub versions.
 */

const fs = require("fs");
const path = require("path");
const { execSync } = require("child_process");

const mode = process.argv[2];
const source = process.argv[3];

const DEST = path.resolve(__dirname, "../public/forgesyte-plugins");

function cleanDest() {
    if (fs.existsSync(DEST)) {
        fs.rmSync(DEST, { recursive: true, force: true });
    }
    fs.mkdirSync(DEST, { recursive: true });
}

function syncFromGithub(repoUrl) {
    if (!repoUrl) {
        console.log("⏭️  No GitHub repo configured, skipping.");
        return false;
    }

    console.log("📦 Cloning plugins from GitHub:", repoUrl);
    try {
        execSync(`git clone --depth 1 "${repoUrl}" "${DEST}"`, {
            stdio: "inherit",
        });

        const gitFolder = path.join(DEST, ".git");
        if (fs.existsSync(gitFolder)) {
            fs.rmSync(gitFolder, { recursive: true, force: true });
        }
        console.log("✅ GitHub plugins synced.");
        return true;
    } catch (err) {
        console.error("❌ Failed to clone from GitHub:", err.message);
        return false;
    }
}

function syncFromLocal(localPath) {
    if (!localPath) {
        console.log("⏭️  No local path configured, skipping.");
        return false;
    }

    const srcPath = path.resolve(localPath);

    if (!fs.existsSync(srcPath)) {
        console.log("⏭️  Local path does not exist:", srcPath);
        return false;
    }

    console.log("📂 Copying plugins from local:", srcPath);
    
    // Copy contents, excluding node_modules, .git, and other dev artifacts
    execSync(`rsync -a --exclude='node_modules' --exclude='.git' --exclude='__pycache__' --exclude='.pytest_cache' --exclude='.mypy_cache' --exclude='.ruff_cache' --exclude='.venv' --exclude='*.egg-info' "${srcPath}/" "${DEST}/"`, { stdio: "inherit" });
    
    console.log("✅ Local plugins synced.");
    return true;
}

// Main logic
if (mode === "auto") {
    const githubRepo = process.env.FORGESYTE_PLUGINS_REPO;
    const localPath = process.env.FORGESYTE_PLUGINS_PATH;

    cleanDest();

    const githubOk = syncFromGithub(githubRepo);
    const localOk = syncFromLocal(localPath);

    if (!githubOk && !localOk) {
        console.log("⚠️  No plugins synced. Set FORGESYTE_PLUGINS_REPO or FORGESYTE_PLUGINS_PATH in .env to enable plugins.");
    } else {
        console.log("🎉 Plugin sync complete.");
    }
}

else if (mode === "local") {
    if (!source) {
        console.error("Usage: node sync-plugins.js local /path/to/plugins");
        process.exit(1);
    }
    cleanDest();
    if (!syncFromLocal(source)) {
        process.exit(1);
    }
}

else if (mode === "github") {
    if (!source) {
        console.error("Usage: node sync-plugins.js github https://github.com/user/repo.git");
        process.exit(1);
    }
    cleanDest();
    if (!syncFromGithub(source)) {
        process.exit(1);
    }
}

else {
    console.error("Usage:");
    console.error("  node sync-plugins.js auto");
    console.error("  node sync-plugins.js local /path/to/plugins");
    console.error("  node sync-plugins.js github https://github.com/user/repo.git");
    process.exit(1);
}
