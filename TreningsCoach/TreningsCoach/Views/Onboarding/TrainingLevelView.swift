//
//  TrainingLevelView.swift
//  TreningsCoach
//
//  Training level selection: Beginner / Intermediate / Advanced
//  Influences coaching tone and intensity
//

import SwiftUI

struct TrainingLevelView: View {
    @ObservedObject var authManager: AuthManager
    let onComplete: () -> Void

    @State private var selectedLevel: TrainingLevel?

    var body: some View {
        ZStack {
            AppTheme.backgroundGradient.ignoresSafeArea()

            VStack(spacing: 32) {
                Spacer()

                // Header
                VStack(spacing: 12) {
                    Image(systemName: "chart.bar.fill")
                        .font(.system(size: 56))
                        .foregroundStyle(AppTheme.primaryAccent)

                    Text(L10n.trainingLevel)
                        .font(.largeTitle.bold())
                        .foregroundStyle(AppTheme.textPrimary)

                    Text(L10n.trainingLevelSubtitle)
                        .font(.subheadline)
                        .foregroundStyle(AppTheme.textSecondary)
                        .multilineTextAlignment(.center)
                }

                // Level cards
                VStack(spacing: 12) {
                    ForEach(TrainingLevel.allCases) { level in
                        levelCard(level: level)
                    }
                }
                .padding(.horizontal, 32)

                // Continue button
                if let selected = selectedLevel {
                    Button {
                        // Save level locally regardless of auth state
                        UserDefaults.standard.set(selected.rawValue, forKey: "training_level")
                        UserDefaults.standard.set(true, forKey: "has_completed_onboarding")
                        // Update backend profile if authenticated
                        Task {
                            await authManager.updateProfile(trainingLevel: selected)
                        }
                        onComplete()
                    } label: {
                        Text(L10n.getStarted)
                            .font(.headline)
                            .foregroundStyle(.white)
                            .frame(maxWidth: .infinity)
                            .padding(16)
                            .background(AppTheme.purpleGradient)
                            .clipShape(RoundedRectangle(cornerRadius: 12))
                    }
                    .padding(.horizontal, 32)
                    .transition(.opacity)
                }

                Spacer()
            }
            .animation(.easeInOut(duration: 0.2), value: selectedLevel)
        }
    }

    private func levelCard(level: TrainingLevel) -> some View {
        let isSelected = selectedLevel == level
        let cardColor = levelColor(for: level)

        return Button {
            selectedLevel = level
        } label: {
            HStack(spacing: 16) {
                Image(systemName: level.iconName)
                    .font(.title2)
                    .foregroundStyle(cardColor)
                    .frame(width: 44, height: 44)
                    .background(cardColor.opacity(0.15))
                    .clipShape(Circle())

                VStack(alignment: .leading, spacing: 4) {
                    Text(level.displayName)
                        .font(.headline)
                        .foregroundStyle(AppTheme.textPrimary)

                    Text(level.description)
                        .font(.caption)
                        .foregroundStyle(AppTheme.textSecondary)
                }

                Spacer()

                if isSelected {
                    Image(systemName: "checkmark.circle.fill")
                        .foregroundStyle(cardColor)
                        .font(.title3)
                }
            }
            .padding(16)
            .background(AppTheme.cardSurface)
            .clipShape(RoundedRectangle(cornerRadius: 14))
            .overlay(
                RoundedRectangle(cornerRadius: 14)
                    .stroke(isSelected ? cardColor : Color.clear, lineWidth: 2)
            )
        }
    }

    private func levelColor(for level: TrainingLevel) -> Color {
        switch level {
        case .beginner: return AppTheme.success
        case .intermediate: return AppTheme.primaryAccent
        case .advanced: return AppTheme.warning
        }
    }
}
