import { useEffect, useState } from 'react';
import { Monitor, Plus, Trash2, Pencil, CheckCircle, X } from 'lucide-react';
import api from '../api.js';
import { useAuth } from '../context/AuthContext.jsx';

const Toast = ({ msg }) => (
  <div className="fixed top-6 right-6 z-50 flex items-center gap-3 bg-gray-900 text-white px-5 py-3.5 rounded-2xl shadow-2xl border border-gray-700">
    <CheckCircle size={18} className="text-green-400 shrink-0" />
    <span className="text-sm font-medium">{msg}</span>
  </div>
);

const Devices = () => {
  const { isAdmin, isOperator } = useAuth();
  const [devices,  setDevices]  = useState([]);
  const [sections, setSections] = useState([]);
  const [loading,  setLoading]  = useState(true);
  const [toast,    setToast]    = useState('');
  const [error,    setError]    = useState('');

  // Modals
  const [createModal, setCreateModal] = useState(false);
  const [editModal,   setEditModal]   = useState(null); // device object

  // Forms
  const [createForm, setCreateForm] = useState({ identifier: '', section_id: '' });
  const [editForm,   setEditForm]   = useState({ identifier: '' });

  const showToast = (msg) => {
    setToast(msg);
    setTimeout(() => setToast(''), 3000);
  };

  const fetchAll = async () => {
    try {
      const [devRes, sitesRes] = await Promise.all([
        api.get('/api/v1/devices/'),
        api.get('/api/v1/sites/'),
      ]);

      setDevices(devRes.data);

      // שולף את כל הsections מכל הsites
      const allSections = [];
      for (const site of sitesRes.data) {
        try {
          const { data } = await api.get(`/api/v1/sites/${site.id}/sections`);
          data.forEach(s => allSections.push({ ...s, siteName: site.name }));
        } catch (_) {}
      }
      setSections(allSections);
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
      await api.post('/api/v1/devices/', createForm);
      setCreateModal(false);
      setCreateForm({ identifier: '', section_id: '' });
      await fetchAll();
      showToast('✅ Device נוסף בהצלחה');
    } catch (e) {
      setError(e.response?.data?.detail || 'Failed to create device');
    }
  };

  const handleEdit = async (e) => {
    e.preventDefault(); setError('');
    try {
      await api.patch(`/api/v1/devices/${editModal.id}`, {
        identifier: editForm.identifier
      });
      setEditModal(null);
      await fetchAll();
      showToast('✅ Device עודכן בהצלחה');
    } catch (e) {
      setError(e.response?.data?.detail || 'Failed to update device');
    }
  };

  const handleDelete = async (id, identifier) => {
    if (!confirm(`למחוק את "${identifier}"?`)) return;
    try {
      await api.delete(`/api/v1/devices/${id}`);
      await fetchAll();
      showToast(`🗑️ Device "${identifier}" נמחק`);
    } catch (e) {
      alert(e.response?.data?.detail || 'Failed to delete device');
    }
  };

  const getSectionName = (section_id) => {
    const s = sections.find(s => s.id === section_id);
    return s ? `${s.siteName} / ${s.name}` : section_id;
  };

  if (loading) return (
    <div className="flex justify-center items-center h-40 text-gray-400">טוען מכשירים...</div>
  );

  return (
    <div className="space-y-6">
      {toast && <Toast msg={toast} />}

      {/* כותרת */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Devices</h1>
          <p className="text-sm text-gray-500 mt-1">
            {isAdmin ? 'כל המכשירים במערכת' : 'המכשירים בתאים שלך'}
          </p>
        </div>
        {isOperator && (
          <button
            onClick={() => { setCreateModal(true); setError(''); }}
            className="flex items-center gap-2 bg-indigo-600 text-white px-5 py-2.5 rounded-xl font-medium hover:bg-indigo-700 transition-all shadow-sm"
          >
            <Plus size={18} /> הוסף Device
          </button>
        )}
      </div>

      {/* טבלה */}
      <div className="bg-white rounded-2xl border border-gray-100 shadow-sm overflow-hidden">
        <table className="w-full text-sm">
          <thead>
            <tr className="bg-gray-50 border-b border-gray-100 text-gray-500 text-xs uppercase tracking-wider">
              <th className="text-left px-6 py-4">Identifier</th>
              <th className="text-left px-6 py-4">Site / Section</th>
              <th className="text-left px-6 py-4">נוסף</th>
              <th className="text-right px-6 py-4">פעולות</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-50">
            {devices.map(d => (
              <tr key={d.id} className="hover:bg-gray-50/50 transition-colors">
                <td className="px-6 py-4 font-medium text-gray-900 flex items-center gap-2">
                  <Monitor size={15} className="text-indigo-400" />
                  {d.identifier}
                </td>
                <td className="px-6 py-4 text-gray-500 text-sm">
                  {getSectionName(d.section_id)}
                </td>
                <td className="px-6 py-4 text-gray-400 text-sm">
                  {new Date(d.created_at).toLocaleDateString('he-IL')}
                </td>
                <td className="px-6 py-4">
                  <div className="flex items-center justify-end gap-2">
                    {isOperator && (
                      <>
                        <button
                          onClick={() => { setEditModal(d); setEditForm({ identifier: d.identifier }); setError(''); }}
                          className="p-1.5 rounded-lg hover:bg-indigo-50 text-gray-400 hover:text-indigo-600 transition-colors"
                          title="ערוך"
                        >
                          <Pencil size={15} />
                        </button>
                        <button
                          onClick={() => handleDelete(d.id, d.identifier)}
                          className="p-1.5 rounded-lg hover:bg-red-50 text-gray-400 hover:text-red-500 transition-colors"
                          title="מחק"
                        >
                          <Trash2 size={15} />
                        </button>
                      </>
                    )}
                  </div>
                </td>
              </tr>
            ))}
            {devices.length === 0 && (
              <tr>
                <td colSpan={4} className="px-6 py-12 text-center text-gray-400">
                  <Monitor size={36} className="mx-auto text-gray-200 mb-2" />
                  אין מכשירים עדיין
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>

      {/* Modal: הוספת Device */}
      {createModal && (
        <div className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-2xl shadow-2xl max-w-md w-full p-8">
            <h2 className="text-xl font-bold text-gray-900 mb-6">הוספת Device חדש</h2>
            <form onSubmit={handleCreate} className="space-y-4">
              <input
                placeholder="Identifier (מזהה המכשיר)" required
                className="w-full px-4 py-3 border border-gray-200 rounded-xl focus:ring-2 focus:ring-indigo-500 outline-none text-sm"
                value={createForm.identifier}
                onChange={e => setCreateForm({ ...createForm, identifier: e.target.value })}
              />
              <select
                className="w-full px-4 py-3 border border-gray-200 rounded-xl focus:ring-2 focus:ring-indigo-500 outline-none text-sm bg-white"
                value={createForm.section_id}
                onChange={e => setCreateForm({ ...createForm, section_id: e.target.value })}
                required
              >
                <option value="">בחר תא</option>
                {sections.map(s => (
                  <option key={s.id} value={s.id}>
                    {s.siteName} / {s.name}
                  </option>
                ))}
              </select>
              {error && <p className="text-sm text-red-500">{error}</p>}
              <div className="flex gap-3 pt-2">
                <button type="button" onClick={() => { setCreateModal(false); setError(''); }}
                  className="flex-1 px-4 py-3 text-gray-600 hover:bg-gray-50 rounded-xl text-sm">
                  ביטול
                </button>
                <button type="submit"
                  className="flex-1 px-4 py-3 bg-indigo-600 text-white rounded-xl hover:bg-indigo-700 text-sm">
                  הוסף
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Modal: עריכת Device */}
      {editModal && (
        <div className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-2xl shadow-2xl max-w-md w-full p-8">
            <h2 className="text-xl font-bold text-gray-900 mb-6">עריכת Device</h2>
            <form onSubmit={handleEdit} className="space-y-4">
              <input
                placeholder="Identifier חדש" required
                className="w-full px-4 py-3 border border-gray-200 rounded-xl focus:ring-2 focus:ring-indigo-500 outline-none text-sm"
                value={editForm.identifier}
                onChange={e => setEditForm({ identifier: e.target.value })}
              />
              {error && <p className="text-sm text-red-500">{error}</p>}
              <div className="flex gap-3 pt-2">
                <button type="button" onClick={() => { setEditModal(null); setError(''); }}
                  className="flex-1 px-4 py-3 text-gray-600 hover:bg-gray-50 rounded-xl text-sm">
                  ביטול
                </button>
                <button type="submit"
                  className="flex-1 px-4 py-3 bg-indigo-600 text-white rounded-xl hover:bg-indigo-700 text-sm">
                  שמור
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

export default Devices;