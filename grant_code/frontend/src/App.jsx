import React, { useState, useEffect } from 'react';
import {
  Users,
  FileCheck,
  BarChart3,
  Settings,
  LogOut,
  Search,
  Filter,
  GraduationCap,
  Calendar,
  ChevronRight,
  TrendingUp,
  Award
} from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import AssessmentModal from './components/AssessmentModal';
import Login from './components/Login';
import api from './services/api';

// No mock data needed anymore

const Sidebar = ({ activeTab, setActiveTab, onLogout, user }) => {
  const menuItems = [
    { id: 'dashboard', icon: BarChart3, label: 'Dashboard' },
    { id: 'applications', icon: FileCheck, label: 'Arizalar' },
    { id: 'students', icon: Users, label: 'Talabalar' },
    { id: 'analytics', icon: TrendingUp, label: 'Tahlil' },
    { id: 'settings', icon: Settings, label: 'Sozlamalar' },
  ];

  return (
    <div className="sidebar glass-card" style={{ height: 'calc(100vh - 40px)', width: '280px', margin: '20px', padding: '30px', display: 'flex', flexDirection: 'column' }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '40px' }}>
        <div style={{ background: 'var(--primary)', padding: '8px', borderRadius: '12px', boxShadow: '0 0 15px var(--primary-glow)' }}>
          <GraduationCap size={24} color="white" />
        </div>
        <h2 style={{ fontSize: '1.25rem', fontWeight: 700, letterSpacing: '-0.5px' }}>GrantPortal</h2>
      </div>

      <nav style={{ flex: 1, display: 'flex', flexDirection: 'column', gap: '8px' }}>
        {menuItems.map((item) => (
          <button
            key={item.id}
            onClick={() => setActiveTab(item.id)}
            className={`btn ${activeTab === item.id ? 'btn-primary' : 'btn-glass'}`}
            style={{ justifyContent: 'flex-start', width: '100%', padding: '12px 16px' }}
          >
            <item.icon size={20} />
            <span>{item.label}</span>
          </button>
        ))}
      </nav>

      <div style={{ marginTop: 'auto', paddingTop: '20px', borderTop: '1px solid var(--surface-border)' }}>
        <p style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', marginBottom: '12px' }}>
          Kirgan: <b>{user?.username}</b>
        </p>
        <button onClick={onLogout} className="btn btn-glass" style={{ width: '100%', justifyContent: 'flex-start', color: 'var(--error)' }}>
          <LogOut size={20} />
          <span>Chiqish</span>
        </button>
      </div>
    </div>
  );
};

const Dashboard = ({ onAssess }) => {
  const [applications, setApplications] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchApps = async () => {
      try {
        const res = await api.get('/applications/');
        setApplications(res.data.results || []);
      } catch (err) {
        console.error("Fetch error", err);
      } finally {
        setLoading(false);
      }
    };
    fetchApps();
  }, []);

  return (
    <div className="animate-in" style={{ flex: 1, padding: '20px 40px 40px 0', overflowY: 'auto' }}>
      <header style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '40px' }}>
        <div>
          <h1 style={{ fontSize: '2.5rem', fontWeight: 700, marginBottom: '8px' }}>Hush kelibsiz!</h1>
          <p style={{ color: 'var(--text-secondary)' }}>Grantlarni qayta taqsimlash platformasi statistikasi</p>
        </div>
        <div className="glass-card" style={{ padding: '8px 20px', display: 'flex', alignItems: 'center', gap: '12px' }}>
          <Calendar size={18} color="var(--primary)" />
          <span style={{ fontWeight: 500 }}>{new Date().toLocaleDateString('uz-UZ', { day: 'numeric', month: 'long', year: 'numeric' })}</span>
        </div>
      </header>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '24px', marginBottom: '40px' }}>
        {[
          { label: "Jami Arizalar", value: applications.length, icon: FileCheck, color: "var(--primary)" },
          { label: "Tasdiqlangan", value: applications.filter(a => a.is_approved).length, icon:Award, color: "var(--success)" },
          { label: "Reviziyada", value: applications.filter(a => a.is_revised).length, icon: Users, color: "var(--warning)" },
          { label: "O'rtacha GPA", value: "4.2", icon: BarChart3, color: "var(--secondary)" },
        ].map((stat, i) => (
          <div key={i} className="glass-card" style={{ padding: '24px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '16px' }}>
              <div style={{ background: `${stat.color}20`, padding: '12px', borderRadius: '12px' }}>
                <stat.icon size={24} color={stat.color} />
              </div>
            </div>
            <h3 style={{ fontSize: '1.75rem', fontWeight: 700, marginBottom: '4px' }}>{stat.value}</h3>
            <p style={{ color: 'var(--text-secondary)', fontSize: '0.875rem' }}>{stat.label}</p>
          </div>
        ))}
      </div>

      <div className="glass-card" style={{ padding: '30px' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '24px' }}>
          <h2 style={{ fontSize: '1.25rem', fontWeight: 600 }}>So'nggi arizalar</h2>
          <button className="btn btn-glass" style={{ fontSize: '0.875rem' }}>Barchasini ko'rish</button>
        </div>

        <div style={{ overflowX: 'auto' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse' }}>
            <thead>
              <tr style={{ textAlign: 'left', color: 'var(--text-secondary)', borderBottom: '1px solid var(--surface-border)' }}>
                <th style={{ padding: '16px' }}>Talaba</th>
                <th style={{ padding: '16px' }}>Guruhi</th>
                <th style={{ padding: '16px' }}>Fakultet</th>
                <th style={{ padding: '16px' }}>Turi</th>
                <th style={{ padding: '16px' }}>Holat</th>
                <th style={{ padding: '16px' }}>Harakat</th>
              </tr>
            </thead>
            <tbody>
              {loading ? (
                <tr><td colSpan="6" style={{ padding: '40px', textAlign: 'center' }}>Yuklanmoqda...</td></tr>
              ) : applications.map((app) => (
                <tr key={app.id} style={{ borderBottom: '1px solid var(--surface-border)', transition: 'var(--transition)' }}>
                  <td style={{ padding: '16px', fontWeight: 500 }}>{app.student?.full_name}</td>
                  <td style={{ padding: '16px' }}>{app.student?.group}</td>
                  <td style={{ padding: '16px' }}>{app.student?.faculty}</td>
                  <td style={{ padding: '16px' }}>{app.type === 'standard' ? 'Oddiy' : 'Imtiyozli'}</td>
                  <td style={{ padding: '16px' }}>
                    <span className={`badge badge-${app.is_approved ? 'success' : app.is_rejected ? 'error' : 'warning'}`}>
                      {app.is_approved ? 'Tasdiqlangan' : app.is_rejected ? 'Rad etilgan' : "Ko'rib chiqilmoqda"}
                    </span>
                  </td>
                  <td style={{ padding: '16px' }}>
                    <button 
                      onClick={() => onAssess(app)}
                      className="btn btn-primary" 
                      style={{ padding: '8px 16px', fontSize: '0.8125rem' }} 
                      title="Baholash"
                    >
                      <span>Baholash</span>
                      <ChevronRight size={14} />
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};

export default function App() {
  const [activeTab, setActiveTab] = useState('dashboard');
  const [selectedStudent, setSelectedStudent] = useState(null);

  return (
    <div style={{ display: 'flex', minHeight: '100vh', background: 'radial-gradient(circle at 0% 0%, #1e1b4b 0%, #0f172a 100%)' }}>
      <Sidebar activeTab={activeTab} setActiveTab={setActiveTab} />
      <Dashboard onAssess={(s) => setSelectedStudent(s)} />

      <AnimatePresence>
        {selectedStudent && (
          <AssessmentModal
            student={selectedStudent}
            onClose={() => setSelectedStudent(null)}
          />
        )}
      </AnimatePresence>
    </div>
  );
}
