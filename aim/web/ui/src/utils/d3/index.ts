import clearArea from './clearArea';
import drawArea from './drawArea';
import drawAxes from './drawAxes';
import drawLines from './drawLines';
import processLineChartData from './processLineChartData';
import getAxisScale from './getAxisScale';
import drawBrush from './drawBrush';
import drawHoverAttributes from './drawHoverAttributes';
import drawParallelAxes from './drawParallelAxes';
import drawParallelLines from './drawParallelLines';
import drawParallelHoverAttributes from './drawParallelHoverAttributes';
import drawParallelAxesBrush from './drawParallelAxesBrush';
import drawParallelColorIndicator from './drawParallelColorIndicator';
import getCoordinates from './getCoordinates';
import drawPoints from './drawPoints';
import drawScatterTrendline from './drawScatterTrendline';
import drawUnableToRender from './drawUnableToRender';

const gradientStartColor = '#2980B9';
const gradientEndColor = '#E74C3C';

enum AlignmentOptionsEnum {
  STEP = 'step',
  EPOCH = 'epoch',
  RELATIVE_TIME = 'relative_time',
  ABSOLUTE_TIME = 'absolute_time',
  CUSTOM_METRIC = 'custom',
}

enum CircleEnum {
  Radius = 2.6,
  ActiveRadius = 5,
}

enum HighlightEnum {
  Off = 0,
  Run = 1,
  Metric = 2,
  Custom = 3,
}

enum ZoomEnum {
  SINGLE = 0,
  MULTIPLE = 1,
}

enum CurveEnum {
  Linear = 'curveLinear',
  Basis = 'curveBasis',
  Bundle = 'curveBundle',
  Cardinal = 'curveCardinal',
  CatmullRom = 'curveCatmullRom',
  MonotoneX = 'curveMonotoneX',
  MonotoneY = 'curveMonotoneY',
  Natural = 'curveNatural',
  Step = 'curveStep',
  StepAfter = 'curveStepAfter',
  StepBefore = 'curveStepBefore',
  BasisClosed = 'curveBasisClosed',
}

enum ScaleEnum {
  Log = 'log',
  Linear = 'linear',
  Point = 'point',
}

enum ChartTypeEnum {
  LineChart = 'LineChart',
  HighPlot = 'HighPlot',
  ScatterPlot = 'ScatterPlot',
  ImageSet = 'ImageSet',
}

enum PointSymbolEnum {
  CIRCLE = 'symbolCircle',
  CROSS = 'symbolCross',
  DIAMOND = 'symbolDiamond',
  SQUARE = 'symbolSquare',
  STAR = 'symbolStar',
  TRIANGLE = 'symbolTriangle',
  WYE = 'symbolWye',
}

enum TrendlineTypeEnum {
  SLR = 'slr',
  LOESS = 'loess',
}

const MIN_LOG_VALUE = 1e-8;

export {
  CircleEnum,
  CurveEnum,
  ScaleEnum,
  ChartTypeEnum,
  AlignmentOptionsEnum,
  PointSymbolEnum,
  TrendlineTypeEnum,
  HighlightEnum,
  ZoomEnum,
  clearArea,
  drawArea,
  drawAxes,
  drawLines,
  getCoordinates,
  drawParallelColorIndicator,
  processLineChartData,
  getAxisScale,
  drawBrush,
  drawHoverAttributes,
  drawParallelAxes,
  drawParallelLines,
  drawParallelHoverAttributes,
  drawParallelAxesBrush,
  drawPoints,
  drawScatterTrendline,
  drawUnableToRender,
  gradientStartColor,
  gradientEndColor,
  MIN_LOG_VALUE,
};
