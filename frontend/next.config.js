/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  swcMinify: true,
  output: 'export',  // Static export for S3
  trailingSlash: true,

  images: {
    unoptimized: true,  // Required for static export
  },

  // Remove rewrites for static export
  // API calls will use full URLs from environment variables
};

module.exports = nextConfig;
