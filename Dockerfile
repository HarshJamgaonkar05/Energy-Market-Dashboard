# Voltaire Terminal — single-image build for Hugging Face Spaces (Docker SDK).
# Builds the Vite frontend and runs the Express server, which serves both the
# UI and /api on one port. FinBERT runs in-process (Spaces give plenty of RAM).
#
# node:22-slim (Debian/glibc) — NOT alpine, because @huggingface/transformers
# pulls in onnxruntime-node, whose native bindings need glibc.
FROM node:22-slim

WORKDIR /app

# Install dependencies first for better layer caching. (NODE_ENV is left unset so
# devDependencies like Vite are installed for the build step.)
COPY package.json package-lock.json ./
RUN npm ci

# Copy the rest and build the frontend into dist/.
COPY . .
RUN npm run build

# Hugging Face Spaces serves the container on port 7860 (see README app_port).
# TRANSFORMERS_CACHE points the FinBERT model cache at a writable dir.
ENV PORT=7860
ENV TRANSFORMERS_CACHE=/tmp/transformers-cache
ENV NODE_ENV=production
EXPOSE 7860

CMD ["npm", "start"]
