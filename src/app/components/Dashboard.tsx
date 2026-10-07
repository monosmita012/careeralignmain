import { useState, useEffect } from 'react';
import { Routes, Route, useNavigate, useLocation } from 'react-router-dom';
import { Home, BookOpen, FileText, User, LogOut, Moon, Sun, GraduationCap, Briefcase } from 'lucide-react';
import { Button } from './ui/button';
import { useUser } from '../context/UserContext';
import { useTheme } from '../context/ThemeContext';
import HomePage from './dashboard/HomePage';
import SyllabusPage from './dashboard/SyllabusPage';
import ResumePage from './dashboard/ResumePage';
import ProfilePage from './dashboard/ProfilePage';
import StudentPage from './dashboard/StudentPage';
import JobSeekerPage from './dashboard/JobSeekerPage';

export default function Dashboard() {
  const navigate = useNavigate();
  const location = useLocation();
  const { userData, logout } = useUser();
  const { theme, toggleTheme } = useTheme();
  const [activeView, setActiveView] = useState<'student' | 'job-seeker'>(userData.userType || 'student');

  useEffect(() => {
    if (!userData.isAuthenticated) {
      navigate('/');
    }
  }, [userData.isAuthenticated, navigate]);

  useEffect(() => {
    if (userData.userType) {
      setActiveView(userData.userType);
    }
  }, [userData.userType]);

  const handleLogout = () => {
    logout();
    navigate('/');
  };

  const navItems = [
    { name: 'Home', icon: Home, path: '/dashboard' },
    { name: 'Syllabus', icon: BookOpen, path: '/dashboard/syllabus' },
    { name: 'Resume', icon: FileText, path: '/dashboard/resume' },
  ];

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900 transition-colors duration-300">
      {/* Top Bar */}
      <div className="bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700 shadow-sm transition-colors duration-300">
        <div className="px-4 sm:px-6 py-3 sm:py-4 flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
          <h1 className="text-xl sm:text-2xl font-bold text-gray-900 dark:text-white">CareerAlign</h1>
          <div className="flex flex-wrap items-center justify-between gap-3 sm:justify-end">
            {/* View Toggle */}
            <div className="flex items-center gap-2 bg-gray-100 dark:bg-gray-700 p-1 rounded-lg">
              <Button
                variant={activeView === 'student' ? 'default' : 'ghost'}
                size="sm"
                onClick={() => {
                  setActiveView('student');
                  navigate('/dashboard/student');
                }}
                className={`transition-all ${
                  activeView === 'student'
                    ? 'bg-purple-600 hover:bg-purple-700 text-white shadow-md'
                    : 'hover:bg-gray-200 dark:hover:bg-gray-600'
                }`}
              >
                <GraduationCap className="w-4 h-4 mr-2" />
                Student
              </Button>
              <Button
                variant={activeView === 'job-seeker' ? 'default' : 'ghost'}
                size="sm"
                onClick={() => {
                  setActiveView('job-seeker');
                  navigate('/dashboard/job-seeker');
                }}
                className={`transition-all ${
                  activeView === 'job-seeker'
                    ? 'bg-green-600 hover:bg-green-700 text-white shadow-md'
                    : 'hover:bg-gray-200 dark:hover:bg-gray-600'
                }`}
              >
                <Briefcase className="w-4 h-4 mr-2" />
                Job Seeker
              </Button>
            </div>
            <Button
              variant="ghost"
              size="icon"
              onClick={toggleTheme}
              className="hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors"
            >
              {theme === 'light' ? <Moon className="w-5 h-5" /> : <Sun className="w-5 h-5" />}
            </Button>
          </div>
        </div>
      </div>

      <div className="flex flex-col lg:flex-row">
        {/* Sidebar */}
        <div className="w-full lg:w-64 lg:shrink-0 bg-white dark:bg-gray-800 lg:min-h-[calc(100vh-73px)] border-b lg:border-b-0 lg:border-r border-gray-200 dark:border-gray-700 flex flex-col transition-colors duration-300">
          <nav className="flex flex-wrap gap-2 p-3 lg:flex-1 lg:flex-col lg:p-4 lg:space-y-2">
            {navItems.map((item) => {
              const isActive = location.pathname === item.path;
              return (
                <Button
                  key={item.path}
                  variant={isActive ? 'default' : 'ghost'}
                  className={`w-auto lg:w-full justify-start transition-all ${
                    isActive
                      ? 'bg-blue-600 hover:bg-blue-700 text-white shadow-md'
                      : 'hover:bg-gray-100 dark:hover:bg-gray-700 text-gray-700 dark:text-gray-300'
                  }`}
                  onClick={() => navigate(item.path)}
                >
                  <item.icon className="w-5 h-5 mr-3" />
                  {item.name}
                </Button>
              );
            })}
          </nav>

          {/* Profile Section */}
          <div className="flex flex-wrap gap-2 p-3 border-t border-gray-200 dark:border-gray-700 lg:flex-col lg:p-4">
            <Button
              variant="ghost"
              className="w-auto min-w-[9rem] flex-1 lg:w-full lg:flex-none justify-start hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors"
              onClick={() => navigate('/dashboard/profile')}
            >
              <div className="w-10 h-10 rounded-full bg-gradient-to-br from-purple-500 to-pink-500 flex items-center justify-center mr-3 flex-shrink-0">
                {userData.profile.profilePicture ? (
                  <img
                    src={userData.profile.profilePicture}
                    alt="Profile"
                    className="w-full h-full rounded-full object-cover"
                  />
                ) : (
                  <User className="w-5 h-5 text-white" />
                )}
              </div>
              <div className="flex-1 text-left overflow-hidden">
                <p className="font-semibold text-sm text-gray-900 dark:text-white truncate">
                  {userData.profile.name || 'User'}
                </p>
                <p className="text-xs text-gray-500 dark:text-gray-400 truncate">View Profile</p>
              </div>
            </Button>
            <Button
              variant="ghost"
              className="w-auto lg:w-full justify-start text-red-600 dark:text-red-400 hover:bg-red-50 dark:hover:bg-red-900/20 transition-colors"
              onClick={handleLogout}
            >
              <LogOut className="w-5 h-5 mr-3" />
              Logout
            </Button>
          </div>
        </div>

        {/* Main Content */}
        <div className="flex-1 min-w-0 p-4 sm:p-6 lg:p-8 overflow-auto">
          <Routes>
            <Route path="/" element={<HomePage />} />
            <Route path="/syllabus" element={<SyllabusPage />} />
            <Route path="/resume" element={<ResumePage />} />
            <Route path="/profile" element={<ProfilePage />} />
            <Route path="/student/*" element={<StudentPage />} />
            <Route path="/job-seeker/*" element={<JobSeekerPage />} />
          </Routes>
        </div>
      </div>
    </div>
  );
}
