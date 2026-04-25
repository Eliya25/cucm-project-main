import { createContext, useContext, useState, useEffect } from "react";
import api from '../api.js';


const AuthContext = createContext(null)


export const AuthProvider = ({children}) => {
    const [user, setUser] = useState(null);
    const [loading, setLoading] = useState(true); // בודק אם קיים SESSION



    useEffect(() => {
        const checkSession = async () => {
            try {
                const {data} = await api.get('/api/v1/auth/me');


                //אם ה-COOKIE תקין מקבלים בחזרה את פרטי המשתמש מהשרת
                setUser({username: data.username, role: data.role})
            } catch {
                //אם המתשמש לא מחובר ה-COOKIE לא קיים אמ פג תוקף
                setUser(null)
            } finally {
                setLoading(false)
            }
        };
        checkSession();
    }, [])


    const login = (userInfo) => {
        setUser(userInfo);
    };

    const logout = () => {
        setUser(null);
    };

    const isSuperAdmin = user?.role === 'superadmin';
    const isAdmin = user?.role === 'admin' || isSuperAdmin;
    const isOperator = user?.role === 'operator' || isAdmin;



    if (loading){
        return (
            <div className="min-h-screen bg-gray-50 flex items-center justify-center">
                <div className="flex flex-col items-center gap-3">
                    <div className="w-8 h-8 border-4 border-indigo-600 border-t-transparent rounded-b-full animate-spin"/>
                    <p className="text-sm text-gray-400">Loading...</p>
                </div>
            </div>
        );
    }

    return (
        <AuthContext.Provider value={{user, login, logout, isSuperAdmin, isAdmin, isOperator}}>
            {children}
        </AuthContext.Provider>
    );
};


export const useAuth = () => useContext(AuthContext)