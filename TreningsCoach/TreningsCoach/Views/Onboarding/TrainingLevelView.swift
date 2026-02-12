//
//  TrainingLevelView.swift
//  TreningsCoach
//
//  Training level selection: Beginner / Intermediate / Advanced
//  Influences coaching tone and intensity — Coachi theme
//

import SwiftUI

struct TrainingLevelView: View {
    @ObservedObject var authManager: AuthManager
    let onComplete: () -> Void

    @State private var selectedLevel: TrainingLevel?
    @State private var appeared = false

    var body: some View {
        VStack(spacing: 0) {
            Spacer()

            Image(systemName: "chart.bar.fill")
                .font(.system(size: 56, weight: .light))
                .foregroundStyle(CoachiTheme.primaryGradient)
                .opacity(appeared ? 1 : 0)

            Text(L10n.trainingLevel)
                .font(.system(size: 28, weight: .bold))
                .foregroundColor(CoachiTheme.textPrimary)
                .padding(.top, 20)
                .opacity(appeared ? 1 : 0)

            Text(L10n.trainingLevelSubtitle)
                .font(.system(size: 15))
                .foregroundColor(CoachiTheme.textSecondary)
                .multilineTextAlignment(.center)
                .padding(.top, 8)
                .opacity(appeared ? 1 : 0)

            VStack(spacing: 12) {
                ForEach(TrainingLevel.allCases) { level in
                    levelCard(level: level)
                }
            }
            .padding(.horizontal, 40).padding(.top, 28)
            .opacity(appeared ? 1 : 0).offset(y: appeared ? 0 : 20)

            if let selected = selectedLevel {
                Button {
                    UserDefaults.standard.set(selected.rawValue, forKey: "training_level")
                    UserDefaults.standard.set(true, forKey: "has_completed_onboarding")
                    Task { await authManager.updateProfile(trainingLevel: selected) }
                    onComplete()
                } label: {
                    Text(L10n.getStarted)
                        .font(.system(size: 17, weight: .bold))
                        .foregroundColor(.white)
                        .frame(maxWidth: .infinity)
                        .frame(height: 56)
                        .background(CoachiTheme.primaryGradient)
                        .clipShape(RoundedRectangle(cornerRadius: 16, style: .continuous))
                }
                .padding(.horizontal, 40).padding(.top, 32)
                .transition(.opacity)
            }

            Spacer()
        }
        .animation(.easeInOut(duration: 0.2), value: selectedLevel)
        .onAppear {
            withAnimation(.easeOut(duration: 0.6).delay(0.1)) { appeared = true }
        }
    }

    private func levelCard(level: TrainingLevel) -> some View {
        let isSelected = selectedLevel == level
        let cardColor = levelColor(for: level)

        return Button {
            selectedLevel = level
        } label: {
            HStack(spacing: 14) {
                Image(systemName: level.iconName)
                    .font(.system(size: 18))
                    .foregroundColor(cardColor)
                    .frame(width: 40, height: 40)
                    .background(cardColor.opacity(0.15))
                    .clipShape(Circle())

                VStack(alignment: .leading, spacing: 4) {
                    Text(level.displayName)
                        .font(.system(size: 16, weight: .semibold))
                        .foregroundColor(isSelected ? CoachiTheme.textPrimary : CoachiTheme.textSecondary)

                    Text(level.description)
                        .font(.system(size: 13))
                        .foregroundColor(CoachiTheme.textTertiary)
                }

                Spacer()

                if isSelected {
                    Image(systemName: "checkmark.circle.fill")
                        .foregroundColor(cardColor)
                }
            }
            .padding(14)
            .background(isSelected ? cardColor.opacity(0.1) : CoachiTheme.surface)
            .clipShape(RoundedRectangle(cornerRadius: 14, style: .continuous))
            .overlay(
                RoundedRectangle(cornerRadius: 14, style: .continuous)
                    .stroke(isSelected ? cardColor.opacity(0.5) : Color.white.opacity(0.06), lineWidth: 1)
            )
        }
        .buttonStyle(.plain)
    }

    private func levelColor(for level: TrainingLevel) -> Color {
        switch level {
        case .beginner: return CoachiTheme.success
        case .intermediate: return CoachiTheme.primary
        case .advanced: return CoachiTheme.accent
        }
    }
}
