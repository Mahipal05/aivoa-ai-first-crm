import type { InteractionDraft, InteractionRecord, ToolEvent, ValidationReport } from "../types";

interface FormPanelProps {
  draft: InteractionDraft;
  validation: ValidationReport;
  lastToolEvent?: ToolEvent;
  recentInteractions: InteractionRecord[];
}

function ReadOnlyField({
  label,
  value,
  updated,
}: {
  label: string;
  value: string;
  updated?: boolean;
}) {
  return (
    <label className={`field ${updated ? "field--updated" : ""}`}>
      <span>{label}</span>
      <input value={value} readOnly />
    </label>
  );
}

function ReadOnlyTextArea({
  label,
  value,
  updated,
}: {
  label: string;
  value: string;
  updated?: boolean;
}) {
  return (
    <label className={`field ${updated ? "field--updated" : ""}`}>
      <span>{label}</span>
      <textarea value={value} readOnly rows={4} />
    </label>
  );
}

function TagGroup({
  label,
  values,
  updated,
}: {
  label: string;
  values: string[];
  updated?: boolean;
}) {
  return (
    <div className={`field ${updated ? "field--updated" : ""}`}>
      <span>{label}</span>
      <div className="tag-row">
        {values.length ? (
          values.map((item) => <span key={item} className="tag">{item}</span>)
        ) : (
          <span className="muted">No items added.</span>
        )}
      </div>
    </div>
  );
}

export function FormPanel({ draft, validation, lastToolEvent, recentInteractions }: FormPanelProps) {
  const changed = new Set(lastToolEvent?.changed_fields ?? []);
  const follows = draft.follow_up_actions.join("\n");

  return (
    <section className="panel form-panel">
      <div className="panel-header">
        <div>
          <p className="eyebrow">Interaction Details</p>
          <h2>Log HCP Interaction</h2>
        </div>
        <span className="status-pill">AI-controlled form</span>
      </div>

      <div className="form-grid">
        <ReadOnlyField
          label="HCP Name"
          value={draft.hcp_name || "Search or select HCP..."}
          updated={changed.has("hcp_name")}
        />
        <ReadOnlyField
          label="Interaction Type"
          value={draft.interaction_type}
          updated={changed.has("interaction_type")}
        />
        <ReadOnlyField
          label="Date"
          value={draft.interaction_date}
          updated={changed.has("interaction_date")}
        />
        <ReadOnlyField
          label="Time"
          value={draft.interaction_time}
          updated={changed.has("interaction_time")}
        />
      </div>

      <ReadOnlyField
        label="Attendees"
        value={draft.attendees.join(", ") || "Enter names or search..."}
        updated={changed.has("attendees")}
      />
      <ReadOnlyTextArea
        label="Topics Discussed"
        value={draft.topics_discussed || "Enter key discussion points..."}
        updated={changed.has("topics_discussed")}
      />

      <div className="section-label">Materials Shared / Samples Distributed</div>
      <div className="form-grid">
        <TagGroup
          label="Materials Shared"
          values={draft.materials_shared}
          updated={changed.has("materials_shared")}
        />
        <TagGroup
          label="Samples Distributed"
          values={draft.samples_distributed}
          updated={changed.has("samples_distributed")}
        />
      </div>

      <div className={`field ${changed.has("sentiment") ? "field--updated" : ""}`}>
        <span>Observed / Inferred HCP Sentiment</span>
        <div className="sentiment-row">
          {(["positive", "neutral", "negative"] as const).map((item) => (
            <label key={item} className={`sentiment-option ${draft.sentiment === item ? "is-active" : ""}`}>
              <input type="radio" checked={draft.sentiment === item} readOnly />
              <span>{item}</span>
            </label>
          ))}
        </div>
      </div>

      <ReadOnlyTextArea
        label="Outcomes"
        value={draft.outcomes || "Key outcomes or agreements..."}
        updated={changed.has("outcomes")}
      />
      <ReadOnlyTextArea
        label="Follow-up Actions"
        value={follows || "Enter next steps or tasks..."}
        updated={changed.has("follow_up_actions")}
      />

      <div className="insight-grid">
        <div className="insight-card">
          <p className="eyebrow">AI Suggested Follow-up</p>
          {draft.ai_suggested_follow_up.length ? (
            <ul className="clean-list">
              {draft.ai_suggested_follow_up.map((item) => <li key={item}>{item}</li>)}
            </ul>
          ) : (
            <p className="muted">Ask the assistant to summarize or save to generate next steps.</p>
          )}
        </div>
        <div className="insight-card">
          <p className="eyebrow">AI Summary</p>
          <p>{draft.ai_summary || "No summary yet."}</p>
        </div>
      </div>

      <div className={`validation-card ${validation.is_valid ? "is-valid" : "is-invalid"}`}>
        <p className="eyebrow">Validation</p>
        <p>{validation.is_valid ? "Ready to save." : "Some required details are still missing."}</p>
        {!!validation.missing_fields.length && (
          <p className="muted">Missing: {validation.missing_fields.join(", ")}</p>
        )}
        {!!validation.warnings.length && (
          <p className="muted">Warnings: {validation.warnings.join(" ")}</p>
        )}
      </div>

      <div className="recent-card">
        <div className="panel-header compact">
          <div>
            <p className="eyebrow">Recently Saved</p>
            <h3>Interaction Timeline</h3>
          </div>
        </div>
        <div className="recent-list">
          {recentInteractions.length ? (
            recentInteractions.map((item) => (
              <article key={item.id} className="recent-item">
                <div>
                  <strong>{item.hcp_name}</strong>
                  <p>{item.interaction_type} - {item.interaction_date ?? "draft"}</p>
                </div>
                <span className={`sentiment-chip sentiment-chip--${item.sentiment}`}>{item.sentiment}</span>
              </article>
            ))
          ) : (
            <p className="muted">Saved interactions will appear here.</p>
          )}
        </div>
      </div>
    </section>
  );
}
