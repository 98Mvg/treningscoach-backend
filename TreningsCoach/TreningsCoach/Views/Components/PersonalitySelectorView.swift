//
//  PersonalitySelectorView.swift
//  TreningsCoach
//
//  Horizontal scroll strip for selecting coach personality during workout
//  Compact design — must not distract from the workout orb
//

import SwiftUI

struct PersonalitySelectorView: View {
    @Binding var selectedPersonality: CoachPersonality
    let onSelect: (CoachPersonality) -> Void

    var body: some View {
        VStack(spacing: 8) {
            Text(L10n.selectCoach)
                .font(.caption.weight(.medium))
                .foregroundStyle(AppTheme.textSecondary)

            ScrollView(.horizontal, showsIndicators: false) {
                HStack(spacing: 10) {
                    ForEach(CoachPersonality.allCases) { personality in
                        personalityChip(personality)
                    }
                }
                .padding(.horizontal, 20)
            }
        }
    }

    private func personalityChip(_ personality: CoachPersonality) -> some View {
        let isSelected = selectedPersonality == personality

        return Button {
            selectedPersonality = personality
            onSelect(personality)
        } label: {
            HStack(spacing: 6) {
                Image(systemName: personality.icon)
                    .font(.caption)
                    .foregroundStyle(isSelected ? .white : personality.accentColor)

                Text(personality.displayName)
                    .font(.caption.weight(.semibold))
                    .foregroundStyle(isSelected ? .white : AppTheme.textPrimary)
            }
            .padding(.horizontal, 12)
            .padding(.vertical, 8)
            .background(
                isSelected
                    ? AnyShapeStyle(personality.accentColor)
                    : AnyShapeStyle(AppTheme.cardSurface)
            )
            .clipShape(Capsule())
            .overlay(
                Capsule()
                    .stroke(
                        isSelected ? personality.accentColor : AppTheme.textSecondary.opacity(0.2),
                        lineWidth: 1
                    )
            )
        }
        .animation(.easeInOut(duration: 0.2), value: isSelected)
    }
}
