import React from 'react';
import { CheckCircle2 } from 'lucide-react';

export function Toast({ message }) {
  if (!message) return null;

  return (
    <div style={{
      position: 'fixed',
      bottom: '24px',
      right: '24px',
      zIndex: 1000,
      backgroundColor: 'var(--bg-drawer)',
      border: '1px solid var(--gold-primary)',
      color: 'var(--text-primary)',
      padding: '0.65rem 1rem',
      borderRadius: '6px',
      boxShadow: 'var(--shadow-gold)',
      display: 'flex',
      alignItems: 'center',
      gap: '0.5rem',
      fontSize: '0.8rem',
      fontFamily: 'var(--font-mono)',
      animation: 'slideUp 0.25s ease'
    }}>
      <CheckCircle2 size={16} style={{ color: 'var(--gold-primary)' }} />
      <span>{message}</span>
    </div>
  );
}
