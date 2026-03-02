//
//  WaveformView.swift
//  TreningsCoach
//
//  Audio bar waveform visualization
//

import SwiftUI

struct WaveformView: View {
    var isActive: Bool = false
    var barCount: Int = 12
    var height: CGFloat = 50

    @State private var phases: [Double] = []

    private var safeBarCount: Int {
        max(1, barCount)
    }

    private var safeHeight: CGFloat {
        guard height.isFinite else { return 50 }
        return max(12, height)
    }

    var body: some View {
        Group {
            if isActive {
                TimelineView(.animation(minimumInterval: 1.0 / 20.0)) { timeline in
                    let now = timeline.date.timeIntervalSinceReferenceDate
                    let safeNow = now.isFinite ? now : 0
                    HStack(spacing: 4) {
                        ForEach(0..<safeBarCount, id: \.self) { index in
                            let phase = phaseFor(index)
                            let wave = sin(safeNow * 3.0 + phase)
                            let normalizedWave = (wave + 1) / 2
                            let minHeight = safeHeight * 0.2
                            let maxHeight = safeHeight * 0.95
                            let rawBarHeight = minHeight + CGFloat(normalizedWave) * (maxHeight - minHeight)
                            let barHeight = rawBarHeight.isFinite ? max(0, rawBarHeight) : minHeight

                            barView(height: barHeight, isAnimated: true)
                        }
                    }
                    .frame(height: safeHeight)
                }
            } else {
                HStack(spacing: 4) {
                    ForEach(0..<safeBarCount, id: \.self) { index in
                        let wave = abs(sin(phaseFor(index) + Double(index) * 0.35))
                        let minHeight = safeHeight * 0.16
                        let maxHeight = safeHeight * 0.42
                        let rawBarHeight = minHeight + CGFloat(wave) * (maxHeight - minHeight)
                        let barHeight = rawBarHeight.isFinite ? max(0, rawBarHeight) : minHeight
                        barView(height: barHeight, isAnimated: false)
                    }
                }
                .frame(height: safeHeight)
            }
        }
        .onAppear {
            if phases.count != safeBarCount {
                phases = (0..<safeBarCount).map { index in Double(index) * 0.5 + Double.random(in: 0...1) }
            }
        }
    }

    private func phaseFor(_ index: Int) -> Double {
        guard index >= 0 else { return 0 }
        if index < phases.count {
            let phase = phases[index]
            return phase.isFinite ? phase : 0
        }
        return Double(index) * 0.5
    }

    private func barView(height: CGFloat, isAnimated: Bool) -> some View {
        RoundedRectangle(cornerRadius: 3)
            .fill(
                LinearGradient(
                    colors: [
                        CoachiTheme.primary.opacity(isAnimated ? 0.9 : 0.35),
                        CoachiTheme.secondary.opacity(isAnimated ? 0.7 : 0.2),
                    ],
                    startPoint: .bottom,
                    endPoint: .top
                )
            )
            .frame(width: 4, height: height)
    }
}
