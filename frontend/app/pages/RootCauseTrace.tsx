import React, { useState, useEffect } from 'react';
import { motion } from 'motion/react';
import { ConceptLensButton } from '../components/ConceptLensButton';
import { WaterfallChart } from '../components/WaterfallChart';
import { ArrowLeft, ChevronDown, Info, Loader2 } from 'lucide-react';
import { dashboardService } from '../services/dashboardService';
import { computeService } from '../services/computeService';
import { PH } from '../constants/placeholders';
import type { TraceConcept } from '../App';
import type { TraceResponse, InterventionItem, WaterfallStep } from '../services/types';

interface RootCauseTraceProps {
  concept: TraceConcept;
  examId: string;
  onBack: () => void;
}

function traceWaterfallToChart(steps: WaterfallStep[]): Array<{ label: string; value: number; type: 'positive' | 'negative' | 'total' }> {
  return steps.map((s, i) => ({
    label: s.label,
    value: s.value,
    type: i === steps.length - 1 ? 'total' : s.value >= 0 ? 'positive' : 'negative',
  }));
}

export const RootCauseTrace: React.FC<RootCauseTraceProps> = ({ concept, examId, onBack }) => {
  const [showExplanation, setShowExplanation] = useState(false);
  const [trace, setTrace] = useState<TraceResponse | null>(null);
  const [interventions, setInterventions] = useState<InterventionItem[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setLoading(true);
    Promise.all([
      dashboardService.getTrace(examId, concept.id),
      computeService.getInterventions(examId),
    ])
      .then(([t, iv]) => {
        setTrace(t);
        setInterventions(iv.interventions.filter(i => i.concept_id === concept.id));
      })
      .catch(() => {})
      .finally(() => setLoading(false));
  }, [examId, concept.id]);

  const getColor = (readiness: number) => {
    if (readiness >= 0.7) return '#FFCB05';
    if (readiness >= 0.5) return '#F5B942';
    return '#E05A5A';
  };

  const waterfallData = trace ? traceWaterfallToChart(trace.waterfall) : [];

  if (loading) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center">
        <Loader2 className="w-8 h-8 animate-spin text-foreground-secondary" />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-background">
      {/* Top bar */}
      <div className="border-b border-border bg-white">
        <div className="px-8 py-4 flex items-center justify-between">
          <div className="flex items-center gap-4">
            <ConceptLensButton variant="subtle" onClick={onBack} className="flex items-center gap-2">
              <ArrowLeft className="w-4 h-4" />
              Back to Dashboard
            </ConceptLensButton>
            <div className="h-6 w-px bg-border" />
            <h1 className="text-xl text-foreground font-medium">Root-Cause Analysis</h1>
          </div>
        </div>
      </div>

      <div className="p-8">
        <div className="max-w-7xl mx-auto">
          <div className="grid grid-cols-2 gap-6">
            {/* Left side */}
            <motion.div className="space-y-6" initial={{ opacity: 0, x: -20 }} animate={{ opacity: 1, x: 0 }}>
              {/* Selected concept card */}
              <div className="bg-white border-2 border-[#FFCB05] rounded-xl p-6 shadow-sm">
                <div className="flex items-start justify-between mb-4">
                  <div>
                    <div className="text-xs text-foreground-secondary uppercase tracking-wide mb-1">Selected Concept</div>
                    <h2 className="text-2xl text-foreground">{trace?.concept_label ?? concept.label}</h2>
                  </div>
                  <div className="text-right">
                    <div className="text-xs text-foreground-secondary mb-1">Readiness</div>
                    <div className="text-3xl" style={{ color: getColor(trace?.direct_readiness ?? concept.readiness) }}>
                      {Math.round((trace?.direct_readiness ?? concept.readiness) * 100)}%
                    </div>
                  </div>
                </div>
                <div className="h-2 bg-elevated rounded-full overflow-hidden">
                  <motion.div
                    className="h-full rounded-full"
                    style={{ backgroundColor: getColor(trace?.direct_readiness ?? concept.readiness) }}
                    initial={{ width: 0 }}
                    animate={{ width: `${(trace?.direct_readiness ?? concept.readiness) * 100}%` }}
                    transition={{ duration: 1, ease: 'easeOut' }}
                  />
                </div>
                {trace && (
                  <div className="mt-3 text-sm text-foreground-secondary">
                    {trace.students_affected} student{trace.students_affected !== 1 ? 's' : ''} below threshold
                  </div>
                )}
              </div>

              {/* Upstream prerequisites */}
              {trace && trace.upstream.length > 0 && (
                <div className="bg-white border border-border rounded-xl p-6 shadow-sm">
                  <h3 className="text-lg text-foreground mb-4">Prerequisite Chain</h3>
                  <div className="space-y-4">
                    {trace.upstream.map((up, idx) => (
                      <motion.div
                        key={up.concept_id}
                        className="relative"
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ delay: idx * 0.1 }}
                      >
                        {idx < trace.upstream.length - 1 && (
                          <div className="absolute left-6 top-full h-4 w-px bg-border" />
                        )}
                        <div className="flex items-center gap-4">
                          <div className="w-12 h-12 rounded-full border-2 flex items-center justify-center flex-shrink-0" style={{ borderColor: getColor(up.readiness) }}>
                            <span className="text-sm font-mono" style={{ color: getColor(up.readiness) }}>
                              {Math.round(up.readiness * 100)}%
                            </span>
                          </div>
                          <div className="flex-1">
                            <div className="text-sm text-foreground">{up.concept_label}</div>
                            <div className="text-xs text-foreground-secondary">
                              Weight: {up.contribution_weight.toFixed(2)} | Penalty: {up.penalty_contribution.toFixed(3)}
                            </div>
                          </div>
                          <div className="text-xs text-foreground-secondary">
                            {up.readiness < 0.5 ? 'Critical gap' : up.readiness < 0.7 ? 'Weak' : 'Strong'}
                          </div>
                        </div>
                      </motion.div>
                    ))}
                  </div>
                </div>
              )}

              {/* Downstream */}
              {trace && trace.downstream.length > 0 && (
                <div className="bg-white border border-border rounded-xl p-6 shadow-sm">
                  <h3 className="text-lg text-foreground mb-4">Downstream Impact</h3>
                  <div className="space-y-3">
                    {trace.downstream.map(d => (
                      <div key={d.concept_id} className="flex items-center justify-between text-sm">
                        <span className="text-foreground">{d.concept_label}</span>
                        <span className="font-mono text-foreground-secondary">+{d.boost_contribution.toFixed(3)}</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </motion.div>

            {/* Right side */}
            <motion.div className="space-y-6" initial={{ opacity: 0, x: 20 }} animate={{ opacity: 1, x: 0 }}>
              <div className="bg-white border border-border rounded-xl p-6 shadow-sm">
                <h3 className="text-lg text-foreground mb-4">Readiness Calculation Breakdown</h3>
                {waterfallData.length > 0 ? (
                  <WaterfallChart data={waterfallData} />
                ) : (
                  <div className="h-48 flex items-center justify-center text-foreground-secondary">{PH.NO_DATA}</div>
                )}
              </div>

              {/* Formula explanation */}
              <div className="bg-white border border-border rounded-xl p-6 shadow-sm">
                <button onClick={() => setShowExplanation(!showExplanation)} className="w-full flex items-center justify-between text-left group">
                  <div className="flex items-center gap-2">
                    <Info className="w-4 h-4 text-primary" />
                    <h3 className="text-lg text-foreground group-hover:text-primary transition-colors">Calculation Formula</h3>
                  </div>
                  <ChevronDown className={`w-4 h-4 text-foreground-secondary transition-transform ${showExplanation ? 'rotate-180' : ''}`} />
                </button>
                {showExplanation && (
                  <motion.div initial={{ opacity: 0, height: 0 }} animate={{ opacity: 1, height: 'auto' }} exit={{ opacity: 0, height: 0 }} className="mt-4 pt-4 border-t border-border space-y-3">
                    <div className="bg-elevated rounded-lg p-4 font-mono text-sm text-foreground">
                      R = α x Direct + β x PrereqAvg + γ x DownstreamBoost
                    </div>
                    <div className="pt-3 border-t border-border">
                      <p className="text-xs text-foreground-secondary leading-relaxed">
                        Readiness is computed as a weighted combination of direct question performance,
                        averaged prerequisite readiness, and potential boost from strong downstream concept understanding.
                      </p>
                    </div>
                  </motion.div>
                )}
              </div>

              {/* Interventions from API */}
              <div className="bg-white border border-border rounded-xl p-6 shadow-sm">
                <h3 className="text-lg text-foreground mb-4">Recommended Interventions</h3>
                {interventions.length > 0 ? (
                  <div className="space-y-3">
                    {interventions.map((iv, idx) => (
                      <div key={idx} className="bg-surface border border-border rounded-lg p-4">
                        <div className="text-sm text-foreground mb-1">{iv.suggested_format}</div>
                        <div className="text-xs text-foreground-secondary leading-relaxed">{iv.rationale}</div>
                        <div className="text-xs text-foreground-secondary mt-2">
                          Impact: {iv.impact.toFixed(2)} | {iv.students_affected} students affected
                        </div>
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="text-sm text-foreground-secondary py-4 text-center">{PH.NO_INTERVENTIONS}</div>
                )}
              </div>
            </motion.div>
          </div>
        </div>
      </div>
    </div>
  );
};
