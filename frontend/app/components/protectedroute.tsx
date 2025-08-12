import { Navigate } from "react-router";
import { useAuth } from "~/context/authcontext";
import type { ReactNode } from "react";

export default function ProtectedRoute({ children }: { children: ReactNode }) {
  const { user, tokenReady } = useAuth();

  // Wait until the refresh-token check is done
  if (!tokenReady) {
    return (
      <div className="flex h-screen items-center justify-center">
        <div className="animate-pulse font-serif">Loading...</div>
      </div>
    );
  }

  // If no logged-in user, send to login
  if (!user) {
    return <Navigate to="/login" replace />;
  }

  return children;
}
