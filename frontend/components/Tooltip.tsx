/**
 * Tooltip Component
 * Shows helpful text on hover with proper styling
 * Uses fixed positioning to avoid being clipped by parent overflow
 */

import { useState, useRef, useEffect } from 'react';
import { createPortal } from 'react-dom';

interface TooltipProps {
  content: string;
  children: React.ReactNode;
}

export function Tooltip({ content, children }: TooltipProps) {
  const [isVisible, setIsVisible] = useState(false);
  const [position, setPosition] = useState({ top: 0, left: 0 });
  const [placement, setPlacement] = useState<'right' | 'left' | 'top'>('right');
  const triggerRef = useRef<HTMLSpanElement>(null);
  const tooltipRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (isVisible && triggerRef.current) {
      const updatePosition = () => {
        if (!triggerRef.current || !tooltipRef.current) return;

        const triggerRect = triggerRef.current.getBoundingClientRect();
        const tooltipRect = tooltipRef.current.getBoundingClientRect();
        const viewportWidth = window.innerWidth;
        const viewportHeight = window.innerHeight;
        const padding = 10;

        let newPlacement: 'right' | 'left' | 'top' = 'right';
        let top = 0;
        let left = 0;

        // Try right placement first
        if (triggerRect.right + tooltipRect.width + padding < viewportWidth) {
          newPlacement = 'right';
          left = triggerRect.right + padding;
          top = triggerRect.top + triggerRect.height / 2 - tooltipRect.height / 2;
        }
        // Try left placement
        else if (triggerRect.left - tooltipRect.width - padding > 0) {
          newPlacement = 'left';
          left = triggerRect.left - tooltipRect.width - padding;
          top = triggerRect.top + triggerRect.height / 2 - tooltipRect.height / 2;
        }
        // Try top placement
        else if (triggerRect.top - tooltipRect.height - padding > 0) {
          newPlacement = 'top';
          left = triggerRect.left + triggerRect.width / 2 - tooltipRect.width / 2;
          top = triggerRect.top - tooltipRect.height - padding;
        }
        // Fallback to right even if it overflows
        else {
          newPlacement = 'right';
          left = Math.min(triggerRect.right + padding, viewportWidth - tooltipRect.width - padding);
          top = triggerRect.top + triggerRect.height / 2 - tooltipRect.height / 2;
        }

        // Ensure tooltip stays within viewport vertically
        top = Math.max(padding, Math.min(top, viewportHeight - tooltipRect.height - padding));

        // Ensure tooltip stays within viewport horizontally
        left = Math.max(padding, Math.min(left, viewportWidth - tooltipRect.width - padding));

        setPosition({ top, left });
        setPlacement(newPlacement);
      };

      // Initial position update
      updatePosition();

      // Update on scroll or resize
      window.addEventListener('scroll', updatePosition, true);
      window.addEventListener('resize', updatePosition);

      return () => {
        window.removeEventListener('scroll', updatePosition, true);
        window.removeEventListener('resize', updatePosition);
      };
    }
  }, [isVisible]);

  const getArrowStyle = (): React.CSSProperties => {
    if (!triggerRef.current) return {};

    const triggerRect = triggerRef.current.getBoundingClientRect();

    switch (placement) {
      case 'left':
        return {
          position: 'absolute',
          right: '-4px',
          top: `${triggerRect.top + triggerRect.height / 2 - position.top}px`,
          width: '8px',
          height: '8px',
          background: 'white',
          border: '1px solid rgb(209, 213, 219)',
          borderLeft: 'none',
          borderBottom: 'none',
          transform: 'rotate(45deg)',
        };
      case 'top':
        return {
          position: 'absolute',
          bottom: '-4px',
          left: `${triggerRect.left + triggerRect.width / 2 - position.left}px`,
          width: '8px',
          height: '8px',
          background: 'white',
          border: '1px solid rgb(209, 213, 219)',
          borderTop: 'none',
          borderLeft: 'none',
          transform: 'rotate(45deg)',
        };
      case 'right':
      default:
        return {
          position: 'absolute',
          left: '-4px',
          top: `${triggerRect.top + triggerRect.height / 2 - position.top}px`,
          width: '8px',
          height: '8px',
          background: 'white',
          border: '1px solid rgb(209, 213, 219)',
          borderRight: 'none',
          borderTop: 'none',
          transform: 'rotate(45deg)',
        };
    }
  };

  const tooltipContent = isVisible ? (
    <div
      ref={tooltipRef}
      className="fixed z-[9999] px-3 py-2 text-sm text-black bg-white border border-gray-300 rounded-lg shadow-xl"
      style={{
        top: `${position.top}px`,
        left: `${position.left}px`,
        maxWidth: '400px',
        whiteSpace: 'normal',
      }}
    >
      {content}
      <div style={getArrowStyle()}></div>
    </div>
  ) : null;

  return (
    <>
      <span className="relative inline-block" ref={triggerRef}>
        <span
          onMouseEnter={() => setIsVisible(true)}
          onMouseLeave={() => setIsVisible(false)}
          className="cursor-help"
        >
          {children}
        </span>
      </span>
      {typeof document !== 'undefined' && tooltipContent && createPortal(tooltipContent, document.body)}
    </>
  );
}
