import React from 'react';
import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { Badge } from '@/components/ui/Badge';
import { ErrorAlert } from '@/components/ui/ErrorAlert';
import { ReadinessGrid } from '@/components/dashboard/ReadinessGrid';
import { SystemHealthCard } from '@/components/dashboard/SystemHealthCard';
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
      version: '1.0.0-level1',
      stage: 'LEVEL 1: PROJECT FOUNDATION',
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
});
