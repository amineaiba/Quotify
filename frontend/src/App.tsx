import { Navigate, Route, Routes } from "react-router-dom";
import { ProtectedRoute } from "./components/ProtectedRoute";
import { Catalog } from "./pages/catalog/Catalog";
import { Conversations } from "./pages/conversations/Conversations";
import { Thread } from "./pages/conversations/Thread";
import { QuoteHistory } from "./pages/history/QuoteHistory";
import { Landing } from "./pages/landing/Landing";
import { Login } from "./pages/login/Login";
import { Review } from "./pages/review/Review";
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
        element={
          <ProtectedRoute>
            <Conversations theme={theme} onToggleTheme={toggleTheme} />
          </ProtectedRoute>
        }
      />
      <Route
        path="/inbox/:id"
        element={
          <ProtectedRoute>
            <Thread theme={theme} onToggleTheme={toggleTheme} />
          </ProtectedRoute>
        }
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
        element={
          <ProtectedRoute>
            <Review theme={theme} onToggleTheme={toggleTheme} />
          </ProtectedRoute>
        }
      />
      <Route
        path="/quotes"
        element={
          <ProtectedRoute>
            <QuoteHistory theme={theme} onToggleTheme={toggleTheme} />
          </ProtectedRoute>
        }
      />
    </Routes>
  );
}

export default App;
