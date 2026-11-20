// https://docs.expo.dev/guides/using-eslint/
const { defineConfig } = require("eslint/config");
const expoConfig = require("eslint-config-expo/flat");
const reactThree = require("@react-three/eslint-plugin");

module.exports = defineConfig([
  expoConfig,
  {
    // @react-three/eslint-plugin only ships legacy (eslintrc) configs,
    // so register it and its recommended rules manually.
    plugins: { "@react-three": reactThree },
    rules: reactThree.configs.recommended.rules,
  },
  {
    // R3F has separate web and native builds. Import it only through
    // features/cube/three/fiber(.native).ts, which picks the right one.
    ignores: ["features/cube/three/**"],
    rules: {
      "no-restricted-imports": [
        "error",
        {
          paths: [
            {
              name: "@react-three/fiber",
              message: 'Import from "@/features/cube/three/fiber" instead.',
            },
            {
              name: "@react-three/fiber/native",
              message: 'Import from "@/features/cube/three/fiber" instead.',
            },
          ],
        },
      ],
    },
  },
  {
    ignores: ["dist/*"],
  },
]);
