import React, { useRef, useEffect, useCallback } from 'react';
import * as d3 from 'd3';
import type { ConceptNode } from '../data/mockData';

interface ConceptDAGProps {
  concepts: ConceptNode[];
  onNodeClick?: (node: ConceptNode) => void;
  selectedNodeId?: string | null;
}

interface SimNode extends d3.SimulationNodeDatum {
  id: string;
  name: string;
  readiness: number;
  depth: number;
  prerequisites: string[];
}

interface SimLink extends d3.SimulationLinkDatum<SimNode> {
  source: SimNode | string;
  target: SimNode | string;
}

const NODE_RADIUS = 28;

function readinessColor(r: number): string {
  if (r >= 0.7) return '#FFCB05';
  if (r >= 0.5) return '#F5B942';
  return '#E05A5A';
}

export const ConceptDAG: React.FC<ConceptDAGProps> = ({
  concepts,
  onNodeClick,
  selectedNodeId,
}) => {
  const containerRef = useRef<HTMLDivElement>(null);
  const svgRef = useRef<SVGSVGElement | null>(null);
  const simRef = useRef<d3.Simulation<SimNode, SimLink> | null>(null);

  const buildGraph = useCallback(() => {
    const container = containerRef.current;
    if (!container) return;

    const width = container.clientWidth;
    const height = container.clientHeight;

    d3.select(container).select('svg').remove();

    const svg = d3
      .select(container)
      .append('svg')
      .attr('width', width)
      .attr('height', height)
      .attr('viewBox', `0 0 ${width} ${height}`);

    svgRef.current = svg.node();

    // Arrow marker
    svg
      .append('defs')
      .append('marker')
      .attr('id', 'arrowhead')
      .attr('viewBox', '0 -5 10 10')
      .attr('refX', NODE_RADIUS + 10)
      .attr('refY', 0)
      .attr('markerWidth', 8)
      .attr('markerHeight', 8)
      .attr('orient', 'auto')
      .append('path')
      .attr('d', 'M0,-5L10,0L0,5')
      .attr('fill', '#DEE2E6');

    svg
      .select('defs')
      .append('marker')
      .attr('id', 'arrowhead-active')
      .attr('viewBox', '0 -5 10 10')
      .attr('refX', NODE_RADIUS + 10)
      .attr('refY', 0)
      .attr('markerWidth', 8)
      .attr('markerHeight', 8)
      .attr('orient', 'auto')
      .append('path')
      .attr('d', 'M0,-5L10,0L0,5')
      .attr('fill', '#FFCB05');

    // Grid background
    const gridDefs = svg.select('defs');
    gridDefs
      .append('pattern')
      .attr('id', 'dag-grid')
      .attr('width', 40)
      .attr('height', 40)
      .attr('patternUnits', 'userSpaceOnUse')
      .append('path')
      .attr('d', 'M 40 0 L 0 0 0 40')
      .attr('fill', 'none')
      .attr('stroke', '#F8F9FA')
      .attr('stroke-width', 1);

    const g = svg.append('g');

    g.append('rect')
      .attr('width', width * 3)
      .attr('height', height * 3)
      .attr('x', -width)
      .attr('y', -height)
      .attr('fill', 'url(#dag-grid)');

    // Zoom
    const zoom = d3
      .zoom<SVGSVGElement, unknown>()
      .scaleExtent([0.3, 3])
      .on('zoom', (event) => {
        g.attr('transform', event.transform);
      });

    svg.call(zoom);

    // Nodes and links data
    const nodes: SimNode[] = concepts.map((c) => ({
      id: c.id,
      name: c.name,
      readiness: c.readiness,
      depth: c.depth,
      prerequisites: c.prerequisites,
      x: c.x ?? width / 2,
      y: c.y ?? height / 2,
    }));

    const links: SimLink[] = [];
    concepts.forEach((c) => {
      c.prerequisites.forEach((preId) => {
        links.push({ source: preId, target: c.id });
      });
    });

    // Force simulation
    const simulation = d3
      .forceSimulation<SimNode>(nodes)
      .force(
        'link',
        d3
          .forceLink<SimNode, SimLink>(links)
          .id((d) => d.id)
          .distance(120)
          .strength(0.8)
      )
      .force('charge', d3.forceManyBody().strength(-400))
      .force('center', d3.forceCenter(width / 2, height / 2))
      .force(
        'y',
        d3
          .forceY<SimNode>()
          .y((d) => 80 + d.depth * 130)
          .strength(0.6)
      )
      .force('collision', d3.forceCollide(NODE_RADIUS + 20));

    simRef.current = simulation;

    // Links
    const linkSel = g
      .append('g')
      .attr('class', 'links')
      .selectAll('line')
      .data(links)
      .enter()
      .append('line')
      .attr('stroke', (d) => {
        const src = typeof d.source === 'string' ? d.source : d.source.id;
        const tgt = typeof d.target === 'string' ? d.target : d.target.id;
        return selectedNodeId && (src === selectedNodeId || tgt === selectedNodeId)
          ? '#FFCB05'
          : '#DEE2E6';
      })
      .attr('stroke-width', (d) => {
        const src = typeof d.source === 'string' ? d.source : d.source.id;
        const tgt = typeof d.target === 'string' ? d.target : d.target.id;
        return selectedNodeId && (src === selectedNodeId || tgt === selectedNodeId)
          ? 3
          : 1.5;
      })
      .attr('marker-end', (d) => {
        const src = typeof d.source === 'string' ? d.source : d.source.id;
        const tgt = typeof d.target === 'string' ? d.target : d.target.id;
        return selectedNodeId && (src === selectedNodeId || tgt === selectedNodeId)
          ? 'url(#arrowhead-active)'
          : 'url(#arrowhead)';
      });

    // Node groups
    const nodeSel = g
      .append('g')
      .attr('class', 'nodes')
      .selectAll<SVGGElement, SimNode>('g')
      .data(nodes)
      .enter()
      .append('g')
      .attr('cursor', 'pointer')
      .on('click', (_event, d) => {
        const orig = concepts.find((c) => c.id === d.id);
        if (orig && onNodeClick) onNodeClick(orig);
      })
      .call(
        d3
          .drag<SVGGElement, SimNode>()
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

    // Outer ring for selected
    nodeSel
      .append('circle')
      .attr('r', NODE_RADIUS + 5)
      .attr('fill', 'none')
      .attr('stroke', (d) => readinessColor(d.readiness))
      .attr('stroke-width', 2.5)
      .attr('opacity', (d) => (d.id === selectedNodeId ? 1 : 0));

    // Main circle
    nodeSel
      .append('circle')
      .attr('r', NODE_RADIUS)
      .attr('fill', '#FFFFFF')
      .attr('stroke', (d) => readinessColor(d.readiness))
      .attr('stroke-width', 2.5);

    // Inner fill
    nodeSel
      .append('circle')
      .attr('r', (d) => NODE_RADIUS * d.readiness)
      .attr('fill', (d) => readinessColor(d.readiness))
      .attr('opacity', 0.15);

    // Readiness text
    nodeSel
      .append('text')
      .attr('text-anchor', 'middle')
      .attr('dy', '0.35em')
      .attr('fill', (d) => readinessColor(d.readiness))
      .attr('font-size', '12px')
      .attr('font-weight', '600')
      .attr('font-family', 'system-ui, -apple-system, sans-serif')
      .text((d) => `${Math.round(d.readiness * 100)}%`);

    // Label
    nodeSel
      .append('text')
      .attr('text-anchor', 'middle')
      .attr('dy', NODE_RADIUS + 16)
      .attr('fill', '#00274C')
      .attr('font-size', '12px')
      .attr('font-weight', '500')
      .attr('font-family', 'system-ui, -apple-system, sans-serif')
      .text((d) => d.name);

    // Pulse animation for nodes below threshold
    nodeSel
      .filter((d) => d.readiness < 0.5)
      .select('circle:nth-child(2)')
      .each(function () {
        const el = d3.select(this);
        function pulse() {
          el.transition()
            .duration(1000)
            .attr('r', NODE_RADIUS + 3)
            .transition()
            .duration(1000)
            .attr('r', NODE_RADIUS)
            .on('end', pulse);
        }
        pulse();
      });

    // Tick
    simulation.on('tick', () => {
      linkSel
        .attr('x1', (d) => (d.source as SimNode).x!)
        .attr('y1', (d) => (d.source as SimNode).y!)
        .attr('x2', (d) => (d.target as SimNode).x!)
        .attr('y2', (d) => (d.target as SimNode).y!);

      nodeSel.attr('transform', (d) => `translate(${d.x},${d.y})`);
    });
  }, [concepts, onNodeClick, selectedNodeId]);

  useEffect(() => {
    buildGraph();
    return () => {
      simRef.current?.stop();
    };
  }, [buildGraph]);

  return (
    <div
      ref={containerRef}
      className="w-full h-full bg-white rounded-xl border border-border overflow-hidden shadow-sm"
    />
  );
};
