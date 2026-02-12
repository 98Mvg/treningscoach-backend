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

    var body: some View {
        TimelineView(.animation(minimumInterval: 1.0 / 20.0)) { timeline in
            let now = timeline.date.timeIntervalSinceReferenceDate
            HStack(spacing: 4) {
                ForEach(0..<barCount, id: \.self) { index in
                    let phase = index < phases.count ? phases[index] : 0
                    let speed = isActive ? 3.0 : 1.2
                    let wave = sin(now * speed + phase)
                    let normalizedWave = (wave + 1) / 2
                    let minHeight: CGFloat = isActive ? height * 0.2 : height * 0.1
                    let maxHeight: CGFloat = isActive ? height * 0.95 : height * 0.5
                    let barHeight = minHeight + CGFloat(normalizedWave) * (maxHeight - minHeight)

                    RoundedRectangle(cornerRadius: 3)
                        .fill(LinearGradient(
                            colors: [CoachiTheme.primary.opacity(isActive ? 0.9 : 0.4), CoachiTheme.secondary.opacity(isActive ? 0.7 : 0.2)],
                            startPoint: .bottom, endPoint: .top
                        ))
                        .frame(width: 4, height: barHeight)
                }
            }
            .frame(height: height)
        }
        .onAppear {
            phases = (0..<barCount).map { index in Double(index) * 0.5 + Double.random(in: 0...1) }
        }
    }
}
