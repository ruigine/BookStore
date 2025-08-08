import {
  isRouteErrorResponse,
  Links,
  Meta,
  Outlet,
  Scripts,
  ScrollRestoration,
} from "react-router";

import type { Route } from "./+types/root";
import "./app.css";
import NavBar from "./components/navbar";
import { AuthProvider } from "./context/authcontext"
import { Link } from "react-router"

export const links: Route.LinksFunction = () => [
  { rel: "preconnect", href: "https://fonts.googleapis.com" },
  {
    rel: "preconnect",
    href: "https://fonts.gstatic.com",
    crossOrigin: "anonymous",
  },
  {
    rel: "stylesheet",
    href: "https://fonts.googleapis.com/css2?family=Rosarivo:ital@0;1&display=swap",
  },
  {
    rel: "stylesheet",
    href: "https://fonts.googleapis.com/css2?family=Eagle+Lake&display=swap",
  },
  {
    rel: "stylesheet",
    href: "https://fonts.googleapis.com/css2?family=Great+Vibes&display=swap",
  },
];

export function Layout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <head>
        <meta charSet="utf-8" />
        <meta name="viewport" content="width=device-width, initial-scale=1" />
        <Meta />
        <Links />
      </head>
      <body>
        {children}
        <ScrollRestoration />
        <Scripts />
      </body>
    </html>
  );
}

export default function App() {
  return (
    <AuthProvider>
      <NavBar />
      <Outlet />
    </AuthProvider>
  );
}

export function ErrorBoundary({ error }: Route.ErrorBoundaryProps) {
  let message = "Oops!";
  let details = "An unexpected error occurred.";
  let stack: string | undefined;

  if (isRouteErrorResponse(error)) {
    message = error.status === 404 ? "404" : "Error";
    details =
      error.status === 404
        ? "The requested page could not be found."
        : error.statusText || details;
  } else if (import.meta.env.DEV && error && error instanceof Error) {
    details = error.message;
    stack = error.stack;
  }

  return (
    <main className="h-screen flex items-center justify-center text-center text-[#5B4636]">
      <div>
        <h1 className="text-5xl font-[Eagle_Lake]">404</h1>
        <div className="flex items-center justify-center gap-4 my-4 text-[#c5bca4] text-xl select-none">
          <span className="border-t border-[#c5bca4] w-10" />
            ❧
          <span className="border-t border-[#c5bca4] w-10" />
        </div>
        <p className="font-serif text-xl italic">
          Like a missing chapter, this page doesn’t exist.
        </p>
        <Link
          to="/browse"
          className="inline-block mt-6 border border-green-900 px-4 py-2 rounded hover:bg-[#5a7249] hover:text-white font-serif"
        >
          ↩ Back to Bookstore
        </Link>
      </div>
    </main>
  );
}
