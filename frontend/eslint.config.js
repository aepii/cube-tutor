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
    ignores: ["dist/*"],
  },
]);
