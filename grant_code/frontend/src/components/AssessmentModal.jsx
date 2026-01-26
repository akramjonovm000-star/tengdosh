import React, { useState, useEffect } from 'react';
import { X, Save, TrendingUp, AlertCircle, CheckCircle2 } from 'lucide-react';
import { motion } from 'framer-motion';
import api from '../services/api';

const CRITERIA_ICONS = {
    1: "📚", 2: "📖", 3: "⚖️", 4: "🏆", 5: "⏰",
    6: "🧘", 7: "🤝", 8: "🎭", 9: "⚽", 10: "🎨", 11: "🆘"
};

export default function AssessmentModal({ student: application, onClose, onSuccess }) {
    const [scores, setScores] = useState({});
    const [saving, setSaving] = useState(false);
    const [success, setSuccess] = useState(false);

    useEffect(() => {
        if (application?.criteria) {
            const initialScores = {};
            application.criteria.forEach(c => {
                initialScores[c.criterion.id] = c.item.score || 0;
            });
            setScores(initialScores);
        }
    }, [application]);

    const totalSocial = Object.values(scores).reduce((a, b) => a + b, 0);

    const handleScoreChange = (criterionId, val, max) => {
        const numVal = Math.min(max, Math.max(0, parseFloat(val) || 0));
        setScores({ ...scores, [criterionId]: numVal });
    };

    const handleSave = async () => {
        setSaving(true);
        try {
            // Save each score
            for (const criteriaItem of application.criteria) {
                const criterionId = criteriaItem.criterion.id;
                const itemId = criteriaItem.item.id;
                const score = scores[criterionId];

                await api.post(`/applications/${application.id}/criterion/${itemId}/score/`, {
                    score: score
                });
            }

            setSuccess(true);
            setTimeout(() => {
                onSuccess?.();
            }, 1500);
        } catch (err) {
            alert("Xatolik yuz berdi: " + (err.response?.data?.detail || err.message));
        } finally {
            setSaving(false);
        }
    };

    return (
        <div style={{ position: 'fixed', inset: 0, zIndex: 1000, display: 'flex', alignItems: 'center', justifyContent: 'center', backgroundColor: 'rgba(0,0,0,0.8)', backdropFilter: 'blur(8px)' }}>
            <motion.div
                initial={{ scale: 0.9, opacity: 0 }}
                animate={{ scale: 1, opacity: 1 }}
                className="glass-card"
                style={{ width: '100%', maxWidth: '900px', maxHeight: '90vh', overflowY: 'auto', padding: '40px' }}
            >
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '30px' }}>
                    <div>
                        <h2 style={{ fontSize: '1.75rem', fontWeight: 700 }}>Baholash: {application.student?.full_name}</h2>
                        <p style={{ color: 'var(--text-secondary)' }}>Fakultet: {application.student?.faculty} | Guruhi: {application.student?.group}</p>
                    </div>
                    <button onClick={onClose} className="btn btn-glass" style={{ padding: '8px', borderRadius: '50%' }}>
                        <X size={24} />
                    </button>
                </div>

                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px', marginBottom: '30px' }}>
                    {application.criteria?.map((criteriaItem) => {
                        const c = criteriaItem.criterion;
                        return (
                            <div key={c.id} className="glass-card" style={{ padding: '16px', background: 'rgba(255,255,255,0.03)' }}>
                                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px' }}>
                                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px', flex: 1 }}>
                                        <span style={{ fontSize: '1.25rem' }}>{CRITERIA_ICONS[c.id] || "📋"}</span>
                                        <span style={{ fontSize: '0.8125rem', fontWeight: 500, lineHeight: 1.2 }}>{c.name}</span>
                                    </div>
                                    <span style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', marginLeft: '10px' }}>Maks: {c.max_score}</span>
                                </div>
                                <input
                                    type="number"
                                    value={scores[c.id] ?? 0}
                                    onChange={(e) => handleScoreChange(c.id, e.target.value, c.max_score)}
                                    style={{
                                        width: '100%',
                                        background: 'rgba(255,255,255,0.05)',
                                        border: '1px solid var(--surface-border)',
                                        borderRadius: '8px',
                                        padding: '10px',
                                        color: 'white',
                                        fontSize: '1rem',
                                        fontWeight: 600,
                                        outline: 'none'
                                    }}
                                />
                            </div>
                        );
                    })}
                </div>

                <div style={{ padding: '24px', background: 'rgba(79, 70, 229, 0.1)', borderRadius: 'var(--radius-md)', border: '1px solid var(--primary-glow)', marginBottom: '30px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                        <TrendingUp size={32} color="var(--primary)" />
                        <div>
                            <p style={{ fontSize: '0.875rem', color: 'var(--text-secondary)' }}>YAKUNIY IJTIMOIY BALL</p>
                            <h3 style={{ fontSize: '1.5rem', fontWeight: 700, color: 'var(--primary)' }}>{totalSocial} / 100</h3>
                        </div>
                    </div>
                    <div style={{ textAlign: 'right' }}>
                        <p style={{ fontSize: '0.875rem', color: 'var(--text-secondary)' }}>AKADEMIK BALL</p>
                        <h3 style={{ fontSize: '1.25rem', fontWeight: 600 }}>{application.student?.education_score}</h3>
                    </div>
                </div>

                <div style={{ display: 'flex', gap: '12px' }}>
                    <button
                        onClick={handleSave}
                        disabled={saving || success}
                        className="btn btn-primary"
                        style={{ flex: 1, height: '54px' }}
                    >
                        {success ? <CheckCircle2 size={24} /> : saving ? 'Saqlanmoqda...' : 'Tasdiqlash va Saqlash'}
                        {!saving && !success && <Save size={20} />}
                    </button>
                    <button onClick={onClose} className="btn btn-glass" style={{ flex: 1 }}>
                        Bekor qilish
                    </button>
                </div>
            </motion.div>
        </div>
    );
}
