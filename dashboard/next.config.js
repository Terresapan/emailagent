/** @type {import('next').NextConfig} */
const nextConfig = {
  output: 'standalone',
  env: {
    API_URL: process.env.API_URL || 'http://localhost:8000',
  },
  modularizeImports: {
    "lucide-react": {
      transform: "lucide-react/dist/esm/icons/{{lowerCase member}}",
      skipDefaultConversion: true,
    },
  },
}

module.exports = nextConfig
