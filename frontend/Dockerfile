FROM node:20-alpine AS build

WORKDIR /app
COPY package.json pnpm-lock.yaml* /app/
RUN corepack enable && pnpm install --frozen-lockfile

COPY . /app
RUN pnpm build

FROM nginx:1.27-alpine
COPY --from=build /app/dist /usr/share/nginx/html
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
