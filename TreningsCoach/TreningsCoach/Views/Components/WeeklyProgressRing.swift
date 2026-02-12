//
//  WeeklyProgressRing.swift
//  TreningsCoach
//
//  Weekly goal progress ring
//

import SwiftUI

struct WeeklyProgressRing: View {
    let completed: Int
    let goal: Int
    var size: CGFloat = 160

    private var progress: Double { Double(completed) / Double(max(goal, 1)) }

    var body: some View {
        ZStack {
            Circle().stroke(CoachiTheme.surface, lineWidth: 12).frame(width: size, height: size)
            Circle()
                .trim(from: 0, to: CGFloat(min(progress, 1.0)))
                .stroke(CoachiTheme.primaryGradient, style: StrokeStyle(lineWidth: 12, lineCap: .round))
                .frame(width: size, height: size)
                .rotationEffect(.degrees(-90))
                .animation(.spring(response: 0.8, dampingFraction: 0.7), value: progress)
            VStack(spacing: 4) {
                Text("\(completed)").font(.system(size: size * 0.25, weight: .bold, design: .rounded)).foregroundColor(CoachiTheme.textPrimary)
                Text("of \(goal)").font(.system(size: size * 0.09, weight: .medium)).foregroundColor(CoachiTheme.textSecondary)
            }
        }
    }
}
