//
//  RecentWorkoutRow.swift
//  TreningsCoach
//
//  Workout history row for home screen
//

import SwiftUI

struct RecentWorkoutRow: View {
    let workout: WorkoutRecord

    var body: some View {
        HStack(spacing: 14) {
            VStack(spacing: 2) {
                Text(workout.dayOfWeek).font(.system(size: 11, weight: .semibold)).foregroundColor(CoachiTheme.textSecondary).textCase(.uppercase)
            }
            .frame(width: 44, height: 44).background(CoachiTheme.surface).clipShape(Circle())

            VStack(alignment: .leading, spacing: 4) {
                Text("\(workout.durationFormatted) workout").font(.system(size: 15, weight: .semibold)).foregroundColor(CoachiTheme.textPrimary)
                Text("\(workout.avgIntensity.capitalized) intensity").font(.system(size: 13, weight: .medium)).foregroundColor(CoachiTheme.textSecondary)
            }

            Spacer()

            Text(workout.avgIntensity.capitalized)
                .font(.system(size: 11, weight: .bold)).foregroundColor(intensityColor)
                .padding(.horizontal, 10).padding(.vertical, 5)
                .background(intensityColor.opacity(0.15)).clipShape(Capsule())
        }
        .padding(.horizontal, 16).padding(.vertical, 12).cardStyle()
    }

    private var intensityColor: Color {
        switch workout.avgIntensity.lowercased() {
        case "calm":     return CoachiTheme.secondary
        case "moderate": return CoachiTheme.primary
        case "intense":  return CoachiTheme.accent
        case "critical": return CoachiTheme.danger
        default:         return CoachiTheme.textSecondary
        }
    }
}
