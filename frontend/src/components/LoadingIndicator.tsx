"use client";

interface LoadingIndicatorProps {
  /** Type of loading indicator to display */
  variant?: "dots" | "spinner" | "skeleton";
  /** Optional text to display alongside the indicator */
  text?: string;
  /** Size of the indicator */
  size?: "sm" | "md" | "lg";
}

export default function LoadingIndicator({
  variant = "dots",
  text,
  size = "md",
}: LoadingIndicatorProps) {
  const sizeClasses = {
    sm: "w-1.5 h-1.5",
    md: "w-2 h-2",
    lg: "w-3 h-3",
  };

  const spinnerSizes = {
    sm: "h-4 w-4",
    md: "h-8 w-8",
    lg: "h-12 w-12",
  };

  if (variant === "spinner") {
    return (
      <div className="flex flex-col items-center gap-2" role="status" aria-label="Loading">
        <div
          className={`animate-spin rounded-full border-b-2 border-blue-600 ${spinnerSizes[size]}`}
        />
        {text && <p className="text-sm text-gray-600">{text}</p>}
        <span className="sr-only">Loading...</span>
      </div>
    );
  }

  if (variant === "skeleton") {
    return (
      <div className="space-y-2 animate-pulse" role="status" aria-label="Loading content">
        <div className="h-4 bg-gray-200 rounded w-3/4" />
        <div className="h-4 bg-gray-200 rounded w-1/2" />
        <div className="h-4 bg-gray-200 rounded w-5/6" />
        {text && <p className="text-sm text-gray-600 mt-2">{text}</p>}
        <span className="sr-only">Loading...</span>
      </div>
    );
  }

  // Default: dots
  return (
    <div className="flex items-center gap-2" role="status" aria-label="Loading">
      <div className="flex space-x-1">
        <div className={`${sizeClasses[size]} bg-gray-400 rounded-full animate-bounce`} />
        <div
          className={`${sizeClasses[size]} bg-gray-400 rounded-full animate-bounce [animation-delay:0.1s]`}
        />
        <div
          className={`${sizeClasses[size]} bg-gray-400 rounded-full animate-bounce [animation-delay:0.2s]`}
        />
      </div>
      {text && <p className="text-sm text-gray-600">{text}</p>}
      <span className="sr-only">Loading...</span>
    </div>
  );
}
