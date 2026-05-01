/** @type {import('next').NextConfig} */
const nextConfig = {
  // Static site generation for website format
  output: 'export',
  distDir: 'dist',
  
  // Disable image optimization for static export
  images: {
    unoptimized: true,
  },
  
  // Environment variables
  env: {
    NEXT_PUBLIC_API_URL: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000',
  },
  
  // Trailing slashes for SEO-friendly URLs
  trailingSlash: true,
};

module.exports = nextConfig;
