import { useState } from "react";
import api from "../api.js";
import { useNavigate } from "react-router-dom";
import { ShieldCheck } from "lucide-react";

const Login = ({onLoginSuccess}) => {
    const [username, setUsername] = useState('');
    const [password, setPassword] = useState('');
    const [loading, setLoading] = useState(false);
    const navigate = useNavigate();

    const handleLogin = async (e) => {
        e.preventDefault();
        setLoading(true);
        try{
            const formData = new FormData();
            formData.append('username', username);
            formData.append('password', password);

            const response = await api.post('/api/v1/auth/login', formData);

            // השמירה של הטוקן ב-localStorage כבר לא נחוצה כי אנחנו משתמשים בעוגיות
            // localStorage.setItem('token', response.data.access_token);
            const userInfo = {
                role: response.data.role,
                username: response.data.username
            }
            
            localStorage.setItem('userInfo', JSON.stringify(userInfo)); // שמירת מידע המשתמש ב-localStorage

            if (onLoginSuccess) onLoginSuccess(userInfo); // העברת מידע המשתמש ל-App.jsx

            navigate('/dashboard'); // הפניה לדשבורד לאחר התחברות מוצלחת   

        } catch (error) {
            alert('Login failed. Please check your credentials and try again.');
            console.error('Login failed:', error);
        } finally {
            setLoading(false);
        }
    }
  return (
    <div className="min-h-screen bg-gray-50 flex flex-col justify-center py-12 sm:px-6 lg:px-8 font-sans">
      <div className="sm:mx-auto sm:w-full sm:max-w-md">
        <div className="flex justify-center">
          <div className="bg-indigo-600 p-3 rounded-2xl shadow-lg">
            <ShieldCheck size={40} className="text-white" />
          </div>
        </div>
        <h2 className="mt-6 text-center text-3xl font-extrabold text-gray-900 tracking-tight">
          Welcome to CUCM Portal
        </h2>
        <p className="mt-2 text-center text-sm text-gray-600">
          Sign in to manage your network sites
        </p>
      </div>

      <div className="mt-8 sm:mx-auto sm:w-full sm:max-w-md">
        <div className="bg-white py-8 px-4 shadow-xl border border-gray-100 sm:rounded-2xl sm:px-10">
          <form className="space-y-6" onSubmit={handleLogin}>
            <div>
              <label className="block text-sm font-medium text-gray-700">Username</label>
              <input
                type="text"
                required
                className="mt-1 block w-full px-4 py-3 border border-gray-300 rounded-xl shadow-sm focus:ring-indigo-500 focus:border-indigo-500 text-sm transition-all"
                placeholder="Enter your username"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700">Password</label>
              <input
                type="password"
                required
                className="mt-1 block w-full px-4 py-3 border border-gray-300 rounded-xl shadow-sm focus:ring-indigo-500 focus:border-indigo-500 text-sm transition-all"
                placeholder="••••••••"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
              />
            </div>

            <button
              type="submit"
              disabled={loading}
              className="w-full flex justify-center py-3 px-4 border border-transparent rounded-xl shadow-sm text-sm font-semibold text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 transition-all disabled:opacity-50"
            >
              {loading ? 'Signing in...' : 'Sign in'}
            </button>
          </form>
        </div>
      </div>
    </div>
  );
}

export default Login
