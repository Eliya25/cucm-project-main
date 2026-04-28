import { useEffect, useState } from 'react';
import { Globe, Users, Layers, Monitor, Activity, ArrowRight, ChevronRight } from 'lucide-react';
import { useAuth } from '../context/AuthContext.jsx';
import { useNavigate } from 'react-router-dom';
import api from '../api.js';

const RoleBadge = ({ role }) => {
  const colors = {
    superadmin: 'bg-purple-100 text-purple-700',
    admin:      'bg-indigo-100 text-indigo-700',
    operator:   'bg-blue-100   text-blue-700',
    viewer:     'bg-gray-100   text-gray-700',
  };
  return (
    <span className={`px-2.5 py-0.5 rounded-full text-xs font-bold uppercase tracking-wide ${colors[role] || 'bg-gray-100 text-gray-700'}`}>
      {role}
    </span>
  );
};

const Row = ({ label, value }) => (
  <div className="flex items-center justify-between py-2 border-b border-gray-50 last:border-0">
    <span className="text-gray-500 text-sm">{label}</span>
    <span className="font-medium text-gray-800 text-sm">{value}</span>
  </div>
);

// כרטיס סטטיסטיקה קליקבילי
const StatCard = ({ icon: Icon, label, value, color, onClick }) => (
  <div
    onClick={onClick}
    className={`bg-white rounded-2xl p-6 border border-gray-100 shadow-sm flex items-center gap-4 ${onClick ? 'cursor-pointer hover:shadow-md hover:border-indigo-100 transition-all group' : ''}`}
  >
    <div className={`p-3 rounded-xl ${color}`}>
      <Icon size={22} className="text-white" />
    </div>
    <div className="flex-1">
      <p className="text-sm text-gray-500 font-medium">{label}</p>
      <p className="text-2xl font-bold text-gray-900">{value}</p>
    </div>
    {onClick && (
      <ChevronRight size={18} className="text-gray-300 group-hover:text-indigo-400 transition-colors" />
    )}
  </div>
);

const Dashboard = () => {
  const { user, isAdmin, isOperator } = useAuth();
  const navigate = useNavigate();

  const [stats,   setStats]   = useState({ sites: 0, devices: 0, users: 0, groups: 0 });
  const [sites,   setSites]   = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchStats = async () => {
      try {
        const [sitesRes, devicesRes] = await Promise.all([
          api.get('/api/v1/sites/'),
          api.get('/api/v1/devices/'),
        ]);

        setSites(sitesRes.data);

        const updated = {
          sites:   sitesRes.data.length,
          devices: devicesRes.data.length,
          users:   0,
          groups:  0,
        };

        if (isAdmin) {
          const [usersRes, groupsRes] = await Promise.all([
            api.get('/api/v1/users/'),
            api.get('/api/v1/groups/'),
          ]);
          updated.users  = usersRes.data.length;
          updated.groups = groupsRes.data.length;
        }

        setStats(updated);
      } catch (e) {
        console.error(e);
      } finally {
        setLoading(false);
      }
    };
    fetchStats();
  }, [isAdmin]);

  return (
    <div className="space-y-8">

      {/* כותרת */}
      <div>
        <h1 className="text-2xl font-bold text-gray-900">
          ברוך הבא, <span className="text-indigo-600">{user?.username}</span>
        </h1>
        <p className="text-gray-500 mt-1 text-sm">סקירה כללית של המערכת</p>
      </div>

      {/* כרטיסי סטטיסטיקה — קליקביליים */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          icon={Globe} label="Sites" value={stats.sites} color="bg-indigo-500"
          onClick={() => navigate('/sites')}
        />
        <StatCard
          icon={Monitor} label="Devices" value={stats.devices} color="bg-blue-500"
          onClick={() => navigate('/devices')}
        />
        {isAdmin && (
          <>
            <StatCard
              icon={Users} label="Users" value={stats.users} color="bg-violet-500"
              onClick={() => navigate('/users')}
            />
            <StatCard
              icon={Layers} label="Groups" value={stats.groups} color="bg-cyan-500"
              onClick={() => navigate('/groups')}
            />
          </>
        )}
      </div>

      {/* Sites עם Sections — לחיצה על Section פותחת את הדף שלו */}
      {!loading && sites.length > 0 && (
        <div className="bg-white rounded-2xl border border-gray-100 shadow-sm overflow-hidden">
          <div className="flex items-center gap-2 px-6 py-4 border-b border-gray-100 bg-gray-50/50">
            <Globe size={18} className="text-indigo-500" />
            <h2 className="font-semibold text-gray-800">האתרים שלך</h2>
          </div>
          <div className="divide-y divide-gray-50">
            {sites.map(site => (
              <SiteRow key={site.id} site={site} navigate={navigate} isOperator={isOperator} />
            ))}
          </div>
        </div>
      )}

      {/* מידע מערכת */}
      <div className="bg-white rounded-2xl border border-gray-100 shadow-sm p-6">
        <div className="flex items-center gap-2 mb-4">
          <Activity size={18} className="text-indigo-500" />
          <h2 className="font-semibold text-gray-800">מידע מערכת</h2>
        </div>
        <div className="space-y-1">
          <Row label="מחובר כ"  value={user?.username} />
          <Row label="תפקיד"    value={<RoleBadge role={user?.role} />} />
          <Row label="סטטוס"    value={<span className="text-green-600 font-medium text-sm">● מחובר</span>} />
        </div>
      </div>
    </div>
  );
};

// קומפוננט Site עם Sections שניתן ללחוץ עליהם
const SiteRow = ({ site, navigate, isOperator }) => {
  const [sections, setSections] = useState([]);
  const [open,     setOpen]     = useState(false);

  const loadSections = async () => {
    if (sections.length > 0) { setOpen(o => !o); return; }
    try {
      const { data } = await api.get(`/api/v1/sites/${site.id}/sections`);
      setSections(data);
      setOpen(true);
    } catch (e) {
      console.error(e);
    }
  };

  return (
    <div>
      <div
        onClick={loadSections}
        className="flex items-center justify-between px-6 py-3 cursor-pointer hover:bg-gray-50/50 transition-colors"
      >
        <div className="flex items-center gap-2">
          <Globe size={15} className="text-indigo-400" />
          <span className="font-medium text-gray-800 text-sm">{site.name}</span>
        </div>
        <ChevronRight size={15} className={`text-gray-400 transition-transform ${open ? 'rotate-90' : ''}`} />
      </div>

      {open && (
        <div className="bg-gray-50/40 border-t border-gray-100/60 divide-y divide-gray-100/40">
          {sections.length === 0 && (
            <p className="px-10 py-3 text-xs text-gray-400">אין Sections</p>
          )}
          {sections.map(section => (
            <div
              key={section.id}
              onClick={() => navigate(`/sites/${site.id}/sections/${section.id}`)}
              className="flex items-center justify-between px-10 py-2.5 cursor-pointer hover:bg-indigo-50/40 transition-colors group"
            >
              <div className="flex items-center gap-2">
                <Layers size={13} className="text-gray-400" />
                <span className="text-sm text-gray-700">{section.name}</span>
              </div>
              <span className="text-xs text-indigo-500 opacity-0 group-hover:opacity-100 transition-opacity flex items-center gap-1">
                פתח <ArrowRight size={12} />
              </span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default Dashboard;