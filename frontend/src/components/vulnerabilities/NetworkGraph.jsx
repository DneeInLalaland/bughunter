import React, { useEffect, useRef } from 'react';
import * as d3 from 'd3';

const NetworkGraph = ({ vulnerabilities }) => {
  const svgRef = useRef();

  useEffect(() => {
    if (!vulnerabilities || vulnerabilities.length === 0) return;

    // สร้าง nodes และ links
    const nodes = [
      { id: 'target', label: 'Target', type: 'target' },
      ...vulnerabilities.slice(0, 20).map((vuln, i) => ({
        id: `vuln-${i}`,
        label: vuln.type,
        severity: vuln.severity,
        type: 'vulnerability',
      })),
    ];

    const links = vulnerabilities.slice(0, 20).map((vuln, i) => ({
      source: 'target',
      target: `vuln-${i}`,
    }));

    // Setup D3
    const width = 600;
    const height = 400;

    d3.select(svgRef.current).selectAll('*').remove();
    const svg = d3.select(svgRef.current).attr('width', width).attr('height', height);

    // Color scale
    const color = d3.scaleOrdinal()
      .domain(['Critical', 'High', 'Medium', 'Low'])
      .range(['#dc2626', '#f97316', '#f59e0b', '#3b82f6']);

    // Force simulation
    const simulation = d3.forceSimulation(nodes)
      .force('link', d3.forceLink(links).id(d => d.id).distance(100))
      .force('charge', d3.forceManyBody().strength(-300))
      .force('center', d3.forceCenter(width / 2, height / 2));

    // Links
    const link = svg.append('g')
      .selectAll('line')
      .data(links)
      .enter()
      .append('line')
      .attr('stroke', '#999')
      .attr('stroke-width', 2);

    // Nodes
    const node = svg.append('g')
      .selectAll('circle')
      .data(nodes)
      .enter()
      .append('circle')
      .attr('r', d => (d.type === 'target' ? 20 : 10))
      .attr('fill', d => (d.type === 'target' ? '#0ea5e9' : color(d.severity)))
      .call(
        d3.drag()
          .on('start', dragstarted)
          .on('drag', dragged)
          .on('end', dragended)
      );

    // Labels
    const labels = svg.append('g')
      .selectAll('text')
      .data(nodes)
      .enter()
      .append('text')
      .text(d => d.label)
      .attr('font-size', 10)
      .attr('dx', 12)
      .attr('dy', 4);

    // Simulation tick
    simulation.on('tick', () => {
      link
        .attr('x1', d => d.source.x)
        .attr('y1', d => d.source.y)
        .attr('x2', d => d.target.x)
        .attr('y2', d => d.target.y);

      node.attr('cx', d => d.x).attr('cy', d => d.y);
      labels.attr('x', d => d.x).attr('y', d => d.y);
    });

    // Drag functions
    function dragstarted(event, d) {
      if (!event.active) simulation.alphaTarget(0.3).restart();
      d.fx = d.x;
      d.fy = d.y;
    }

    function dragged(event, d) {
      d.fx = event.x;
      d.fy = event.y;
    }

    function dragended(event, d) {
      if (!event.active) simulation.alphaTarget(0);
      d.fx = null;
      d.fy = null;
    }
  }, [vulnerabilities]);

  return (
    <div className="flex justify-center">
      <svg ref={svgRef}></svg>
    </div>
  );
};

export default NetworkGraph;
