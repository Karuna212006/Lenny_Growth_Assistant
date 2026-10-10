import React, { useState } from 'react';
import { BookOpen, ChevronDown, ChevronUp, Quote, Sparkles } from 'lucide-react';

export default function Citations({ citations }) {
  const [expandedIndex, setExpandedIndex] = useState(null);

  if (!citations || citations.length === 0) return null;

  return (
    <div className="citations-wrapper">
      <div className="citations-header">
        <div className="citations-header-title">
          <BookOpen size={13} className="citations-icon" />
          <span>Grounded Sources</span>
          <span className="citations-count-pill">{citations.length}</span>
        </div>
        <span className="citations-hint">Click source to view transcript excerpt</span>
      </div>

      <div className="citations-grid">
        {citations.map((c, idx) => {
          const isExpanded = expandedIndex === idx;
          const rawScore = typeof c.score === 'number' ? c.score : 0.85;
          const scorePercent = (rawScore * 100).toFixed(0) + '%';

          return (
            <div key={idx} className="citation-item-container">
              <button
                type="button"
                className={`citation-chip ${isExpanded ? 'expanded' : ''}`}
                onClick={() => setExpandedIndex(isExpanded ? null : idx)}
                title={c.title || 'Transcript source'}
              >
                <span className="citation-guest">
                  {c.guest || 'Lenny Archive'}
                </span>
                <span className="citation-score">
                  <Sparkles size={10} className="score-sparkle" />
                  {scorePercent}
                </span>
                {isExpanded ? (
                  <ChevronUp size={12} className="chevron-icon" />
                ) : (
                  <ChevronDown size={12} className="chevron-icon" />
                )}
              </button>

              {isExpanded && (
                <div className="citation-drawer animate-in fade-in zoom-in-95 duration-200">
                  <div className="citation-drawer-title">
                    {c.title}
                  </div>
                  {c.guest && (
                    <div className="citation-drawer-meta">
                      Guest: <strong>{c.guest}</strong>
                    </div>
                  )}
                  {c.text && (
                    <div className="citation-drawer-quote">
                      <Quote size={12} className="quote-icon" />
                      <p>"{c.text}"</p>
                    </div>
                  )}
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
