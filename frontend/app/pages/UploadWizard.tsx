import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'motion/react';
import { ConceptLensButton } from '../components/ConceptLensButton';
import { LoadingSpinner } from '../components/LoadingSpinner';
import { Upload, CheckCircle2, ArrowRight, FileText, Network, Settings, Zap, Download, Table, X, AlertCircle } from 'lucide-react';
import { coursesService } from '../services/coursesService';
import { examsService } from '../services/examsService';
import { uploadService } from '../services/uploadService';
import { parametersService } from '../services/parametersService';
import { computeService } from '../services/computeService';
import { PH } from '../constants/placeholders';
import type { CourseResponse, ExamResponse, ScoresUploadResponse, MappingUploadResponse, GraphUploadResponse, ComputeResponse } from '../services/types';
import { ApiError } from '../services/apiClient';

interface UploadWizardProps {
  onComplete: (courseId: string, examId: string) => void;
}

const steps = [
  { id: 1, name: 'Upload Scores', icon: Upload },
  { id: 2, name: 'Concept Mapping', icon: Network },
  { id: 3, name: 'Configure Parameters', icon: Settings },
  { id: 4, name: 'Compute', icon: Zap },
];

export const UploadWizard: React.FC<UploadWizardProps> = ({ onComplete }) => {
  const [currentStep, setCurrentStep] = useState(1);
  const [isProcessing, setIsProcessing] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Course / exam selection
  const [courses, setCourses] = useState<CourseResponse[]>([]);
  const [selectedCourseId, setSelectedCourseId] = useState<string>('');
  const [exams, setExams] = useState<ExamResponse[]>([]);
  const [selectedExamId, setSelectedExamId] = useState<string>('');
  const [newCourseName, setNewCourseName] = useState('');
  const [newExamName, setNewExamName] = useState('');

  // Step 1 — scores
  const [scoresFile, setScoresFile] = useState<File | null>(null);
  const [scoresResult, setScoresResult] = useState<ScoresUploadResponse | null>(null);

  // Step 2 — mapping
  const [mappingFile, setMappingFile] = useState<File | null>(null);
  const [mappingResult, setMappingResult] = useState<MappingUploadResponse | null>(null);

  // Step 3 — params
  const [alpha, setAlpha] = useState(0.6);
  const [beta, setBeta] = useState(0.3);
  const [gamma, setGamma] = useState(0.2);
  const [threshold, setThreshold] = useState(0.6);
  const [k, setK] = useState(4);

  // Step 4 — compute
  const [computeResult, setComputeResult] = useState<ComputeResponse | null>(null);

  useEffect(() => {
    coursesService.list().then(setCourses).catch(() => {});
  }, []);

  useEffect(() => {
    if (selectedCourseId) {
      examsService.list(selectedCourseId).then(setExams).catch(() => {});
    } else {
      setExams([]);
    }
  }, [selectedCourseId]);

  const ensureCourseAndExam = async (): Promise<{ courseId: string; examId: string }> => {
    let cId = selectedCourseId;
    if (!cId && newCourseName.trim()) {
      const c = await coursesService.create({ name: newCourseName.trim() });
      cId = c.id;
      setSelectedCourseId(cId);
    }
    if (!cId) throw new Error('Please select or create a course first.');

    let eId = selectedExamId;
    if (!eId && newExamName.trim()) {
      const e = await examsService.create(cId, { name: newExamName.trim() });
      eId = e.id;
      setSelectedExamId(eId);
    }
    if (!eId) throw new Error('Please select or create an exam first.');
    return { courseId: cId, examId: eId };
  };

  const handleUploadScores = async () => {
    if (!scoresFile) return;
    setError(null);
    setIsProcessing(true);
    try {
      const { examId } = await ensureCourseAndExam();
      const res = await uploadService.uploadScores(examId, scoresFile);
      if (res.status === 'error') {
        setError(res.errors.map(e => e.message).join('; '));
      } else {
        setScoresResult(res);
      }
    } catch (e) {
      setError(e instanceof ApiError ? e.detail : String(e));
    } finally {
      setIsProcessing(false);
    }
  };

  const handleUploadMapping = async () => {
    if (!mappingFile) return;
    setError(null);
    setIsProcessing(true);
    try {
      const { examId } = await ensureCourseAndExam();
      const res = await uploadService.uploadMapping(examId, mappingFile);
      if (res.status === 'error') {
        setError(res.errors.map(e => e.message).join('; '));
      } else {
        setMappingResult(res);
      }
    } catch (e) {
      setError(e instanceof ApiError ? e.detail : String(e));
    } finally {
      setIsProcessing(false);
    }
  };

  const handleSaveParams = async () => {
    setError(null);
    try {
      const { examId } = await ensureCourseAndExam();
      await parametersService.update(examId, { alpha, beta, gamma, threshold, k });
    } catch (e) {
      setError(e instanceof ApiError ? e.detail : String(e));
    }
  };

  const handleCompute = async () => {
    setError(null);
    setIsProcessing(true);
    try {
      const { courseId, examId } = await ensureCourseAndExam();
      await handleSaveParams();
      const res = await computeService.run(examId, { alpha, beta, gamma, threshold, k });
      setComputeResult(res);
      setTimeout(() => {
        onComplete(courseId, examId);
      }, 1500);
    } catch (e) {
      setError(e instanceof ApiError ? e.detail : String(e));
    } finally {
      setIsProcessing(false);
    }
  };

  const handleNext = () => {
    if (currentStep === 4) {
      handleCompute();
    } else {
      setCurrentStep(currentStep + 1);
    }
  };

  const canAdvance = (): boolean => {
    if (isProcessing) return false;
    if (currentStep === 1) return scoresResult !== null && scoresResult.status === 'success';
    if (currentStep === 2) return mappingResult !== null && mappingResult.status === 'success';
    return true;
  };

  return (
    <div className="min-h-screen bg-background p-8">
      <div className="max-w-5xl mx-auto space-y-8">
        <div className="space-y-2">
          <h1 className="text-3xl text-foreground">Data Import Wizard</h1>
          <p className="text-foreground-secondary">
            Upload assessment data and configure conceptual analysis
          </p>
        </div>

        {/* Step indicator */}
        <div className="flex items-center justify-between">
          {steps.map((step, idx) => (
            <React.Fragment key={step.id}>
              <div className="flex items-center gap-3">
                <motion.div
                  className={`w-10 h-10 rounded-full border-2 flex items-center justify-center ${
                    currentStep >= step.id
                      ? 'border-[#FFCB05] bg-[#FFCB05]/10'
                      : 'border-border bg-surface'
                  }`}
                  animate={{ scale: currentStep === step.id ? 1.1 : 1 }}
                >
                  {currentStep > step.id ? (
                    <CheckCircle2 className="w-5 h-5 text-[#FFCB05]" />
                  ) : (
                    <step.icon className={`w-5 h-5 ${currentStep >= step.id ? 'text-[#FFCB05]' : 'text-foreground-secondary'}`} />
                  )}
                </motion.div>
                <div>
                  <div className="text-xs text-foreground-secondary">Step {step.id}</div>
                  <div className={`text-sm ${currentStep >= step.id ? 'text-foreground' : 'text-foreground-secondary'}`}>
                    {step.name}
                  </div>
                </div>
              </div>
              {idx < steps.length - 1 && <div className="flex-1 h-px bg-border mx-4" />}
            </React.Fragment>
          ))}
        </div>

        {/* Error banner */}
        {error && (
          <div className="bg-critical/10 border border-critical/30 rounded-xl p-4 flex items-start gap-3">
            <AlertCircle className="w-5 h-5 text-critical mt-0.5 flex-shrink-0" />
            <div className="text-sm text-critical">{error}</div>
            <button onClick={() => setError(null)} className="ml-auto"><X className="w-4 h-4 text-critical" /></button>
          </div>
        )}

        {/* Content area */}
        <div className="bg-white border border-border rounded-xl p-8 min-h-[500px] shadow-sm">
          {/* Course / Exam selectors (always visible) */}
          <div className="flex items-center gap-3 mb-6 pb-6 border-b border-border">
            <div className="flex-1">
              <label className="text-xs text-foreground-secondary mb-1 block">Course</label>
              <select
                value={selectedCourseId}
                onChange={(e) => { setSelectedCourseId(e.target.value); setSelectedExamId(''); }}
                className="w-full bg-surface border border-border rounded-lg px-3 py-2 text-sm text-foreground focus:outline-none focus:ring-2 focus:ring-[#FFCB05]"
              >
                <option value="">{courses.length ? PH.SELECT_COURSE : PH.NO_DATA}</option>
                {courses.map(c => <option key={c.id} value={c.id}>{c.name}</option>)}
              </select>
              <input
                type="text"
                placeholder="...or create new course"
                value={newCourseName}
                onChange={(e) => { setNewCourseName(e.target.value); setSelectedCourseId(''); }}
                className="w-full mt-1 bg-surface border border-border rounded-lg px-3 py-1.5 text-xs text-foreground focus:outline-none focus:ring-2 focus:ring-[#FFCB05]"
              />
            </div>
            <div className="flex-1">
              <label className="text-xs text-foreground-secondary mb-1 block">Exam</label>
              <select
                value={selectedExamId}
                onChange={(e) => setSelectedExamId(e.target.value)}
                className="w-full bg-surface border border-border rounded-lg px-3 py-2 text-sm text-foreground focus:outline-none focus:ring-2 focus:ring-[#FFCB05]"
              >
                <option value="">{exams.length ? PH.SELECT_EXAM : PH.NO_DATA}</option>
                {exams.map(e => <option key={e.id} value={e.id}>{e.name}</option>)}
              </select>
              <input
                type="text"
                placeholder="...or create new exam"
                value={newExamName}
                onChange={(e) => { setNewExamName(e.target.value); setSelectedExamId(''); }}
                className="w-full mt-1 bg-surface border border-border rounded-lg px-3 py-1.5 text-xs text-foreground focus:outline-none focus:ring-2 focus:ring-[#FFCB05]"
              />
            </div>
          </div>

          <AnimatePresence mode="wait">
            {/* Step 1 - Upload Scores */}
            {currentStep === 1 && (
              <motion.div key="step1" initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -20 }} className="space-y-6">
                <div className="flex items-start justify-between">
                  <div>
                    <h2 className="text-xl text-foreground">Upload Assessment Scores</h2>
                    <p className="text-sm text-foreground-secondary mt-1">
                      CSV with columns: StudentID, QuestionID, Score (optional: MaxScore)
                    </p>
                  </div>
                  <button className="text-sm text-[#00274C] hover:text-[#FFCB05] flex items-center gap-1 transition-colors">
                    <Download className="w-4 h-4" /> Download Template
                  </button>
                </div>

                <div className="border-2 border-dashed border-border rounded-xl p-12 text-center cursor-pointer hover:border-[#FFCB05] hover:bg-surface/50 transition-all group relative">
                  <input
                    type="file"
                    accept=".csv,.tsv"
                    className="absolute inset-0 opacity-0 cursor-pointer"
                    onChange={(e) => { setScoresFile(e.target.files?.[0] ?? null); setScoresResult(null); }}
                  />
                  {scoresFile ? (
                    <div className="space-y-4">
                      <div className="inline-flex items-center justify-center w-16 h-16 rounded-2xl bg-[#FFCB05]/10">
                        <FileText className="w-8 h-8 text-[#00274C]" />
                      </div>
                      <div>
                        <div className="text-foreground font-medium">{scoresFile.name}</div>
                        <div className="text-sm text-foreground-secondary mt-1">{(scoresFile.size / 1024).toFixed(1)} KB</div>
                      </div>
                      <button onClick={(e) => { e.stopPropagation(); setScoresFile(null); setScoresResult(null); }} className="text-xs text-critical hover:underline">Remove file</button>
                    </div>
                  ) : (
                    <div className="space-y-4">
                      <div className="inline-flex items-center justify-center w-16 h-16 rounded-2xl bg-surface group-hover:bg-[#FFCB05]/10 transition-colors">
                        <Upload className="w-8 h-8 text-foreground-secondary group-hover:text-[#00274C] transition-colors" />
                      </div>
                      <div>
                        <div className="text-foreground group-hover:text-[#00274C] transition-colors font-medium">Click to upload or drag and drop</div>
                        <div className="text-sm text-foreground-secondary mt-1">CSV, TSV up to 10MB</div>
                      </div>
                    </div>
                  )}
                </div>

                {scoresFile && !scoresResult && (
                  <ConceptLensButton variant="primary" onClick={handleUploadScores} disabled={isProcessing}>
                    {isProcessing ? 'Uploading...' : 'Upload Scores'}
                  </ConceptLensButton>
                )}

                {scoresResult && scoresResult.status === 'success' && (
                  <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} className="bg-[#FFCB05]/5 border border-[#FFCB05]/20 rounded-xl p-4">
                    <div className="flex items-start gap-3">
                      <CheckCircle2 className="w-5 h-5 text-[#00274C] mt-0.5" />
                      <div className="space-y-2 flex-1">
                        <div className="text-sm text-foreground font-medium">Scores uploaded successfully</div>
                        <div className="grid grid-cols-2 gap-3 mt-3">
                          <div className="bg-white rounded-lg p-3 text-center">
                            <div className="text-lg text-[#00274C] font-medium">{scoresResult.row_count.toLocaleString()}</div>
                            <div className="text-xs text-foreground-secondary">Rows</div>
                          </div>
                          <div className="bg-white rounded-lg p-3 text-center">
                            <div className="text-lg text-[#00274C] font-medium">0</div>
                            <div className="text-xs text-foreground-secondary">Errors</div>
                          </div>
                        </div>
                      </div>
                    </div>
                  </motion.div>
                )}
              </motion.div>
            )}

            {/* Step 2 - Concept Mapping */}
            {currentStep === 2 && (
              <motion.div key="step2" initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -20 }} className="space-y-6">
                <h2 className="text-xl text-foreground">Upload Concept Mapping</h2>
                <p className="text-sm text-foreground-secondary">
                  CSV with columns: QuestionID, ConceptID (optional: Weight)
                </p>

                <div className="border-2 border-dashed border-border rounded-xl p-12 text-center cursor-pointer hover:border-[#FFCB05] hover:bg-surface/50 transition-all group relative">
                  <input
                    type="file"
                    accept=".csv,.tsv"
                    className="absolute inset-0 opacity-0 cursor-pointer"
                    onChange={(e) => { setMappingFile(e.target.files?.[0] ?? null); setMappingResult(null); }}
                  />
                  {mappingFile ? (
                    <div className="space-y-4">
                      <div className="inline-flex items-center justify-center w-16 h-16 rounded-2xl bg-[#FFCB05]/10">
                        <FileText className="w-8 h-8 text-[#00274C]" />
                      </div>
                      <div className="text-foreground font-medium">{mappingFile.name}</div>
                      <button onClick={(e) => { e.stopPropagation(); setMappingFile(null); setMappingResult(null); }} className="text-xs text-critical hover:underline">Remove</button>
                    </div>
                  ) : (
                    <div className="space-y-4">
                      <div className="inline-flex items-center justify-center w-16 h-16 rounded-2xl bg-surface group-hover:bg-[#FFCB05]/10 transition-colors">
                        <Network className="w-8 h-8 text-foreground-secondary group-hover:text-[#00274C] transition-colors" />
                      </div>
                      <div className="text-foreground font-medium">Click to upload mapping CSV</div>
                    </div>
                  )}
                </div>

                {mappingFile && !mappingResult && (
                  <ConceptLensButton variant="primary" onClick={handleUploadMapping} disabled={isProcessing}>
                    {isProcessing ? 'Uploading...' : 'Upload Mapping'}
                  </ConceptLensButton>
                )}

                {mappingResult && mappingResult.status === 'success' && (
                  <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} className="bg-[#FFCB05]/5 border border-[#FFCB05]/20 rounded-xl p-4">
                    <div className="flex items-center gap-2">
                      <CheckCircle2 className="w-4 h-4 text-[#00274C]" />
                      <span className="text-sm text-foreground">{mappingResult.concept_count} concepts mapped successfully</span>
                    </div>
                  </motion.div>
                )}
              </motion.div>
            )}

            {/* Step 3 - Configure Parameters */}
            {currentStep === 3 && (
              <motion.div key="step3" initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -20 }} className="space-y-6">
                <h2 className="text-xl text-foreground">Configure Analysis Parameters</h2>
                <p className="text-sm text-foreground-secondary">Set weights for readiness calculation algorithm</p>

                <div className="space-y-6">
                  {[
                    { label: 'Direct Mastery Weight (α)', value: alpha, set: setAlpha },
                    { label: 'Prerequisite Weight (β)', value: beta, set: setBeta },
                    { label: 'Downstream Weight (γ)', value: gamma, set: setGamma },
                    { label: 'Readiness Threshold', value: threshold, set: setThreshold },
                  ].map(({ label, value, set }) => (
                    <div key={label} className="space-y-3 bg-surface border border-border rounded-xl p-5">
                      <div className="flex items-center justify-between">
                        <label className="text-sm text-foreground font-medium">{label}</label>
                        <span className="text-sm text-[#00274C] font-mono bg-[#FFCB05]/10 px-3 py-1 rounded-lg">{value.toFixed(2)}</span>
                      </div>
                      <input type="range" min="0" max="1" step="0.05" value={value} onChange={(e) => set(Number(e.target.value))} className="w-full accent-[#FFCB05]" />
                    </div>
                  ))}
                  <div className="space-y-3 bg-surface border border-border rounded-xl p-5">
                    <div className="flex items-center justify-between">
                      <label className="text-sm text-foreground font-medium">Clusters (k)</label>
                      <span className="text-sm text-[#00274C] font-mono bg-[#FFCB05]/10 px-3 py-1 rounded-lg">{k}</span>
                    </div>
                    <input type="range" min="2" max="20" step="1" value={k} onChange={(e) => setK(Number(e.target.value))} className="w-full accent-[#FFCB05]" />
                  </div>
                </div>
              </motion.div>
            )}

            {/* Step 4 - Compute */}
            {currentStep === 4 && (
              <motion.div key="step4" initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -20 }} className="space-y-6 flex flex-col items-center justify-center min-h-[400px]">
                {computeResult ? (
                  <>
                    <CheckCircle2 className="w-16 h-16 text-[#FFCB05]" />
                    <h2 className="text-xl text-foreground text-center">Computation Complete</h2>
                    <div className="bg-surface border border-border rounded-xl p-6 space-y-4 w-full max-w-md">
                      <div className="flex items-center justify-between"><span className="text-foreground-secondary">Students</span><span className="text-foreground font-medium">{computeResult.students_processed}</span></div>
                      <div className="h-px bg-border" />
                      <div className="flex items-center justify-between"><span className="text-foreground-secondary">Concepts</span><span className="text-foreground font-medium">{computeResult.concepts_processed}</span></div>
                      <div className="h-px bg-border" />
                      <div className="flex items-center justify-between"><span className="text-foreground-secondary">Time</span><span className="text-foreground font-medium">{computeResult.time_ms.toFixed(0)} ms</span></div>
                    </div>
                  </>
                ) : !isProcessing ? (
                  <>
                    <div className="w-20 h-20 rounded-2xl bg-[#FFCB05]/10 flex items-center justify-center">
                      <Zap className="w-10 h-10 text-[#00274C]" />
                    </div>
                    <h2 className="text-xl text-foreground text-center">Ready to Compute</h2>
                    <p className="text-sm text-foreground-secondary text-center max-w-md">
                      All data validated. Click below to compute concept readiness scores and generate intervention recommendations.
                    </p>
                  </>
                ) : (
                  <>
                    <LoadingSpinner size={64} message="Computing readiness scores across dependency graph..." />
                    <h2 className="text-xl text-foreground text-center">Processing...</h2>
                  </>
                )}
              </motion.div>
            )}
          </AnimatePresence>
        </div>

        {/* Navigation */}
        <div className="flex items-center justify-between">
          <ConceptLensButton variant="subtle" onClick={() => currentStep > 1 && setCurrentStep(currentStep - 1)} disabled={currentStep === 1 || isProcessing}>
            Back
          </ConceptLensButton>
          <ConceptLensButton variant="primary" onClick={handleNext} disabled={!canAdvance()} className="flex items-center gap-2">
            {currentStep === 4 ? (isProcessing ? 'Computing...' : 'Compute & Continue') : 'Continue'}
            {!isProcessing && <ArrowRight className="w-4 h-4" />}
          </ConceptLensButton>
        </div>
      </div>
    </div>
  );
};
