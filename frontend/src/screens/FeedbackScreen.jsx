import './FeedbackScreen.css'

const ERROR_LABELS = {
  article_omission: 'Article বাদ পড়েছে',
  vowel_elongation: 'Vowel টানা হয়েছে',
  vowel_quality_substitution: 'Vowel quality — সাবধান',
  w_onset: '/w/ উচ্চারণ',
}

const ERROR_ICONS = {
  article_omission: '📌',
  vowel_elongation: '〰️',
  vowel_quality_substitution: '🔊',
  w_onset: '👄',
}

export default function FeedbackScreen({ result, onReset }) {
  if (!result) return null

  const { transcript, errors = [], feedback_bengali, token_cost_usd } = result

  const uniqueErrorTypes = [...new Set(errors.map((e) => e.error_type))]

  return (
    <div className="feedback-screen">
      <div className="feedback-header">
        <div className="brand">Meliglossa</div>
        <div className="step-label">ধাপ ৩ — ফলাফল</div>
      </div>

      {/* Feedback card */}
      <div className="feedback-card">
        <div className="card-section-label">কোচের মন্তব্য</div>
        <p className="feedback-text">{feedback_bengali}</p>
      </div>

      {/* Detected errors */}
      {uniqueErrorTypes.length > 0 && (
        <div className="errors-card">
          <div className="card-section-label">যা লক্ষ্য করলাম</div>
          <ul className="error-list">
            {uniqueErrorTypes.map((type) => (
              <li key={type} className="error-item">
                <span className="error-icon">{ERROR_ICONS[type] ?? '⚠️'}</span>
                <span className="error-label">{ERROR_LABELS[type] ?? type}</span>
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Transcript */}
      <div className="transcript-card">
        <div className="card-section-label">Whisper শুনেছে</div>
        <p className="transcript-text">{transcript}</p>
        <HighlightedTranscript transcript={transcript} errors={errors} />
      </div>

      {/* Footer */}
      <div className="feedback-footer">
        {token_cost_usd != null && (
          <p className="cost-note">API cost: ${token_cost_usd.toFixed(4)}</p>
        )}
        <button className="btn-primary" onClick={onReset}>
          আবার চেষ্টা করো →
        </button>
      </div>
    </div>
  )
}

function HighlightedTranscript({ transcript, errors }) {
  if (!errors || errors.length === 0) return null

  // Collect all matched words/phrases from errors that have a matched_text field
  const highlights = errors
    .filter((e) => e.matched_text)
    .map((e) => ({ text: e.matched_text.toLowerCase(), type: e.error_type }))

  if (highlights.length === 0) return null

  // Simple word-level highlight: split on spaces, wrap matches
  const words = transcript.split(/(\s+)/)
  const result = words.map((token, i) => {
    const lower = token.toLowerCase().trim()
    const hit = highlights.find((h) => lower === h.text || lower.startsWith(h.text))
    if (hit) {
      return (
        <mark key={i} className={`highlight highlight-${hit.type}`}>
          {token}
        </mark>
      )
    }
    return token
  })

  return (
    <p className="transcript-highlighted">
      {result}
    </p>
  )
}
