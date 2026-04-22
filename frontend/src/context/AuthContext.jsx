/**
 * Authentication context for managing user state across the application.
 * Provides login, logout, token management, and 2FA support.
 */

import { createContext, useContext, useState, useEffect, useCallback } from 'react';
import { authAPI, profileAPI } from '../api';

const AuthContext = createContext(null);

// Role labels in Arabic
const ROLE_LABELS = {
  admin: 'مدير النظام',
  warehouse: 'موظف المخازن',
  sales: 'موظف المبيعات',
  accountant: 'المحاسب',
  hr: 'موظف الموارد البشرية',
  purchasing: 'موظف المشتريات',
  project_manager: 'مدير المشاريع',
};

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [permissions, setPermissions] = useState([]);
  const [pending2FA, setPending2FA] = useState(false);
  const [pending2FAData, setPending2FAData] = useState(null);

  // Check for existing token on mount and fetch user profile
  useEffect(() => {
    const token = localStorage.getItem('access_token');
    if (token) {
      fetchProfile();
    } else {
      setLoading(false);
    }
  }, []);

  const fetchProfile = async () => {
    try {
      const response = await profileAPI.getProfile();
      const userData = {
        ...response.data,
        role_display: ROLE_LABELS[response.data.role] || response.data.role,
      };
      setUser(userData);
      setIsAuthenticated(true);
      setPermissions(response.data.permissions || []);
    } catch (error) {
      // Token might be expired or invalid
      localStorage.removeItem('access_token');
      localStorage.removeItem('refresh_token');
      setUser(null);
      setIsAuthenticated(false);
    } finally {
      setLoading(false);
    }
  };

  const login = async (username, password) => {
    const response = await authAPI.login({ username, password });
    const data = response.data;

    // Check if 2FA is required
    if (data.requires_2fa) {
      setPending2FA(true);
      setPending2FAData({
        username,
        temp_token: data.temp_token,
      });
      return { requires_2fa: true };
    }

    // Normal login - store tokens
    const { access, refresh, user: userData } = data;
    localStorage.setItem('access_token', access);
    localStorage.setItem('refresh_token', refresh);

    const userWithRole = {
      ...userData,
      role_display: ROLE_LABELS[userData.role] || userData.role,
    };

    setUser(userWithRole);
    setIsAuthenticated(true);
    setPending2FA(false);
    setPending2FAData(null);

    return userWithRole;
  };

  const verify2FA = async (code) => {
    if (!pending2FAData) {
      throw new Error('لا يوجد طلب مصادقة ثنائية معلق');
    }

    const response = await authAPI.login2FA({
      username: pending2FAData.username,
      code,
      temp_token: pending2FAData.temp_token,
    });

    const { access, refresh, user: userData } = response.data;
    localStorage.setItem('access_token', access);
    localStorage.setItem('refresh_token', refresh);

    const userWithRole = {
      ...userData,
      role_display: ROLE_LABELS[userData.role] || userData.role,
    };

    setUser(userWithRole);
    setIsAuthenticated(true);
    setPending2FA(false);
    setPending2FAData(null);

    return userWithRole;
  };

  const cancel2FA = () => {
    setPending2FA(false);
    setPending2FAData(null);
  };

  const logout = useCallback(() => {
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    setUser(null);
    setIsAuthenticated(false);
    setPermissions([]);
    setPending2FA(false);
    setPending2FAData(null);
  }, []);

  const updateProfile = async (data) => {
    const response = await profileAPI.updateProfile(data);
    const userData = {
      ...response.data.user,
      role_display: ROLE_LABELS[response.data.user.role] || response.data.user.role,
    };
    setUser(userData);
    return userData;
  };

  const changePassword = async (data) => {
    await profileAPI.changePassword(data);
  };

  const hasPermission = useCallback((code) => {
    if (!user) return false;
    if (user.role === 'admin') return true;
    return permissions.includes(code);
  }, [user, permissions]);

  const value = {
    user,
    loading,
    isAuthenticated,
    login,
    logout,
    updateProfile,
    changePassword,
    verify2FA,
    cancel2FA,
    pending2FA,
    pending2FAData,
    hasPermission,
    permissions,
    isAdmin: user?.role === 'admin',
    isWarehouse: user?.role === 'admin' || user?.role === 'warehouse',
    isSales: user?.role === 'admin' || user?.role === 'sales',
    isAccountant: user?.role === 'admin' || user?.role === 'accountant',
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}

export default AuthContext;
