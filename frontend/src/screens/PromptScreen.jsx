import './PromptScreen.css'

export default function PromptScreen({ prompt, onNext }) {
  return (
    <div className="prompt-screen">
      <div className="prompt-header">
        <div className="brand">Meliglossa</div>
        <div className="tagline">Accent Coach</div>
      </div>

      <div className="prompt-card">
        <div className="step-label">ধাপ ১ — বাক্যটি পড়ো</div>

        <p className="bengali-instruction">{prompt.bengali_instruction}</p>

        <div className="sentence-box">
          <p className="sentence-text">{prompt.english}</p>
        </div>

        <p className="hint-text">
          মাইক্রোফোনে বলার আগে বাক্যটি মনে মনে একবার পড়ে নাও।
        </p>
      </div>

      <div className="prompt-footer">
        <button className="btn-primary" onClick={onNext}>
          রেকর্ড করতে প্রস্তুত →
        </button>
      </div>
    </div>
  )
}
