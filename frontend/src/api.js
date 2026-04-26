import axios from 'axios';

const api = axios.create({
  baseURL: 'http://localhost:8080',
  withCredentials: true, // שולח cookies אוטומטית בכל בקשה
});

// ── Interceptor לטיפול בtokens פגי תוקף ─────────────────────────
// כשהשרת מחזיר 401 — מנסה לרענן את הaccess token אוטומטית
// אם הרענון הצליח — חוזר על הבקשה המקורית
// אם הרענון נכשל — יוצא מהמערכת

let isRefreshing = false;
// תור של בקשות שממתינות לרענון הtoken
let waitingQueue = [];

const processQueue = (error) => {
  waitingQueue.forEach(({ resolve, reject }) => {
    if (error) reject(error);
    else resolve();
  });
  waitingQueue = [];
};

api.interceptors.response.use(
  // בקשה הצליחה — מחזיר את התשובה כמו שהיא
  (response) => response,

  async (error) => {
    const originalRequest = error.config;

    // טיפול רק בשגיאות 401 שלא נסינו כבר לרענן
    if (error.response?.status !== 401 || originalRequest._retry) {
      return Promise.reject(error);
    }

    // לא מנסים לרענן את בקשת הrrefresh עצמה — זה יגרום ללולאה אינסופית
    if (originalRequest.url?.includes('/auth/refresh') ||
        originalRequest.url?.includes('/auth/login')) {
      return Promise.reject(error);
    }

    // אם כבר מרעננים — נוסיף לתור ונחכה
    if (isRefreshing) {
      return new Promise((resolve, reject) => {
        waitingQueue.push({ resolve, reject });
      }).then(() => api(originalRequest));
    }

    // מתחילים רענון
    originalRequest._retry = true;
    isRefreshing = true;

    try {
      // קורא לrefresh — השרת מקבל את הcookie אוטומטית וממחזיר cookie חדש
      await api.post('/api/v1/auth/refresh');

      // הרענון הצליח — מאפשרים לבקשות בתור להמשיך
      processQueue(null);
      isRefreshing = false;

      // חוזרים על הבקשה המקורית עם הcookie החדש
      return api(originalRequest);

    } catch (refreshError) {
      // הרענון נכשל — הsession פג לגמרי, יוצאים
      processQueue(refreshError);
      isRefreshing = false;

      // מנקים את מצב המשתמש ושולחים לlogin
      localStorage.removeItem('userInfo');
      window.location.href = '/login';
      return Promise.reject(refreshError);
    }
  }
);

export default api;