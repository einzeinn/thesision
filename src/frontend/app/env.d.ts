declare module '*.css';

interface AnimeOptions {
  targets: Element | Element[];
  opacity?: [number, number];
  scale?: [number, number];
  strokeDashoffset?: (target: SVGPathElement) => [number, number];
  duration?: number;
  easing?: string;
  delay?: number | ((element: Element, index: number) => number);
  complete?: (animation: { animatables: Array<{ target: Element }> }) => void;
}

interface AnimeFunction {
  (options: AnimeOptions): void;
  stagger(interval: number): (element: Element, index: number) => number;
}

interface Window { anime?: AnimeFunction; d3?: typeof import('d3'); }
