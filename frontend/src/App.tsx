import { Navigate, Route, Routes } from "react-router-dom";
import { ProtectedRoute } from "./components/ProtectedRoute";
import { Catalog } from "./pages/catalog/Catalog";
import { Landing } from "./pages/landing/Landing";
import { Login } from "./pages/login/Login";
import { Placeholder } from "./pages/Placeholder";
import { useAuth } from "./lib/AuthContext";
import { useTheme } from "./lib/useTheme";

function App() {
  const { theme, toggleTheme } = useTheme();
  const { isAuthenticated, isLoading } = useAuth();

  return (
    <Routes>
      <Route path="/" element={<Landing theme={theme} onToggleTheme={toggleTheme} />} />
      <Route
        path="/login"
        element={isAuthenticated && !isLoading ? <Navigate to="/catalog" replace /> : <Login />}
      />
      <Route
        path="/inbox"
        element={<Placeholder title="Conversations" phase="Inbox — phase 5" />}
      />
      <Route
        path="/catalog"
        element={
          <ProtectedRoute>
            <Catalog theme={theme} onToggleTheme={toggleTheme} />
          </ProtectedRoute>
        }
      />
      <Route
        path="/review"
        element={<Placeholder title="Review queue" phase="Blocked on Quote model — phase 6" />}
      />
      <Route
        path="/quotes"
        element={<Placeholder title="Quote history" phase="Blocked on Quote model — phase 6" />}
      />
    </Routes>
  );
}

export default App;
