import { useEffect, useState } from 'react';
import { Globe, Plus, ChevronDown, ChevronRight, Trash2, Link2, Layers, CheckCircle } from 'lucide-react';
import api from '../api.js';
import { useAuth } from '../context/AuthContext.jsx';

const Sites = () => {
  const { isSuperAdmin, isAdmin } = useAuth();
  const [sites,        setSites]        = useState([]);
  const [groups,       setGroups]       = useState([]);
  const [expanded,     setExpanded]     = useState({});
  const [sections,     setSections]     = useState({});
  const [loading,      setLoading]      = useState(true);
  const [toast,        setToast]        = useState(''); // הודעת הצלחה

  // Modals
  const [siteModal,    setSiteModal]    = useState(false);
  const [sectionModal, setSectionModal] = useState(null); // site_id
  const [linkModal,    setLinkModal]    = useState(null); // { section_id, site_id }

  // Forms
  const [siteForm,    setSiteForm]    = useState({ name: '', description: '', group_id: '' });
  const [sectionForm, setSectionForm] = useState({ name: '', description: '' });
  const [linkForm,    setLinkForm]    = useState({ group_id: '', is_admin: false });
  const [error,       setError]       = useState('');

  // ── הצגת Toast הצלחה ────────────────────────────────────────────
  const showToast = (msg) => {
    setToast(msg);
    setTimeout(() => setToast(''), 3000);
  };

  // ── שליפת Sites ו-Groups ─────────────────────────────────────────
  const fetchSites = async () => {
    try {
      const [sitesRes, groupsRes] = await Promise.all([
        api.get('/api/v1/sites/'),
        api.get('/api/v1/groups/'),
      ]);
      setSites(sitesRes.data);
      setGroups(groupsRes.data);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  // ── שליפת Sections - תמיד מהשרת (בלי cache) ────────────────────
  const fetchSections = async (siteId) => {
    try {
      const { data } = await api.get(`/api/v1/sites/${siteId}/sections`);
      setSections(prev => ({ ...prev, [siteId]: data }));
    } catch (e) {
      console.error(e);
    }
  };

  useEffect(() => { fetchSites(); }, []);

  // ── פתיחה/סגירה של Site ─────────────────────────────────────────
  const toggleExpand = (siteId) => {
    const isOpen = expanded[siteId];
    setExpanded(prev => ({ ...prev, [siteId]: !isOpen }));
    if (!isOpen) fetchSections(siteId); // שולף sections בכל פתיחה
  };

  // ── יצירת Site ──────────────────────────────────────────────────
  const handleCreateSite = async (e) => {
    e.preventDefault(); setError('');
    try {
      await api.post('/api/v1/sites/', siteForm);
      setSiteModal(false);
      setSiteForm({ name: '', description: '', group_id: '' });
      await fetchSites();
      showToast(`✅ Site "${siteForm.name}" נוצר בהצלחה`);
    } catch (e) {
      setError(e.response?.data?.detail || 'Failed to create site');
    }
  };

  // ── מחיקת Site ──────────────────────────────────────────────────
  const handleDeleteSite = async (id, name) => {
    if (!isSuperAdmin) return;
    if (!confirm(`למחוק את "${name}" וכל הSections שלו?`)) return;
    try {
      await api.delete(`/api/v1/sites/${id}`);
      await fetchSites();
      showToast(`🗑️ Site "${name}" נמחק`);
    } catch (e) {
      alert(e.response?.data?.detail || 'Failed to delete site');
    }
  };

  // ── יצירת Section ────────────────────────────────────────────────
  const handleCreateSection = async (e) => {
    e.preventDefault(); setError('');
    const siteId = sectionModal;
    const sectionName = sectionForm.name;
    try {
      await api.post('/api/v1/sites/sections', {
        ...sectionForm,
        site_id: siteId,
      });
      setSectionModal(null);
      setSectionForm({ name: '', description: '' });
      await fetchSections(siteId); // מרענן את הרשימה
      showToast(`✅ Section "${sectionName}" נוסף בהצלחה`);
    } catch (e) {
      setError(e.response?.data?.detail || 'Failed to create section');
    }
  };

  // ── מחיקת Section ────────────────────────────────────────────────
  const handleDeleteSection = async (sectionId, siteId, name) => {
    if (!isSuperAdmin) return;
    if (!confirm(`למחוק את Section "${name}"?`)) return;
    try {
      await api.delete(`/api/v1/sites/sections/${sectionId}`);
      await fetchSections(siteId);
      showToast(`🗑️ Section "${name}" נמחק`);
    } catch (e) {
      alert(e.response?.data?.detail || 'Failed to delete section');
    }
  };

  // ── קישור Section לGroup ─────────────────────────────────────────
  const handleLinkSection = async (e) => {
    e.preventDefault(); setError('');
    const { section_id } = linkModal;
    const groupName = groups.find(g => g.id === linkForm.group_id)?.name || '';
    try {
      await api.post(
        `/api/v1/groups/${linkForm.group_id}/link-section`,
        null,
        { params: { section_id, is_admin: linkForm.is_admin } }
      );
      setLinkModal(null);
      setLinkForm({ group_id: '', is_admin: false });
      showToast(`✅ Section קושר לGroup "${groupName}" בהצלחה`);
    } catch (e) {
      setError(e.response?.data?.detail || 'Failed to link section');
    }
  };

  const groupName = (id) => groups.find(g => g.id === id)?.name || '—';

  if (loading) return <div className="flex justify-center p-10 text-gray-400">טוען אתרים...</div>;

  return (
    <div className="space-y-6">

      {/* Toast הודעת הצלחה */}
      {toast && (
        <div className="fixed top-6 right-6 z-50 flex items-center gap-3 bg-gray-900 text-white px-5 py-3.5 rounded-2xl shadow-2xl border border-gray-700 animate-fade-in">
          <CheckCircle size={18} className="text-green-400 shrink-0" />
          <span className="text-sm font-medium">{toast}</span>
        </div>
      )}

      {/* כותרת */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Sites & Sections</h1>
          <p className="text-sm text-gray-500 mt-1">ניהול אתרים, תאים וקישור לקבוצות</p>
        </div>
        {isAdmin && (
          <button onClick={() => { setSiteModal(true); setError(''); }}
            className="flex items-center gap-2 bg-indigo-600 text-white px-5 py-2.5 rounded-xl font-medium hover:bg-indigo-700 transition-all shadow-sm">
            <Plus size={18} /> הוסף Site
          </button>
        )}
      </div>

      {/* רשימת Sites */}
      <div className="space-y-3">
        {sites.map(site => (
          <div key={site.id} className="bg-white rounded-2xl border border-gray-100 shadow-sm overflow-hidden">

            {/* שורת Site */}
            <div
              className="flex items-center justify-between px-6 py-4 cursor-pointer hover:bg-gray-50/50 transition-colors"
              onClick={() => toggleExpand(site.id)}
            >
              <div className="flex items-center gap-3">
                {expanded[site.id]
                  ? <ChevronDown size={18} className="text-indigo-500" />
                  : <ChevronRight size={18} className="text-gray-400" />
                }
                <div className="p-2 bg-indigo-50 rounded-lg">
                  <Globe size={16} className="text-indigo-600" />
                </div>
                <div>
                  <p className="font-semibold text-gray-900">{site.name}</p>
                  {site.description && <p className="text-xs text-gray-400">{site.description}</p>}
                </div>
              </div>

              <div className="flex items-center gap-3" onClick={e => e.stopPropagation()}>
                <span className="text-xs text-gray-400 bg-gray-50 border border-gray-100 px-2 py-1 rounded-lg">
                  {groupName(site.group_id)}
                </span>
                {isAdmin && (
                  <button
                    onClick={() => { setSectionModal(site.id); setSectionForm({ name: '', description: '' }); setError(''); }}
                    className="text-xs text-indigo-600 hover:text-indigo-800 flex items-center gap-1 px-2 py-1 hover:bg-indigo-50 rounded-lg transition-colors">
                    <Plus size={14} /> הוסף Section
                  </button>
                )}
                {isSuperAdmin && (
                  <button
                    onClick={() => handleDeleteSite(site.id, site.name)}
                    className="p-1.5 rounded-lg hover:bg-red-50 text-gray-400 hover:text-red-500 transition-colors">
                    <Trash2 size={16} />
                  </button>
                )}
              </div>
            </div>

            {/* Sections */}
            {expanded[site.id] && (
              <div className="border-t border-gray-100 bg-gray-50/30 divide-y divide-gray-100/60">
                {!sections[site.id] && (
                  <p className="px-8 py-4 text-xs text-gray-400">טוען...</p>
                )}
                {sections[site.id]?.length === 0 && (
                  <p className="px-8 py-4 text-xs text-gray-400">אין Sections עדיין. הוסף אחד למעלה.</p>
                )}
                {sections[site.id]?.map(section => (
                  <div key={section.id} className="flex items-center justify-between px-8 py-3">
                    <div className="flex items-center gap-2">
                      <Layers size={14} className="text-gray-400" />
                      <span className="text-sm text-gray-700 font-medium">{section.name}</span>
                      {section.description && (
                        <span className="text-xs text-gray-400">· {section.description}</span>
                      )}
                    </div>
                    <div className="flex items-center gap-2">
                      {isAdmin && (
                        <button
                          onClick={() => { setLinkModal({ section_id: section.id, site_id: site.id }); setError(''); }}
                          className="text-xs text-indigo-600 hover:text-indigo-800 flex items-center gap-1 px-2 py-1 hover:bg-indigo-50 rounded-lg transition-colors">
                          <Link2 size={13} /> קשר לGroup
                        </button>
                      )}
                      {isSuperAdmin && (
                        <button
                          onClick={() => handleDeleteSection(section.id, site.id, section.name)}
                          className="p-1 rounded-lg hover:bg-red-50 text-gray-400 hover:text-red-500 transition-colors">
                          <Trash2 size={14} />
                        </button>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        ))}

        {sites.length === 0 && (
          <div className="bg-white rounded-2xl border border-gray-100 shadow-sm p-12 text-center">
            <Globe size={40} className="mx-auto text-gray-200 mb-3" />
            <p className="text-gray-400">אין Sites עדיין. צור את הראשון.</p>
          </div>
        )}
      </div>

      {/* Modal: יצירת Site */}
      {siteModal && (
        <Modal title="יצירת Site חדש" onClose={() => { setSiteModal(false); setError(''); }}>
          <form onSubmit={handleCreateSite} className="space-y-4">
            <Input placeholder="שם ה-Site" required value={siteForm.name}
              onChange={e => setSiteForm({ ...siteForm, name: e.target.value })} />
            <Input placeholder="תיאור (אופציונלי)" value={siteForm.description}
              onChange={e => setSiteForm({ ...siteForm, description: e.target.value })} />
            <select
              className="w-full px-4 py-3 border border-gray-200 rounded-xl focus:ring-2 focus:ring-indigo-500 outline-none text-sm bg-white"
              value={siteForm.group_id}
              onChange={e => setSiteForm({ ...siteForm, group_id: e.target.value })}
              required
            >
              <option value="">בחר קבוצה</option>
              {groups.map(g => <option key={g.id} value={g.id}>{g.name}</option>)}
            </select>
            {error && <p className="text-sm text-red-500">{error}</p>}
            <ModalActions onCancel={() => { setSiteModal(false); setError(''); }} submitLabel="צור Site" />
          </form>
        </Modal>
      )}

      {/* Modal: הוספת Section */}
      {sectionModal && (
        <Modal title="הוספת Section" onClose={() => { setSectionModal(null); setError(''); }}>
          <form onSubmit={handleCreateSection} className="space-y-4">
            <Input placeholder="שם ה-Section" required value={sectionForm.name}
              onChange={e => setSectionForm({ ...sectionForm, name: e.target.value })} />
            <Input placeholder="תיאור (אופציונלי)" value={sectionForm.description}
              onChange={e => setSectionForm({ ...sectionForm, description: e.target.value })} />
            {error && <p className="text-sm text-red-500">{error}</p>}
            <ModalActions onCancel={() => { setSectionModal(null); setError(''); }} submitLabel="הוסף Section" />
          </form>
        </Modal>
      )}

      {/* Modal: קישור Section לGroup */}
      {linkModal && (
        <Modal title="קישור Section לקבוצה" onClose={() => { setLinkModal(null); setError(''); }}>
          <form onSubmit={handleLinkSection} className="space-y-4">
            <select
              className="w-full px-4 py-3 border border-gray-200 rounded-xl focus:ring-2 focus:ring-indigo-500 outline-none text-sm bg-white"
              value={linkForm.group_id}
              onChange={e => setLinkForm({ ...linkForm, group_id: e.target.value })}
              required
            >
              <option value="">בחר קבוצה</option>
              {groups.map(g => <option key={g.id} value={g.id}>{g.name}</option>)}
            </select>
            <label className="flex items-center gap-3 cursor-pointer">
              <input type="checkbox" className="w-4 h-4 accent-indigo-600 rounded"
                checked={linkForm.is_admin}
                onChange={e => setLinkForm({ ...linkForm, is_admin: e.target.checked })} />
              <span className="text-sm text-gray-700">הרשאת Admin (יכול להוסיף/לערוך Devices)</span>
            </label>
            {error && <p className="text-sm text-red-500">{error}</p>}
            <ModalActions onCancel={() => { setLinkModal(null); setError(''); }} submitLabel="קשר לקבוצה" />
          </form>
        </Modal>
      )}
    </div>
  );
};

// ── קומפוננטות עזר ────────────────────────────────────────────────

const Modal = ({ title, onClose, children }) => (
  <div className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center z-50 p-4">
    <div className="bg-white rounded-2xl shadow-2xl max-w-md w-full p-8 border border-gray-100">
      <h2 className="text-xl font-bold text-gray-900 mb-6">{title}</h2>
      {children}
    </div>
  </div>
);

const Input = (props) => (
  <input
    className="w-full px-4 py-3 border border-gray-200 rounded-xl focus:ring-2 focus:ring-indigo-500 outline-none text-sm"
    {...props}
  />
);

const ModalActions = ({ onCancel, submitLabel }) => (
  <div className="flex gap-3 pt-2">
    <button type="button" onClick={onCancel}
      className="flex-1 px-4 py-3 text-gray-600 font-medium hover:bg-gray-50 rounded-xl transition-colors text-sm">
      ביטול
    </button>
    <button type="submit"
      className="flex-1 px-4 py-3 bg-indigo-600 text-white font-medium rounded-xl hover:bg-indigo-700 transition-colors text-sm">
      {submitLabel}
    </button>
  </div>
);

export default Sites;