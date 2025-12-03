import React from 'react';
import { cn } from '@/lib/utils';

/**
 * A wrapper that makes amounts clickable for drill-down.
 * Adds hover styling: underline, pointer cursor, subtle color change.
 */
export function ClickableAmount({
  children,
  onClick,
  className,
  disabled = false,
}) {
  if (disabled || !onClick) {
    return <span className={className}>{children}</span>;
  }

  return (
    <button
      type="button"
      onClick={onClick}
      className={cn(
        'hover:underline hover:text-indigo-600 dark:hover:text-indigo-400 cursor-pointer transition-colors focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-1 rounded-sm',
        className
      )}
    >
      {children}
    </button>
  );
}

export default ClickableAmount;
