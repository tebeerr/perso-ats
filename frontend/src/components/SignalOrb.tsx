import { useEffect, useState } from 'react'
import { Activity, Orbit, Sparkles } from 'lucide-react'

type SignalOrbProps = {
  score: number | null
  analyses: number
}

type Pointer = {
  x: number
  y: number
}

const initialPointer: Pointer = { x: 50, y: 50 }

export function SignalOrb({ score, analyses }: SignalOrbProps) {
  const [pointer, setPointer] = useState(initialPointer)
  const [reducedMotion, setReducedMotion] = useState(false)

  useEffect(() => {
    const mediaQuery = window.matchMedia('(prefers-reduced-motion: reduce)')
    const updateMotionPreference = () => setReducedMotion(mediaQuery.matches)
    updateMotionPreference()
    mediaQuery.addEventListener('change', updateMotionPreference)
    return () => mediaQuery.removeEventListener('change', updateMotionPreference)
  }, [])

  const handlePointerMove = (event: React.PointerEvent<HTMLDivElement>) => {
    if (reducedMotion) return
    const bounds = event.currentTarget.getBoundingClientRect()
    setPointer({
      x: ((event.clientX - bounds.left) / bounds.width) * 100,
      y: ((event.clientY - bounds.top) / bounds.height) * 100,
    })
  }

  const handlePointerLeave = () => setPointer(initialPointer)
  const tiltX = reducedMotion ? 0 : (pointer.y - 50) * -0.14
  const tiltY = reducedMotion ? 0 : (pointer.x - 50) * 0.14
  const displayScore = score === null ? '--' : Math.round(score)

  return (
    <div
      className="signal-orb"
      onPointerMove={handlePointerMove}
      onPointerLeave={handlePointerLeave}
      style={{ '--tilt-x': `${tiltX}deg`, '--tilt-y': `${tiltY}deg` } as React.CSSProperties}
      aria-label={score === null ? 'Resume analysis signal' : `Latest ATS score ${displayScore} out of 100`}
      role="img"
    >
      <div className="signal-grid" />
      <div className="signal-halo signal-halo-one" />
      <div className="signal-halo signal-halo-two" />
      <div className="signal-core">
        <div className="signal-core-glow" />
        <Sparkles size={17} />
        <strong>{displayScore}</strong>
        <span>ATS SIGNAL</span>
      </div>
      <div className="signal-orbit signal-orbit-one"><i /><i /><i /></div>
      <div className="signal-orbit signal-orbit-two"><i /><i /></div>
      <div className="signal-stat signal-stat-top"><Orbit size={13} /><span>LIVE MODEL</span></div>
      <div className="signal-stat signal-stat-bottom"><Activity size={13} /><span>{analyses ? `${analyses} ANALYS${analyses === 1 ? 'IS' : 'ES'}` : 'READY TO SCAN'}</span></div>
    </div>
  )
}
