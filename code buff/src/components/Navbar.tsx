import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';

export default function Navbar() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  return (
    <nav className="border-b border-slate-800 bg-slate-900/50">
      <div className="mx-auto max-w-6xl flex items-center justify-between px-4 py-3">
        <Link to="/" className="text-lg font-bold text-white hover:text-blue-400 transition-colors">
          PuterImage Studio
        </Link>
        <div className="flex items-center gap-4">
          {user ? (
            <>
              <Link
                to="/settings"
                className="text-sm text-slate-400 hover:text-white transition-colors"
              >
                <span className="hidden sm:inline">Settings</span>
                <span className="sm:hidden">⚙</span>
              </Link>
              <span className="text-sm text-slate-500 hidden sm:inline">
                {user.username}
              </span>
              <button
                onClick={handleLogout}
                className="text-sm text-slate-400 hover:text-red-400 transition-colors"
              >
                Logout
              </button>
            </>
          ) : (
            <>
              <Link
                to="/login"
                className="text-sm text-slate-400 hover:text-white transition-colors"
              >
                Sign In
              </Link>
              <Link
                to="/register"
                className="rounded-lg bg-blue-600 px-3 py-1.5 text-sm font-medium text-white hover:bg-blue-700 transition-colors"
              >
                Sign Up
              </Link>
            </>
          )}
        </div>
      </div>
    </nav>
  );
}
