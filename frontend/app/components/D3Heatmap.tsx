import React, { useRef, useEffect } from 'react';
import * as d3 from 'd3';
import type { ConceptNode, Student } from '../data/mockData';

interface D3HeatmapProps {
  concepts: ConceptNode[];
  students: Student[];
  onConceptClick?: (concept: ConceptNode) => void;
}

function readinessColor(r: number): string {
  if (r >= 0.7) return 'rgba(255, 203, 5, 0.85)';
  if (r >= 0.5) return 'rgba(245, 185, 66, 0.85)';
  return 'rgba(224, 90, 90, 0.85)';
}

export const D3Heatmap: React.FC<D3HeatmapProps> = ({
  concepts,
  students,
  onConceptClick,
}) => {
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const container = containerRef.current;
    if (!container) return;

    d3.select(container).select('svg').remove();
    d3.select(container).selectAll('.heatmap-tooltip').remove();

    const displayStudents = students.slice(0, 20);
    const displayConcepts = concepts.slice(0, 10);

    const margin = { top: 30, right: 10, bottom: 10, left: 110 };
    const cellSize = 32;
    const gap = 2;

    const width = margin.left + margin.right + displayStudents.length * (cellSize + gap);
    const height = margin.top + margin.bottom + displayConcepts.length * (cellSize + gap);

    const svg = d3
      .select(container)
      .append('svg')
      .attr('width', width)
      .attr('height', height);

    // Tooltip
    const tooltip = d3
      .select(container)
      .append('div')
      .attr('class', 'heatmap-tooltip')
      .style('position', 'absolute')
      .style('pointer-events', 'none')
      .style('background', '#00274C')
      .style('color', '#fff')
      .style('padding', '8px 12px')
      .style('border-radius', '8px')
      .style('font-size', '12px')
      .style('font-family', 'system-ui, -apple-system, sans-serif')
      .style('opacity', 0)
      .style('z-index', '20')
      .style('white-space', 'nowrap');

    // Column headers (student labels)
    svg
      .append('g')
      .selectAll('text')
      .data(displayStudents)
      .enter()
      .append('text')
      .attr('x', (_, i) => margin.left + i * (cellSize + gap) + cellSize / 2)
      .attr('y', margin.top - 8)
      .attr('text-anchor', 'middle')
      .attr('fill', '#5C6B7D')
      .attr('font-size', '10px')
      .attr('font-family', 'system-ui')
      .text((_, i) => `S${i + 1}`);

    // Row labels (concept names)
    svg
      .append('g')
      .selectAll('text')
      .data(displayConcepts)
      .enter()
      .append('text')
      .attr('x', margin.left - 8)
      .attr('y', (_, i) => margin.top + i * (cellSize + gap) + cellSize / 2)
      .attr('dy', '0.35em')
      .attr('text-anchor', 'end')
      .attr('fill', '#5C6B7D')
      .attr('font-size', '12px')
      .attr('font-family', 'system-ui')
      .text((d) => d.name);

    // Cells
    const cellData: {
      concept: ConceptNode;
      student: Student;
      value: number;
      row: number;
      col: number;
    }[] = [];

    displayConcepts.forEach((concept, row) => {
      displayStudents.forEach((student, col) => {
        cellData.push({
          concept,
          student,
          value: student.conceptReadiness[concept.id] ?? 0,
          row,
          col,
        });
      });
    });

    svg
      .append('g')
      .selectAll('rect')
      .data(cellData)
      .enter()
      .append('rect')
      .attr('x', (d) => margin.left + d.col * (cellSize + gap))
      .attr('y', (d) => margin.top + d.row * (cellSize + gap))
      .attr('width', cellSize)
      .attr('height', cellSize)
      .attr('rx', 4)
      .attr('ry', 4)
      .attr('fill', (d) => readinessColor(d.value))
      .attr('cursor', 'pointer')
      .attr('opacity', 0)
      .on('mouseenter', function (event, d) {
        d3.select(this)
          .transition()
          .duration(100)
          .attr('stroke', '#00274C')
          .attr('stroke-width', 2);

        tooltip
          .html(
            `<strong>${d.concept.name}</strong><br/>` +
              `${d.student.name}<br/>` +
              `Readiness: ${Math.round(d.value * 100)}%`
          )
          .style('left', `${event.offsetX + 14}px`)
          .style('top', `${event.offsetY - 14}px`)
          .transition()
          .duration(100)
          .style('opacity', 1);
      })
      .on('mousemove', function (event) {
        tooltip
          .style('left', `${event.offsetX + 14}px`)
          .style('top', `${event.offsetY - 14}px`);
      })
      .on('mouseleave', function () {
        d3.select(this)
          .transition()
          .duration(100)
          .attr('stroke', 'none');
        tooltip.transition().duration(100).style('opacity', 0);
      })
      .on('click', (_, d) => {
        if (onConceptClick) onConceptClick(d.concept);
      })
      .transition()
      .duration(400)
      .delay((d) => (d.row + d.col) * 8)
      .attr('opacity', 1);

    // Value text inside cells
    svg
      .append('g')
      .selectAll('text')
      .data(cellData)
      .enter()
      .append('text')
      .attr('x', (d) => margin.left + d.col * (cellSize + gap) + cellSize / 2)
      .attr('y', (d) => margin.top + d.row * (cellSize + gap) + cellSize / 2)
      .attr('dy', '0.35em')
      .attr('text-anchor', 'middle')
      .attr('fill', '#FFFFFF')
      .attr('font-size', '10px')
      .attr('font-weight', '500')
      .attr('font-family', 'SF Mono, Monaco, monospace')
      .attr('pointer-events', 'none')
      .attr('opacity', 0)
      .text((d) => Math.round(d.value * 100))
      .transition()
      .duration(400)
      .delay((d) => (d.row + d.col) * 8 + 200)
      .attr('opacity', 1);

    return () => {
      tooltip.remove();
    };
  }, [concepts, students, onConceptClick]);

  return (
    <div ref={containerRef} className="w-full overflow-x-auto relative" style={{ minHeight: 380 }} />
  );
};
