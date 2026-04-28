import { createBrowserRouter, RouterProvider, Navigate, Outlet } from 'react-router-dom';
import { AuthProvider, useAuth } from './context/AuthContext.jsx';

import Sidebar        from './components/Sidebar.jsx';
import Login          from './pages/Login.jsx';
import Dashboard      from './pages/Dashboard.jsx';
import Sites          from './pages/Sites.jsx';
import Users          from './pages/Users.jsx';
import Groups         from './pages/Groups.jsx';
import Devices        from './pages/Devices.jsx';
import SectionDetail  from './pages/SectionDetail.jsx';
import Settings       from './pages/Settings.jsx';
import BulkActions    from './pages/BulkActions.jsx';

import './App.css';

// ── Layout מוגן ───────────────────────────────────────────────────
const ProtectedLayout = () => {
  const { user } = useAuth();
  if (!user) return <Navigate to="/login" replace />;
  return (
    <div className="flex h-screen bg-gray-50 overflow-hidden">
      <Sidebar />
      <main className="flex-1 overflow-y-auto p-8">
        <div className="max-w-7xl mx-auto">
          <Outlet />
        </div>
      </main>
    </div>
  );
};

// ── Routes לפי הרשאות ─────────────────────────────────────────────
const AdminRoute = ({ children }) => {
  const { isAdmin } = useAuth();
  return isAdmin ? children : <Navigate to="/dashboard" replace />;
};

const OperatorRoute = ({ children }) => {
  const { isOperator } = useAuth();
  return isOperator ? children : <Navigate to="/dashboard" replace />;
};

const SuperAdminRoute = ({ children }) => {
  const { isSuperAdmin } = useAuth();
  return isSuperAdmin ? children : <Navigate to="/dashboard" replace />;
};

// ── Router ────────────────────────────────────────────────────────
const buildRouter = (user) => createBrowserRouter([
  {
    path: '/login',
    element: !user ? <Login /> : <Navigate to="/dashboard" replace />,
  },
  {
    path: '/',
    element: <ProtectedLayout />,
    children: [
      { index: true, element: <Navigate to="/dashboard" replace /> },

      { path: 'dashboard', element: <Dashboard /> },
      { path: 'settings',  element: <Settings /> },

      // Admin ומעלה
      { path: 'sites',        element: <AdminRoute><Sites /></AdminRoute> },
      { path: 'groups',       element: <AdminRoute><Groups /></AdminRoute> },
      { path: 'users',        element: <AdminRoute><Users /></AdminRoute> },
      { path: 'bulk-actions', element: <AdminRoute><BulkActions /></AdminRoute> },

      // Operator ומעלה — Devices ו-SectionDetail
      { path: 'devices',                              element: <OperatorRoute><Devices /></OperatorRoute> },
      { path: 'sites/:siteId/sections/:sectionId',    element: <OperatorRoute><SectionDetail /></OperatorRoute> },
    ],
  },
  {
    path: '*',
    element: <Navigate to="/dashboard" replace />,
  },
]);

const AppRoutes = () => {
  const { user } = useAuth();
  const router = buildRouter(user);
  return <RouterProvider router={router} />;
};

const App = () => (
  <AuthProvider>
    <AppRoutes />
  </AuthProvider>
);

export default App;