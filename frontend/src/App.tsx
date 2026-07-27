import { useEffect, useState } from "react";

import { authToken } from "./api/client";
import { Dashboard } from "./pages/Dashboard";
import { Login } from "./pages/Login";

export default function App() {
  const [authenticated, setAuthenticated] = useState(Boolean(authToken.get()));

  useEffect(() => {
    const unauthorized = () => setAuthenticated(false);
    window.addEventListener("wattsup:unauthorized", unauthorized);
    return () =>
      window.removeEventListener("wattsup:unauthorized", unauthorized);
  }, []);

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
