import React, { useState, useEffect, useContext } from 'react';
import { motion } from 'motion/react';
import { ConceptLensSlider } from '../components/ConceptLensSlider';
import { AlertPanel } from '../components/AlertPanel';
import { ConceptDAG } from '../components/ConceptDAG';
import { D3Heatmap } from '../components/D3Heatmap';
import { InstructorTaskBar } from '../components/InstructorTaskBar';
import { AlertCircle } from 'lucide-react';
import { AppCtx } from '../App';
import type { TraceConcept } from '../App';
import { dashboardService } from '../services/dashboardService';
import { parametersService } from '../services/parametersService';
import { coursesService } from '../services/coursesService';
import { examsService } from '../services/examsService';
import { computeService } from '../services/computeService';
import { PH } from '../constants/placeholders';
import type {
  AggregateItem,
  AlertItem,
  CourseResponse,
  DashboardResponse,
  ExamResponse,
  HeatmapCell,
  InterventionItem,
} from '../services/types';

interface ConceptNode {
  id: string;
  name: string;
  readiness: number;
  depth: number;
  prerequisites: string[];
  x?: number;
  y?: number;
}

interface Student {
  id: string;
  name: string;
  conceptReadiness: Record<string, number>;
}

interface InstructorDashboardProps {
  onConceptClick: (concept: TraceConcept) => void;
}

function aggregatesToConcepts(aggs: AggregateItem[]): ConceptNode[] {
  return aggs.map((a, idx) => ({
    id: a.concept_id,
    name: a.concept_label,
    readiness: a.mean_readiness,
    depth: 0,
    prerequisites: [],
    x: 200 + (idx % 4) * 200,
    y: 100 + Math.floor(idx / 4) * 150,
  }));
}

function heatmapToStudents(cells: HeatmapCell[], conceptIds: string[]): Student[] {
  const conceptBuckets: Record<string, HeatmapCell[]> = {};
  for (const c of cells) {
    if (!conceptBuckets[c.concept_id]) conceptBuckets[c.concept_id] = [];
    conceptBuckets[c.concept_id].push(c);
  }

  const studentCount = Object.values(conceptBuckets)[0]
    ?.reduce((sum, b) => sum + b.count, 0) ?? 0;

  return Array.from({ length: Math.min(studentCount, 30) }, (_, i) => {
    const readiness: Record<string, number> = {};
    for (const cid of conceptIds) {
      const buckets = conceptBuckets[cid] ?? [];
      const total = buckets.reduce((s, b) => s + b.count, 0);
      if (total === 0) { readiness[cid] = 0; continue; }
      let weighted = 0;
      for (const b of buckets) {
        const [lo] = b.bucket.split('-').map(Number);
        weighted += ((lo + 10) / 100) * (b.count / total);
      }
      readiness[cid] = weighted + (Math.random() * 0.15 - 0.075);
    }
    return { id: `s${i + 1}`, name: `Student ${i + 1}`, conceptReadiness: readiness };
  });
}

function alertItemsToAlerts(items: AlertItem[]): Array<{
  id: string; conceptId: string; conceptName: string;
  severity: 'high' | 'medium' | 'low'; impact: number;
  studentsAffected: number; message: string;
}> {
  return items.map((a, i) => ({
    id: `alert-${i}`,
    conceptId: a.concept_id,
    conceptName: a.concept_label,
    severity: a.impact > 5 ? 'high' : a.impact > 2 ? 'medium' : 'low',
    impact: a.impact,
    studentsAffected: a.students_below_threshold,
    message: a.recommended_action,
  }));
}

export const InstructorDashboard: React.FC<InstructorDashboardProps> = ({ onConceptClick }) => {
  const { courseId, examId, setCourseId, setExamId } = useContext(AppCtx);

  const [courses, setCourses] = useState<CourseResponse[]>([]);
  const [exams, setExams] = useState<ExamResponse[]>([]);
  const [loading, setLoading] = useState(false);

  const [dashboard, setDashboard] = useState<DashboardResponse | null>(null);
  const [interventions, setInterventions] = useState<InterventionItem[]>([]);
  const [parameters, setParameters] = useState({ alpha: 0.6, beta: 0.3, gamma: 0.2, threshold: 0.6 });
  const [selectedConceptId, setSelectedConceptId] = useState<string | null>(null);

  const concepts = dashboard ? aggregatesToConcepts(dashboard.aggregates) : [];
  const students = dashboard ? heatmapToStudents(dashboard.heatmap, concepts.map(c => c.id)) : [];
  const alerts = dashboard ? alertItemsToAlerts(dashboard.alerts) : [];

  useEffect(() => { coursesService.list().then(setCourses).catch(() => {}); }, []);

  useEffect(() => {
    if (courseId) examsService.list(courseId).then(setExams).catch(() => {});
    else setExams([]);
  }, [courseId]);

  useEffect(() => {
    if (!examId) return;
    setLoading(true);
    Promise.all([
      dashboardService.getDashboard(examId),
      parametersService.get(examId),
      computeService.getInterventions(examId),
    ])
      .then(([d, p, iv]) => {
        setDashboard(d);
        setParameters({ alpha: p.alpha, beta: p.beta, gamma: p.gamma, threshold: p.threshold });
        setInterventions(iv.interventions);
      })
      .catch(() => {})
      .finally(() => setLoading(false));
  }, [examId]);

  const handleNodeClick = (node: ConceptNode) => {
    setSelectedConceptId(node.id);
    onConceptClick({ id: node.id, label: node.name, readiness: node.readiness });
  };

  return (
    <div className="min-h-screen bg-background">
      <InstructorTaskBar
        pageTitle="Dashboard"
        courses={courses}
        exams={exams}
        courseId={courseId}
        examId={examId}
        onCourseChange={setCourseId}
        onExamChange={setExamId}
        studentCount={students.length}
        conceptCount={concepts.length}
      />

      {loading ? (
        <div className="flex items-center justify-center h-96">
          <div className="text-foreground-secondary">{PH.LOADING}</div>
        </div>
      ) : !dashboard || concepts.length === 0 ? (
        <div className="flex items-center justify-center h-96">
          <div className="text-foreground-secondary">{examId ? PH.NO_DATA : 'Select a course and exam above to view dashboard'}</div>
        </div>
      ) : (
        <div className="p-8 space-y-6">
          {/* Parameters */}
          <motion.div className="bg-white border border-border rounded-xl p-6 shadow-sm" initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }}>
            <div className="mb-6">
              <h2 className="text-lg text-foreground">Analysis Parameters</h2>
              <p className="text-xs text-foreground-secondary mt-1">
                These weights control how the AI computes concept readiness: direct mastery, prerequisite penalties, and downstream boosts are combined into a single score per concept.
              </p>
            </div>
            {/* Combined weight bar */}
            <div className="mb-6">
              <div className="flex items-center gap-2 text-xs text-foreground-secondary mb-2">
                <span>Weight Distribution</span>
              </div>
              <div className="flex h-3 rounded-full overflow-hidden">
                <div
                  className="transition-all duration-300"
                  style={{
                    width: `${(parameters.alpha / (parameters.alpha + parameters.beta + parameters.gamma)) * 100}%`,
                    backgroundColor: '#FFCB05',
                  }}
                  title={`Direct (α): ${(parameters.alpha * 100).toFixed(0)}%`}
                />
                <div
                  className="transition-all duration-300"
                  style={{
                    width: `${(parameters.beta / (parameters.alpha + parameters.beta + parameters.gamma)) * 100}%`,
                    backgroundColor: '#00274C',
                  }}
                  title={`Prerequisite (β): ${(parameters.beta * 100).toFixed(0)}%`}
                />
                <div
                  className="transition-all duration-300"
                  style={{
                    width: `${(parameters.gamma / (parameters.alpha + parameters.beta + parameters.gamma)) * 100}%`,
                    backgroundColor: '#56B4E9',
                  }}
                  title={`Downstream (γ): ${(parameters.gamma * 100).toFixed(0)}%`}
                />
              </div>
              <div className="flex items-center justify-between mt-2 text-xs text-foreground-secondary">
                <div className="flex items-center gap-1.5">
                  <div className="w-2.5 h-2.5 rounded-sm" style={{ backgroundColor: '#FFCB05' }} />
                  <span>Direct (α) {(parameters.alpha * 100).toFixed(0)}%</span>
                </div>
                <div className="flex items-center gap-1.5">
                  <div className="w-2.5 h-2.5 rounded-sm" style={{ backgroundColor: '#00274C' }} />
                  <span>Prerequisite (β) {(parameters.beta * 100).toFixed(0)}%</span>
                </div>
                <div className="flex items-center gap-1.5">
                  <div className="w-2.5 h-2.5 rounded-sm" style={{ backgroundColor: '#56B4E9' }} />
                  <span>Downstream (γ) {(parameters.gamma * 100).toFixed(0)}%</span>
                </div>
              </div>
            </div>
            <div className="grid grid-cols-4 gap-6">
              <ConceptLensSlider label="Direct Weight (α)" value={parameters.alpha} min={0} max={1} step={0.05} onChange={(v) => setParameters({ ...parameters, alpha: v })} description="How much raw question performance counts" />
              <ConceptLensSlider label="Prerequisite Penalty (β)" value={parameters.beta} min={0} max={1} step={0.05} onChange={(v) => setParameters({ ...parameters, beta: v })} description="Penalty when prerequisite topics are weak" />
              <ConceptLensSlider label="Downstream Boost (γ)" value={parameters.gamma} min={0} max={1} step={0.05} onChange={(v) => setParameters({ ...parameters, gamma: v })} description="Bonus when downstream topics are strong" />
              <ConceptLensSlider label="Readiness Threshold" value={parameters.threshold} min={0} max={1} step={0.05} onChange={(v) => setParameters({ ...parameters, threshold: v })} description="Score above which a concept is mastered" />
            </div>
          </motion.div>

          {/* Main content grid */}
          <div className="grid grid-cols-3 gap-6">
            <motion.div className="col-span-2 bg-white border border-border rounded-xl p-6 shadow-sm" initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.1 }}>
              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <h2 className="text-lg text-foreground">Concept Readiness Matrix</h2>
                  <div className="flex items-center gap-2 text-xs text-foreground-secondary">
                    <div className="flex items-center gap-1"><div className="w-3 h-3 rounded bg-primary/80" /><span>High</span></div>
                    <div className="flex items-center gap-1"><div className="w-3 h-3 rounded bg-warning/80" /><span>Medium</span></div>
                    <div className="flex items-center gap-1"><div className="w-3 h-3 rounded bg-critical/80" /><span>Low</span></div>
                  </div>
                </div>
                {students.length > 0 ? (
                  <D3Heatmap concepts={concepts} students={students} onConceptClick={handleNodeClick} />
                ) : (
                  <div className="h-64 flex items-center justify-center text-foreground-secondary">{PH.NO_HEATMAP}</div>
                )}
              </div>
            </motion.div>

            <motion.div className="bg-white border border-border rounded-xl p-6 shadow-sm" initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.2 }}>
              <div className="space-y-4">
                <div className="flex items-center gap-2">
                  <AlertCircle className="w-5 h-5 text-critical" />
                  <h2 className="text-lg text-foreground">Root Cause Analysis</h2>
                </div>
                {alerts.length > 0 ? (
                  <div className="space-y-3">
                    {alerts.slice(0, 5).map((alert) => (
                      <AlertPanel
                        key={alert.id}
                        alert={alert}
                        onClick={() => {
                          const concept = concepts.find(c => c.id === alert.conceptId);
                          if (concept) handleNodeClick(concept);
                        }}
                      />
                    ))}
                  </div>
                ) : (
                  <div className="text-sm text-foreground-secondary py-8 text-center">{PH.NO_ALERTS}</div>
                )}
              </div>
            </motion.div>
          </div>

          {/* Knowledge Graph */}
          <motion.div className="bg-white border border-border rounded-xl p-6 shadow-sm" initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.3 }}>
            <div className="space-y-4">
              <h2 className="text-lg text-foreground">Knowledge Graph</h2>
              <div className="h-[600px]">
                <ConceptDAG examId={examId} concepts={concepts} onNodeClick={handleNodeClick} selectedNodeId={selectedConceptId} />
              </div>
              <div className="text-xs text-foreground-secondary text-center pt-2">
                Click a node for root-cause analysis. Double-click to expand with AI-suggested subtopics.
              </div>
            </div>
          </motion.div>
        </div>
      )}
    </div>
  );
};
