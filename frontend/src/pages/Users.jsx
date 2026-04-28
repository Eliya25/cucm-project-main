import { useEffect, useState } from 'react';
import { Plus, Trash2, ToggleLeft, ToggleRight, Shield, UserCircle, CheckCircle, Search, X } from 'lucide-react';
import api from '../api.js';
import { useAuth } from '../context/AuthContext.jsx';

const Toast = ({ msg, type = 'success' }) => (
  <div className={`fixed top-6 right-6 z-50 flex items-center gap-3 px-5 py-3.5 rounded-2xl shadow-2xl border animate-fade-in
    ${type === 'success' ? 'bg-gray-900 border-gray-700' : 'bg-red-900 border-red-700'}`}>
    <CheckCircle size={18} className={type === 'success' ? 'text-green-400' : 'text-red-400'} />
    <span className="text-sm font-medium text-white">{msg}</span>
  </div>
);

const roleBadge = (role) => ({
  superadmin: 'bg-purple-100 text-purple-700 border border-purple-200',
  admin:      'bg-indigo-100 text-indigo-700 border border-indigo-200',
  operator:   'bg-blue-100   text-blue-700   border border-blue-200',
  viewer:     'bg-gray-100   text-gray-600   border border-gray-200',
}[role] || 'bg-gray-100 text-gray-600');

const Users = () => {
  const { isSuperAdmin } = useAuth();
  const [users,   setUsers]   = useState([]);
  const [loading, setLoading] = useState(true);
  const [modal,   setModal]   = useState(false);
  const [search,  setSearch]  = useState('');
  const [form,    setForm]    = useState({ username: '', password: '', role: 'viewer' });
  const [error,   setError]   = useState('');
  const [toast,   setToast]   = useState(null);

  const showToast = (msg, type = 'success') => {
    setToast({ msg, type });
    setTimeout(() => setToast(null), 3000);
  };

  const fetchUsers = async () => {
    try {
      const { data } = await api.get('/api/v1/users/');
      setUsers(data);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { fetchUsers(); }, []);

  const handleCreate = async (e) => {
    e.preventDefault(); setError('');
    try {
      await api.post('/api/v1/users/', form);
      setModal(false);
      setForm({ username: '', password: '', role: 'viewer' });
      await fetchUsers();
      showToast(`✅ המשתמש "${form.username}" נוצר בהצלחה`);
    } catch (e) {
      setError(e.response?.data?.detail || 'Failed to create user');
    }
  };

  const handleDelete = async (id, username) => {
    if (!confirm(`למחוק את המשתמש "${username}"?`)) return;
    try {
      await api.delete(`/api/v1/users/${id}`);
      await fetchUsers();
      showToast(`🗑️ המשתמש "${username}" נמחק`);
    } catch (e) {
      showToast(e.response?.data?.detail || 'Failed to delete user', 'error');
    }
  };

  const handleToggle = async (id, username, isActive) => {
    try {
      await api.patch(`/api/v1/users/${id}/toggle-active`);
      await fetchUsers();
      showToast(`${isActive ? '⏸️ הושבת' : '▶️ הופעל'}: ${username}`);
    } catch (e) {
      showToast(e.response?.data?.detail || 'Failed', 'error');
    }
  };

  const availableRoles = isSuperAdmin ? ['viewer', 'operator', 'admin'] : ['viewer', 'operator'];

  const filtered = users.filter(u =>
    u.username.toLowerCase().includes(search.toLowerCase()) ||
    u.role.toLowerCase().includes(search.toLowerCase())
  );

  const stats = {
    total:    users.length,
    active:   users.filter(u => u.is_active).length,
    admins:   users.filter(u => ['admin', 'superadmin'].includes(u.role)).length,
    operators: users.filter(u => u.role === 'operator').length,
  };

  if (loading) return (
    <div className="flex items-center justify-center h-40">
      <div className="w-8 h-8 border-4 border-indigo-600 border-t-transparent rounded-full animate-spin" />
    </div>
  );

  return (
    <div className="space-y-6">
      {toast && <Toast msg={toast.msg} type={toast.type} />}

      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">ניהול משתמשים</h1>
          <p className="text-sm text-gray-500 mt-1">
            {isSuperAdmin ? 'כל המשתמשים במערכת' : 'המשתמשים שאתה מנהל'}
          </p>
        </div>
        <button onClick={() => { setModal(true); setError(''); }}
          className="flex items-center gap-2 bg-indigo-600 text-white px-5 py-2.5 rounded-xl font-semibold hover:bg-indigo-700 transition-all shadow-sm shadow-indigo-200">
          <Plus size={18} /> משתמש חדש
        </button>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-4 gap-3">
        {[
          { label: 'סה"כ', value: stats.total,     color: 'bg-gray-50 border-gray-200 text-gray-700' },
          { label: 'פעילים', value: stats.active,  color: 'bg-green-50 border-green-200 text-green-700' },
          { label: 'Admins', value: stats.admins,  color: 'bg-indigo-50 border-indigo-200 text-indigo-700' },
          { label: 'Operators', value: stats.operators, color: 'bg-blue-50 border-blue-200 text-blue-700' },
        ].map(s => (
          <div key={s.label} className={`rounded-xl border px-4 py-3 ${s.color}`}>
            <p className="text-2xl font-bold">{s.value}</p>
            <p className="text-xs font-medium mt-0.5 opacity-70">{s.label}</p>
          </div>
        ))}
      </div>

      {/* Search */}
      <div className="relative">
        <Search size={16} className="absolute left-4 top-3.5 text-gray-400" />
        <input
          placeholder="חיפוש לפי שם משתמש או תפקיד..."
          className="w-full pl-10 pr-4 py-3 bg-white border border-gray-200 rounded-xl text-sm outline-none focus:ring-2 focus:ring-indigo-500 transition-all"
          value={search}
          onChange={e => setSearch(e.target.value)}
        />
        {search && (
          <button onClick={() => setSearch('')} className="absolute right-4 top-3.5 text-gray-400 hover:text-gray-600">
            <X size={16} />
          </button>
        )}
      </div>

      {/* Table */}
      <div className="bg-white rounded-2xl border border-gray-100 shadow-sm overflow-hidden">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-gray-100 text-gray-400 text-xs uppercase tracking-wider bg-gray-50/80">
              <th className="text-left px-6 py-4 font-semibold">משתמש</th>
              <th className="text-left px-6 py-4 font-semibold">תפקיד</th>
              <th className="text-left px-6 py-4 font-semibold">סטטוס</th>
              <th className="text-left px-6 py-4 font-semibold">נוצר</th>
              <th className="text-right px-6 py-4 font-semibold">פעולות</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-50">
            {filtered.map(u => (
              <tr key={u.id} className="hover:bg-gray-50/40 transition-colors group">
                <td className="px-6 py-4">
                  <div className="flex items-center gap-3">
                    <div className={`w-8 h-8 rounded-full flex items-center justify-center text-xs font-bold
                      ${u.role === 'superadmin' ? 'bg-purple-100 text-purple-700' :
                        u.role === 'admin'      ? 'bg-indigo-100 text-indigo-700' :
                        u.role === 'operator'   ? 'bg-blue-100 text-blue-700' :
                                                  'bg-gray-100 text-gray-600'}`}>
                      {u.username.charAt(0).toUpperCase()}
                    </div>
                    <div>
                      <div className="flex items-center gap-1.5">
                        {u.role === 'superadmin' && <Shield size={12} className="text-purple-500" />}
                        <span className="font-semibold text-gray-900">{u.username}</span>
                      </div>
                    </div>
                  </div>
                </td>
                <td className="px-6 py-4">
                  <span className={`px-2.5 py-1 rounded-lg text-xs font-bold uppercase tracking-wide ${roleBadge(u.role)}`}>
                    {u.role}
                  </span>
                </td>
                <td className="px-6 py-4">
                  <div className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-lg text-xs font-medium
                    ${u.is_active ? 'bg-green-50 text-green-700 border border-green-200' : 'bg-gray-50 text-gray-400 border border-gray-200'}`}>
                    <span className={`w-1.5 h-1.5 rounded-full ${u.is_active ? 'bg-green-500 animate-pulse' : 'bg-gray-400'}`} />
                    {u.is_active ? 'פעיל' : 'מושבת'}
                  </div>
                </td>
                <td className="px-6 py-4 text-gray-400 text-xs">
                  {new Date(u.created_at).toLocaleDateString('he-IL')}
                </td>
                <td className="px-6 py-4">
                  {u.role !== 'superadmin' && (
                    <div className="flex items-center justify-end gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                      <button onClick={() => handleToggle(u.id, u.username, u.is_active)}
                        className={`p-2 rounded-lg transition-colors text-xs font-medium flex items-center gap-1
                          ${u.is_active
                            ? 'hover:bg-amber-50 text-gray-400 hover:text-amber-600'
                            : 'hover:bg-green-50 text-gray-400 hover:text-green-600'}`}
                        title={u.is_active ? 'השבת' : 'הפעל'}>
                        {u.is_active ? <ToggleRight size={18} /> : <ToggleLeft size={18} />}
                      </button>
                      <button onClick={() => handleDelete(u.id, u.username)}
                        className="p-2 rounded-lg hover:bg-red-50 text-gray-400 hover:text-red-500 transition-colors"
                        title="מחק">
                        <Trash2 size={16} />
                      </button>
                    </div>
                  )}
                </td>
              </tr>
            ))}
            {filtered.length === 0 && (
              <tr>
                <td colSpan={5} className="px-6 py-16 text-center">
                  <UserCircle size={40} className="mx-auto text-gray-200 mb-3" />
                  <p className="text-gray-400 text-sm">
                    {search ? `אין תוצאות עבור "${search}"` : 'אין משתמשים עדיין'}
                  </p>
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>

      {/* Modal: יצירת משתמש */}
      {modal && (
        <div className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-2xl shadow-2xl max-w-md w-full border border-gray-100 overflow-hidden">
            <div className="bg-gradient-to-r from-indigo-600 to-indigo-700 px-8 py-6">
              <h2 className="text-xl font-bold text-white">משתמש חדש</h2>
              <p className="text-indigo-200 text-sm mt-1">הוספת משתמש למערכת</p>
            </div>
            <form onSubmit={handleCreate} className="p-8 space-y-4">
              <div>
                <label className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-1.5 block">שם משתמש</label>
                <input placeholder="הכנס שם משתמש" required
                  className="w-full px-4 py-3 border border-gray-200 rounded-xl focus:ring-2 focus:ring-indigo-500 outline-none text-sm bg-gray-50 focus:bg-white transition-all"
                  value={form.username} onChange={e => setForm({ ...form, username: e.target.value })} />
              </div>
              <div>
                <label className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-1.5 block">סיסמה</label>
                <input placeholder="הכנס סיסמה" type="password" required
                  className="w-full px-4 py-3 border border-gray-200 rounded-xl focus:ring-2 focus:ring-indigo-500 outline-none text-sm bg-gray-50 focus:bg-white transition-all"
                  value={form.password} onChange={e => setForm({ ...form, password: e.target.value })} />
              </div>
              <div>
                <label className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-1.5 block">תפקיד</label>
                <select className="w-full px-4 py-3 border border-gray-200 rounded-xl focus:ring-2 focus:ring-indigo-500 outline-none text-sm bg-gray-50 focus:bg-white transition-all"
                  value={form.role} onChange={e => setForm({ ...form, role: e.target.value })}>
                  {availableRoles.map(r => (
                    <option key={r} value={r}>{r.charAt(0).toUpperCase() + r.slice(1)}</option>
                  ))}
                </select>
              </div>
              {error && (
                <div className="bg-red-50 border border-red-200 rounded-xl px-4 py-3">
                  <p className="text-sm text-red-600">{error}</p>
                </div>
              )}
              <div className="flex gap-3 pt-2">
                <button type="button" onClick={() => { setModal(false); setError(''); }}
                  className="flex-1 px-4 py-3 text-gray-600 font-medium hover:bg-gray-50 rounded-xl transition-colors text-sm border border-gray-200">
                  ביטול
                </button>
                <button type="submit"
                  className="flex-1 px-4 py-3 bg-indigo-600 text-white font-semibold rounded-xl hover:bg-indigo-700 transition-colors text-sm shadow-sm shadow-indigo-200">
                  צור משתמש
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

export default Users;