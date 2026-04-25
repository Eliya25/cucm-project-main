import { useEffect, useState } from 'react';
import { Globe, Users, Layers, Monitor, Activity } from 'lucide-react';
import { useAuth } from '../context/AuthContext.jsx';
import api from '../api.js';

// ── כרטיס סטטיסטיקה ──────────────────────────────────────────────
const StatCard = ({ icon: Icon, label, value, color }) => (
  <div className="bg-white rounded-2xl p-6 border border-gray-100 shadow-sm flex items-center gap-4">
    <div className={`p-3 rounded-xl ${color}`}>
      <Icon size={22} className="text-white" />
    </div>
    <div>
      <p className="text-sm text-gray-500 font-medium">{label}</p>
      <p className="text-2xl font-bold text-gray-900">{value}</p>
    </div>
  </div>
);

// ── שורת מידע ─────────────────────────────────────────────────────
const Row = ({ label, value }) => (
  <div className="flex items-center justify-between py-2 border-b border-gray-50 last:border-0">
    <span className="text-gray-500 text-sm">{label}</span>
    <span className="font-medium text-gray-800 text-sm">{value}</span>
  </div>
);

// ── Badge תפקיד ───────────────────────────────────────────────────
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

// ── הדף הראשי ─────────────────────────────────────────────────────
const Dashboard = () => {
  const { user, isAdmin } = useAuth();

  // הגדרת stats עם ערכי ברירת מחדל - מונע את השגיאה
  const [stats, setStats] = useState({
    sites:   0,
    devices: 0,
    users:   0,
    groups:  0,
  });

  useEffect(() => {
    const fetchStats = async () => {
      try {
        const [sitesRes, devicesRes] = await Promise.all([
          api.get('/api/v1/sites/'),
          api.get('/api/v1/devices/'),
        ]);

        const updated = {
          sites:   sitesRes.data.length,
          devices: devicesRes.data.length,
          users:   0,
          groups:  0,
        };

        // Admin ומעלה - מביא גם users ו-groups
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
        console.error('Failed to fetch stats:', e);
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

      {/* כרטיסי סטטיסטיקה */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard icon={Globe}   label="Sites"   value={stats.sites}   color="bg-indigo-500" />
        <StatCard icon={Monitor} label="Devices" value={stats.devices} color="bg-blue-500"   />
        {isAdmin && (
          <>
            <StatCard icon={Users}  label="Users"  value={stats.users}  color="bg-violet-500" />
            <StatCard icon={Layers} label="Groups" value={stats.groups} color="bg-cyan-500"   />
          </>
        )}
      </div>

      {/* מידע על המשתמש */}
      <div className="bg-white rounded-2xl border border-gray-100 shadow-sm p-6">
        <div className="flex items-center gap-2 mb-4">
          <Activity size={18} className="text-indigo-500" />
          <h2 className="font-semibold text-gray-800">מידע מערכת</h2>
        </div>
        <div className="space-y-1">
          <Row label="מחובר כ"    value={user?.username} />
          <Row label="תפקיד"      value={<RoleBadge role={user?.role} />} />
          <Row label="סטטוס"  value={<span className="text-green-600 font-medium text-sm">● מחובר</span>} />
        </div>
      </div>

    </div>
  );
};

export default Dashboard;