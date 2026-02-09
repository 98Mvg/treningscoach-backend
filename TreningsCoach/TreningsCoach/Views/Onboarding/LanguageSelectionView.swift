//
//  LanguageSelectionView.swift
//  TreningsCoach
//
//  First onboarding screen: Choose English or Norwegian
//  Controls both UI text and coach voice language
//

import SwiftUI

struct LanguageSelectionView: View {
    let onLanguageSelected: (AppLanguage) -> Void

    var body: some View {
        ZStack {
            AppTheme.backgroundGradient.ignoresSafeArea()

            VStack(spacing: 40) {
                Spacer()

                // Title
                VStack(spacing: 12) {
                    Image(systemName: "globe")
                        .font(.system(size: 56))
                        .foregroundStyle(AppTheme.primaryAccent)

                    Text(L10n.chooseLanguage)
                        .font(.largeTitle.bold())
                        .foregroundStyle(AppTheme.textPrimary)

                    Text(L10n.languageSubtitle)
                        .font(.subheadline)
                        .foregroundStyle(AppTheme.textSecondary)
                }

                // Language cards
                VStack(spacing: 16) {
                    languageCard(language: .en)
                    languageCard(language: .no)
                }
                .padding(.horizontal, 32)

                Spacer()
                Spacer()
            }
        }
    }

    private func languageCard(language: AppLanguage) -> some View {
        Button {
            L10n.set(language)
            onLanguageSelected(language)
        } label: {
            HStack(spacing: 16) {
                Text(language.flagEmoji)
                    .font(.system(size: 40))

                VStack(alignment: .leading, spacing: 4) {
                    Text(language.displayName)
                        .font(.title3.bold())
                        .foregroundStyle(AppTheme.textPrimary)

                    Text(language == .en ? "English language & coach" : "Norsk spraak & coach")
                        .font(.caption)
                        .foregroundStyle(AppTheme.textSecondary)
                }

                Spacer()

                Image(systemName: "chevron.right")
                    .foregroundStyle(AppTheme.primaryAccent)
            }
            .padding(20)
            .background(AppTheme.cardSurface)
            .clipShape(RoundedRectangle(cornerRadius: 16))
            .overlay(
                RoundedRectangle(cornerRadius: 16)
                    .stroke(AppTheme.primaryAccent.opacity(0.2), lineWidth: 1)
            )
        }
    }
}
