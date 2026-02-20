import React, { useState, useEffect, useContext } from 'react';
import { motion } from 'motion/react';
import { ConfidenceBadge } from '../components/ConfidenceBadge';
import { InstructorTaskBar } from '../components/InstructorTaskBar';
import { BookOpen, TrendingUp, Target, ChevronRight, Mail, Phone, MapPin, Loader2, AlertCircle } from 'lucide-react';
import { StudentConceptGraph } from '../components/StudentConceptGraph';
import { AppCtx } from '../App';
import { reportsService } from '../services/reportsService';
import type { StudentListItem } from '../services/reportsService';
import { coursesService } from '../services/coursesService';
import { examsService } from '../services/examsService';
import { ApiError } from '../services/apiClient';
import { config } from '../services/config';
import { PH } from '../constants/placeholders';
import type { CourseResponse, ExamResponse, StudentReportResponse } from '../services/types';

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
  const [students, setStudents] = useState<StudentListItem[]>([]);
  const [studentsLoading, setStudentsLoading] = useState(false);
  const [studentsError, setStudentsError] = useState<string | null>(null);
  const [selectedStudentId, setSelectedStudentId] = useState<string>('');
  const [report, setReport] = useState<StudentReportResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [expandedConcept, setExpandedConcept] = useState<string | null>(null);

  useEffect(() => { coursesService.list().then(setCourses).catch(() => {}); }, []);

  useEffect(() => {
    if (courseId) examsService.list(courseId).then(setExams).catch(() => {});
    else setExams([]);
  }, [courseId]);

  useEffect(() => {
    if (!examId) {
      setStudents([]);
      setSelectedStudentId('');
      setStudentsError(null);
      return;
    }
    setStudentsLoading(true);
    setSelectedStudentId('');
    setStudentsError(null);
    reportsService.listStudents(examId)
      .then(r => {
        const normalizedStudents = [...new Set(r.students.map((s) => s.student_id.trim()).filter(Boolean))]
          .sort((a, b) => a.localeCompare(b))
          .map((student_id) => ({ student_id } as StudentListItem));
        setStudents(normalizedStudents);
        if (normalizedStudents.length === 0) {
          setStudentsError('No students found. Run Compute first to generate student results.');
        }
      })
      .catch((err) => {
        setStudents([]);
        if (err instanceof ApiError && (err.status === 401 || err.status === 403)) {
          setStudentsError('Unauthorized. Set instructor credentials in frontend .env and retry.');
          return;
        }
        setStudentsError(err?.message ?? 'Failed to load students. Check that Compute has been run.');
      })
      .finally(() => setStudentsLoading(false));
  }, [examId]);

  useEffect(() => {
    if (!selectedStudentId || !examId) { setReport(null); return; }
    setLoading(true);
    reportsService.getByStudentId(examId, selectedStudentId)
      .then(setReport)
      .catch(() => setReport(null))
      .finally(() => setLoading(false));
  }, [selectedStudentId, examId]);

  const concepts = report ? reportToConcepts(report) : [];
  const studentReadiness: Record<string, number> = {};
  if (report) {
    for (const r of report.readiness) studentReadiness[r.concept_id] = r.final_readiness;
  }

  const strongConceptCount = concepts.filter(c => (studentReadiness[c.id] ?? 0) >= HIGH_READINESS).length;
  const overallProgress = concepts.length > 0
    ? Math.round((concepts.reduce((s, c) => s + (studentReadiness[c.id] ?? 0), 0) / concepts.length) * 100)
    : 0;

  const studentSelectorPlaceholder = !examId
    ? 'Select an exam first'
    : studentsLoading
    ? 'Loading students...'
    : students.length > 0
    ? PH.SELECT_STUDENT
    : 'Run Compute to see students';

  const studyPlan = report?.study_plan ?? [];
  const weakConcepts = report?.top_weak_concepts ?? [];
  const contactOrFallback = (value: string) => value.trim() || 'Not provided';

  const getColor = (readiness: number) => {
    if (readiness >= 0.7) return '#FFCB05';
    if (readiness >= 0.5) return '#56B4E9';
    return '#D55E00';
  };

  const getConfidenceLevel = (readiness: number): 'high' | 'medium' | 'low' => {
    if (readiness >= 0.7) return 'high';
    if (readiness >= 0.5) return 'medium';
    return 'low';
  };

  const studentSelectorControl = (
    <>
      <label className="text-xs font-medium text-foreground-secondary flex-shrink-0">Student</label>
      <select
        value={selectedStudentId}
        onChange={(e) => setSelectedStudentId(e.target.value)}
        disabled={studentsLoading || !examId || students.length === 0}
        className="bg-surface border border-border rounded-lg px-4 py-2 text-sm text-foreground appearance-none bg-[length:16px_16px] bg-[position:right_12px_center] bg-no-repeat bg-[url('data:image/svg+xml;charset=utf-8,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20width%3D%2216%22%20height%3D%2216%22%20viewBox%3D%220%200%2024%2024%22%20fill%3D%22none%22%20stroke%3D%22%2364748b%22%20stroke-width%3D%222%22%20stroke-linecap%3D%22round%22%20stroke-linejoin%3D%22round%22%3E%3Cpath%20d%3D%22m6%209%206%206%206-6%22%2F%3E%3C%2Fsvg%3E')] focus:outline-none focus:ring-2 focus:ring-[#FFCB05] pr-10 min-w-[220px] disabled:opacity-60"
      >
        <option value="">{studentSelectorPlaceholder}</option>
        {students.map(s => (
          <option key={s.student_id} value={s.student_id}>{s.student_id}</option>
        ))}
      </select>
      {studentsError && !studentsLoading && (
        <div className="flex items-center gap-1.5 text-xs text-[#D55E00] max-w-[260px]">
          <AlertCircle className="w-3.5 h-3.5 flex-shrink-0" />
          <span className="truncate">{studentsError}</span>
        </div>
      )}
    </>
  );

  return (
    <div className="min-h-screen bg-background">
      <InstructorTaskBar
        pageTitle="Students"
        courses={courses}
        exams={exams}
        courseId={courseId}
        examId={examId}
        onCourseChange={setCourseId}
        onExamChange={setExamId}
        studentCount={concepts.length > 0 ? 1 : undefined}
        conceptCount={concepts.length || undefined}
        extraControl={studentSelectorControl}
      />
      {report && (
        <div className="bg-white border-b border-border px-8 py-2">
          <div className="text-sm text-foreground-secondary text-right">
            Overall Progress: <span className="text-[#00274C] font-medium">{overallProgress}%</span>
          </div>
        </div>
      )}

      {loading ? (
        <div className="flex items-center justify-center h-96">
          <Loader2 className="w-8 h-8 animate-spin text-foreground-secondary" />
        </div>
      ) : !report ? (
        <div className="flex items-center justify-center h-96">
          <div className="text-foreground-secondary">
            {!examId
              ? 'Select a course and exam above to view student reports'
              : students.length === 0
              ? 'No computed results yet — run Compute on the Upload page first'
              : 'Select a student above to view their report'}
          </div>
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
              <motion.div className="flex-1 bg-gradient-to-br from-[#56B4E9]/10 to-[#56B4E9]/5 border border-[#56B4E9]/30 rounded-xl p-6" initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.2 }}>
                <div className="flex items-start justify-between">
                  <div>
                    <div className="text-xs text-foreground-secondary uppercase tracking-wide mb-2">To Improve</div>
                    <div className="text-4xl text-[#00274C] font-medium mb-1">{weakConcepts.length}</div>
                    <p className="text-xs text-foreground-secondary">Concepts needing additional practice</p>
                  </div>
                  <div className="w-12 h-12 rounded-xl bg-[#56B4E9]/20 flex items-center justify-center">
                    <TrendingUp className="w-6 h-6 text-[#56B4E9]" />
                  </div>
                </div>
              </motion.div>
              <motion.div className="flex-1 bg-gradient-to-br from-[#D55E00]/10 to-[#D55E00]/5 border border-[#D55E00]/30 rounded-xl p-6" initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.3 }}>
                <div className="flex items-start justify-between">
                  <div>
                    <div className="text-xs text-foreground-secondary uppercase tracking-wide mb-2">Priority Focus</div>
                    <div className="text-4xl text-[#00274C] font-medium mb-1">{studyPlan.length}</div>
                    <p className="text-xs text-foreground-secondary">Study plan items</p>
                  </div>
                  <div className="w-12 h-12 rounded-xl bg-[#D55E00]/20 flex items-center justify-center">
                    <BookOpen className="w-6 h-6 text-[#D55E00]" />
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
                  <div className="text-xl font-medium">{contactOrFallback(config.contacts.instructor.name)}</div>
                  <div className="space-y-2 text-sm opacity-90">
                    <div className="flex items-center gap-2"><Mail className="w-4 h-4" /><span>{contactOrFallback(config.contacts.instructor.email)}</span></div>
                    <div className="flex items-center gap-2"><Phone className="w-4 h-4" /><span>{contactOrFallback(config.contacts.instructor.phone)}</span></div>
                    <div className="flex items-center gap-2"><MapPin className="w-4 h-4" /><span>{contactOrFallback(config.contacts.instructor.office)}</span></div>
                  </div>
                  <div className="pt-2 text-xs opacity-75">Office Hours: {contactOrFallback(config.contacts.instructor.hours)}</div>
                </div>
                <div className="space-y-3">
                  <div className="text-sm opacity-75 uppercase tracking-wide">Teaching Assistant</div>
                  <div className="text-xl font-medium">{contactOrFallback(config.contacts.ta.name)}</div>
                  <div className="space-y-2 text-sm opacity-90">
                    <div className="flex items-center gap-2"><Mail className="w-4 h-4" /><span>{contactOrFallback(config.contacts.ta.email)}</span></div>
                    <div className="flex items-center gap-2"><Phone className="w-4 h-4" /><span>{contactOrFallback(config.contacts.ta.phone)}</span></div>
                    <div className="flex items-center gap-2"><MapPin className="w-4 h-4" /><span>{contactOrFallback(config.contacts.ta.office)}</span></div>
                  </div>
                  <div className="pt-2 text-xs opacity-75">Office Hours: {contactOrFallback(config.contacts.ta.hours)}</div>
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
