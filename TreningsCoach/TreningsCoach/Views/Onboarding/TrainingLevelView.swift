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
        GeometryReader { geo in
            ScrollView(showsIndicators: false) {
                VStack(spacing: 0) {
                    Spacer(minLength: max(20, geo.size.height * 0.08))

                    Image(systemName: "chart.bar.fill")
                        .font(.largeTitle.weight(.light))
                        .foregroundStyle(CoachiTheme.primaryGradient)
                        .opacity(appeared ? 1 : 0)

                    Text(L10n.trainingLevel)
                        .font(.title.weight(.bold))
                        .foregroundColor(CoachiTheme.textPrimary)
                        .multilineTextAlignment(.center)
                        .padding(.top, 20)
                        .opacity(appeared ? 1 : 0)

                    Text(L10n.trainingLevelSubtitle)
                        .font(.body)
                        .foregroundColor(CoachiTheme.textSecondary)
                        .multilineTextAlignment(.center)
                        .fixedSize(horizontal: false, vertical: true)
                        .padding(.top, 8)
                        .opacity(appeared ? 1 : 0)

                    VStack(spacing: 12) {
                        ForEach(TrainingLevel.allCases) { level in
                            levelCard(level: level)
                        }
                    }
                    .padding(.top, 24)
                    .opacity(appeared ? 1 : 0)
                    .offset(y: appeared ? 0 : 20)

                    if let selected = selectedLevel {
                        Button {
                            UserDefaults.standard.set(selected.rawValue, forKey: "training_level")
                            UserDefaults.standard.set(true, forKey: "has_completed_onboarding")
                            Task { await authManager.updateProfile(trainingLevel: selected) }
                            onComplete()
                        } label: {
                            Text(L10n.getStarted)
                                .font(.headline.weight(.bold))
                                .foregroundColor(.white)
                                .frame(maxWidth: .infinity)
                                .frame(minHeight: 56)
                                .background(CoachiTheme.primaryGradient)
                                .clipShape(RoundedRectangle(cornerRadius: 16, style: .continuous))
                        }
                        .padding(.top, 26)
                        .transition(.opacity)
                    }

                    Spacer(minLength: max(18, geo.size.height * 0.08))
                }
                .frame(minHeight: geo.size.height)
                .padding(.horizontal, geo.size.width < 390 ? 20 : 24)
                .padding(.top, max(20, geo.safeAreaInsets.top + 4))
                .padding(.bottom, max(24, geo.safeAreaInsets.bottom + 8))
            }
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
                    .font(.title3)
                    .foregroundColor(cardColor)
                    .frame(width: 40, height: 40)
                    .background(cardColor.opacity(0.15))
                    .clipShape(Circle())

                VStack(alignment: .leading, spacing: 4) {
                    Text(level.displayName)
                        .font(.body.weight(.semibold))
                        .foregroundColor(isSelected ? CoachiTheme.textPrimary : CoachiTheme.textSecondary)

                    Text(level.description)
                        .font(.footnote)
                        .foregroundColor(CoachiTheme.textTertiary)
                        .fixedSize(horizontal: false, vertical: true)
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
