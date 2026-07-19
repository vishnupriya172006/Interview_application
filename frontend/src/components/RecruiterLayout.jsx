import React, { useState } from 'react';
import { useNavigate, useLocation, Link } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { 
  LayoutDashboard, 
  CalendarPlus, 
  FileSpreadsheet, 
  LogOut, 
  ShieldAlert, 
  Menu, 
  X, 
  Activity,
  User as UserIcon
} from 'lucide-react';

const RecruiterLayout = ({ children }) => {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const [mobileOpen, setMobileOpen] = useState(false);

  const menuItems = [
    { name: 'Dashboard', path: '/dashboard', icon: LayoutDashboard },
    { name: 'Schedule Interview', path: '/schedule', icon: CalendarPlus },
    { name: 'Integrity Reports', path: '/reports', icon: FileSpreadsheet },
  ];

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  return (
    <div className="flex h-screen w-screen overflow-hidden bg-dark-950 bg-grid text-dark-50">
      {/* Sidebar for Desktop */}
      <aside className="hidden w-64 border-r border-dark-800 bg-dark-900/60 backdrop-blur-md md:flex md:flex-col justify-between">
        <div>
          {/* Logo Header */}
          <div className="flex h-16 items-center gap-3 px-6 border-b border-dark-800">
            <ShieldAlert className="h-7 w-7 text-brand-500" />
            <span className="text-lg font-bold tracking-tight bg-gradient-to-r from-brand-400 to-indigo-600 bg-clip-text text-transparent">
              InterviewGuard AI
            </span>
          </div>

          {/* Navigation links */}
          <nav className="space-y-1 px-4 py-6">
            {menuItems.map((item) => {
              const isActive = location.pathname === item.path;
              const Icon = item.icon;
              return (
                <Link
                  key={item.name}
                  to={item.path}
                  className={`flex items-center gap-3 px-4 py-3 rounded-lg text-sm font-medium transition-all duration-200 ${
                    isActive 
                      ? 'bg-brand-600/15 text-brand-400 border border-brand-500/20' 
                      : 'text-dark-300 hover:bg-dark-800 hover:text-dark-50'
                  }`}
                >
                  <Icon className="h-5 w-5" />
                  {item.name}
                </Link>
              );
            })}
          </nav>
        </div>

        {/* Profile and Logout info at the bottom */}
        <div className="border-t border-dark-800 p-4 space-y-3">
          <div className="flex items-center gap-3 px-2">
            <div className="flex h-10 w-10 items-center justify-center rounded-full bg-brand-600/10 text-brand-400 border border-brand-500/20">
              <UserIcon className="h-5 w-5" />
            </div>
            <div className="overflow-hidden">
              <p className="text-sm font-semibold truncate">{user?.full_name}</p>
              <p className="text-xs text-dark-300 truncate">{user?.company_name || 'Recruiter'}</p>
            </div>
          </div>
          <button
            onClick={handleLogout}
            className="flex w-full items-center gap-3 px-4 py-3 rounded-lg text-sm font-medium text-rose-400 hover:bg-rose-500/10 transition-colors"
          >
            <LogOut className="h-5 w-5" />
            Sign Out
          </button>
        </div>
      </aside>

      {/* Mobile Drawer */}
      {mobileOpen && (
        <div className="fixed inset-0 z-50 flex md:hidden bg-dark-950/80 backdrop-blur-sm">
          <aside className="w-64 bg-dark-900 border-r border-dark-800 flex flex-col justify-between p-6">
            <div>
              <div className="flex items-center justify-between mb-8">
                <span className="text-lg font-bold tracking-tight text-brand-500">InterviewGuard AI</span>
                <button onClick={() => setMobileOpen(false)}>
                  <X className="h-6 w-6 text-dark-300" />
                </button>
              </div>
              <nav className="space-y-2">
                {menuItems.map((item) => {
                  const isActive = location.pathname === item.path;
                  const Icon = item.icon;
                  return (
                    <Link
                      key={item.name}
                      to={item.path}
                      onClick={() => setMobileOpen(false)}
                      className={`flex items-center gap-3 px-4 py-3 rounded-lg text-sm font-medium transition-all ${
                        isActive 
                          ? 'bg-brand-600/20 text-brand-400' 
                          : 'text-dark-300 hover:bg-dark-800'
                      }`}
                    >
                      <Icon className="h-5 w-5" />
                      {item.name}
                    </Link>
                  );
                })}
              </nav>
            </div>
            <div className="border-t border-dark-800 pt-4 space-y-4">
              <div className="flex items-center gap-3">
                <div className="flex h-10 w-10 items-center justify-center rounded-full bg-brand-600/20 text-brand-400">
                  <UserIcon className="h-5 w-5" />
                </div>
                <div>
                  <p className="text-sm font-semibold truncate">{user?.full_name}</p>
                  <p className="text-xs text-dark-300 truncate">{user?.company_name}</p>
                </div>
              </div>
              <button
                onClick={handleLogout}
                className="flex w-full items-center gap-3 px-4 py-3 rounded-lg text-sm font-medium text-rose-400 hover:bg-rose-500/10 transition-colors"
              >
                <LogOut className="h-5 w-5" />
                Sign Out
              </button>
            </div>
          </aside>
        </div>
      )}

      {/* Main Content Area */}
      <div className="flex flex-1 flex-col overflow-hidden">
        {/* Top Navbar */}
        <header className="flex h-16 items-center justify-between border-b border-dark-800 bg-dark-900/40 px-6 backdrop-blur-md">
          <div className="flex items-center gap-4">
            <button 
              className="block md:hidden text-dark-300 hover:text-dark-50" 
              onClick={() => setMobileOpen(true)}
            >
              <Menu className="h-6 w-6" />
            </button>
            <h1 className="text-base font-semibold text-dark-100 hidden md:block">
              Welcome back, {user?.full_name}
            </h1>
          </div>
          
          <div className="flex items-center gap-3">
            {/* Live Feed Status */}
            <span className="flex items-center gap-2 px-3 py-1.5 rounded-full bg-emerald-500/10 border border-emerald-500/20 text-xs font-semibold text-emerald-400 animate-pulse">
              <Activity className="h-3.5 w-3.5" />
              AI Core Online
            </span>
          </div>
        </header>

        {/* Content Injector */}
        <main className="flex-1 overflow-y-auto p-6 md:p-8">
          {children}
        </main>
      </div>
    </div>
  );
};

export default RecruiterLayout;
