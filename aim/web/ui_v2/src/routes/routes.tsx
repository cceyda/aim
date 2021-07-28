import React from 'react';

const Runs = React.lazy(() => import('pages/Runs/Runs'));
const Metrics = React.lazy(() => import('pages/Metrics/MetricsContainer'));
const Params = React.lazy(() => import('pages/Params/ParamsContainer'));

const PATHS = {
  RUNS: '/runs',
  METRICS: '/metrics',
  PARAMS: '/params',
  TAGS: '/tags',
  BOOKMARKS: '/bookmarks',
};

const routes = {
  RUNS: {
    path: PATHS.RUNS,
    component: Runs,
    showInSidebar: true,
    displayName: 'Runs',
  },
  METRICS: {
    path: PATHS.METRICS,
    component: Metrics,
    showInSidebar: true,
    displayName: 'Metrics',
  },
  PARAMS: {
    path: PATHS.PARAMS,
    component: Params,
    showInSidebar: true,
    displayName: 'Params',
  },
};

export { PATHS, routes };