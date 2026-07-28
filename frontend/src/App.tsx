import { useEffect, useState } from "react";
import { useQuery } from "@tanstack/react-query";

import { authToken } from "./api/client";
import { Dashboard } from "./pages/Dashboard";
import { Login } from "./pages/Login";
import { Setup } from "./pages/Setup";
import { setupRequired } from "./api/setup";

export default function App() {
  const [authenticated, setAuthenticated] = useState(Boolean(authToken.get()));
  const {
    data: needsSetup,
    isLoading,
    refetch,
  } = useQuery({
    queryKey: ["setup-status"],
    queryFn: setupRequired,
  });

  useEffect(() => {
    const unauthorized = () => setAuthenticated(false);
    window.addEventListener("wattsup:unauthorized", unauthorized);
    return () =>
      window.removeEventListener("wattsup:unauthorized", unauthorized);
  }, []);

  if (isLoading) return null;
  if (needsSetup) {
    return <Setup onComplete={() => void refetch()} />;
  }
  if (!authenticated) {
    return <Login onAuthenticated={() => setAuthenticated(true)} />;
  }
  return (
    <Dashboard
      onLogout={() => {
        authToken.clear();
        setAuthenticated(false);
      }}
    />
  );
}
