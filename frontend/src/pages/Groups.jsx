import { useEffect, useState } from 'react';
import { Layers, Plus, UserPlus, Trash2, CheckCircle, Users, Link2, X } from 'lucide-react';
import api from '../api.js';
import { useAuth } from '../context/AuthContext.jsx';

const Toast = ({ msg, type = 'success' }) => (
  <div className={`fixed top-6 right-6 z-50 flex items-center gap-3 px-5 py-3.5 rounded-2xl shadow-2xl border
    ${type === 'success' ? 'bg-gray-900 border-gray-700' : 'bg-red-900 border-red-700'}`}>
    <CheckCircle size={18} className={type === 'success' ? 'text-green-400' : 'text-red-400'} />
    <span className="text-sm font-medium text-white">{msg}</span>
  </div>
);

const classColor = {
  viewer:   'bg-gray-100 text-gray-600 border border-gray-200',
  operator: 'bg-blue-100 text-blue-700 border border-blue-200',
  admin:    'bg-indigo-100 text-indigo-700 border border-indigo-200',
};

const Groups = () => {
  const { isSuperAdmin } = useAuth();
  const [groups,  setGroups]  = useState([]);
  const [users,   setUsers]   = useState([]);
  const [loading, setLoading] = useState(true);
  const [modal,   setModal]   = useState(false);
  const [addUser, setAddUser] = useState(null); // group object
  const [form,    setForm]    = useState({ name: '', description: '', classification: 'viewer' });
  const [addForm, setAddForm] = useState({ user_id: '' });
  const [error,   setError]   = useState('');
  const [toast,   setToast]   = useState(null);

  const showToast = (msg, type = 'success') => {
    setToast({ msg, type });
    setTimeout(() => setToast(null), 3000);
  };

  const fetchAll = async () => {
    try {
      const [gr, us] = await Promise.all([
        api.get('/api/v1/groups/'),
        api.get('/api/v1/users/'),
      ]);
      setGroups(gr.data);
      setUsers(us.data);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { fetchAll(); }, []);

  const handleCreate = async (e) => {
    e.preventDefault(); setError('');
    try {
      await api.post('/api/v1/groups/', form);
      setModal(false);
      setForm({ name: '', description: '', classification: 'viewer' });
      await fetchAll();
      showToast(`✅ הקבוצה "${form.name}" נוצרה`);
    } catch (e) {
      setError(e.response?.data?.detail || 'Failed');
    }
  };

  const handleDelete = async (id, name) => {
    if (!confirm(`למחוק את הקבוצה "${name}"?\nכל הקישורים לתאים ולמשתמשים יימחקו.`)) return;
    try {
      await api.delete(`/api/v1/groups/${id}`);
      await fetchAll();
      showToast(`🗑️ הקבוצה "${name}" נמחקה`);
    } catch (e) {
      showToast(e.response?.data?.detail || 'Failed to delete group', 'error');
    }
  };

  const handleAddUser = async (e) => {
    e.preventDefault(); setError('');
    const userName = users.find(u => u.id === addForm.user_id)?.username || '';
    try {
      await api.post(`/api/v1/groups/${addUser.id}/add-user`, null, {
        params: { user_id: addForm.user_id }
      });
      setAddUser(null);
      setAddForm({ user_id: '' });
      await fetchAll();
      showToast(`✅ ${userName} נוסף לקבוצה`);
    } catch (e) {
      setError(e.response?.data?.detail || 'Failed');
    }
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
          <h1 className="text-2xl font-bold text-gray-900">קבוצות</h1>
          <p className="text-sm text-gray-500 mt-1">ניהול קבוצות גישה ושיוך תאים ומשתמשים</p>
        </div>
        <button onClick={() => { setModal(true); setError(''); }}
          className="flex items-center gap-2 bg-indigo-600 text-white px-5 py-2.5 rounded-xl font-semibold hover:bg-indigo-700 transition-all shadow-sm shadow-indigo-200">
          <Plus size={18} /> קבוצה חדשה
        </button>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-3 gap-3">
        {[
          { label: 'סה"כ קבוצות', value: groups.length, color: 'bg-indigo-50 border-indigo-200 text-indigo-700' },
          { label: 'Viewer', value: groups.filter(g => g.classification === 'viewer').length, color: 'bg-gray-50 border-gray-200 text-gray-700' },
          { label: 'Operator+', value: groups.filter(g => ['operator','admin'].includes(g.classification)).length, color: 'bg-blue-50 border-blue-200 text-blue-700' },
        ].map(s => (
          <div key={s.label} className={`rounded-xl border px-4 py-3 ${s.color}`}>
            <p className="text-2xl font-bold">{s.value}</p>
            <p className="text-xs font-medium mt-0.5 opacity-70">{s.label}</p>
          </div>
        ))}
      </div>

      {/* Grid of Groups */}
      <div className="grid gap-4 md:grid-cols-2">
        {groups.map(g => (
          <div key={g.id}
            className="bg-white rounded-2xl border border-gray-100 shadow-sm overflow-hidden hover:shadow-md hover:border-indigo-100 transition-all">

            {/* כותרת הכרטיס */}
            <div className="flex items-start justify-between p-5 border-b border-gray-50">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-indigo-500 to-cyan-500 flex items-center justify-center shadow-sm shadow-indigo-200">
                  <Layers size={18} className="text-white" />
                </div>
                <div>
                  <p className="font-bold text-gray-900">{g.name}</p>
                  {g.description && <p className="text-xs text-gray-400 mt-0.5">{g.description}</p>}
                </div>
              </div>
              <div className="flex items-center gap-1.5">
                <span className={`px-2.5 py-1 rounded-lg text-xs font-bold uppercase tracking-wide ${classColor[g.classification] || classColor.viewer}`}>
                  {g.classification}
                </span>
              </div>
            </div>

            {/* מידע ופעולות */}
            <div className="px-5 py-3 flex items-center justify-between">
              <p className="text-xs text-gray-400">
                נוצר {new Date(g.created_at).toLocaleDateString('he-IL')}
              </p>
              <div className="flex items-center gap-1">
                <button
                  onClick={() => { setAddUser(g); setAddForm({ user_id: '' }); setError(''); }}
                  className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium text-indigo-600 hover:bg-indigo-50 transition-colors"
                  title="הוסף משתמש">
                  <UserPlus size={14} /> הוסף משתמש
                </button>
                {isSuperAdmin && (
                  <button
                    onClick={() => handleDelete(g.id, g.name)}
                    className="p-1.5 rounded-lg hover:bg-red-50 text-gray-400 hover:text-red-500 transition-colors"
                    title="מחק קבוצה">
                    <Trash2 size={15} />
                  </button>
                )}
              </div>
            </div>
          </div>
        ))}

        {groups.length === 0 && (
          <div className="col-span-2 bg-white rounded-2xl border border-gray-100 p-16 text-center">
            <div className="w-14 h-14 rounded-2xl bg-gray-50 flex items-center justify-center mx-auto mb-4">
              <Layers size={28} className="text-gray-300" />
            </div>
            <p className="text-gray-500 font-medium">אין קבוצות עדיין</p>
            <p className="text-gray-400 text-sm mt-1">צור קבוצה ראשונה כדי להתחיל</p>
          </div>
        )}
      </div>

      {/* Modal: יצירת קבוצה */}
      {modal && (
        <div className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-2xl shadow-2xl max-w-md w-full overflow-hidden">
            <div className="bg-gradient-to-r from-indigo-600 to-cyan-600 px-8 py-6">
              <h2 className="text-xl font-bold text-white">קבוצה חדשה</h2>
              <p className="text-indigo-200 text-sm mt-1">הגדר שם, תיאור ורמת גישה</p>
            </div>
            <form onSubmit={handleCreate} className="p-8 space-y-4">
              <div>
                <label className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-1.5 block">שם הקבוצה</label>
                <input placeholder="לדוגמה: צוות ירושלים" required
                  className="w-full px-4 py-3 border border-gray-200 rounded-xl focus:ring-2 focus:ring-indigo-500 outline-none text-sm bg-gray-50 focus:bg-white transition-all"
                  value={form.name} onChange={e => setForm({ ...form, name: e.target.value })} />
              </div>
              <div>
                <label className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-1.5 block">תיאור</label>
                <input placeholder="תיאור קצר (אופציונלי)"
                  className="w-full px-4 py-3 border border-gray-200 rounded-xl focus:ring-2 focus:ring-indigo-500 outline-none text-sm bg-gray-50 focus:bg-white transition-all"
                  value={form.description} onChange={e => setForm({ ...form, description: e.target.value })} />
              </div>
              <div>
                <label className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-1.5 block">רמת סיווג</label>
                <div className="grid grid-cols-3 gap-2">
                  {['viewer', 'operator', 'admin'].map(r => (
                    <button key={r} type="button"
                      onClick={() => setForm({ ...form, classification: r })}
                      className={`py-2.5 px-3 rounded-xl text-xs font-semibold uppercase border transition-all ${
                        form.classification === r
                          ? 'bg-indigo-600 text-white border-indigo-600 shadow-sm'
                          : 'bg-gray-50 text-gray-600 border-gray-200 hover:border-indigo-300'
                      }`}>
                      {r}
                    </button>
                  ))}
                </div>
              </div>
              {error && (
                <div className="bg-red-50 border border-red-200 rounded-xl px-4 py-3">
                  <p className="text-sm text-red-600">{error}</p>
                </div>
              )}
              <div className="flex gap-3 pt-2">
                <button type="button" onClick={() => { setModal(false); setError(''); }}
                  className="flex-1 px-4 py-3 text-gray-600 hover:bg-gray-50 rounded-xl text-sm border border-gray-200">ביטול</button>
                <button type="submit"
                  className="flex-1 px-4 py-3 bg-indigo-600 text-white font-semibold rounded-xl hover:bg-indigo-700 text-sm">צור קבוצה</button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Modal: הוספת משתמש */}
      {addUser && (
        <div className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-2xl shadow-2xl max-w-md w-full overflow-hidden">
            <div className="bg-gradient-to-r from-cyan-600 to-indigo-600 px-8 py-6">
              <h2 className="text-xl font-bold text-white">הוספת משתמש</h2>
              <p className="text-cyan-200 text-sm mt-1">קבוצה: <span className="font-bold text-white">{addUser.name}</span></p>
            </div>
            <form onSubmit={handleAddUser} className="p-8 space-y-4">
              <div>
                <label className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-1.5 block">בחר משתמש</label>
                <select
                  className="w-full px-4 py-3 border border-gray-200 rounded-xl focus:ring-2 focus:ring-indigo-500 outline-none text-sm bg-gray-50 focus:bg-white transition-all"
                  value={addForm.user_id}
                  onChange={e => setAddForm({ user_id: e.target.value })}
                  required>
                  <option value="">-- בחר משתמש --</option>
                  {users.filter(u => u.role !== 'superadmin').map(u => (
                    <option key={u.id} value={u.id}>{u.username} ({u.role})</option>
                  ))}
                </select>
              </div>
              {error && (
                <div className="bg-red-50 border border-red-200 rounded-xl px-4 py-3">
                  <p className="text-sm text-red-600">{error}</p>
                </div>
              )}
              <div className="flex gap-3 pt-2">
                <button type="button" onClick={() => { setAddUser(null); setError(''); }}
                  className="flex-1 px-4 py-3 text-gray-600 hover:bg-gray-50 rounded-xl text-sm border border-gray-200">ביטול</button>
                <button type="submit"
                  className="flex-1 px-4 py-3 bg-indigo-600 text-white font-semibold rounded-xl hover:bg-indigo-700 text-sm">הוסף</button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

export default Groups;