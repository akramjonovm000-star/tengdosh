import React, { useState } from 'react';
import { Lock, User, GraduationCap, ArrowRight } from 'lucide-react';
import { motion } from 'framer-motion';
import axios from 'axios';

export default function Login({ onLogin }) {
    const [username, setUsername] = useState('');
    const [password, setPassword] = useState('');
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState('');

    const handleSubmit = async (e) => {
        e.preventDefault();
        setLoading(true);
        setError('');
        try {
            const response = await axios.post('/grant/api/v1/user/login/', {
                username,
                password
            });
            const data = response.data;
            if (data.access) {
                localStorage.setItem('grant_token', data.access);
                onLogin(data.user || { username });
            }
        } catch (err) {
            setError('Login yoki parol xato!');
        } finally {
            setLoading(false);
        }
    };

    return (
        <div style={{ minHeight: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center', background: 'radial-gradient(circle at top right, #1e1b4b, #0f172a)' }}>
            <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                className="glass-card"
                style={{ width: '100%', maxWidth: '400px', padding: '40px' }}
            >
                <div style={{ textAlign: 'center', marginBottom: '40px' }}>
                    <div style={{
                        display: 'inline-flex',
                        background: 'var(--primary)',
                        padding: '16px',
                        borderRadius: '20px',
                        marginBottom: '20px',
                        boxShadow: '0 0 30px var(--primary-glow)'
                    }}>
                        <GraduationCap size={40} color="white" />
                    </div>
                    <h1 style={{ fontSize: '2rem', fontWeight: 700, marginBottom: '8px' }}>GrantPortal</h1>
                    <p style={{ color: 'var(--text-secondary)' }}>Tizimga kirish</p>
                </div>

                <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
                    <div style={{ position: 'relative' }}>
                        <User size={18} style={{ position: 'absolute', left: '16px', top: '50%', transform: 'translateY(-50%)', color: 'var(--text-secondary)' }} />
                        <input
                            type="text"
                            placeholder="Username"
                            required
                            value={username}
                            onChange={(e) => setUsername(e.target.value)}
                            style={{
                                width: '100%',
                                padding: '14px 16px 14px 48px',
                                background: 'rgba(255,255,255,0.05)',
                                border: '1px solid var(--surface-border)',
                                borderRadius: '12px',
                                color: 'white',
                                outline: 'none'
                            }}
                        />
                    </div>

                    <div style={{ position: 'relative' }}>
                        <Lock size={18} style={{ position: 'absolute', left: '16px', top: '50%', transform: 'translateY(-50%)', color: 'var(--text-secondary)' }} />
                        <input
                            type="password"
                            placeholder="Password"
                            required
                            value={password}
                            onChange={(e) => setPassword(e.target.value)}
                            style={{
                                width: '100%',
                                padding: '14px 16px 14px 48px',
                                background: 'rgba(255,255,255,0.05)',
                                border: '1px solid var(--surface-border)',
                                borderRadius: '12px',
                                color: 'white',
                                outline: 'none'
                            }}
                        />
                    </div>

                    {error && (
                        <div style={{ color: 'var(--error)', fontSize: '0.875rem', textAlign: 'center', background: 'rgba(239, 68, 68, 0.1)', padding: '10px', borderRadius: '8px' }}>
                            {error}
                        </div>
                    )}

                    <button
                        type="submit"
                        disabled={loading}
                        className="btn btn-primary"
                        style={{ width: '100%', height: '54px', fontSize: '1rem' }}
                    >
                        {loading ? 'Kirilmoqda...' : 'Kirish'}
                        {!loading && <ArrowRight size={20} />}
                    </button>
                </form>

                <p style={{ textAlign: 'center', marginTop: '30px', color: 'var(--text-secondary)', fontSize: '0.875rem' }}>
                    Ma'muriyat uchun maxsus kirish
                </p>
            </motion.div>
        </div>
    );
}
