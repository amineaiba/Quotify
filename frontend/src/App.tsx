import { Route, Routes } from "react-router-dom";
import { Landing } from "./pages/landing/Landing";
import { Placeholder } from "./pages/Placeholder";

function App() {
  return (
    <Routes>
      <Route path="/" element={<Landing />} />
      <Route path="/login" element={<Placeholder title="Sign in" phase="Auth — phase 3" />} />
      <Route
        path="/inbox"
        element={<Placeholder title="Conversations" phase="Inbox — phase 5" />}
      />
      <Route path="/catalog" element={<Placeholder title="Catalog" phase="Catalog — phase 4" />} />
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
