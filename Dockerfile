# Voltaire Terminal — single-image build for Hugging Face Spaces (Docker SDK).
# Builds the Vite frontend and runs the Express server, which serves both the
# UI and /api on one port. FinBERT runs in-process (Spaces give plenty of RAM).
#
# node:22-slim (Debian/glibc) — NOT alpine, because @huggingface/transformers
# pulls in onnxruntime-node, whose native bindings need glibc.
FROM node:22-slim

WORKDIR /app

# Python 3 + venv: the "EIA Release Lab" button (POST /api/release-lab/run) spawns
# analytics/release_lab.py, so the runtime needs Python. We build a venv at
# /app/.venv — the exact path the server probes (server/index.js PY) — and install
# only the libs that pipeline imports (numpy / pandas / requests).
RUN apt-get update \
 && apt-get install -y --no-install-recommends python3 python3-venv python3-pip \
 && rm -rf /var/lib/apt/lists/* \
 && python3 -m venv /app/.venv \
 && /app/.venv/bin/pip install --no-cache-dir --upgrade pip \
 && /app/.venv/bin/pip install --no-cache-dir numpy pandas requests

# Install Node dependencies first for better layer caching. (NODE_ENV is left unset
# so devDependencies like Vite are installed for the build step.)
COPY package.json package-lock.json ./
RUN npm ci

# Copy the rest and build the frontend into dist/. (.dockerignore keeps the venv,
# node_modules, deliverables/PDFs and offline data out of the build context.)
COPY . .
RUN npm run build

# Hugging Face Spaces serves the container on port 7860 (see README app_port).
# TRANSFORMERS_CACHE points the FinBERT model cache at a writable dir. Set the EIA
# key as a Space *secret* named EIA_API_KEY — both the Node server and the Python
# pipeline read it from the environment.
ENV PORT=7860
ENV TRANSFORMERS_CACHE=/tmp/transformers-cache
ENV NODE_ENV=production
EXPOSE 7860

CMD ["npm", "start"]
