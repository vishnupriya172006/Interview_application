import React, { createContext, useContext, useState, useEffect } from 'react';
import axios from 'axios';

const AuthContext = createContext(null);

export const API_URL = import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000/api';

// Pre-configure axios default headers
export const api = axios.create({
  baseURL: API_URL,
});

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [token, setToken] = useState(localStorage.getItem('token') || '');
  const [loading, setLoading] = useState(true);

  // Apply token to axios headers whenever it changes
  useEffect(() => {
    if (token) {
      localStorage.setItem('token', token);
      api.defaults.headers.common['Authorization'] = `Bearer ${token}`;
    } else {
      localStorage.removeItem('token');
      delete api.defaults.headers.common['Authorization'];
    }
  }, [token]);

  // Load user details on startup if token exists
  useEffect(() => {
    const fetchCurrentUser = async () => {
      if (!token) {
        setLoading(false);
        return;
      }
      try {
        // Query recruiter interviews to verify token validity, or fetch details if we add a /me route.
        // For simplicity, we decode JWT subject or retrieve user detail from login payload.
        // If token exists, we load user from localStorage if cached, or clear if expired.
        const cachedUser = localStorage.getItem('user');
        if (cachedUser) {
          setUser(JSON.parse(cachedUser));
        } else {
          // If no cached user detail but token exists, reset
          logout();
        }
      } catch (err) {
        console.error('Failed to validate session token:', err);
        logout();
      } finally {
        setLoading(false);
      }
    };
    fetchCurrentUser();
  }, [token]);

  const extractApiError = (error) => {
    const responseData = error.response?.data;
    if (responseData) {
      if (typeof responseData.detail === 'string') {
        return responseData.detail;
      }
      if (Array.isArray(responseData.detail)) {
        return responseData.detail.map((item) => item.msg || item.detail || JSON.stringify(item)).join(' ');
      }
      if (typeof responseData === 'string') {
        return responseData;
      }
      return JSON.stringify(responseData);
    }
    if (error.response) {
      return error.response.data?.detail || JSON.stringify(error.response.data);
    }
    if (error.request) {
      return 'Network error: unable to reach the backend API. Check that the backend is running and that CORS is configured correctly.';
    }
    return error.message || 'Unknown error occurred.';
  };

  const login = async (email, password) => {
    try {
      const response = await api.post('/auth/login', { email, password });
      const { access_token, user: userData } = response.data;
      
      setUser(userData);
      setToken(access_token);
      localStorage.setItem('user', JSON.stringify(userData));
      return { success: true };
    } catch (error) {
      return { success: false, error: extractApiError(error) || 'Incorrect email or password.' };
    }
  };

  const signup = async (email, password, fullName, companyName) => {
    try {
      await api.post('/auth/register', {
        email,
        password,
        full_name: fullName,
        company_name: companyName || null
      });
      // Automatically log in after registration
      return await login(email, password);
    } catch (error) {
      return { success: false, error: extractApiError(error) || 'Failed to register account.' };
    }
  };

  const logout = () => {
    setUser(null);
    setToken('');
    localStorage.removeItem('user');
    localStorage.removeItem('token');
  };

  const forgotPassword = async (email) => {
    try {
      await api.post('/auth/forgot-password', { email });
      return { success: true };
    } catch (error) {
      return { success: false, error: error.response?.data?.detail || 'Failed to request reset.' };
    }
  };

  const resetPassword = async (tokenParam, newPassword) => {
    try {
      await api.post('/auth/reset-password', { token: tokenParam, new_password: newPassword });
      return { success: true };
    } catch (error) {
      return { success: false, error: error.response?.data?.detail || 'Failed to update password.' };
    }
  };

  const value = {
    user,
    token,
    loading,
    login,
    signup,
    logout,
    forgotPassword,
    resetPassword
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};
