/** @type {import('next').NextConfig} */
const nextConfig = {
  // Standalone output produces a minimal server bundle for slim containers.
  output: "standalone",
  reactStrictMode: true,
};

module.exports = nextConfig;
