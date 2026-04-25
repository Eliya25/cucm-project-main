import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { ShieldCheck, Lock, User } from "lucide-react";
import { useAuth } from "../context/AuthContext.jsx";

import api from "../api.js";

const Login = ({onLoginSuccess}) => {
    const [username, setUsername] = useState('');
    const [password, setPassword] = useState('');
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState('');
    const { login} = useAuth()
    const navigate = useNavigate();

    const handleLogin = async (e) => {
        e.preventDefault();
        setLoading(true);
        setError('');
        try{
            const form = new FormData();
            form.append('username', username);
            form.append('password', password);

            const {data} = await api.post('/api/v1/auth/login', form);
            login({role: data.role, username: data.username});
            navigate("/dashboard")
            
        } catch {
            setError('Wrong username or password. ')
        } finally {
            setLoading(false);
        }
    }


 return (
    <div className="min-h-screen bg-[#F9FAFB] flex items-center justify-center p-4 font-sans">
      <div className="max-w-md w-full bg-white p-10 rounded-2xl shadow-xl border border-gray-100 space-y-8">
 
        <div className="text-center">
          <div className="inline-flex items-center justify-center w-16 h-16 bg-indigo-600 rounded-2xl shadow-lg shadow-indigo-200 mb-4">
            <ShieldCheck size={32} className="text-white" />
          </div>
          <h2 className="text-3xl font-extrabold text-gray-900 tracking-tight">CUCM Portal</h2>
          <p className="mt-2 text-sm text-gray-500">Sign in to your administration dashboard</p>
        </div>
 
        <form onSubmit={handleLogin} className="space-y-4">
          <div className="relative">
            <User className="absolute left-3 top-3.5 text-gray-400" size={18} />
            <input
              type="text" placeholder="Username" required
              className="w-full pl-10 pr-4 py-3 bg-gray-50 border border-gray-200 rounded-xl focus:ring-2 focus:ring-indigo-500 focus:bg-white outline-none transition-all"
              value={username} onChange={e => setUsername(e.target.value)}
            />
          </div>
          <div className="relative">
            <Lock className="absolute left-3 top-3.5 text-gray-400" size={18} />
            <input
              type="password" placeholder="Password" required
              className="w-full pl-10 pr-4 py-3 bg-gray-50 border border-gray-200 rounded-xl focus:ring-2 focus:ring-indigo-500 focus:bg-white outline-none transition-all"
              value={password} onChange={e => setPassword(e.target.value)}
            />
          </div>
 
          {error && <p className="text-sm text-red-500 text-center">{error}</p>}
 
          <button
            type="submit" disabled={loading}
            className="w-full py-3.5 bg-indigo-600 hover:bg-indigo-700 text-white font-bold rounded-xl shadow-lg shadow-indigo-200 transition-all active:scale-[0.98] disabled:opacity-50"
          >
            {loading ? 'Authenticating...' : 'Sign In'}
          </button>
        </form>
      </div>
    </div>
  );
};

export default Login
