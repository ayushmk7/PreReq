import React from 'react';
import { Users, TrendingUp, BookOpen, GraduationCap } from 'lucide-react';
import { PH } from '../constants/placeholders';
import type { CourseResponse, ExamResponse } from '../services/types';

interface InstructorTaskBarProps {
  pageTitle?: string;
  courses: CourseResponse[];
  exams: ExamResponse[];
  courseId: string | null;
  examId: string | null;
  onCourseChange: (id: string | null) => void;
  onExamChange: (id: string | null) => void;
  studentCount?: number;
  conceptCount?: number;
}

const selectClass =
  "bg-surface border border-border rounded-lg px-4 py-2 text-sm text-foreground appearance-none bg-[length:16px_16px] bg-[position:right_12px_center] bg-no-repeat bg-[url('data:image/svg+xml;charset=utf-8,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20width%3D%2216%22%20height%3D%2216%22%20viewBox%3D%220%200%2024%2024%22%20fill%3D%22none%22%20stroke%3D%22%2364748b%22%20stroke-width%3D%222%22%20stroke-linecap%3D%22round%22%20stroke-linejoin%3D%22round%22%3E%3Cpath%20d%3D%22m6%209%206%206%206-6%22%2F%3E%3C%2Fsvg%3E')] focus:outline-none focus:ring-2 focus:ring-[#FFCB05] pr-10 min-w-[180px]";

export const InstructorTaskBar: React.FC<InstructorTaskBarProps> = ({
  pageTitle,
  courses,
  exams,
  courseId,
  examId,
  onCourseChange,
  onExamChange,
  studentCount,
  conceptCount,
}) => {
  return (
    <div className="border-b border-border bg-white">
      <div className="px-8 py-3 flex items-center">
        {/* Page title — fixed width left column */}
        {pageTitle && (
          <h1 className="text-lg font-semibold text-[#00274C] w-[120px] flex-shrink-0">{pageTitle}</h1>
        )}

        {/* Selectors — centered, evenly spaced */}
        <div className="flex items-center gap-5 flex-1">
          <div className="flex items-center gap-2">
            <GraduationCap className="w-4 h-4 text-foreground-secondary flex-shrink-0" />
            <select
              value={courseId ?? ''}
              onChange={(e) => { onCourseChange(e.target.value || null); onExamChange(null); }}
              className={selectClass}
            >
              <option value="">{courses.length ? PH.SELECT_COURSE : PH.NO_DATA}</option>
              {courses.map(c => <option key={c.id} value={c.id}>{c.name}</option>)}
            </select>
          </div>

          <div className="flex items-center gap-2">
            <BookOpen className="w-4 h-4 text-foreground-secondary flex-shrink-0" />
            <select
              value={examId ?? ''}
              onChange={(e) => onExamChange(e.target.value || null)}
              className={selectClass}
            >
              <option value="">{PH.SELECT_EXAM}</option>
              {exams.map(e => <option key={e.id} value={e.id}>{e.name}</option>)}
            </select>
          </div>
        </div>

        {/* Stats — right-aligned, fixed spacing */}
        <div className="flex items-center gap-5 flex-shrink-0">
          {studentCount !== undefined && (
            <div className="flex items-center gap-2">
              <Users className="w-4 h-4 text-foreground-secondary flex-shrink-0" />
              <span className="text-sm text-foreground whitespace-nowrap">{studentCount} students</span>
            </div>
          )}
          {conceptCount !== undefined && (
            <div className="flex items-center gap-2">
              <TrendingUp className="w-4 h-4 text-foreground-secondary flex-shrink-0" />
              <span className="text-sm text-foreground whitespace-nowrap">{conceptCount} concepts</span>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
