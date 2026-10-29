import React from 'react';
import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { Badge } from '@/components/ui/Badge';
import { ErrorAlert } from '@/components/ui/ErrorAlert';
import { ReadinessGrid } from '@/components/dashboard/ReadinessGrid';
import { SystemHealthCard } from '@/components/dashboard/SystemHealthCard';
import { MeterLookupView } from '@/components/dashboard/MeterLookupView';
import { DiscrepancyExplorer } from '@/components/dashboard/DiscrepancyExplorer';
import { AiInvestigationView } from '@/components/dashboard/AiInvestigationView';
import { EvidenceGraphView } from '@/components/dashboard/EvidenceGraphView';
import { WhatIfSimulatorView } from '@/components/dashboard/WhatIfSimulatorView';
import type { HealthStatusData, SubsystemHealth } from '@/types/api';

describe('Frontend UI Components', () => {
  it('renders Badge with correct variant text', () => {
    render(<Badge variant="emerald">ACTIVE</Badge>);
    expect(screen.getByText('ACTIVE')).toBeDefined();
  });

  it('renders ErrorAlert with code and message', () => {
    render(
      <ErrorAlert
        title="Gateway Offline"
        message="Failed to connect to backend"
        code="ERR_OFFLINE"
      />
    );
    expect(screen.getByText('Gateway Offline')).toBeDefined();
    expect(screen.getByText('ERR_OFFLINE')).toBeDefined();
    expect(screen.getByText('Failed to connect to backend')).toBeDefined();
  });

  it('renders SystemHealthCard with project metadata', () => {
    const mockHealth: HealthStatusData = {
      status: 'healthy',
      project: 'GRIDGUARD NEXUS X',
      version: '3.0.0-level3',
      stage: 'LEVEL 3: CORE ELECTRICITY INTELLIGENCE',
      environment: 'development',
      uptime_seconds: 120.4,
      database: {
        name: 'PostgreSQL Persistent Storage',
        status: 'operational',
        details: 'Connected',
        ready: true,
      },
      subsystems: [],
    };

    render(<SystemHealthCard health={mockHealth} latencyMs={14} />);
    expect(screen.getByText('GRIDGUARD NEXUS X')).toBeDefined();
    expect(screen.getByText('SYSTEM OPERATIONAL')).toBeDefined();
    expect(screen.getByText('14 ms')).toBeDefined();
    expect(screen.getByText('120.4s')).toBeDefined();
  });

  it('renders ReadinessGrid with subsystem items', () => {
    const subsystems: SubsystemHealth[] = [
      {
        name: 'API Gateway',
        status: 'operational',
        details: 'Ready',
        ready: true,
      },
      {
        name: 'Energy Accounting',
        status: 'standby',
        details: 'Target: Level 2',
        ready: false,
      },
    ];

    render(<ReadinessGrid subsystems={subsystems} />);
    expect(screen.getByText('API Gateway')).toBeDefined();
    expect(screen.getByText('Energy Accounting')).toBeDefined();
    expect(screen.getByText('1 of 2 Ready')).toBeDefined();
  });

  it('renders MeterLookupView with privacy compliance banner', () => {
    render(<MeterLookupView />);
    expect(screen.getByText(/National Ideathon Privacy Safeguard/i)).toBeDefined();
    expect(screen.getByPlaceholderText(/Enter meter identifier/i)).toBeDefined();
  });

  it('renders DiscrepancyExplorer with non-prejudgment mandate', () => {
    render(<DiscrepancyExplorer />);
    expect(screen.getByText(/Forensic Non-Prejudgment Mandate/i)).toBeDefined();
    expect(screen.getByText(/Select Physical Distribution Boundary/i)).toBeDefined();
  });

  it('renders AiInvestigationView with multi-hypothesis forensic headers', () => {
    render(<AiInvestigationView />);
    expect(screen.getByText(/Level 4: AI-Assisted Forensic Investigation/i)).toBeDefined();
    expect(screen.getByText(/Multi-hypothesis forensic matrix, 6-factor explainable prioritization/i)).toBeDefined();
    expect(screen.getByText(/Boundary:/i)).toBeDefined();
  });

  it('renders EvidenceGraphView with node lineage header and boundary select', () => {
    render(<EvidenceGraphView />);
    expect(screen.getByText(/Level 5: Interactive Evidence Investigation Graph/i)).toBeDefined();
    expect(screen.getByText(/End-to-end evidence lineage connecting Detected Discrepancy/i)).toBeDefined();
    expect(screen.getByText(/Boundary:/i)).toBeDefined();
  });

  it('renders WhatIfSimulatorView with scenario templates and simulation button', () => {
    render(<WhatIfSimulatorView />);
    expect(screen.getByText(/Level 5: What-If Simulation & Before-and-After Comparison/i)).toBeDefined();
    expect(screen.getByText(/Select Repeatable What-If Assumption Scenario:/i)).toBeDefined();
    expect(screen.getByText(/Run What-If Simulation/i)).toBeDefined();
  });
});
