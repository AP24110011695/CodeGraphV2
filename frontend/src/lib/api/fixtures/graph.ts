import type { GraphResponse, NodeDetailResponse } from '../types'

export const mockGraphResponse: GraphResponse = {
  repository_id: 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11',
  generated_at: '2026-08-01T10:05:00Z',
  metrics: {
    node_count: 3,
    edge_count: 3,
    has_cycles: false,
    cycle_count: 0,
    entry_point_count: 1,
    leaf_count: 1,
  },
  nodes: [
    {
      id: 'f1002-router-py',
      path: 'app/api/v1/auth.py',
      language: 'python',
      symbol_count: 2,
      metrics: {
        in_degree: 0,
        out_degree: 2,
        pagerank: 0.15,
        is_entry_point: true,
        is_leaf: false,
      },
    },
    {
      id: 'f1001-auth-py',
      path: 'app/services/auth.py',
      language: 'python',
      symbol_count: 3,
      metrics: {
        in_degree: 1,
        out_degree: 1,
        pagerank: 0.45,
        is_entry_point: false,
        is_leaf: false,
      },
    },
    {
      id: 'f1003-config-py',
      path: 'app/config.py',
      language: 'python',
      symbol_count: 1,
      metrics: {
        in_degree: 2,
        out_degree: 0,
        pagerank: 0.4,
        is_entry_point: false,
        is_leaf: true,
      },
    },
  ],
  edges: [
    {
      from_file_id: 'f1002-router-py',
      to_file_id: 'f1001-auth-py',
      import_name: 'AuthService',
    },
    {
      from_file_id: 'f1002-router-py',
      to_file_id: 'f1003-config-py',
      import_name: 'get_settings',
    },
    {
      from_file_id: 'f1001-auth-py',
      to_file_id: 'f1003-config-py',
      import_name: 'get_settings',
    },
  ],
}

export const mockNodeDetailAuth: NodeDetailResponse = {
  id: 'f1001-auth-py',
  path: 'app/services/auth.py',
  language: 'python',
  symbol_count: 3,
  metrics: {
    in_degree: 1,
    out_degree: 1,
    pagerank: 0.45,
    is_entry_point: false,
    is_leaf: false,
  },
  symbols: [
    {
      id: 's1-auth-01',
      name: 'AuthService',
      kind: 'class',
      start_line: 10,
      end_line: 45,
    },
    {
      id: 's1-auth-02',
      name: 'login',
      kind: 'method',
      start_line: 18,
      end_line: 32,
    },
    {
      id: 's1-auth-03',
      name: 'verify_token',
      kind: 'method',
      start_line: 34,
      end_line: 44,
    },
  ],
  dependencies: [
    {
      file_id: 'f1003-config-py',
      path: 'app/config.py',
      language: 'python',
      import_name: 'get_settings',
    },
  ],
  dependents: [
    {
      file_id: 'f1002-router-py',
      path: 'app/api/v1/auth.py',
      language: 'python',
      import_name: 'AuthService',
    },
  ],
}
