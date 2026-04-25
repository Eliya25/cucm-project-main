import { Link, useLocation, useNavigate } from "react-router-dom";
import {LayoutDashboard, Globe, Users, LogOut, ShieldCheck, Settings, Layers, Zap} from "lucide-react";
import { useAuth } from "../context/AuthContext.jsx";
import api from "../api.js";

const Sidebar = () => {

  const { user, logout, isSuperAdmin, isAdmin} = useAuth();
  const navigate = useNavigate();
  const location = useLocation();


    const handleLogout = async () => {
        try {
            await api.post('/api/v1/auth/logout'); // קריאה ל-API כדי לבצע logout בצד השרת
            
        }  catch (_){

        } finally {
          logout()
          navigate('/login')
        }
    };

    const roleBadge = {
      superadmin: {label: 'Super Admin', cls: 'bg-purple-500/20 text-purple-300 border border-purple-500/30'},
      admin: {label: 'Admin', cls: 'bg-indigo-500/20 text-indigo-300 border border-indigo-500/30'},
      operator: {label: 'Operator', cls: 'bg-blue-500/20  text-blue-300  border border-blue-500/30'},
      viewer: {label: 'Viewer', cls: 'bg-gray-500/20  text-gray-300  border border-gray-500/30'}
    }[user?.role] || {label: user?.role, cls: 'bg-gray-700 text-gray-300'};
    return (
        <aside className="w-72 h-screen bg-[#0f1623] text-gray-300 flex flex-col border-r border-gray-800 font-sans shrink-0">

      {/* Logo */}
      <div className="p-6 flex items-center gap-3 border-b border-gray-800/60">
        <div className="bg-indigo-600 p-2 rounded-lg shadow-lg shadow-indigo-900/40">
          <ShieldCheck size={22} className="text-white" />
        </div>
        <div>
          <span className="text-lg font-bold text-white tracking-tight">CUCM Portal</span>
          <p className="text-[10px] text-gray-500 uppercase tracking-widest">Management System</p>
        </div>
      </div>
 
      {/* User info */}
      <div className="px-4 py-3 mx-4 mt-4 rounded-xl bg-gray-800/40 border border-gray-700/40">
        <p className="text-sm font-semibold text-white">{user?.username}</p>
        <span className={`mt-1 inline-block text-[10px] font-bold px-2 py-0.5 rounded-full uppercase tracking-widest ${roleBadge.cls}`}>
          {roleBadge.label}
        </span>
      </div>
 
      {/* Nav */}
      <nav className="flex-1 px-4 py-5 space-y-1 overflow-y-auto">
        <NavItem to="/dashboard" icon={LayoutDashboard} label="Overview" active={location.pathname === '/dashboard'} />
        
        {isAdmin && (
          <>
            <p className="px-3 pt-4 pb-1 text-[10px] font-bold text-gray-600 uppercase tracking-widest">Management</p>
            <NavItem to="/sites"  icon={Globe}   label="Sites & Sections" active={location.pathname === '/sites'}  />
            <NavItem to="/groups" icon={Layers}   label="Groups"          active={location.pathname === '/groups'} />
            <NavItem to="/users"  icon={Users}    label="Users"           active={location.pathname === '/users'}  />
            <NavItem to="/bulk-actions" icon={Zap} label="Bulk Actions"   active={location.pathname === '/bulk-actions'} />
          </>
        )}
      </nav>
 
      {/* Bottom: Settings + Logout */}
      <div className="px-4 pb-4 space-y-1 border-t border-gray-800 pt-3">
        <NavItem to="/settings" icon={Settings} label="Settings" active={location.pathname === '/settings'} />
        <button
          onClick={handleLogout}
          className="flex items-center w-full px-4 py-2.5 text-sm font-medium text-red-400 hover:bg-red-500/10 rounded-xl transition-all group"
        >
          <LogOut size={18} className="mr-3 group-hover:-translate-x-1 transition-transform" />
          Logout
        </button>
      </div>
    </aside>
  );
};
 
const NavItem = ({ to, icon: Icon, label, active }) => (
  <Link
    to={to}
    className={`flex items-center px-4 py-2.5 text-sm font-medium rounded-xl transition-all duration-150 ${
      active
        ? 'bg-indigo-600/20 text-indigo-300 border border-indigo-500/30'
        : 'hover:bg-gray-800 hover:text-white text-gray-400'
    }`}
  >
    <Icon size={18} className={`mr-3 ${active ? 'text-indigo-400' : 'text-gray-500'}`} />
    {label}
  </Link>
);

export default Sidebar;