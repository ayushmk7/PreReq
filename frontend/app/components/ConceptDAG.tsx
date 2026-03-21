import React, { useRef, useEffect, useCallback, useState } from 'react';
import * as d3 from 'd3';
import { Loader2, X } from 'lucide-react';
import type { GraphRetrieveNode, GraphRetrieveEdge } from '../services/types';
import { graphService } from '../services/graphService';

interface ConceptDAGProps {
  examId?: string | null;
  concepts?: Array<{ id: string; name: string; readiness: number; depth: number; prerequisites: string[] }>;
  onNodeClick?: (node: { id: string; name: string; readiness: number; depth: number; prerequisites: string[] }) => void;
  selectedNodeId?: string | null;
}

interface SimNode extends d3.SimulationNodeDatum {
  id: string;
  label: string;
  readiness: number | null;
  isCsvObserved: boolean;
  depth: number;
  expanded: boolean;
}

interface SimLink extends d3.SimulationLinkDatum<SimNode> {
  source: SimNode | string;
  target: SimNode | string;
  weight: number;
}

interface ExpandedTopicsInfo {
  parentLabel: string;
  topics: Array<{ id: string; label: string }>;
}

const NODE_RADIUS = 28;

function readinessColor(r: number | null, observed: boolean): string {
  if (!observed || r === null) return '#B0BEC5';
  if (r >= 0.7) return '#FFCB05';
  if (r >= 0.5) return '#56B4E9';
  return '#D55E00';
}

export const ConceptDAG: React.FC<ConceptDAGProps> = ({
  examId,
  concepts: legacyConcepts,
  onNodeClick,
  selectedNodeId,
}) => {
  const containerRef = useRef<HTMLDivElement>(null);
  const svgRef = useRef<SVGSVGElement | null>(null);
  const simRef = useRef<d3.Simulation<SimNode, SimLink> | null>(null);

  const [graphNodes, setGraphNodes] = useState<GraphRetrieveNode[]>([]);
  const [graphEdges, setGraphEdges] = useState<GraphRetrieveEdge[]>([]);
  const [expandingNode, setExpandingNode] = useState<string | null>(null);
  const [expandedTopics, setExpandedTopics] = useState<ExpandedTopicsInfo | null>(null);
  const [loaded, setLoaded] = useState(false);

  useEffect(() => {
    if (examId) {
      graphService.getGraph(examId)
        .then((resp) => {
          if (resp.status === 'ok' && resp.nodes.length > 0) {
            setGraphNodes(resp.nodes);
            setGraphEdges(resp.edges);
          } else if (legacyConcepts && legacyConcepts.length > 0) {
            fallbackToLegacy();
          }
        })
        .catch(() => { fallbackToLegacy(); })
        .finally(() => setLoaded(true));
    } else {
      fallbackToLegacy();
      setLoaded(true);
    }
  }, [examId]);

  const fallbackToLegacy = () => {
    if (!legacyConcepts) return;
    const nodes: GraphRetrieveNode[] = legacyConcepts.map((c) => ({
      id: c.id,
      label: c.name,
      readiness: c.readiness,
      is_csv_observed: true,
      depth: c.depth,
    }));
    const edges: GraphRetrieveEdge[] = [];
    for (const c of legacyConcepts) {
      for (const pid of c.prerequisites) {
        edges.push({ source: pid, target: c.id, weight: 0.5 });
      }
    }
    setGraphNodes(nodes);
    setGraphEdges(edges);
  };

  const handleExpandNode = useCallback(async (nodeId: string) => {
    if (!examId || expandingNode) return;
    setExpandingNode(nodeId);
    try {
      const resp = await graphService.expandNode(examId, { concept_id: nodeId, max_depth: 3 });
      if (resp.status === 'ok') {
        const parentNode = graphNodes.find((n) => n.id === nodeId);
        setGraphNodes((prev) => {
          const existingIds = new Set(prev.map((n) => n.id));
          const newOnes = resp.new_nodes.filter((n) => !existingIds.has(n.id));
          const updated = prev.map((n) => n.id === nodeId ? { ...n } : n);
          return [...updated, ...newOnes];
        });
        setGraphEdges((prev) => {
          const existing = new Set(prev.map((e) => `${e.source}->${e.target}`));
          const newOnes = resp.new_edges.filter((e) => !existing.has(`${e.source}->${e.target}`));
          return [...prev, ...newOnes];
        });
        if (resp.new_nodes.length > 0) {
          setExpandedTopics({
            parentLabel: parentNode?.label ?? nodeId,
            topics: resp.new_nodes.map((n) => ({ id: n.id, label: n.label })),
          });
        }
      }
    } catch {
      // AI expansion unavailable
    } finally {
      setExpandingNode(null);
    }
  }, [examId, expandingNode, graphNodes]);

  const buildGraph = useCallback(() => {
    const container = containerRef.current;
    if (!container || graphNodes.length === 0) return;

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

    svg.append('defs').append('marker')
      .attr('id', 'arrowhead').attr('viewBox', '0 -5 10 10')
      .attr('refX', NODE_RADIUS + 10).attr('refY', 0)
      .attr('markerWidth', 8).attr('markerHeight', 8).attr('orient', 'auto')
      .append('path').attr('d', 'M0,-5L10,0L0,5').attr('fill', '#64748b');

    svg.select('defs').append('marker')
      .attr('id', 'arrowhead-active').attr('viewBox', '0 -5 10 10')
      .attr('refX', NODE_RADIUS + 10).attr('refY', 0)
      .attr('markerWidth', 8).attr('markerHeight', 8).attr('orient', 'auto')
      .append('path').attr('d', 'M0,-5L10,0L0,5').attr('fill', '#FFCB05');

    const g = svg.append('g');

    const zoom = d3.zoom<SVGSVGElement, unknown>()
      .scaleExtent([0.2, 4])
      .on('zoom', (event) => { g.attr('transform', event.transform); });
    svg.call(zoom);

    const expandedSet = new Set<string>();
    const nodes: SimNode[] = graphNodes.map((n) => ({
      id: n.id,
      label: n.label,
      readiness: n.readiness ?? null,
      isCsvObserved: n.is_csv_observed,
      depth: n.depth,
      expanded: expandedSet.has(n.id),
      x: width / 2 + (Math.random() - 0.5) * 200,
      y: 80 + n.depth * 130 + (Math.random() - 0.5) * 40,
    }));

    const nodeMap = new Map(nodes.map((n) => [n.id, n]));
    const links: SimLink[] = graphEdges
      .filter((e) => nodeMap.has(e.source) && nodeMap.has(e.target))
      .map((e) => ({ source: e.source, target: e.target, weight: e.weight }));

    const simulation = d3.forceSimulation<SimNode>(nodes)
      .force('link', d3.forceLink<SimNode, SimLink>(links).id((d) => d.id).distance(100).strength(0.7))
      .force('charge', d3.forceManyBody().strength(-350))
      .force('center', d3.forceCenter(width / 2, height / 2))
      .force('y', d3.forceY<SimNode>().y((d) => 80 + d.depth * 120).strength(0.4))
      .force('collision', d3.forceCollide(NODE_RADIUS + 18));

    simRef.current = simulation;

    const linkSel = g.append('g').attr('class', 'links').selectAll('line')
      .data(links).enter().append('line')
      .attr('stroke', (d) => {
        const src = typeof d.source === 'string' ? d.source : d.source.id;
        const tgt = typeof d.target === 'string' ? d.target : d.target.id;
        return selectedNodeId && (src === selectedNodeId || tgt === selectedNodeId) ? '#FFCB05' : '#64748b';
      })
      .attr('stroke-width', (d) => {
        const src = typeof d.source === 'string' ? d.source : d.source.id;
        const tgt = typeof d.target === 'string' ? d.target : d.target.id;
        return selectedNodeId && (src === selectedNodeId || tgt === selectedNodeId) ? 3 : 2;
      })
      .attr('stroke-opacity', 0.7)
      .attr('marker-end', (d) => {
        const src = typeof d.source === 'string' ? d.source : d.source.id;
        const tgt = typeof d.target === 'string' ? d.target : d.target.id;
        return selectedNodeId && (src === selectedNodeId || tgt === selectedNodeId)
          ? 'url(#arrowhead-active)' : 'url(#arrowhead)';
      });

    const nodeSel = g.append('g').attr('class', 'nodes')
      .selectAll<SVGGElement, SimNode>('g')
      .data(nodes).enter().append('g')
      .attr('cursor', 'pointer')
      .on('click', (_event, d) => {
        if (onNodeClick) {
          const orig = legacyConcepts?.find((c) => c.id === d.id);
          if (orig) onNodeClick(orig);
        }
      })
      .on('dblclick', (_event, d) => {
        handleExpandNode(d.id);
      })
      .call(
        d3.drag<SVGGElement, SimNode>()
          .on('start', (event, d) => { if (!event.active) simulation.alphaTarget(0.3).restart(); d.fx = d.x; d.fy = d.y; })
          .on('drag', (event, d) => { d.fx = event.x; d.fy = event.y; })
          .on('end', (event, d) => { if (!event.active) simulation.alphaTarget(0); d.fx = null; d.fy = null; })
      );

    // Outer glow ring for selected node
    nodeSel.append('circle')
      .attr('r', NODE_RADIUS + 5)
      .attr('fill', 'none')
      .attr('stroke', (d) => readinessColor(d.readiness, d.isCsvObserved))
      .attr('stroke-width', 2.5)
      .attr('opacity', (d) => (d.id === selectedNodeId ? 1 : 0));

    // Main circle
    nodeSel.append('circle')
      .attr('r', NODE_RADIUS)
      .attr('fill', '#FFFFFF')
      .attr('stroke', (d) => readinessColor(d.readiness, d.isCsvObserved))
      .attr('stroke-width', 2.5);

    // Inner readiness fill (only for observed concepts)
    nodeSel.filter((d) => d.isCsvObserved && d.readiness !== null)
      .append('circle')
      .attr('r', (d) => NODE_RADIUS * (d.readiness ?? 0))
      .attr('fill', (d) => readinessColor(d.readiness, d.isCsvObserved))
      .attr('opacity', 0.15);

    // Readiness label (only for observed)
    nodeSel.filter((d) => d.isCsvObserved && d.readiness !== null)
      .append('text')
      .attr('text-anchor', 'middle').attr('dy', '0.35em')
      .attr('fill', (d) => readinessColor(d.readiness, d.isCsvObserved))
      .attr('font-size', '12px').attr('font-weight', '600')
      .attr('font-family', 'system-ui, -apple-system, sans-serif')
      .text((d) => `${Math.round((d.readiness ?? 0) * 100)}%`);

    // Expand icon for non-observed (AI-expanded) nodes that have no readiness
    nodeSel.filter((d) => !d.isCsvObserved)
      .append('text')
      .attr('text-anchor', 'middle').attr('dy', '0.35em')
      .attr('fill', '#9BA7B4')
      .attr('font-size', '10px').attr('font-weight', '500')
      .attr('font-family', 'system-ui')
      .text('...');

    // Node label below
    nodeSel.append('text')
      .attr('text-anchor', 'middle').attr('dy', NODE_RADIUS + 16)
      .attr('fill', (d) => d.isCsvObserved ? '#00274C' : '#78909C')
      .attr('font-size', '11px').attr('font-weight', '500')
      .attr('font-family', 'system-ui, -apple-system, sans-serif')
      .text((d) => d.label.length > 18 ? d.label.slice(0, 16) + '...' : d.label);

    // Pulse for low-readiness observed nodes
    nodeSel.filter((d) => d.isCsvObserved && (d.readiness ?? 1) < 0.5)
      .select('circle:nth-child(2)')
      .each(function () {
        const el = d3.select(this);
        function pulse() {
          el.transition().duration(1000).attr('r', NODE_RADIUS + 3)
            .transition().duration(1000).attr('r', NODE_RADIUS).on('end', pulse);
        }
        pulse();
      });

    simulation.on('tick', () => {
      linkSel
        .attr('x1', (d) => (d.source as SimNode).x!)
        .attr('y1', (d) => (d.source as SimNode).y!)
        .attr('x2', (d) => (d.target as SimNode).x!)
        .attr('y2', (d) => (d.target as SimNode).y!);
      nodeSel.attr('transform', (d) => `translate(${d.x},${d.y})`);
    });
  }, [graphNodes, graphEdges, onNodeClick, selectedNodeId, handleExpandNode, legacyConcepts]);

  useEffect(() => {
    buildGraph();
    return () => { simRef.current?.stop(); };
  }, [buildGraph]);

  if (!loaded && examId) {
    return (
      <div className="w-full h-full flex items-center justify-center">
        <Loader2 className="w-6 h-6 animate-spin text-foreground-secondary" />
      </div>
    );
  }

  return (
    <div className="relative w-full h-full">
      <div ref={containerRef} className="w-full h-full bg-white rounded-xl border border-border overflow-hidden shadow-sm" />
      {expandingNode && (
        <div className="absolute top-3 right-3 flex items-center gap-2 bg-white/90 border border-border rounded-lg px-3 py-1.5 text-xs text-foreground-secondary shadow-sm">
          <Loader2 className="w-3.5 h-3.5 animate-spin" />
          Expanding {expandingNode}...
        </div>
      )}
      {expandedTopics && (
        <div className="absolute top-3 right-3 bg-white border border-border rounded-xl shadow-lg p-4 max-w-[260px] max-h-[320px] overflow-y-auto z-10">
          <div className="flex items-center justify-between mb-3">
            <h3 className="text-sm font-semibold text-[#00274C]">Subtopics of {expandedTopics.parentLabel}</h3>
            <button onClick={() => setExpandedTopics(null)} className="text-foreground-secondary hover:text-foreground">
              <X className="w-4 h-4" />
            </button>
          </div>
          <ul className="space-y-1.5">
            {expandedTopics.topics.map((t) => (
              <li key={t.id} className="flex items-center gap-2 text-xs text-foreground">
                <span className="w-1.5 h-1.5 rounded-full bg-[#B0BEC5] flex-shrink-0" />
                {t.label}
              </li>
            ))}
          </ul>
        </div>
      )}
      <div className="absolute bottom-3 left-3 flex items-center gap-3 text-[10px] text-foreground-secondary bg-white/80 rounded-lg px-3 py-2 border border-border">
        <span className="flex items-center gap-1"><span className="w-2 h-2 rounded-full bg-[#FFCB05]" /> High</span>
        <span className="flex items-center gap-1"><span className="w-2 h-2 rounded-full bg-[#56B4E9]" /> Medium</span>
        <span className="flex items-center gap-1"><span className="w-2 h-2 rounded-full bg-[#D55E00]" /> Low</span>
        <span className="flex items-center gap-1"><span className="w-2 h-2 rounded-full bg-[#B0BEC5]" /> AI-expanded</span>
        <span className="ml-2 opacity-60">Double-click to expand</span>
      </div>
    </div>
  );
};
