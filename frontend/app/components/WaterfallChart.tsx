import React, { useRef, useEffect } from 'react';
import * as d3 from 'd3';
import type { WaterfallItem } from '../data/mockData';

interface WaterfallChartProps {
  data: WaterfallItem[];
}

export const WaterfallChart: React.FC<WaterfallChartProps> = ({ data }) => {
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const container = containerRef.current;
    if (!container || data.length === 0) return;

    d3.select(container).select('svg').remove();

    const margin = { top: 20, right: 30, bottom: 20, left: 130 };
    const width = container.clientWidth - margin.left - margin.right;
    const height = data.length * 52;

    const svg = d3
      .select(container)
      .append('svg')
      .attr('width', width + margin.left + margin.right)
      .attr('height', height + margin.top + margin.bottom)
      .append('g')
      .attr('transform', `translate(${margin.left},${margin.top})`);

    // Compute running totals
    let runningTotal = 0;
    const computed = data.map((item) => {
      const start = runningTotal;
      if (item.type !== 'total') {
        runningTotal += item.value;
      }
      return {
        ...item,
        start: item.type === 'total' ? 0 : Math.min(start, start + item.value),
        end: item.type === 'total' ? item.value : Math.max(start, start + item.value),
      };
    });

    const maxVal = d3.max(computed, (d) => Math.max(Math.abs(d.start), Math.abs(d.end))) ?? 1;

    const x = d3.scaleLinear().domain([0, maxVal * 1.15]).range([0, width]);

    const y = d3
      .scaleBand<number>()
      .domain(computed.map((_, i) => i))
      .range([0, height])
      .padding(0.3);

    const barColor = (type: string) => {
      if (type === 'total') return '#2ED3A6';
      if (type === 'positive') return '#6B8AFF';
      return '#E05A5A';
    };

    // Connector lines between bars
    computed.forEach((d, i) => {
      if (i < computed.length - 1 && d.type !== 'total') {
        svg
          .append('line')
          .attr('x1', x(d.end))
          .attr('y1', y(i)! + y.bandwidth())
          .attr('x2', x(d.end))
          .attr('y2', y(i + 1)!)
          .attr('stroke', '#DEE2E6')
          .attr('stroke-width', 1)
          .attr('stroke-dasharray', '3,3');
      }
    });

    // Bars
    const bars = svg
      .selectAll('.bar')
      .data(computed)
      .enter()
      .append('rect')
      .attr('class', 'bar')
      .attr('y', (_, i) => y(i)!)
      .attr('height', y.bandwidth())
      .attr('rx', 4)
      .attr('ry', 4)
      .attr('fill', (d) => barColor(d.type))
      .attr('opacity', (d) => (d.type === 'total' ? 1 : 0.85))
      .attr('x', (d) => x(d.start))
      .attr('width', 0);

    bars
      .transition()
      .duration(600)
      .delay((_, i) => i * 100)
      .attr('width', (d) => Math.max(x(d.end) - x(d.start), 2));

    // Labels (concept names)
    svg
      .selectAll('.label')
      .data(computed)
      .enter()
      .append('text')
      .attr('x', -8)
      .attr('y', (_, i) => y(i)! + y.bandwidth() / 2)
      .attr('dy', '0.35em')
      .attr('text-anchor', 'end')
      .attr('fill', '#00274C')
      .attr('font-size', '12px')
      .attr('font-family', 'system-ui, -apple-system, sans-serif')
      .text((d) => d.label);

    // Value labels inside bars
    svg
      .selectAll('.value')
      .data(computed)
      .enter()
      .append('text')
      .attr('x', (d) => x(d.start) + 8)
      .attr('y', (_, i) => y(i)! + y.bandwidth() / 2)
      .attr('dy', '0.35em')
      .attr('fill', '#FFFFFF')
      .attr('font-size', '11px')
      .attr('font-weight', '600')
      .attr('font-family', 'SF Mono, Monaco, monospace')
      .attr('opacity', 0)
      .text((d) => `${d.type === 'negative' ? '' : ''}${(d.value * 100).toFixed(0)}%`)
      .transition()
      .delay((_, i) => i * 100 + 300)
      .duration(300)
      .attr('opacity', 1);
  }, [data]);

  return (
    <div ref={containerRef} className="w-full" style={{ minHeight: data.length * 52 + 40 }} />
  );
};
