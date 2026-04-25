import { useEffect, useState } from 'react';
import { Users as UsersIcon, Plus, Trash2, ToggleLeft, ToggleRight, Shield } from 'lucide-react';
import api from '../api.js';
import { useAuth } from '../context/AuthContext.jsx';

const ROLES = ['viewer', 'operator', 'admin'];

const Users = () => {
  const { isSuperAdmin } = useAuth();
  const [users,     setUsers]     = useState([]);
  const [loading,   setLoading]   = useState(true);
  const [modal,     setModal]     = useState(false);
  const [form,      setForm]      = useState({ username: '', password: '', role: 'viewer' });
  const [error,     setError]     = useState('');

  const fetchUsers = async () => {
    try {
      const { data } = await api.get('/api/v1/users/');
      // SuperAdmin רואה הכל, Admin רואה הכל חוץ מ-superadmin (מסונן בבק)
      setUsers(data);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { fetchUsers(); }, []);

  const handleCreate = async (e) => {
    e.preventDefault();
    setError('');
    try {
      await api.post('/api/v1/users/', form);
      setModal(false);
      setForm({ username: '', password: '', role: 'viewer' });
      fetchUsers();
    } catch (e) {
      setError(e.response?.data?.detail || 'Failed to create user');
    }
  };

  const handleDelete = async (id, username) => {
    if (!confirm(`Delete user "${username}"?`)) return;
    try {
      await api.delete(`/api/v1/users/${id}`);
      fetchUsers();
    } catch (e) {
      alert(e.response?.data?.detail || 'Failed to delete user');
    }
  };

  const handleToggle = async (id) => {
    try {
      await api.patch(`/api/v1/users/${id}/toggle-active`);
      fetchUsers();
    } catch (e) {
      alert(e.response?.data?.detail || 'Failed to toggle user');
    }
  };

  const roleBadge = (role) => ({
    superadmin: 'bg-purple-100 text-purple-700',
    admin:      'bg-indigo-100 text-indigo-700',
    operator:   'bg-blue-100 text-blue-700',
    viewer:     'bg-gray-100 text-gray-600',
  }[role] || 'bg-gray-100 text-gray-600');

  // Roles available to create (superadmin cannot be created via UI)
  const availableRoles = isSuperAdmin ? ['viewer', 'operator', 'admin'] : ['viewer', 'operator'];

  if (loading) return <div className="flex justify-center p-10 text-gray-400">Loading users...</div>;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">User Management</h1>
          <p className="text-sm text-gray-500 mt-1">
            {isSuperAdmin ? 'All users in the system' : 'Users you manage'}
          </p>
        </div>
        <button
          onClick={() => setModal(true)}
          className="flex items-center gap-2 bg-indigo-600 text-white px-5 py-2.5 rounded-xl font-medium hover:bg-indigo-700 transition-all shadow-sm"
        >
          <Plus size={18} /> Add User
        </button>
      </div>

      {/* Table */}
      <div className="bg-white rounded-2xl border border-gray-100 shadow-sm overflow-hidden">
        <table className="w-full text-sm">
          <thead>
            <tr className="bg-gray-50 border-b border-gray-100 text-gray-500 text-xs uppercase tracking-wider">
              <th className="text-left px-6 py-4">Username</th>
              <th className="text-left px-6 py-4">Role</th>
              <th className="text-left px-6 py-4">Status</th>
              <th className="text-left px-6 py-4">Created</th>
              <th className="text-right px-6 py-4">Actions</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-50">
            {users.map(u => (
              <tr key={u.id} className="hover:bg-gray-50/50 transition-colors">
                <td className="px-6 py-4 font-medium text-gray-900 flex items-center gap-2">
                  {u.role === 'superadmin' && <Shield size={14} className="text-purple-500" />}
                  {u.username}
                </td>
                <td className="px-6 py-4">
                  <span className={`px-2.5 py-0.5 rounded-full text-xs font-bold uppercase tracking-wide ${roleBadge(u.role)}`}>
                    {u.role}
                  </span>
                </td>
                <td className="px-6 py-4">
                  <span className={`flex items-center gap-1.5 text-xs font-medium ${u.is_active ? 'text-green-600' : 'text-gray-400'}`}>
                    <span className={`w-1.5 h-1.5 rounded-full ${u.is_active ? 'bg-green-500' : 'bg-gray-400'}`} />
                    {u.is_active ? 'Active' : 'Disabled'}
                  </span>
                </td>
                <td className="px-6 py-4 text-gray-400">
                  {new Date(u.created_at).toLocaleDateString()}
                </td>
                <td className="px-6 py-4">
                  <div className="flex items-center justify-end gap-2">
                    {u.role !== 'superadmin' && (
                      <>
                        <button
                          onClick={() => handleToggle(u.id)}
                          className="p-1.5 rounded-lg hover:bg-gray-100 text-gray-400 hover:text-indigo-600 transition-colors"
                          title={u.is_active ? 'Deactivate' : 'Activate'}
                        >
                          {u.is_active ? <ToggleRight size={18} /> : <ToggleLeft size={18} />}
                        </button>
                        <button
                          onClick={() => handleDelete(u.id, u.username)}
                          className="p-1.5 rounded-lg hover:bg-red-50 text-gray-400 hover:text-red-500 transition-colors"
                          title="Delete"
                        >
                          <Trash2 size={16} />
                        </button>
                      </>
                    )}
                  </div>
                </td>
              </tr>
            ))}
            {users.length === 0 && (
              <tr><td colSpan={5} className="px-6 py-10 text-center text-gray-400">No users found</td></tr>
            )}
          </tbody>
        </table>
      </div>

      {/* Modal */}
      {modal && (
        <div className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-2xl shadow-2xl max-w-md w-full p-8 border border-gray-100">
            <h2 className="text-xl font-bold text-gray-900 mb-6">Create New User</h2>
            <form onSubmit={handleCreate} className="space-y-4">
              <input
                placeholder="Username" required
                className="w-full px-4 py-3 border border-gray-200 rounded-xl focus:ring-2 focus:ring-indigo-500 outline-none text-sm"
                value={form.username} onChange={e => setForm({ ...form, username: e.target.value })}
              />
              <input
                placeholder="Password" type="password" required
                className="w-full px-4 py-3 border border-gray-200 rounded-xl focus:ring-2 focus:ring-indigo-500 outline-none text-sm"
                value={form.password} onChange={e => setForm({ ...form, password: e.target.value })}
              />
              <select
                className="w-full px-4 py-3 border border-gray-200 rounded-xl focus:ring-2 focus:ring-indigo-500 outline-none text-sm bg-white"
                value={form.role} onChange={e => setForm({ ...form, role: e.target.value })}
              >
                {availableRoles.map(r => (
                  <option key={r} value={r}>{r.charAt(0).toUpperCase() + r.slice(1)}</option>
                ))}
              </select>
              {error && <p className="text-sm text-red-500">{error}</p>}
              <div className="flex gap-3 pt-2">
                <button type="button" onClick={() => { setModal(false); setError(''); }}
                  className="flex-1 px-4 py-3 text-gray-600 font-medium hover:bg-gray-50 rounded-xl transition-colors text-sm">
                  Cancel
                </button>
                <button type="submit"
                  className="flex-1 px-4 py-3 bg-indigo-600 text-white font-medium rounded-xl hover:bg-indigo-700 transition-colors text-sm">
                  Create User
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