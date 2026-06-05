import { useState, useRef, useEffect, useCallback } from 'react'
import './RecordScreen.css'

const API_BASE = import.meta.env.VITE_API_BASE ?? ''
const CANVAS_WIDTH = 320
const CANVAS_HEIGHT = 80

export default function RecordScreen({ promptText, onResult, onBack }) {
  const [phase, setPhase] = useState('idle') // idle | recording | recorded | submitting | error
  const [errorMsg, setErrorMsg] = useState('')
  const [audioURL, setAudioURL] = useState(null)
  const [audioBlob, setAudioBlob] = useState(null)

  const mediaRecorderRef = useRef(null)
  const chunksRef = useRef([])
  const streamRef = useRef(null)
  const canvasRef = useRef(null)
  const analyserRef = useRef(null)
  const animFrameRef = useRef(null)
  const audioCtxRef = useRef(null)

  const drawWaveform = useCallback(() => {
    const analyser = analyserRef.current
    const canvas = canvasRef.current
    if (!analyser || !canvas) return

    const ctx = canvas.getContext('2d')
    const bufferLength = analyser.frequencyBinCount
    const dataArray = new Uint8Array(bufferLength)

    const draw = () => {
      animFrameRef.current = requestAnimationFrame(draw)
      analyser.getByteTimeDomainData(dataArray)

      ctx.clearRect(0, 0, CANVAS_WIDTH, CANVAS_HEIGHT)

      ctx.lineWidth = 2
      ctx.strokeStyle = '#4f46e5'
      ctx.beginPath()

      const sliceWidth = CANVAS_WIDTH / bufferLength
      let x = 0
      for (let i = 0; i < bufferLength; i++) {
        const v = dataArray[i] / 128.0
        const y = (v * CANVAS_HEIGHT) / 2
        if (i === 0) ctx.moveTo(x, y)
        else ctx.lineTo(x, y)
        x += sliceWidth
      }
      ctx.lineTo(CANVAS_WIDTH, CANVAS_HEIGHT / 2)
      ctx.stroke()
    }

    draw()
  }, [])

  const stopAnimation = useCallback(() => {
    if (animFrameRef.current) {
      cancelAnimationFrame(animFrameRef.current)
      animFrameRef.current = null
    }
    // draw flat line
    const canvas = canvasRef.current
    if (canvas) {
      const ctx = canvas.getContext('2d')
      ctx.clearRect(0, 0, CANVAS_WIDTH, CANVAS_HEIGHT)
      ctx.lineWidth = 2
      ctx.strokeStyle = '#e5e7eb'
      ctx.beginPath()
      ctx.moveTo(0, CANVAS_HEIGHT / 2)
      ctx.lineTo(CANVAS_WIDTH, CANVAS_HEIGHT / 2)
      ctx.stroke()
    }
  }, [])

  const startRecording = useCallback(async () => {
    setErrorMsg('')
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true })
      streamRef.current = stream

      const audioCtx = new AudioContext()
      audioCtxRef.current = audioCtx
      const source = audioCtx.createMediaStreamSource(stream)
      const analyser = audioCtx.createAnalyser()
      analyser.fftSize = 1024
      source.connect(analyser)
      analyserRef.current = analyser

      const mimeType = MediaRecorder.isTypeSupported('audio/webm;codecs=opus')
        ? 'audio/webm;codecs=opus'
        : 'audio/webm'
      const recorder = new MediaRecorder(stream, { mimeType })
      mediaRecorderRef.current = recorder
      chunksRef.current = []

      recorder.ondataavailable = (e) => {
        if (e.data.size > 0) chunksRef.current.push(e.data)
      }

      recorder.onstop = () => {
        const blob = new Blob(chunksRef.current, { type: mimeType })
        setAudioBlob(blob)
        setAudioURL(URL.createObjectURL(blob))
        setPhase('recorded')
        stopAnimation()
        stream.getTracks().forEach((t) => t.stop())
        audioCtx.close()
      }

      recorder.start()
      setPhase('recording')
      drawWaveform()
    } catch (err) {
      setErrorMsg('মাইক্রোফোন ব্যবহার করতে পারছি না। অনুমতি দাও।')
      setPhase('error')
    }
  }, [drawWaveform, stopAnimation])

  const stopRecording = useCallback(() => {
    if (mediaRecorderRef.current && mediaRecorderRef.current.state !== 'inactive') {
      mediaRecorderRef.current.stop()
    }
  }, [])

  const submitAudio = useCallback(async () => {
    if (!audioBlob) return
    setPhase('submitting')

    try {
      const formData = new FormData()
      formData.append('audio', audioBlob, 'recording.webm')
      formData.append('prompt_text', promptText)

      const resp = await fetch(`${API_BASE}/analyse`, {
        method: 'POST',
        body: formData,
      })

      if (!resp.ok) {
        const text = await resp.text()
        throw new Error(`Server error ${resp.status}: ${text}`)
      }

      const data = await resp.json()
      onResult(data)
    } catch (err) {
      setErrorMsg(`সমস্যা হয়েছে: ${err.message}`)
      setPhase('error')
    }
  }, [audioBlob, promptText, onResult])

  const reset = useCallback(() => {
    if (audioURL) URL.revokeObjectURL(audioURL)
    setAudioURL(null)
    setAudioBlob(null)
    setErrorMsg('')
    setPhase('idle')
    stopAnimation()
  }, [audioURL, stopAnimation])

  // draw flat line on mount
  useEffect(() => {
    stopAnimation()
  }, [stopAnimation])

  // cleanup on unmount
  useEffect(() => {
    return () => {
      stopAnimation()
      streamRef.current?.getTracks().forEach((t) => t.stop())
      audioCtxRef.current?.close()
    }
  }, [stopAnimation])

  const isRecording = phase === 'recording'
  const isRecorded = phase === 'recorded'
  const isSubmitting = phase === 'submitting'

  return (
    <div className="record-screen">
      <div className="record-header">
        <button className="btn-back" onClick={onBack}>← ফিরে যাও</button>
        <div className="step-label">ধাপ ২ — রেকর্ড করো</div>
      </div>

      <div className="sentence-reminder">
        <p>{promptText}</p>
      </div>

      <div className="waveform-container">
        <canvas
          ref={canvasRef}
          width={CANVAS_WIDTH}
          height={CANVAS_HEIGHT}
          className="waveform"
        />
        {isRecording && <div className="recording-dot" />}
      </div>

      <div className="record-button-area">
        {!isRecorded && !isSubmitting && (
          <button
            className={`record-btn ${isRecording ? 'recording' : ''}`}
            onClick={isRecording ? stopRecording : startRecording}
            aria-label={isRecording ? 'রেকর্ড বন্ধ করো' : 'রেকর্ড শুরু করো'}
            disabled={phase === 'error'}
          >
            {isRecording ? (
              <span className="stop-icon" />
            ) : (
              <span className="mic-icon">🎙</span>
            )}
          </button>
        )}

        {isSubmitting && (
          <div className="spinner-wrap">
            <div className="spinner" />
            <p className="submitting-text">বিশ্লেষণ করছি…</p>
          </div>
        )}

        <p className="record-hint">
          {phase === 'idle' && 'বড় বোতামে চাপো — বলো — আবার চাপো।'}
          {phase === 'recording' && 'রেকর্ড হচ্ছে… শেষ হলে আবার চাপো।'}
          {phase === 'recorded' && 'শুনে দেখো, তারপর পাঠাও।'}
          {phase === 'submitting' && ''}
          {phase === 'error' && ''}
        </p>
      </div>

      {isRecorded && (
        <div className="playback-area">
          <audio controls src={audioURL} className="audio-player" />
          <div className="playback-actions">
            <button className="btn-secondary" onClick={reset}>আবার রেকর্ড করো</button>
            <button className="btn-primary" onClick={submitAudio}>
              পাঠাও →
            </button>
          </div>
        </div>
      )}

      {phase === 'error' && (
        <div className="error-banner">
          <p>{errorMsg}</p>
          <button className="btn-secondary" onClick={reset}>আবার চেষ্টা করো</button>
        </div>
      )}
    </div>
  )
}
