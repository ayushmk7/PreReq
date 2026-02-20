import React, { useRef, useEffect } from 'react';
import * as d3 from 'd3';
import type { ConceptNode } from '../data/mockData';

interface StudentConceptGraphProps {
  concepts: ConceptNode[];
  studentReadiness: Record<string, number>;
}

interface SNode extends d3.SimulationNodeDatum {
  id: string;
  name: string;
  readiness: number;
  depth: number;
}

function readinessColor(r: number): string {
  if (r >= 0.7) return '#FFCB05';
  if (r >= 0.5) return '#F5B942';
  return '#E05A5A';
}

export const StudentConceptGraph: React.FC<StudentConceptGraphProps> = ({
  concepts,
  studentReadiness,
}) => {
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const container = containerRef.current;
    if (!container) return;

    d3.select(container).select('svg').remove();

    const width = container.clientWidth;
    const height = container.clientHeight || 380;

    const svg = d3
      .select(container)
      .append('svg')
      .attr('width', width)
      .attr('height', height);

    const g = svg.append('g');

    const zoom = d3
      .zoom<SVGSVGElement, unknown>()
      .scaleExtent([0.4, 3])
      .on('zoom', (event) => g.attr('transform', event.transform));

    svg.call(zoom);

    const nodes: SNode[] = concepts.map((c) => ({
      id: c.id,
      name: c.name,
      readiness: studentReadiness[c.id] ?? c.readiness,
      depth: c.depth,
    }));

    const links: { source: string; target: string }[] = [];
    concepts.forEach((c) => {
      c.prerequisites.forEach((preId) => {
        links.push({ source: preId, target: c.id });
      });
    });

    const simulation = d3
      .forceSimulation<SNode>(nodes)
      .force(
        'link',
        d3
          .forceLink(links)
          .id((d: any) => d.id)
          .distance(90)
          .strength(0.7)
      )
      .force('charge', d3.forceManyBody().strength(-300))
      .force('center', d3.forceCenter(width / 2, height / 2))
      .force(
        'radial',
        d3.forceRadial<SNode>(
          (d) => 40 + d.depth * 60,
          width / 2,
          height / 2
        ).strength(0.4)
      )
      .force('collision', d3.forceCollide(36));

    // Links
    const linkSel = g
      .append('g')
      .selectAll('line')
      .data(links)
      .enter()
      .append('line')
      .attr('stroke', '#DEE2E6')
      .attr('stroke-width', 1.5)
      .attr('opacity', 0.6);

    // Tooltip
    const tooltip = d3
      .select(container)
      .append('div')
      .style('position', 'absolute')
      .style('pointer-events', 'none')
      .style('background', '#00274C')
      .style('color', '#fff')
      .style('padding', '6px 10px')
      .style('border-radius', '8px')
      .style('font-size', '12px')
      .style('font-family', 'system-ui, -apple-system, sans-serif')
      .style('opacity', 0)
      .style('white-space', 'nowrap')
      .style('z-index', '10');

    // Node groups
    const nodeSel = g
      .append('g')
      .selectAll<SVGGElement, SNode>('g')
      .data(nodes)
      .enter()
      .append('g')
      .attr('cursor', 'pointer')
      .on('mouseenter', (event, d) => {
        tooltip
          .html(`<strong>${d.name}</strong><br/>Readiness: ${Math.round(d.readiness * 100)}%`)
          .style('left', `${event.offsetX + 12}px`)
          .style('top', `${event.offsetY - 10}px`)
          .transition()
          .duration(150)
          .style('opacity', 1);
      })
      .on('mousemove', (event) => {
        tooltip
          .style('left', `${event.offsetX + 12}px`)
          .style('top', `${event.offsetY - 10}px`);
      })
      .on('mouseleave', () => {
        tooltip.transition().duration(150).style('opacity', 0);
      })
      .call(
        d3
          .drag<SVGGElement, SNode>()
          .on('start', (event, d) => {
            if (!event.active) simulation.alphaTarget(0.3).restart();
            d.fx = d.x;
            d.fy = d.y;
          })
          .on('drag', (event, d) => {
            d.fx = event.x;
            d.fy = event.y;
          })
          .on('end', (event, d) => {
            if (!event.active) simulation.alphaTarget(0);
            d.fx = null;
            d.fy = null;
          })
      );

    // Node circle
    nodeSel
      .append('circle')
      .attr('r', 26)
      .attr('fill', '#FFFFFF')
      .attr('stroke', (d) => readinessColor(d.readiness))
      .attr('stroke-width', 2.5);

    // Inner fill
    nodeSel
      .append('circle')
      .attr('r', (d) => 26 * d.readiness)
      .attr('fill', (d) => readinessColor(d.readiness))
      .attr('opacity', 0.15);

    // Percentage text
    nodeSel
      .append('text')
      .attr('text-anchor', 'middle')
      .attr('dy', '0.35em')
      .attr('fill', (d) => readinessColor(d.readiness))
      .attr('font-size', '11px')
      .attr('font-weight', '600')
      .attr('font-family', 'system-ui')
      .text((d) => `${Math.round(d.readiness * 100)}%`);

    // Name label
    nodeSel
      .append('text')
      .attr('text-anchor', 'middle')
      .attr('dy', 42)
      .attr('fill', '#00274C')
      .attr('font-size', '11px')
      .attr('font-family', 'system-ui')
      .text((d) => d.name);

    simulation.on('tick', () => {
      linkSel
        .attr('x1', (d: any) => d.source.x)
        .attr('y1', (d: any) => d.source.y)
        .attr('x2', (d: any) => d.target.x)
        .attr('y2', (d: any) => d.target.y);
      nodeSel.attr('transform', (d) => `translate(${d.x},${d.y})`);
    });

    return () => {
      simulation.stop();
      tooltip.remove();
    };
  }, [concepts, studentReadiness]);

  return (
    <div ref={containerRef} className="w-full h-full relative" style={{ minHeight: 380 }} />
  );
};
