import { useState, useRef, useEffect, type ReactNode } from 'react';

interface TooltipProps {
  text: string;
  children: ReactNode;
}

export function Tooltip({ text, children }: TooltipProps) {
  const [visible, setVisible] = useState(false);
  const [position, setPosition] = useState<'top' | 'bottom'>('top');
  const triggerRef = useRef<HTMLSpanElement>(null);
  const tooltipRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (visible && triggerRef.current) {
      const rect = triggerRef.current.getBoundingClientRect();
      setPosition(rect.top < 80 ? 'bottom' : 'top');
    }
  }, [visible]);

  return (
    <span
      ref={triggerRef}
      className="relative inline-flex items-center"
      onMouseEnter={() => setVisible(true)}
      onMouseLeave={() => setVisible(false)}
      onTouchStart={() => setVisible((v) => !v)}
    >
      {children}
      {visible && (
        <div
          ref={tooltipRef}
          role="tooltip"
          className={`absolute z-50 w-64 px-3 py-2 text-xs text-white bg-gray-900 border border-gray-700 rounded-lg shadow-xl
            transition-opacity duration-150 opacity-100
            ${position === 'top' ? 'bottom-full mb-2' : 'top-full mt-2'}
            left-1/2 -translate-x-1/2`}
        >
          {text}
          {/* Arrow */}
          <div
            className={`absolute left-1/2 -translate-x-1/2 w-2 h-2 bg-gray-900 border-gray-700 rotate-45
              ${position === 'top'
                ? 'top-full -mt-1 border-r border-b'
                : 'bottom-full -mb-1 border-l border-t'
              }`}
          />
        </div>
      )}
    </span>
  );
}

interface InfoTooltipProps {
  text: string;
}

export function InfoTooltip({ text }: InfoTooltipProps) {
  return (
    <Tooltip text={text}>
      <span
        className="inline-flex items-center justify-center w-4 h-4 ml-1 text-[10px] text-gray-500 hover:text-white bg-gray-700/50 hover:bg-gray-600 rounded-full cursor-help transition-colors"
        aria-label={text}
      >
        ⓘ
      </span>
    </Tooltip>
  );
}
