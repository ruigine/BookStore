import { type RouteConfig, route } from "@react-router/dev/routes";

export default [
  route("browse", "routes/browse.tsx"),
  route("login", "routes/login.tsx")
] satisfies RouteConfig[];