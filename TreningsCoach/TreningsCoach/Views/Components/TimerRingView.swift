//
//  TimerRingView.swift
//  TreningsCoach
//
//  Circular progress ring that wraps around the voice orb
//  Shows elapsed workout time as a visual arc
//

import SwiftUI

struct TimerRingView: View {
    let elapsedTime: TimeInterval
    var totalTime: TimeInterval = 45 * 60  // 45 min default (matches auto-timeout)
    var ringSize: CGFloat = 170
    var lineWidth: CGFloat = 5

    // Progress from 0.0 to 1.0
    private var progress: Double {
        guard totalTime > 0 else { return 0 }
        return min(elapsedTime / totalTime, 1.0)
    }

    var body: some View {
        ZStack {
            // Background track (dim ring)
            Circle()
                .stroke(
                    AppTheme.secondaryAccent.opacity(0.15),
                    style: StrokeStyle(lineWidth: lineWidth, lineCap: .round)
                )
                .frame(width: ringSize, height: ringSize)

            // Progress arc (bright cyan)
            Circle()
                .trim(from: 0, to: progress)
                .stroke(
                    AppTheme.secondaryAccent,
                    style: StrokeStyle(lineWidth: lineWidth, lineCap: .round)
                )
                .frame(width: ringSize, height: ringSize)
                .rotationEffect(.degrees(-90))  // Start from top
                .animation(.linear(duration: 1), value: progress)
        }
    }
}

#Preview {
    ZStack {
        AppTheme.backgroundGradient.ignoresSafeArea()
        TimerRingView(elapsedTime: 300, totalTime: 2700)
    }
}
