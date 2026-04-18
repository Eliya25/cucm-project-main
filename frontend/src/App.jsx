import { createBrowserRouter, RouterProvider, Navigate, Outlet } from 'react-router-dom';
import { useState} from 'react';

import './App.css'
import api from './api.js'
import Sidebar from './components/Sidebar.jsx';
import Login from './pages/Login.jsx';
import Sites from './pages/Sites.jsx';
import Dashboard from './pages/Dashboard.jsx';
import Users from './pages/Users.jsx';



function App() {
  const [user, setUser] = useState(JSON.parse(localStorage.getItem('userInfo')) || null); // אחזור מידע המשתמש מ-localStorage

  const router = createBrowserRouter([
    {
      path: "/login",
      element: !user ? <Login onLoginSuccess={setUser} /> : <Navigate to="/dashboard" replace />
    },
    {
      path: "/",
      element: user ? (
        <div className="flex h-screen bg-gray-50 overflow-hidden">
          <Sidebar user={user} setUser={setUser}/>
          <main className="flex-1 overflow-y-auto p-8">
          <div className='max-w-7xl mx-auto'>
            <Outlet />
          </div>
        </main>
      </div>
      ) : <Navigate to="/login" replace />,
      children: [
        {index: true, element: <Navigate to="/dashboard" replace />},
        {path: "dashboard", element: <Dashboard />},
        {path: "sites", element: <Sites />},
        {path: "users", element: user?.role === 'superadmin' ? <Users /> : <Navigate to="/dashboard" replace />},
      ]
    },
  ]);
  

  return<RouterProvider router={router} />;
}



export default App
