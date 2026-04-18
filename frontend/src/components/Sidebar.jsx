import { Link, useNavigate } from "react-router-dom";
import {LayoutDashboard, Globe, Users, LogOut, ShieldCheck} from "lucide-react";
import api from "../api.js";

const Sidebar = ({setUser, user}) => {

    const navigate = useNavigate();

    const handleLogout = async () => {
        try {
            await api.post('/api/v1/auth/logout'); // קריאה ל-API כדי לבצע logout בצד השרת
            localStorage.removeItem('userInfo'); // הסרת מידע המשתמש מ-localStorage
            setUser(null); // עדכון מצב המשתמש ל-null ב-App.jsx
            navigate('/login'); // הפניה לדף התחברות לאחר logout
            
        } catch (error) {
            console.error('Logout failed:', error);
            setUser(null); // גם במקרה של שגיאה, נעדכן את מצב המשתמש ל-null כדי למנוע גישה לא מורשית
            navigate('/login'); // הפניה לדף התחברות במקרה של שגיאה גם כן   
        }
    }
    return (
        <aside className="w-72 h-screen bg-[#111827] text-gray-300 flex flex-col border-r border-gray-800 font-sans">
      <div className="p-6 flex items-center gap-3 border-b border-gray-800/50">
        <div className="bg-indigo-600 p-2 rounded-lg">
          <ShieldCheck size={24} className="text-white" />
        </div>
        <span className="text-xl font-bold text-white tracking-tight italic">CUCM</span>
      </div>

      <nav className="flex-1 px-4 py-6 space-y-1">
        <SidebarLink to="/dashboard" icon={LayoutDashboard} label="Overview" />
        <SidebarLink to="/sites" icon={Globe} label="Sites" />

        {/* תיקון: שימוש ב-user.role שהגיע מה-Props */}
        {user?.role === 'superadmin' && (
          <div className="pt-4">
            <p className="px-4 text-[10px] font-bold text-gray-500 uppercase tracking-widest mb-2">Administration</p>
            <SidebarLink to="/users" icon={Users} label="User Management" />
          </div>
        )}
      </nav>

      <div className="p-4 border-t border-gray-800">
        <button onClick={handleLogout} className="flex items-center w-full px-4 py-3 text-sm font-medium text-red-400 hover:bg-red-500/10 rounded-xl transition-all group">
          <LogOut size={20} className="mr-3 group-hover:-translate-x-1 transition-transform" />
          Logout
        </button>
      </div>
    </aside>

        
    );
};

const SidebarLink = ({ to, icon: Icon, label }) => (
  <Link 
    to={to} 
    className="flex items-center px-4 py-3 text-sm font-medium rounded-xl hover:bg-gray-800 hover:text-white transition-all duration-200"
  >
    <Icon size={20} className="mr-3 text-gray-400 group-hover:text-indigo-500" />
    {label}
  </Link>
);

export default Sidebar;