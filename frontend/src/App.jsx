import { useState } from 'react'
import PromptScreen from './screens/PromptScreen'
import RecordScreen from './screens/RecordScreen'
import FeedbackScreen from './screens/FeedbackScreen'
import './App.css'

const PROMPTS = [
  {
    english: "The reason is that the problem is more common than we think.",
    bengali_instruction: "নিচের বাক্যটি জোরে পড়ো — article (the / a) গুলোতে মনোযোগ দাও।",
  },
  {
    english: "What was the answer to the question about the environment?",
    bengali_instruction: "নিচের বাক্যটি স্বাভাবিকভাবে পড়ো — প্রতিটি শব্দ স্পষ্ট করে বলো।",
  },
  {
    english: "The solution is not obvious, but the difference is important.",
    bengali_instruction: "নিচের বাক্যটি পড়ো — vowel-গুলো ছোট ও দ্রুত রাখার চেষ্টা করো।",
  },
]

export default function App() {
  const [screen, setScreen] = useState('prompt')
  const [promptIndex] = useState(() => Math.floor(Math.random() * PROMPTS.length))
  const [result, setResult] = useState(null)

  const prompt = PROMPTS[promptIndex]

  return (
    <div className="app">
      {screen === 'prompt' && (
        <PromptScreen
          prompt={prompt}
          onNext={() => setScreen('record')}
        />
      )}
      {screen === 'record' && (
        <RecordScreen
          promptText={prompt.english}
          onResult={(data) => {
            setResult(data)
            setScreen('feedback')
          }}
          onBack={() => setScreen('prompt')}
        />
      )}
      {screen === 'feedback' && (
        <FeedbackScreen
          result={result}
          onReset={() => {
            setResult(null)
            setScreen('prompt')
          }}
        />
      )}
    </div>
  )
}
