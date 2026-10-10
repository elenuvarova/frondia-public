# Frondia on Next.js — one server for the whole site. Build context is site/ (the npm workspace root).
#   docker build -f web/Dockerfile -t frondia-web .      (run from site/)
# The base is pinned to one release and its multi-arch digest (re-check 4): a rebuild gets the same Node and Alpine,
# not whatever node:22-alpine points at that day. To update: docker buildx imagetools inspect node:22-alpine, then
# put the new version tag and its Digest here (both stages use it).
ARG NODE_IMAGE=node:22.23.3-alpine3.24@sha256:0a7108bf6c7bf5de370ffb1a3ed6be93d405b43ff159f681a8d18c0e2bc2e402
FROM ${NODE_IMAGE} AS build
WORKDIR /site
COPY package.json package-lock.json ./
COPY web/package.json web/
RUN npm ci --include=dev --no-audit --no-fund
COPY web web
COPY public public
ENV NEXT_TELEMETRY_DISABLED=1
RUN npm run build -w web

FROM ${NODE_IMAGE}
WORKDIR /app
ENV NODE_ENV=production NEXT_TELEMETRY_DISABLED=1 PORT=3000 HOSTNAME=0.0.0.0
# standalone keeps the workspace layout: the server sits in web/, public/ and static files beside it
COPY --from=build /site/web/.next/standalone ./
COPY --from=build /site/web/.next/static ./web/.next/static
COPY --from=build /site/public ./web/public
COPY --from=build /site/web/icons ./web/icons
USER node
EXPOSE 3000
HEALTHCHECK --interval=30s --timeout=3s --start-period=10s --retries=3 \
  CMD wget -q -O /dev/null http://127.0.0.1:3000/health || exit 1
CMD ["node", "web/server.js"]
