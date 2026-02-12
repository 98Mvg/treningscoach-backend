//
//  TimerRingView.swift
//  TreningsCoach
//
//  Circular progress ring for workout timer
//

import SwiftUI

struct TimerRingView: View {
    let progress: Double  // 0.0 to 1.0
    var size: CGFloat = 200
    var lineWidth: CGFloat = 8

    var body: some View {
        ZStack {
            Circle().stroke(CoachiTheme.surface, lineWidth: lineWidth).frame(width: size, height: size)

            Circle()
                .trim(from: 0, to: CGFloat(min(progress, 1.0)))
                .stroke(
                    AngularGradient(colors: [CoachiTheme.primary, CoachiTheme.secondary, CoachiTheme.primary],
                                    center: .center, startAngle: .degrees(0), endAngle: .degrees(360)),
                    style: StrokeStyle(lineWidth: lineWidth, lineCap: .round)
                )
                .frame(width: size, height: size)
                .rotationEffect(.degrees(-90))
                .animation(.easeInOut(duration: 1), value: progress)

            if progress > 0.01 {
                Circle().fill(CoachiTheme.primary).frame(width: lineWidth * 1.5, height: lineWidth * 1.5)
                    .glow(color: CoachiTheme.primary, radius: 8)
                    .offset(y: -size / 2)
                    .rotationEffect(.degrees(360 * progress - 90))
                    .animation(.easeInOut(duration: 1), value: progress)
            }
        }
    }
}
