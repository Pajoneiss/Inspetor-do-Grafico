import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Static export for serving via Flask on Railway
  output: 'export',

  // Disable image optimization for static export
  images: {
    unoptimized: true,
  },

  // Base path (empty for root)
  basePath: '',

  // Trailing slash for static file compatibility
  trailingSlash: true,

  // Disable TypeScript errors blocking build
  typescript: {
    ignoreBuildErrors: true,
  },

  // Disable ESLint errors blocking build
  eslint: {
    ignoreDuringBuilds: true,
  },
};

export default nextConfig;
