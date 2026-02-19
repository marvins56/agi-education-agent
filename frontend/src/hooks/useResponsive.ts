"use client";

import { useState, useEffect } from 'react';

export interface BreakpointConfig {
  sm: number;
  md: number;
  lg: number;
  xl: number;
  '2xl': number;
}

const defaultBreakpoints: BreakpointConfig = {
  sm: 640,
  md: 768,
  lg: 1024,
  xl: 1280,
  '2xl': 1536,
};

export interface ResponsiveState {
  width: number;
  height: number;
  isMobile: boolean;
  isTablet: boolean;
  isDesktop: boolean;
  isSmallScreen: boolean;
  currentBreakpoint: string;
}

export const useResponsive = (breakpoints: BreakpointConfig = defaultBreakpoints): ResponsiveState => {
  const [dimensions, setDimensions] = useState(() => {
    if (typeof window !== 'undefined') {
      return {
        width: window.innerWidth,
        height: window.innerHeight,
      };
    }
    return { width: 1024, height: 768 }; // Default for SSR
  });

  useEffect(() => {
    if (typeof window === 'undefined') return;

    const updateDimensions = () => {
      setDimensions({
        width: window.innerWidth,
        height: window.innerHeight,
      });
    };

    // Set initial dimensions
    updateDimensions();

    // Add event listener
    window.addEventListener('resize', updateDimensions);
    window.addEventListener('orientationchange', updateDimensions);

    // Cleanup
    return () => {
      window.removeEventListener('resize', updateDimensions);
      window.removeEventListener('orientationchange', updateDimensions);
    };
  }, []);

  // Calculate responsive states
  const isMobile = dimensions.width < breakpoints.md;
  const isTablet = dimensions.width >= breakpoints.md && dimensions.width < breakpoints.lg;
  const isDesktop = dimensions.width >= breakpoints.lg;
  const isSmallScreen = dimensions.width < breakpoints.sm;

  // Determine current breakpoint
  const getCurrentBreakpoint = (): string => {
    if (dimensions.width >= breakpoints['2xl']) return '2xl';
    if (dimensions.width >= breakpoints.xl) return 'xl';
    if (dimensions.width >= breakpoints.lg) return 'lg';
    if (dimensions.width >= breakpoints.md) return 'md';
    if (dimensions.width >= breakpoints.sm) return 'sm';
    return 'xs';
  };

  return {
    width: dimensions.width,
    height: dimensions.height,
    isMobile,
    isTablet,
    isDesktop,
    isSmallScreen,
    currentBreakpoint: getCurrentBreakpoint(),
  };
};

// Additional utility hooks
export const useMediaQuery = (query: string): boolean => {
  const [matches, setMatches] = useState(false);

  useEffect(() => {
    if (typeof window === 'undefined') return;

    const mediaQueryList = window.matchMedia(query);
    const updateMatch = () => setMatches(mediaQueryList.matches);

    // Set initial value
    updateMatch();

    // Add listener
    mediaQueryList.addEventListener('change', updateMatch);

    // Cleanup
    return () => mediaQueryList.removeEventListener('change', updateMatch);
  }, [query]);

  return matches;
};

// Breakpoint-specific hooks
export const useBreakpoint = () => {
  const { currentBreakpoint, width, height } = useResponsive();
  
  return {
    isXs: currentBreakpoint === 'xs',
    isSm: currentBreakpoint === 'sm',
    isMd: currentBreakpoint === 'md',
    isLg: currentBreakpoint === 'lg',
    isXl: currentBreakpoint === 'xl',
    is2Xl: currentBreakpoint === '2xl',
    current: currentBreakpoint,
    width,
    height,
  };
};

// Container query hook for component-level responsive design
export const useContainerQuery = (containerRef: React.RefObject<HTMLElement>) => {
  const [containerDimensions, setContainerDimensions] = useState({ width: 0, height: 0 });

  useEffect(() => {
    if (!containerRef.current) return;

    const updateContainerDimensions = () => {
      if (containerRef.current) {
        const rect = containerRef.current.getBoundingClientRect();
        setContainerDimensions({
          width: rect.width,
          height: rect.height,
        });
      }
    };

    // Initial measurement
    updateContainerDimensions();

    // Use ResizeObserver if available
    if ('ResizeObserver' in window) {
      const resizeObserver = new ResizeObserver(updateContainerDimensions);
      resizeObserver.observe(containerRef.current);

      return () => resizeObserver.disconnect();
    }

    // Fallback to window resize
    const win = globalThis.window;
    win.addEventListener('resize', updateContainerDimensions);
    return () => win.removeEventListener('resize', updateContainerDimensions);
  }, [containerRef]);

  return containerDimensions;
};