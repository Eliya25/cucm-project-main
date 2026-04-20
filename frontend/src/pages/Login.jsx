import { useState } from "react";
import api from "../api.js";
import { useNavigate } from "react-router-dom";
import { ShieldCheck, Lock, User } from "lucide-react";

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
    <div className="min-h-screen bg-[#F9FAFB] flex items-center justify-center p-4 font-sans">
      <div className="max-w-md w-full space-y-8 bg-white p-10 rounded-2xl shadow-xl border border-gray-100">
        <div className="text-center">
          <div className="inline-flex items-center justify-center w-16 h-16 bg-indigo-600 rounded-2xl shadow-lg mb-4">
            <ShieldCheck size={32} className="text-white" />
          </div>
          <h2 className="text-3xl font-extrabold text-gray-900 tracking-tight">CUCM Portal</h2>
          <p className="mt-2 text-sm text-gray-500">Sign in to your administration dashboard</p>
        </div>

        <form className="mt-8 space-y-6" onSubmit={handleLogin}>
          <div className="space-y-4">
            <div className="relative">
              <User className="absolute left-3 top-3.5 text-gray-400" size={18} />
              <input
                type="text"
                placeholder="Username"
                className="w-full pl-10 pr-4 py-3 bg-gray-50 border border-gray-200 rounded-xl focus:ring-2 focus:ring-indigo-500 focus:bg-white outline-none transition-all"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                required
              />
            </div>
            <div className="relative">
              <Lock className="absolute left-3 top-3.5 text-gray-400" size={18} />
              <input
                type="password"
                placeholder="Password"
                className="w-full pl-10 pr-4 py-3 bg-gray-50 border border-gray-200 rounded-xl focus:ring-2 focus:ring-indigo-500 focus:bg-white outline-none transition-all"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
              />
            </div>
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full py-3.5 px-4 bg-indigo-600 hover:bg-indigo-700 text-white font-bold rounded-xl shadow-lg shadow-indigo-200 transition-all active:scale-[0.98] disabled:opacity-50"
          >
            {loading ? 'Authenticating...' : 'Sign In'}
          </button>
        </form>
      </div>
    </div>
  );
}

export default Login
