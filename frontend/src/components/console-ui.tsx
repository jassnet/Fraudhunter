import type { ButtonHTMLAttributes, ReactNode, TextareaHTMLAttributes } from "react";

import type { ReviewStatus, RiskLevel } from "@/lib/console-types";

function classNames(...values: Array<string | false | null | undefined>) {
  return values.filter(Boolean).join(" ");
}

const STATUS_LABELS: Record<ReviewStatus, string> = {
  unhandled: "未対応",
  investigating: "調査中",
  confirmed_fraud: "不正",
  white: "正常（ホワイト）",
};

export function reviewStatusLabel(status: ReviewStatus) {
  return STATUS_LABELS[status];
}

type PageHeaderProps = {
  title: string;
  description: string;
  actions?: ReactNode;
};

export function PageHeader({ title, description, actions }: PageHeaderProps) {
  return (
    <header className="page-header">
      <div>
        <h1 className="page-title">{title}</h1>
        <p className="page-description">{description}</p>
      </div>
      {actions ? <div className="page-actions">{actions}</div> : null}
    </header>
  );
}

type PanelProps = {
  title: string;
  description?: string;
  actions?: ReactNode;
  children: ReactNode;
  className?: string;
};

export function Panel({ title, description, actions, children, className }: PanelProps) {
  return (
    <section className={classNames("panel", className)}>
      <div className="panel-header">
        <div>
          <h2 className="panel-title">{title}</h2>
          {description ? <p className="panel-description">{description}</p> : null}
        </div>
        {actions ? <div>{actions}</div> : null}
      </div>
      {children}
    </section>
  );
}

type MetricCardProps = {
  label: string;
  value: string;
  caption: string;
};

export function MetricCard({ label, value, caption }: MetricCardProps) {
  return (
    <section className="metric-card">
      <div className="metric-label">{label}</div>
      <div className="metric-value">{value}</div>
      <div className="metric-caption">{caption}</div>
    </section>
  );
}

type MetricStripItem = {
  label: string;
  value: string;
  caption: string;
  tone?: "danger" | "warning" | "neutral";
};

type MetricStripProps = {
  items: MetricStripItem[];
};

export function MetricStrip({ items }: MetricStripProps) {
  return (
    <section className="metric-strip" aria-label="主要な指標">
      {items.map((item) => (
        <div
          key={item.label}
          className={classNames(
            "metric-strip-item",
            item.tone === "danger" && "metric-tone-danger",
            item.tone === "warning" && "metric-tone-warning",
          )}
        >
          <div className="metric-label">{item.label}</div>
          <div className="metric-value">{item.value}</div>
          <div className="metric-caption">{item.caption}</div>
        </div>
      ))}
    </section>
  );
}

type ActionButtonProps = ButtonHTMLAttributes<HTMLButtonElement> & {
  tone?: "default" | "danger" | "warning";
};

export function ActionButton({ tone = "default", className, type, ...props }: ActionButtonProps) {
  return (
    <button
      {...props}
      className={classNames("button", `button-${tone}`, className)}
      type={type ?? "button"}
    />
  );
}

export function LoadingState({ message = "読み込み中..." }: { message?: string }) {
  return (
    <div className="loading-state" role="status" aria-live="polite">
      {message}
    </div>
  );
}

export function ErrorState({ message }: { message: string }) {
  return (
    <div className="error-state" role="alert" aria-live="assertive">
      {message}
    </div>
  );
}

export function EmptyState({ message }: { message: string }) {
  return (
    <div className="empty-state" role="status" aria-live="polite">
      {message}
    </div>
  );
}

type ReviewReasonDialogProps = {
  open: boolean;
  title: string;
  description: string;
  confirmLabel: string;
  confirmTone?: "default" | "danger" | "warning";
  value: string;
  error?: string | null;
  busy?: boolean;
  onChange: (value: string) => void;
  onCancel: () => void;
  onConfirm: () => void;
  presets?: string[];
  textareaProps?: Omit<TextareaHTMLAttributes<HTMLTextAreaElement>, "value" | "onChange">;
};

export function ReviewReasonDialog({
  open,
  title,
  description,
  confirmLabel,
  confirmTone = "warning",
  value,
  error,
  busy = false,
  onChange,
  onCancel,
  onConfirm,
  presets = [],
  textareaProps,
}: ReviewReasonDialogProps) {
  if (!open) {
    return null;
  }

  return (
    <div className="dialog-backdrop">
      <div className="dialog-card" role="dialog" aria-modal="true" aria-label={title}>
        <div className="dialog-header">
          <div>
            <h2 className="dialog-title">{title}</h2>
            <p className="dialog-description">{description}</p>
          </div>
        </div>
        <label className="form-field" htmlFor="review-reason">
          <span>理由</span>
          <textarea
            {...textareaProps}
            id="review-reason"
            className="dialog-textarea"
            value={value}
            onChange={(event) => onChange(event.target.value)}
          />
        </label>
        {presets.length > 0 ? (
          <div className="dialog-presets" aria-label="判定理由のテンプレート">
            {presets.map((preset) => (
              <button
                key={preset}
                type="button"
                className="dialog-preset"
                onClick={() => onChange(value.trim() ? `${value.trim()}\n${preset}` : preset)}
              >
                {preset}
              </button>
            ))}
          </div>
        ) : null}
        <div className="dialog-meta">
          <span>{value.trim().length}/500</span>
        </div>
        {error ? <ErrorState message={error} /> : null}
        <div className="dialog-footer">
          <ActionButton onClick={onCancel} disabled={busy}>
            中止
          </ActionButton>
          <ActionButton tone={confirmTone} onClick={onConfirm} disabled={busy}>
            {confirmLabel}
          </ActionButton>
        </div>
      </div>
    </div>
  );
}

export function StatusBadge({ status }: { status: ReviewStatus }) {
  return <span className={classNames("badge", `status-${status}`)}>{reviewStatusLabel(status)}</span>;
}

function resolveRiskTone(level: RiskLevel, score: number) {
  if (level === "high" || score >= 65) {
    return "high";
  }
  if (level === "medium" || score >= 30) {
    return "medium";
  }
  return "low";
}

type RiskBadgeProps = {
  score: number;
  level: RiskLevel;
  emphasized?: boolean;
};

export function RiskBadge({ score, level, emphasized = false }: RiskBadgeProps) {
  const tone = resolveRiskTone(level, score);
  return (
    <span className={classNames("badge", "risk-badge", `risk-${tone}`, emphasized && "risk-emphasis")}>
      <span className="risk-score">{score}</span>
    </span>
  );
}

type StatusCountStripProps = {
  counts: Record<ReviewStatus, number>;
};

export function StatusCountStrip({ counts }: StatusCountStripProps) {
  const items: Array<{ key: ReviewStatus; value: number }> = [
    { key: "unhandled", value: counts.unhandled },
    { key: "investigating", value: counts.investigating },
    { key: "confirmed_fraud", value: counts.confirmed_fraud },
    { key: "white", value: counts.white },
  ];

  return (
    <div className="status-count-strip" aria-label="判定状態ごとの件数">
      {items.map((item) => (
        <div key={item.key} className="status-count-item">
          <StatusBadge status={item.key} />
          <span>{item.value}件</span>
        </div>
      ))}
    </div>
  );
}
