import { existsSync, readFileSync } from "node:fs";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const frontendDir = dirname(fileURLToPath(import.meta.url));
const rootEnvPath = resolve(frontendDir, "../.env");

function loadPublicRootEnv() {
  if (!existsSync(rootEnvPath)) return {};

  return readFileSync(rootEnvPath, "utf8")
    .split(/\r?\n/)
    .reduce((env, line) => {
      const trimmed = line.trim();
      if (!trimmed || trimmed.startsWith("#")) return env;

      const separatorIndex = trimmed.indexOf("=");
      if (separatorIndex <= 0) return env;

      const key = trimmed.slice(0, separatorIndex).trim();
      if (!key.startsWith("NEXT_PUBLIC_") || process.env[key]) return env;

      const value = trimmed
        .slice(separatorIndex + 1)
        .trim()
        .replace(/^['"]|['"]$/g, "");

      process.env[key] = value;
      return { ...env, [key]: value };
    }, {});
}

const publicRootEnv = loadPublicRootEnv();

/** @type {import('next').NextConfig} */
const nextConfig = {
  output: "standalone",
  allowedDevOrigins: ["127.0.0.1"],
  env: publicRootEnv,
};

export default nextConfig;
