import { describe, it, expect, vi, beforeEach } from 'vitest';
import { ApiClientError, gridGuardApi } from '@/lib/api';

describe('gridGuardApi client', () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  it('correctly unpacks successful health response envelope', async () => {
    const mockHealthData = {
      status: 'healthy',
      project: 'GRIDGUARD NEXUS X',
      version: '1.0.0-level1',
      stage: 'LEVEL 1: PROJECT FOUNDATION',
      environment: 'development',
      uptime_seconds: 42.5,
      database: {
        name: 'PostgreSQL Persistent Storage',
        status: 'operational',
        details: 'Connected',
        ready: true,
      },
      subsystems: [],
    };

    const mockResponse = {
      status: 'success',
      data: mockHealthData,
      meta: {
        version: '1.0.0-level1',
        timestamp: '2026-10-29T15:00:00Z',
      },
    };

    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      status: 200,
      json: async () => mockResponse,
    });

    const result = await gridGuardApi.getHealth();
    expect(result.data.project).toBe('GRIDGUARD NEXUS X');
    expect(result.data.version).toBe('1.0.0-level1');
    expect(result.latencyMs).toBeGreaterThanOrEqual(0);
  });

  it('throws ApiClientError with code and details on 422 validation failure', async () => {
    const mockErrorPayload = {
      status: 'error',
      error: {
        code: 'ERR_VALIDATION_FAILED',
        message: 'Validation failed for field station_id',
        field: 'station_id',
        details: [{ field: 'station_id', message: 'String should match pattern' }],
      },
      meta: {
        version: '1.0.0-level1',
        timestamp: '2026-10-29T15:00:00Z',
      },
    };

    global.fetch = vi.fn().mockResolvedValue({
      ok: false,
      status: 422,
      json: async () => mockErrorPayload,
    });

    await expect(
      gridGuardApi.validateTelemetry({
        station_id: 'invalid!',
        grid_frequency_hz: 10,
        voltage_rms: -1,
        feeder_count: 0,
      })
    ).rejects.toThrowError(ApiClientError);
  });
});
