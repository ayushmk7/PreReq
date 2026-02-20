import React, { useState, useEffect, useContext } from 'react';
import { motion } from 'motion/react';
import { ConfidenceBadge } from '../components/ConfidenceBadge';
import { BookOpen, TrendingUp, Target, ChevronRight, ChevronDown, Mail, Phone, MapPin, Loader2 } from 'lucide-react';
import { StudentConceptGraph } from '../components/StudentConceptGraph';
import { AppCtx } from '../App';
import { reportsService } from '../services/reportsService';
import { coursesService } from '../services/coursesService';
import { examsService } from '../services/examsService';
import { PH } from '../constants/placeholders';
import type { CourseResponse, ExamResponse, StudentReportResponse, StudentTokenItem } from '../services/types';

const HIGH_READINESS = 0.7;

interface ConceptNode {
  id: string;
  name: string;
  readiness: number;
  depth: number;
  prerequisites: string[];
}

function reportToConcepts(report: StudentReportResponse): ConceptNode[] {
  const graphNodes = (report.concept_graph as { nodes?: Array<{ id: string; label: string; readiness?: number }> })?.nodes ?? [];
  const graphEdges = (report.concept_graph as { edges?: Array<{ source: string; target: string }> })?.edges ?? [];

  const prereqMap: Record<string, string[]> = {};
  for (const e of graphEdges) {
    if (!prereqMap[e.target]) prereqMap[e.target] = [];
    prereqMap[e.target].push(e.source);
  }

  return graphNodes.map((n) => {
    const r = report.readiness.find(r => r.concept_id === n.id);
    return {
      id: n.id,
      name: n.label ?? n.id,
      readiness: r?.final_readiness ?? n.readiness ?? 0,
      depth: 0,
      prerequisites: prereqMap[n.id] ?? [],
    };
  });
}

export const StudentReport: React.FC = () => {
  const { courseId, examId, setCourseId, setExamId } = useContext(AppCtx);

  const [courses, setCourses] = useState<CourseResponse[]>([]);
  const [exams, setExams] = useState<ExamResponse[]>([]);
  const [tokens, setTokens] = useState<StudentTokenItem[]>([]);
  const [selectedToken, setSelectedToken] = useState<string>('');
  const [report, setReport] = useState<StudentReportResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [expandedConcept, setExpandedConcept] = useState<string | null>(null);

  useEffect(() => { coursesService.list().then(setCourses).catch(() => {}); }, []);

  useEffect(() => {
    if (courseId) examsService.list(courseId).then(setExams).catch(() => {});
    else setExams([]);
  }, [courseId]);

  useEffect(() => {
    if (examId) reportsService.listTokens(examId).then(r => setTokens(r.tokens)).catch(() => setTokens([]));
    else setTokens([]);
  }, [examId]);

  useEffect(() => {
    if (!selectedToken) { setReport(null); return; }
    setLoading(true);
    reportsService.getByToken(selectedToken)
      .then(setReport)
      .catch(() => setReport(null))
      .finally(() => setLoading(false));
  }, [selectedToken]);

  const concepts = report ? reportToConcepts(report) : [];
  const studentReadiness: Record<string, number> = {};
  if (report) {
    for (const r of report.readiness) studentReadiness[r.concept_id] = r.final_readiness;
  }

  const strongConceptCount = concepts.filter(c => (studentReadiness[c.id] ?? 0) >= HIGH_READINESS).length;
  const overallProgress = concepts.length > 0
    ? Math.round((concepts.reduce((s, c) => s + (studentReadiness[c.id] ?? 0), 0) / concepts.length) * 100)
    : 0;

  const studyPlan = report?.study_plan ?? [];
  const weakConcepts = report?.top_weak_concepts ?? [];

  const getColor = (readiness: number) => {
    if (readiness >= 0.7) return '#FFCB05';
    if (readiness >= 0.5) return '#F5B942';
    return '#E05A5A';
  };

  const getConfidenceLevel = (readiness: number): 'high' | 'medium' | 'low' => {
    if (readiness >= 0.7) return 'high';
    if (readiness >= 0.5) return 'medium';
    return 'low';
  };

  return (
    <div className="min-h-screen bg-background">
      {/* Header */}
      <div className="bg-white border-b border-border">
        <div className="px-8 py-6">
          <div className="max-w-5xl mx-auto">
            <div className="flex items-start justify-between mb-6">
              <div className="flex-1">
                <h1 className="text-2xl text-foreground mb-3">Student Concept Readiness Report</h1>
                <div className="flex items-center gap-3">
                  <select value={courseId ?? ''} onChange={(e) => { setCourseId(e.target.value || null); setExamId(null); }} className="bg-surface border border-border rounded-lg px-3 py-2 text-sm text-foreground focus:outline-none focus:ring-2 focus:ring-[#FFCB05]">
                    <option value="">{courses.length ? PH.SELECT_COURSE : PH.NO_DATA}</option>
                    {courses.map(c => <option key={c.id} value={c.id}>{c.name}</option>)}
                  </select>
                  <select value={examId ?? ''} onChange={(e) => setExamId(e.target.value || null)} className="bg-surface border border-border rounded-lg px-3 py-2 text-sm text-foreground focus:outline-none focus:ring-2 focus:ring-[#FFCB05]">
                    <option value="">{exams.length ? PH.SELECT_EXAM : PH.NO_DATA}</option>
                    {exams.map(e => <option key={e.id} value={e.id}>{e.name}</option>)}
                  </select>
                </div>
              </div>

              {/* Student token selector */}
              <div>
                <label className="text-xs text-foreground-secondary mb-1 block">Student</label>
                <select
                  value={selectedToken}
                  onChange={(e) => setSelectedToken(e.target.value)}
                  className="bg-surface border border-border rounded-lg px-3 py-2 text-sm text-foreground focus:outline-none focus:ring-2 focus:ring-[#FFCB05] min-w-[200px]"
                >
                  <option value="">{tokens.length ? PH.SELECT_STUDENT : PH.NO_STUDENTS}</option>
                  {tokens.map(t => <option key={t.token} value={t.token}>{t.student_id}</option>)}
                </select>
              </div>
            </div>

            {report && (
              <div className="text-sm text-foreground-secondary">
                Overall Progress: <span className="text-[#00274C] font-medium">{overallProgress}%</span>
              </div>
            )}
          </div>
        </div>
      </div>

      {loading ? (
        <div className="flex items-center justify-center h-96">
          <Loader2 className="w-8 h-8 animate-spin text-foreground-secondary" />
        </div>
      ) : !report ? (
        <div className="flex items-center justify-center h-96">
          <div className="text-foreground-secondary">{selectedToken ? PH.NO_DATA : 'Select a course, exam, and student to view report'}</div>
        </div>
      ) : (
        <div className="px-8 py-8">
          <div className="max-w-5xl mx-auto space-y-8">
            {/* Summary cards */}
            <div className="flex gap-4">
              <motion.div className="flex-1 bg-gradient-to-br from-[#FFCB05]/10 to-[#FFCB05]/5 border border-[#FFCB05]/30 rounded-xl p-6" initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.1 }}>
                <div className="flex items-start justify-between">
                  <div>
                    <div className="text-xs text-foreground-secondary uppercase tracking-wide mb-2">Strong Concepts</div>
                    <div className="text-4xl text-[#00274C] font-medium mb-1">{strongConceptCount}</div>
                    <p className="text-xs text-foreground-secondary">Concepts mastered with high readiness</p>
                  </div>
                  <div className="w-12 h-12 rounded-xl bg-[#FFCB05]/20 flex items-center justify-center">
                    <Target className="w-6 h-6 text-[#00274C]" />
                  </div>
                </div>
              </motion.div>
              <motion.div className="flex-1 bg-gradient-to-br from-[#F5B942]/10 to-[#F5B942]/5 border border-[#F5B942]/30 rounded-xl p-6" initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.2 }}>
                <div className="flex items-start justify-between">
                  <div>
                    <div className="text-xs text-foreground-secondary uppercase tracking-wide mb-2">To Improve</div>
                    <div className="text-4xl text-[#00274C] font-medium mb-1">{weakConcepts.length}</div>
                    <p className="text-xs text-foreground-secondary">Concepts needing additional practice</p>
                  </div>
                  <div className="w-12 h-12 rounded-xl bg-[#F5B942]/20 flex items-center justify-center">
                    <TrendingUp className="w-6 h-6 text-[#F5B942]" />
                  </div>
                </div>
              </motion.div>
              <motion.div className="flex-1 bg-gradient-to-br from-[#E05A5A]/10 to-[#E05A5A]/5 border border-[#E05A5A]/30 rounded-xl p-6" initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.3 }}>
                <div className="flex items-start justify-between">
                  <div>
                    <div className="text-xs text-foreground-secondary uppercase tracking-wide mb-2">Priority Focus</div>
                    <div className="text-4xl text-[#00274C] font-medium mb-1">{studyPlan.length}</div>
                    <p className="text-xs text-foreground-secondary">Study plan items</p>
                  </div>
                  <div className="w-12 h-12 rounded-xl bg-[#E05A5A]/20 flex items-center justify-center">
                    <BookOpen className="w-6 h-6 text-[#E05A5A]" />
                  </div>
                </div>
              </motion.div>
            </div>

            {/* Personal concept graph */}
            <motion.div className="bg-white border border-border rounded-xl p-6" initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.4 }}>
              <h2 className="text-lg text-foreground mb-4">Your Concept Map</h2>
              <div className="bg-surface rounded-lg overflow-hidden" style={{ height: '400px' }}>
                <StudentConceptGraph concepts={concepts} studentReadiness={studentReadiness} />
              </div>
              <p className="text-xs text-foreground-secondary text-center mt-4">Interactive view showing mastery across all course concepts</p>
            </motion.div>

            {/* Study plan */}
            <motion.div className="bg-white border border-border rounded-xl p-6" initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.5 }}>
              <div className="mb-6">
                <h2 className="text-lg text-foreground mb-2">Personalized Study Plan</h2>
                <p className="text-sm text-foreground-secondary">
                  Concepts are ordered by prerequisite dependencies. Focus on earlier items first.
                </p>
              </div>

              {studyPlan.length > 0 ? (
                <div className="space-y-4">
                  {studyPlan.map((item, idx) => (
                    <motion.div key={item.concept_id} className="relative" initial={{ opacity: 0, x: -20 }} animate={{ opacity: 1, x: 0 }} transition={{ delay: 0.6 + idx * 0.05 }}>
                      {idx < studyPlan.length - 1 && <div className="absolute left-6 top-full h-4 w-0.5 bg-border" />}
                      <div
                        className="bg-surface border border-border rounded-xl p-5 hover:border-[#FFCB05]/50 hover:shadow-sm transition-all cursor-pointer"
                        onClick={() => setExpandedConcept(expandedConcept === item.concept_id ? null : item.concept_id)}
                      >
                        <div className="flex items-start gap-4">
                          <div className="flex-shrink-0 w-12 h-12 rounded-full border-2 flex items-center justify-center" style={{ borderColor: getColor(item.readiness), backgroundColor: `${getColor(item.readiness)}15` }}>
                            <span className="text-sm font-mono font-medium" style={{ color: getColor(item.readiness) }}>{idx + 1}</span>
                          </div>
                          <div className="flex-1">
                            <div className="flex items-start justify-between mb-2">
                              <div>
                                <h3 className="text-base text-foreground mb-1">{item.concept_label}</h3>
                                <p className="text-xs text-foreground-secondary">{item.reason}</p>
                              </div>
                              <ConfidenceBadge level={getConfidenceLevel(item.readiness)} />
                            </div>
                            <div className="space-y-1.5">
                              <div className="flex items-center justify-between text-xs">
                                <span className="text-foreground-secondary">Current</span>
                                <span className="text-foreground-secondary">Target (70%)</span>
                              </div>
                              <div className="relative h-2 bg-white rounded-full overflow-hidden border border-border/50">
                                <motion.div className="absolute inset-y-0 left-0 rounded-full" style={{ backgroundColor: getColor(item.readiness) }} initial={{ width: 0 }} animate={{ width: `${item.readiness * 100}%` }} transition={{ duration: 0.8, delay: 0.6 + idx * 0.05 }} />
                                <div className="absolute top-0 bottom-0 w-0.5 bg-[#00274C]" style={{ left: '70%' }} />
                              </div>
                              <div className="flex items-center justify-between text-xs font-mono">
                                <span style={{ color: getColor(item.readiness) }}>{Math.round(item.readiness * 100)}%</span>
                                <span className="text-[#00274C]">70%</span>
                              </div>
                            </div>
                            {expandedConcept === item.concept_id && (
                              <motion.div initial={{ opacity: 0, height: 0 }} animate={{ opacity: 1, height: 'auto' }} className="mt-4 pt-4 border-t border-border">
                                <div className="text-xs text-foreground-secondary">{item.explanation}</div>
                              </motion.div>
                            )}
                          </div>
                          <ChevronRight className={`w-5 h-5 text-foreground-secondary transition-transform ${expandedConcept === item.concept_id ? 'rotate-90' : ''}`} />
                        </div>
                      </div>
                    </motion.div>
                  ))}
                </div>
              ) : (
                <div className="text-sm text-foreground-secondary py-8 text-center">{PH.NO_STUDY_PLAN}</div>
              )}
            </motion.div>

            {/* Contact info with placeholders */}
            <motion.div className="bg-[#00274C] text-white rounded-xl p-8" initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 1 }}>
              <h3 className="text-lg font-medium mb-4">Need Help? Contact Your Instructor</h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div className="space-y-3">
                  <div className="text-sm opacity-75 uppercase tracking-wide">Instructor</div>
                  <div className="text-xl font-medium">{PH.INSTRUCTOR_NAME}</div>
                  <div className="space-y-2 text-sm opacity-90">
                    <div className="flex items-center gap-2"><Mail className="w-4 h-4" /><span>{PH.INSTRUCTOR_EMAIL}</span></div>
                    <div className="flex items-center gap-2"><Phone className="w-4 h-4" /><span>{PH.INSTRUCTOR_PHONE}</span></div>
                    <div className="flex items-center gap-2"><MapPin className="w-4 h-4" /><span>{PH.INSTRUCTOR_OFFICE}</span></div>
                  </div>
                  <div className="pt-2 text-xs opacity-75">Office Hours: {PH.INSTRUCTOR_HOURS}</div>
                </div>
                <div className="space-y-3">
                  <div className="text-sm opacity-75 uppercase tracking-wide">Teaching Assistant</div>
                  <div className="text-xl font-medium">{PH.TA_NAME}</div>
                  <div className="space-y-2 text-sm opacity-90">
                    <div className="flex items-center gap-2"><Mail className="w-4 h-4" /><span>{PH.TA_EMAIL}</span></div>
                    <div className="flex items-center gap-2"><Phone className="w-4 h-4" /><span>{PH.TA_PHONE}</span></div>
                    <div className="flex items-center gap-2"><MapPin className="w-4 h-4" /><span>{PH.TA_OFFICE}</span></div>
                  </div>
                  <div className="pt-2 text-xs opacity-75">Office Hours: {PH.TA_HOURS}</div>
                </div>
              </div>
              <div className="mt-6 pt-6 border-t border-white/20">
                <p className="text-sm opacity-90">
                  Don't hesitate to reach out! We're here to help you succeed.
                </p>
              </div>
            </motion.div>
          </div>
        </div>
      )}
    </div>
  );
};
