import * as React from 'react';
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from '@/components/ui/tooltip';
import { Info } from 'lucide-react';
import { cn } from '@/lib/utils';

/**
 * InfoTooltip - A tooltip component that displays helpful information
 * about metrics and widgets with a configurable delay.
 *
 * @param {string} content - The tooltip content/description
 * @param {string} title - Optional title for the tooltip
 * @param {React.ReactNode} children - The element to wrap with tooltip
 * @param {boolean} showIcon - Whether to show an info icon (default: false)
 * @param {number} delay - Delay in ms before showing tooltip (default: 700)
 * @param {string} side - Tooltip position: 'top' | 'bottom' | 'left' | 'right'
 * @param {string} className - Additional classes for the trigger wrapper
 */
export function InfoTooltip({
  content,
  title,
  children,
  showIcon = false,
  delay = 700,
  side = 'top',
  className,
}) {
  return (
    <TooltipProvider delayDuration={delay}>
      <Tooltip>
        <TooltipTrigger asChild>
          <span className={cn('inline-flex items-center gap-1 cursor-help', className)}>
            {children}
            {showIcon && (
              <Info className="h-3 w-3 text-muted-foreground opacity-50 hover:opacity-100 transition-opacity" />
            )}
          </span>
        </TooltipTrigger>
        <TooltipContent
          side={side}
          className="max-w-xs p-3 text-sm leading-relaxed"
        >
          {title && (
            <p className="font-semibold mb-1 text-foreground">{title}</p>
          )}
          <p className="text-muted-foreground">{content}</p>
        </TooltipContent>
      </Tooltip>
    </TooltipProvider>
  );
}

/**
 * MetricTooltip - Specifically for wrapping metric labels with descriptions
 */
export function MetricTooltip({
  label,
  description,
  delay = 700,
  side = 'top',
  className,
}) {
  return (
    <TooltipProvider delayDuration={delay}>
      <Tooltip>
        <TooltipTrigger asChild>
          <span className={cn('cursor-help border-b border-dashed border-muted-foreground/30 hover:border-muted-foreground/60 transition-colors', className)}>
            {label}
          </span>
        </TooltipTrigger>
        <TooltipContent
          side={side}
          className="max-w-xs p-3 text-sm leading-relaxed"
        >
          <p className="text-muted-foreground">{description}</p>
        </TooltipContent>
      </Tooltip>
    </TooltipProvider>
  );
}

/**
 * CardTitleTooltip - For card headers/titles with info about the entire widget
 */
export function CardTitleTooltip({
  children,
  description,
  delay = 1000,
  side = 'bottom',
}) {
  return (
    <TooltipProvider delayDuration={delay}>
      <Tooltip>
        <TooltipTrigger asChild>
          <span className="cursor-help">
            {children}
          </span>
        </TooltipTrigger>
        <TooltipContent
          side={side}
          className="max-w-sm p-3 text-sm leading-relaxed"
        >
          <p className="text-muted-foreground">{description}</p>
        </TooltipContent>
      </Tooltip>
    </TooltipProvider>
  );
}

export default InfoTooltip;
