import { useState, useEffect } from 'react';
import { Bell, Shield, Key, Save, Monitor, Globe, CheckCircle } from 'lucide-react';
import { useAuth } from '../context/AuthContext.jsx';
import api from '../api.js';

const Toast = ({ msg }) => (
  <div className="fixed top-6 right-6 z-50 flex items-center gap-3 bg-gray-900 text-white px-5 py-3.5 rounded-2xl shadow-2xl border border-gray-700">
    <CheckCircle size={18} className="text-green-400 shrink-0" />
    <span className="text-sm font-medium">{msg}</span>
  </div>
);

const Section = ({ title, icon: Icon, children, badge }) => (
  <div className="bg-white rounded-2xl border border-gray-100 shadow-sm overflow-hidden">
    <div className="flex items-center justify-between px-6 py-4 border-b border-gray-100 bg-gray-50/50">
      <div className="flex items-center gap-3">
        <Icon size={18} className="text-indigo-500" />
        <h2 className="font-semibold text-gray-800">{title}</h2>
      </div>
      {badge && (
        <span className="text-xs bg-amber-100 text-amber-700 px-2.5 py-1 rounded-full font-medium">
          {badge}
        </span>
      )}
    </div>
    <div className="p-6 space-y-5">{children}</div>
  </div>
);

const Row = ({ label, description, children }) => (
  <div className="flex items-center justify-between">
    <div>
      <p className="text-sm font-medium text-gray-800">{label}</p>
      {description && <p className="text-xs text-gray-400 mt-0.5">{description}</p>}
    </div>
    {children}
  </div>
);

const Toggle = ({ checked, onChange, disabled }) => (
  <button
    type="button"
    onClick={() => !disabled && onChange(!checked)}
    disabled={disabled}
    className={`relative w-11 h-6 rounded-full transition-colors duration-200 ${
      disabled ? 'opacity-40 cursor-not-allowed' :
      checked ? 'bg-indigo-600' : 'bg-gray-200'
    }`}
  >
    <span className={`absolute top-0.5 left-0.5 w-5 h-5 bg-white rounded-full shadow transition-transform duration-200 ${checked ? 'translate-x-5' : ''}`} />
  </button>
);

const Settings = () => {
  const { user } = useAuth();
  // user מכיל: { username, role } בלבד — id לא נשמר ב-AuthContext
  // לכן שינוי סיסמה עובד דרך /me/change-password ולא דרך /{id}

  const [darkMode,  setDarkMode]  = useState(document.documentElement.classList.contains('dark'));
  const [language,  setLanguage]  = useState(localStorage.getItem('language') || 'he');
  const [pwForm,    setPwForm]    = useState({ current: '', next: '', confirm: '' });
  const [pwError,   setPwError]   = useState('');
  const [toast,     setToast]     = useState('');

  const showToast = (msg) => {
    setToast(msg);
    setTimeout(() => setToast(''), 3000);
  };

  const handleDarkMode = (val) => {
    setDarkMode(val);
    if (val) {
      document.documentElement.classList.add('dark');
      localStorage.setItem('darkMode', 'true');
    } else {
      document.documentElement.classList.remove('dark');
      localStorage.setItem('darkMode', 'false');
    }
    showToast(val ? '🌙 Dark mode הופעל' : '☀️ Light mode הופעל');
  };

  const handleLanguage = (val) => {
    setLanguage(val);
    localStorage.setItem('language', val);
    document.documentElement.setAttribute('lang', val);
    document.body.setAttribute('dir', val === 'he' ? 'rtl' : 'ltr');
    showToast(val === 'he' ? '🇮🇱 שפה שונתה לעברית' : '🇺🇸 Language changed to English');
  };

  const handleChangePassword = async (e) => {
    e.preventDefault();
    setPwError('');

    if (pwForm.next !== pwForm.confirm) {
      setPwError('הסיסמאות החדשות אינן תואמות'); return;
    }
    if (pwForm.next.length < 8) {
      setPwError('הסיסמה חייבת להיות לפחות 8 תווים'); return;
    }
    if (pwForm.current === pwForm.next) {
      setPwError('הסיסמה החדשה חייבת להיות שונה מהנוכחית'); return;
    }

    try {
      // endpoint ייעודי לשינוי סיסמה אישי — לא דורש id
      await api.patch('/api/v1/users/me/change-password', {
        current_password: pwForm.current,
        new_password: pwForm.next,
      });
      setPwForm({ current: '', next: '', confirm: '' });
      showToast('✅ הסיסמה שונתה בהצלחה');
    } catch (e) {
      setPwError(e.response?.data?.detail || 'שגיאה בשינוי הסיסמה');
    }
  };

  useEffect(() => {
    const savedDark = localStorage.getItem('darkMode') === 'true';
    const savedLang = localStorage.getItem('language') || 'he';
    if (savedDark) document.documentElement.classList.add('dark');
    document.documentElement.setAttribute('lang', savedLang);
    document.body.setAttribute('dir', savedLang === 'he' ? 'rtl' : 'ltr');
  }, []);

  return (
    <div className="space-y-6">
      {toast && <Toast msg={toast} />}

      <div>
        <h1 className="text-2xl font-bold text-gray-900">Settings</h1>
        <p className="text-sm text-gray-500 mt-1">העדפות אישיות והגדרות חשבון</p>
      </div>

      {/* מראה */}
      <Section title="מראה" icon={Monitor}>
        <Row label="Dark Mode" description="מעבר לתצוגה כהה">
          <Toggle checked={darkMode} onChange={handleDarkMode} />
        </Row>
        <Row label="שפת ממשק" description="שפה וכיוון טקסט">
          <div className="flex gap-2">
            <button onClick={() => handleLanguage('he')}
              className={`px-4 py-2 rounded-xl text-sm font-medium border transition-all ${
                language === 'he' ? 'bg-indigo-600 text-white border-indigo-600'
                : 'bg-white text-gray-600 border-gray-200 hover:border-indigo-300'}`}>
              🇮🇱 עברית
            </button>
            <button onClick={() => handleLanguage('en')}
              className={`px-4 py-2 rounded-xl text-sm font-medium border transition-all ${
                language === 'en' ? 'bg-indigo-600 text-white border-indigo-600'
                : 'bg-white text-gray-600 border-gray-200 hover:border-indigo-300'}`}>
              🇺🇸 English
            </button>
          </div>
        </Row>
      </Section>

      {/* התראות */}
      <Section title="התראות" icon={Bell} badge="Coming Soon — נדרש CUCM">
        <Row label="התראות טלפונים נפולים" description="דורש חיבור CUCM">
          <Toggle checked={false} onChange={() => {}} disabled />
        </Row>
        <Row label="התראות מערכת" description="יהיה זמין עם WebSocket">
          <Toggle checked={false} onChange={() => {}} disabled />
        </Row>
        <div className="bg-amber-50 border border-amber-200 rounded-xl px-4 py-3">
          <p className="text-xs text-amber-700 font-medium">
            💡 התראות יהיו זמינות לאחר שילוב CUCM API
          </p>
        </div>
      </Section>

      {/* חשבון */}
      <Section title="חשבון" icon={Shield}>
        <Row label="שם משתמש" description="שם הכניסה שלך">
          <span className="text-sm font-medium text-gray-600 bg-gray-100 px-3 py-1.5 rounded-lg">
            {user?.username}
          </span>
        </Row>
        <Row label="תפקיד" description="רמת ההרשאות שלך">
          <span className="text-sm font-bold text-indigo-600 bg-indigo-50 px-3 py-1.5 rounded-lg uppercase tracking-wide">
            {user?.role}
          </span>
        </Row>
        <Row label="סטטוס API" description="חיבור לשרת הבקאנד">
          <span className="text-sm text-green-600 font-medium flex items-center gap-1.5">
            <span className="w-2 h-2 bg-green-500 rounded-full animate-pulse" />
            מחובר
          </span>
        </Row>
      </Section>

      {/* שינוי סיסמה */}
      <Section title="שינוי סיסמה" icon={Key}>
        <form onSubmit={handleChangePassword} className="space-y-3">
          <input type="password" placeholder="סיסמה נוכחית" required
            className="w-full px-4 py-3 border border-gray-200 rounded-xl text-sm outline-none focus:ring-2 focus:ring-indigo-500"
            value={pwForm.current} onChange={e => setPwForm({ ...pwForm, current: e.target.value })} />
          <input type="password" placeholder="סיסמה חדשה (מינימום 8 תווים)" required
            className="w-full px-4 py-3 border border-gray-200 rounded-xl text-sm outline-none focus:ring-2 focus:ring-indigo-500"
            value={pwForm.next} onChange={e => setPwForm({ ...pwForm, next: e.target.value })} />
          <input type="password" placeholder="אימות סיסמה חדשה" required
            className="w-full px-4 py-3 border border-gray-200 rounded-xl text-sm outline-none focus:ring-2 focus:ring-indigo-500"
            value={pwForm.confirm} onChange={e => setPwForm({ ...pwForm, confirm: e.target.value })} />
          {pwError && <p className="text-sm text-red-500">{pwError}</p>}
          <button type="submit"
            className="flex items-center gap-2 bg-indigo-600 text-white px-5 py-2.5 rounded-xl font-medium hover:bg-indigo-700 transition-all text-sm">
            <Save size={16} /> שמור סיסמה
          </button>
        </form>
      </Section>

      {/* מידע מערכת */}
      <Section title="מידע מערכת" icon={Globe}>
        <Row label="כתובת API" description="">
          <span className="text-sm text-gray-500 font-mono bg-gray-100 px-3 py-1.5 rounded-lg">
            localhost:8080
          </span>
        </Row>
        <Row label="גרסת Frontend" description="">
          <span className="text-sm text-gray-500 bg-gray-100 px-3 py-1.5 rounded-lg">v1.0.0</span>
        </Row>
      </Section>
    </div>
  );
};

export default Settings;