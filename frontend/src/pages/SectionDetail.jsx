import { useEffect, useState, useRef } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  Monitor, Plus, Trash2, Pencil, ArrowRight,
  Layers, CheckCircle, Upload, X, FileSpreadsheet, AlertCircle
} from 'lucide-react';
import api from '../api.js';
import { useAuth } from '../context/AuthContext.jsx';

// ── Toast ─────────────────────────────────────────────────────────
const Toast = ({ msg, type = 'success' }) => (
  <div className={`fixed top-6 right-6 z-50 flex items-center gap-3 px-5 py-3.5 rounded-2xl shadow-2xl border
    ${type === 'success' ? 'bg-gray-900 border-gray-700' : 'bg-red-900 border-red-700'}`}>
    {type === 'success'
      ? <CheckCircle size={18} className="text-green-400 shrink-0" />
      : <AlertCircle size={18} className="text-red-400 shrink-0" />
    }
    <span className="text-sm font-medium text-white">{msg}</span>
  </div>
);

// ── Import Summary ────────────────────────────────────────────────
const ImportSummary = ({ summary, onClose }) => (
  <div className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center z-50 p-4">
    <div className="bg-white rounded-2xl shadow-2xl max-w-sm w-full overflow-hidden">
      <div className="bg-gradient-to-r from-green-500 to-emerald-600 px-8 py-6">
        <h2 className="text-xl font-bold text-white">יבוא הושלם!</h2>
        <p className="text-green-100 text-sm mt-1">סיכום תוצאות היבוא מExcel</p>
      </div>
      <div className="p-6 space-y-3">
        <SummaryRow label="נמצאו בקובץ"     value={summary.total_in_file}      color="text-gray-700" />
        <SummaryRow label="נוספו בהצלחה"    value={summary.added}              color="text-green-600" bold />
        <SummaryRow label="כבר קיימים"       value={summary.already_exists}     color="text-amber-600" />
        <SummaryRow label="כפולות בקובץ"     value={summary.duplicates_in_file} color="text-gray-400" />
        <SummaryRow label="תאים לא תקינים"   value={summary.invalid_cells}      color="text-red-500" />
      </div>
      <div className="px-6 pb-6">
        <button onClick={onClose}
          className="w-full py-3 bg-indigo-600 text-white font-semibold rounded-xl hover:bg-indigo-700 transition-colors">
          סגור
        </button>
      </div>
    </div>
  </div>
);

const SummaryRow = ({ label, value, color, bold }) => (
  <div className="flex items-center justify-between py-2 border-b border-gray-50 last:border-0">
    <span className="text-sm text-gray-500">{label}</span>
    <span className={`text-sm ${color} ${bold ? 'font-bold text-lg' : 'font-medium'}`}>{value}</span>
  </div>
);

// ── Main Page ─────────────────────────────────────────────────────
const SectionDetail = () => {
  const { siteId, sectionId } = useParams();
  const navigate = useNavigate();
  const { isOperator } = useAuth();
  const fileInputRef = useRef(null);

  const [section,      setSection]      = useState(null);
  const [site,         setSite]         = useState(null);
  const [devices,      setDevices]      = useState([]);
  const [loading,      setLoading]      = useState(true);
  const [toast,        setToast]        = useState(null);
  const [error,        setError]        = useState('');
  const [importing,    setImporting]    = useState(false);
  const [importResult, setImportResult] = useState(null);

  // Modals
  const [createModal, setCreateModal] = useState(false);
  const [editModal,   setEditModal]   = useState(null);
  const [identifier,  setIdentifier]  = useState('');
  const [editIdent,   setEditIdent]   = useState('');

  const showToast = (msg, type = 'success') => {
    setToast({ msg, type });
    setTimeout(() => setToast(null), 3000);
  };

  const fetchData = async () => {
    try {
      const [siteRes, sectionsRes, devicesRes] = await Promise.all([
        api.get(`/api/v1/sites/${siteId}`),
        api.get(`/api/v1/sites/${siteId}/sections`),
        api.get('/api/v1/devices/'),
      ]);

      setSite(siteRes.data);
      const found = sectionsRes.data.find(s => s.id === sectionId);
      setSection(found || null);
      setDevices(devicesRes.data.filter(d => d.section_id === sectionId));
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { fetchData(); }, [siteId, sectionId]);

  // ── יבוא מExcel ───────────────────────────────────────────────
  const handleFileSelect = async (e) => {
    const file = e.target.files[0];
    if (!file) return;

    // ריסט input כדי שאפשר לבחור אותו קובץ שוב
    e.target.value = '';

    setImporting(true);
    showToast('📤 מייבא כתובות MAC מהקובץ...');

    try {
      const formData = new FormData();
      formData.append('file', file);

      const { data } = await api.post(
        `/api/v1/devices/import/${sectionId}`,
        formData,
        { headers: { 'Content-Type': 'multipart/form-data' } }
      );

      await fetchData(); // מרענן את רשימת הDevices
      setImportResult(data.summary);
    } catch (e) {
      showToast(e.response?.data?.detail || 'שגיאה בייבוא הקובץ', 'error');
    } finally {
      setImporting(false);
    }
  };

  // ── הוספה ידנית ───────────────────────────────────────────────
  const handleCreate = async (e) => {
    e.preventDefault(); setError('');
    try {
      await api.post('/api/v1/devices/', { identifier, section_id: sectionId });
      setCreateModal(false);
      setIdentifier('');
      await fetchData();
      showToast('✅ המכשיר נוסף בהצלחה');
    } catch (e) {
      setError(e.response?.data?.detail || 'Failed to add device');
    }
  };

  const handleEdit = async (e) => {
    e.preventDefault(); setError('');
    try {
      await api.patch(`/api/v1/devices/${editModal.id}`, { identifier: editIdent });
      setEditModal(null);
      await fetchData();
      showToast('✅ המכשיר עודכן');
    } catch (e) {
      setError(e.response?.data?.detail || 'Failed to update');
    }
  };

  const handleDelete = async (id, ident) => {
    if (!confirm(`למחוק את "${ident}"?`)) return;
    try {
      await api.delete(`/api/v1/devices/${id}`);
      await fetchData();
      showToast(`🗑️ "${ident}" נמחק`);
    } catch (e) {
      showToast(e.response?.data?.detail || 'Failed to delete', 'error');
    }
  };

  if (loading) return (
    <div className="flex items-center justify-center h-40">
      <div className="w-8 h-8 border-4 border-indigo-600 border-t-transparent rounded-full animate-spin" />
    </div>
  );

  if (!section) return (
    <div className="text-center py-20 text-gray-400">תא לא נמצא</div>
  );

  return (
    <div className="space-y-6">
      {toast && <Toast msg={toast.msg} type={toast.type} />}
      {importResult && <ImportSummary summary={importResult} onClose={() => setImportResult(null)} />}

      {/* Input קובץ מוסתר */}
      <input
        ref={fileInputRef}
        type="file"
        accept=".xlsx,.xls"
        onChange={handleFileSelect}
        className="hidden"
      />

      {/* Breadcrumb */}
      <div className="flex items-center gap-2 text-sm text-gray-400">
        <button onClick={() => navigate('/sites')} className="hover:text-indigo-600 transition-colors">Sites</button>
        <ArrowRight size={14} />
        <button onClick={() => navigate('/sites')} className="hover:text-indigo-600 transition-colors">{site?.name}</button>
        <ArrowRight size={14} />
        <span className="text-gray-700 font-medium">{section.name}</span>
      </div>

      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="p-3 bg-indigo-50 rounded-xl">
            <Layers size={22} className="text-indigo-600" />
          </div>
          <div>
            <h1 className="text-2xl font-bold text-gray-900">{section.name}</h1>
            <p className="text-sm text-gray-500 mt-0.5">
              {site?.name} · <span className="font-medium text-indigo-600">{devices.length} מכשירים</span>
            </p>
          </div>
        </div>

        {isOperator && (
          <div className="flex items-center gap-2">
            {/* יבוא מExcel */}
            <button
              onClick={() => fileInputRef.current?.click()}
              disabled={importing}
              className="flex items-center gap-2 bg-emerald-600 text-white px-4 py-2.5 rounded-xl font-medium hover:bg-emerald-700 transition-all shadow-sm disabled:opacity-50"
              title="יבוא כתובות MAC מקובץ Excel"
            >
              {importing
                ? <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                : <FileSpreadsheet size={17} />
              }
              {importing ? 'מייבא...' : 'יבוא מ-Excel'}
            </button>

            {/* הוספה ידנית */}
            <button
              onClick={() => { setCreateModal(true); setError(''); setIdentifier(''); }}
              className="flex items-center gap-2 bg-indigo-600 text-white px-4 py-2.5 rounded-xl font-medium hover:bg-indigo-700 transition-all shadow-sm"
            >
              <Plus size={17} /> הוסף ידנית
            </button>
          </div>
        )}
      </div>

      {/* טבלת Devices */}
      <div className="bg-white rounded-2xl border border-gray-100 shadow-sm overflow-hidden">
        {devices.length === 0 ? (
          <div className="py-20 text-center">
            <div className="w-16 h-16 rounded-2xl bg-gray-50 flex items-center justify-center mx-auto mb-4">
              <Monitor size={32} className="text-gray-300" />
            </div>
            <p className="text-gray-500 font-medium">אין מכשירים בתא הזה</p>
            <p className="text-gray-400 text-sm mt-1">העלה קובץ Excel עם כתובות MAC או הוסף ידנית</p>
            {isOperator && (
              <div className="flex items-center justify-center gap-3 mt-5">
                <button onClick={() => fileInputRef.current?.click()}
                  className="flex items-center gap-2 bg-emerald-600 text-white px-4 py-2.5 rounded-xl text-sm font-medium hover:bg-emerald-700 transition-colors">
                  <FileSpreadsheet size={16} /> יבוא מ-Excel
                </button>
                <button onClick={() => { setCreateModal(true); setIdentifier(''); }}
                  className="flex items-center gap-2 bg-indigo-600 text-white px-4 py-2.5 rounded-xl text-sm font-medium hover:bg-indigo-700 transition-colors">
                  <Plus size={16} /> הוסף ידנית
                </button>
              </div>
            )}
          </div>
        ) : (
          <>
            <div className="px-6 py-3 bg-gray-50/80 border-b border-gray-100 flex items-center justify-between">
              <span className="text-xs font-semibold text-gray-400 uppercase tracking-wider">
                {devices.length} מכשירים
              </span>
            </div>
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-gray-100 text-gray-400 text-xs uppercase tracking-wider">
                  <th className="text-left px-6 py-3 font-semibold">MAC Address</th>
                  <th className="text-left px-6 py-3 font-semibold">נוסף</th>
                  {isOperator && <th className="text-right px-6 py-3 font-semibold">פעולות</th>}
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-50">
                {devices.map((d, i) => (
                  <tr key={d.id} className="hover:bg-gray-50/40 transition-colors group">
                    <td className="px-6 py-3.5">
                      <div className="flex items-center gap-3">
                        <div className="w-8 h-8 rounded-lg bg-indigo-50 flex items-center justify-center shrink-0">
                          <Monitor size={14} className="text-indigo-500" />
                        </div>
                        <span className="font-mono text-sm font-medium text-gray-900 tracking-wide">
                          {d.identifier}
                        </span>
                      </div>
                    </td>
                    <td className="px-6 py-3.5 text-gray-400 text-xs">
                      {new Date(d.created_at).toLocaleDateString('he-IL')}
                    </td>
                    {isOperator && (
                      <td className="px-6 py-3.5">
                        <div className="flex items-center justify-end gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                          <button
                            onClick={() => { setEditModal(d); setEditIdent(d.identifier); setError(''); }}
                            className="p-1.5 rounded-lg hover:bg-indigo-50 text-gray-400 hover:text-indigo-600 transition-colors"
                            title="ערוך">
                            <Pencil size={14} />
                          </button>
                          <button
                            onClick={() => handleDelete(d.id, d.identifier)}
                            className="p-1.5 rounded-lg hover:bg-red-50 text-gray-400 hover:text-red-500 transition-colors"
                            title="מחק">
                            <Trash2 size={14} />
                          </button>
                        </div>
                      </td>
                    )}
                  </tr>
                ))}
              </tbody>
            </table>
          </>
        )}
      </div>

      {/* Modal: הוספה ידנית */}
      {createModal && (
        <div className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-2xl shadow-2xl max-w-md w-full overflow-hidden">
            <div className="bg-gradient-to-r from-indigo-600 to-indigo-700 px-8 py-6">
              <h2 className="text-xl font-bold text-white">הוספת מכשיר</h2>
              <p className="text-indigo-200 text-sm mt-1">תא: {section.name}</p>
            </div>
            <form onSubmit={handleCreate} className="p-8 space-y-4">
              <div>
                <label className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-1.5 block">
                  MAC Address
                </label>
                <input
                  placeholder="AA:BB:CC:DD:EE:FF" required
                  className="w-full px-4 py-3 border border-gray-200 rounded-xl focus:ring-2 focus:ring-indigo-500 outline-none text-sm font-mono bg-gray-50 focus:bg-white transition-all"
                  value={identifier}
                  onChange={e => setIdentifier(e.target.value)}
                />
              </div>
              {error && (
                <div className="bg-red-50 border border-red-200 rounded-xl px-4 py-3">
                  <p className="text-sm text-red-600">{error}</p>
                </div>
              )}
              <div className="flex gap-3 pt-2">
                <button type="button" onClick={() => { setCreateModal(false); setError(''); }}
                  className="flex-1 px-4 py-3 text-gray-600 hover:bg-gray-50 rounded-xl text-sm border border-gray-200">
                  ביטול
                </button>
                <button type="submit"
                  className="flex-1 px-4 py-3 bg-indigo-600 text-white font-semibold rounded-xl hover:bg-indigo-700 text-sm">
                  הוסף
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Modal: עריכה */}
      {editModal && (
        <div className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-2xl shadow-2xl max-w-md w-full overflow-hidden">
            <div className="bg-gradient-to-r from-amber-500 to-orange-500 px-8 py-6">
              <h2 className="text-xl font-bold text-white">עריכת מכשיר</h2>
              <p className="text-amber-100 text-sm mt-1 font-mono">{editModal.identifier}</p>
            </div>
            <form onSubmit={handleEdit} className="p-8 space-y-4">
              <div>
                <label className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-1.5 block">
                  MAC Address חדש
                </label>
                <input required
                  className="w-full px-4 py-3 border border-gray-200 rounded-xl focus:ring-2 focus:ring-indigo-500 outline-none text-sm font-mono bg-gray-50 focus:bg-white transition-all"
                  value={editIdent}
                  onChange={e => setEditIdent(e.target.value)}
                />
              </div>
              {error && (
                <div className="bg-red-50 border border-red-200 rounded-xl px-4 py-3">
                  <p className="text-sm text-red-600">{error}</p>
                </div>
              )}
              <div className="flex gap-3 pt-2">
                <button type="button" onClick={() => { setEditModal(null); setError(''); }}
                  className="flex-1 px-4 py-3 text-gray-600 hover:bg-gray-50 rounded-xl text-sm border border-gray-200">
                  ביטול
                </button>
                <button type="submit"
                  className="flex-1 px-4 py-3 bg-amber-500 text-white font-semibold rounded-xl hover:bg-amber-600 text-sm">
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

export default SectionDetail;