import { Component } from "react";
import { AlertTriangle } from "lucide-react";

// Catches render errors in a page subtree so one bad panel can't white-screen the
// whole terminal. Shows a compact, recoverable error card instead. Resets when
// the `resetKey` (active page) changes, so navigating away clears the error.
export class ErrorBoundary extends Component {
  constructor(props) {
    super(props);
    this.state = { error: null };
  }

  static getDerivedStateFromError(error) {
    return { error };
  }

  componentDidUpdate(prev) {
    if (prev.resetKey !== this.props.resetKey && this.state.error) {
      this.setState({ error: null });
    }
  }

  render() {
    if (this.state.error) {
      return (
        <div className="flex items-start gap-3 m-4 p-4 bg-red-950/30 border border-red-900/50 text-red-200">
          <AlertTriangle size={16} className="flex-shrink-0 mt-0.5 text-red-400" />
          <div className="text-[12px]">
            <div className="font-semibold">This view hit a rendering error.</div>
            <div className="mt-1 text-red-300/80 font-mono text-[10px] break-all">{String(this.state.error?.message || this.state.error)}</div>
            <button
              onClick={() => this.setState({ error: null })}
              className="mt-2 px-2 py-1 text-[10px] uppercase tracking-wider bg-red-900/40 border border-red-800/60 hover:bg-red-900/60 transition-colors"
            >
              Retry
            </button>
          </div>
        </div>
      );
    }
    return this.props.children;
  }
}
