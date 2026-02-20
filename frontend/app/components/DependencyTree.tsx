import React, { useRef, useEffect } from 'react';
import * as d3 from 'd3';
import type { ConceptNode } from '../data/mockData';

interface DependencyTreeProps {
  concept: ConceptNode;
  allConcepts: ConceptNode[];
}

interface TreeNode {
  id: string;
  name: string;
  readiness: number;
  children: TreeNode[];
}

function readinessColor(r: number): string {
  if (r >= 0.7) return '#FFCB05';
  if (r >= 0.5) return '#F5B942';
  return '#E05A5A';
}

function buildTree(concept: ConceptNode, allConcepts: ConceptNode[], visited: Set<string> = new Set()): TreeNode {
  visited.add(concept.id);
  const children = concept.prerequisites
    .map((pid) => allConcepts.find((c) => c.id === pid))
    .filter((c): c is ConceptNode => c != null && !visited.has(c.id))
    .map((c) => buildTree(c, allConcepts, new Set(visited)));

  return {
    id: concept.id,
    name: concept.name,
    readiness: concept.readiness,
    children,
  };
}

export const DependencyTree: React.FC<DependencyTreeProps> = ({ concept, allConcepts }) => {
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const container = containerRef.current;
    if (!container) return;

    d3.select(container).select('svg').remove();

    const width = container.clientWidth;
    const height = container.clientHeight || 260;
    const margin = { top: 30, right: 40, bottom: 30, left: 40 };

    const svg = d3
      .select(container)
      .append('svg')
      .attr('width', width)
      .attr('height', height);

    const g = svg
      .append('g')
      .attr('transform', `translate(${margin.left},${margin.top})`);

    const treeData = buildTree(concept, allConcepts);
    const root = d3.hierarchy(treeData);

    const treeLayout = d3
      .tree<TreeNode>()
      .size([width - margin.left - margin.right, height - margin.top - margin.bottom - 20]);

    treeLayout(root);

    // Curved links
    const linkGenerator = d3
      .linkVertical<d3.HierarchyPointLink<TreeNode>, d3.HierarchyPointNode<TreeNode>>()
      .x((d) => d.x)
      .y((d) => d.y);

    g.selectAll('.link')
      .data(root.links())
      .enter()
      .append('path')
      .attr('class', 'link')
      .attr('d', (d) => linkGenerator(d as any) ?? '')
      .attr('fill', 'none')
      .attr('stroke', '#DEE2E6')
      .attr('stroke-width', 2)
      .attr('opacity', 0)
      .transition()
      .duration(600)
      .attr('opacity', 1);

    // Highlight path from leaves to root
    g.selectAll('.link-highlight')
      .data(root.links())
      .enter()
      .append('path')
      .attr('class', 'link-highlight')
      .attr('d', (d) => linkGenerator(d as any) ?? '')
      .attr('fill', 'none')
      .attr('stroke', (d) =>
        d.target.data.readiness < 0.5 ? '#E05A5A' : '#FFCB05'
      )
      .attr('stroke-width', 2.5)
      .attr('opacity', 0)
      .attr('stroke-dasharray', function () {
        return (this as SVGPathElement).getTotalLength();
      })
      .attr('stroke-dashoffset', function () {
        return (this as SVGPathElement).getTotalLength();
      })
      .transition()
      .delay(400)
      .duration(800)
      .attr('opacity', 0.6)
      .attr('stroke-dashoffset', 0);

    // Nodes
    const NODE_R = 22;
    const nodeSel = g
      .selectAll<SVGGElement, d3.HierarchyPointNode<TreeNode>>('.node')
      .data(root.descendants())
      .enter()
      .append('g')
      .attr('class', 'node')
      .attr('transform', (d) => `translate(${d.x},${d.y})`);

    // Node circle
    nodeSel
      .append('circle')
      .attr('r', NODE_R)
      .attr('fill', '#FFFFFF')
      .attr('stroke', (d) => readinessColor(d.data.readiness))
      .attr('stroke-width', (d) => (d.depth === 0 ? 3 : 2.5))
      .attr('opacity', 0)
      .transition()
      .duration(500)
      .delay((_, i) => i * 80)
      .attr('opacity', 1);

    // Inner fill
    nodeSel
      .append('circle')
      .attr('r', (d) => NODE_R * d.data.readiness)
      .attr('fill', (d) => readinessColor(d.data.readiness))
      .attr('opacity', 0)
      .transition()
      .duration(500)
      .delay((_, i) => i * 80)
      .attr('opacity', 0.15);

    // Readiness percentage
    nodeSel
      .append('text')
      .attr('text-anchor', 'middle')
      .attr('dy', '0.35em')
      .attr('fill', (d) => readinessColor(d.data.readiness))
      .attr('font-size', '11px')
      .attr('font-weight', '600')
      .attr('font-family', 'system-ui')
      .text((d) => `${Math.round(d.data.readiness * 100)}%`);

    // Name label
    nodeSel
      .append('text')
      .attr('text-anchor', 'middle')
      .attr('dy', NODE_R + 16)
      .attr('fill', '#00274C')
      .attr('font-size', '11px')
      .attr('font-weight', '500')
      .attr('font-family', 'system-ui')
      .text((d) => d.data.name);

    return () => {
      d3.select(container).select('svg').remove();
    };
  }, [concept, allConcepts]);

  return <div ref={containerRef} className="w-full h-full" style={{ minHeight: 260 }} />;
};
