//
//  StatCardView.swift
//  TreningsCoach
//
//  Reusable stat card for profile screen
//  Shows icon + value + label in a dark themed card
//

import SwiftUI

struct StatCardView: View {
    let title: String
    let value: String
    let icon: String
    var color: Color = AppTheme.primaryAccent

    var body: some View {
        VStack(spacing: 8) {
            Image(systemName: icon)
                .font(.title2)
                .foregroundStyle(color)

            Text(value)
                .font(.title2.bold())
                .foregroundStyle(AppTheme.textPrimary)

            Text(title)
                .font(.caption)
                .foregroundStyle(AppTheme.textSecondary)
        }
        .frame(maxWidth: .infinity)
        .padding(.vertical, 16)
        .cardStyle()
    }
}

#Preview {
    ZStack {
        AppTheme.backgroundGradient.ignoresSafeArea()
        HStack(spacing: 12) {
            StatCardView(title: "Workouts", value: "12", icon: "figure.run", color: AppTheme.primaryAccent)
            StatCardView(title: "Minutes", value: "340", icon: "clock.fill", color: AppTheme.secondaryAccent)
            StatCardView(title: "Streak", value: "5", icon: "flame.fill", color: AppTheme.warning)
        }
        .padding()
    }
}
