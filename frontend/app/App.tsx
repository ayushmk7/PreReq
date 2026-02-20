import React, { useState } from 'react';
import { LandingPage } from './pages/LandingPage';
import { UploadWizard } from './pages/UploadWizard';
import { InstructorDashboard } from './pages/InstructorDashboard';
import { RootCauseTrace } from './pages/RootCauseTrace';
import { StudentReport } from './pages/StudentReport';
import { Sidebar } from './components/Sidebar';
import { Chatbot } from './components/Chatbot';

type View = 'landing' | 'upload' | 'dashboard' | 'trace' | 'student';

export interface AppContext {
  courseId: string | null;
  examId: string | null;
  setCourseId: (id: string | null) => void;
  setExamId: (id: string | null) => void;
}

export const AppCtx = React.createContext<AppContext>({
  courseId: null,
  examId: null,
  setCourseId: () => {},
  setExamId: () => {},
});

export interface TraceConcept {
  id: string;
  label: string;
  readiness: number;
}

export default function App() {
  const [currentView, setCurrentView] = useState<View>('landing');
  const [selectedConcept, setSelectedConcept] = useState<TraceConcept | null>(null);
  const [courseId, setCourseId] = useState<string | null>(null);
  const [examId, setExamId] = useState<string | null>(null);

  const handleStart = () => {
    setCurrentView('upload');
  };

  const handleUploadComplete = (newCourseId: string, newExamId: string) => {
    setCourseId(newCourseId);
    setExamId(newExamId);
    setCurrentView('dashboard');
  };

  const handleConceptClick = (concept: TraceConcept) => {
    setSelectedConcept(concept);
    setCurrentView('trace');
  };

  const handleBackToDashboard = () => {
    setCurrentView('dashboard');
    setSelectedConcept(null);
  };

  const handleNavigate = (view: View) => {
    setCurrentView(view);
    if (view !== 'trace') {
      setSelectedConcept(null);
    }
  };

  return (
    <AppCtx.Provider value={{ courseId, examId, setCourseId, setExamId }}>
      <div className="min-h-screen bg-background">
        <Sidebar currentView={currentView} onNavigate={handleNavigate} />
        <div className="pl-20">
          {currentView === 'landing' && <LandingPage onStart={handleStart} />}
          {currentView === 'upload' && <UploadWizard onComplete={handleUploadComplete} />}
          {currentView === 'dashboard' && <InstructorDashboard onConceptClick={handleConceptClick} />}
          {currentView === 'trace' && selectedConcept && examId && (
            <RootCauseTrace concept={selectedConcept} examId={examId} onBack={handleBackToDashboard} />
          )}
          {currentView === 'student' && <StudentReport />}
        </div>
        <Chatbot examId={examId} />
      </div>
    </AppCtx.Provider>
  );
}
