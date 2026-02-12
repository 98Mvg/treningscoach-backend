//
//  LanguageSelectionView.swift
//  TreningsCoach
//
//  Onboarding step 2: Choose English or Norwegian
//  Controls both UI text and coach voice language
//

import SwiftUI

struct LanguageSelectionView: View {
    let onLanguageSelected: (AppLanguage) -> Void
    @State private var appeared = false

    var body: some View {
        VStack(spacing: 0) {
            Spacer()

            Image(systemName: "globe")
                .font(.system(size: 56, weight: .light))
                .foregroundStyle(CoachiTheme.primaryGradient)
                .opacity(appeared ? 1 : 0)

            Text(L10n.chooseLanguage)
                .font(.system(size: 28, weight: .bold))
                .foregroundColor(CoachiTheme.textPrimary)
                .padding(.top, 20)
                .opacity(appeared ? 1 : 0)

            Text(L10n.languageSubtitle)
                .font(.system(size: 15))
                .foregroundColor(CoachiTheme.textSecondary)
                .padding(.top, 8)
                .opacity(appeared ? 1 : 0)

            VStack(spacing: 14) {
                languageCard(language: .en)
                languageCard(language: .no)
            }
            .padding(.horizontal, 40).padding(.top, 36)
            .opacity(appeared ? 1 : 0).offset(y: appeared ? 0 : 20)

            Spacer()
            Spacer()
        }
        .onAppear {
            withAnimation(.easeOut(duration: 0.6).delay(0.1)) { appeared = true }
        }
    }

    private func languageCard(language: AppLanguage) -> some View {
        Button {
            L10n.set(language)
            onLanguageSelected(language)
        } label: {
            HStack(spacing: 14) {
                Text(language.flagEmoji)
                    .font(.system(size: 36))

                VStack(alignment: .leading, spacing: 4) {
                    Text(language.displayName)
                        .font(.system(size: 17, weight: .semibold))
                        .foregroundColor(CoachiTheme.textPrimary)

                    Text(language == .en ? "English language & coach" : "Norsk spraak & coach")
                        .font(.system(size: 13))
                        .foregroundColor(CoachiTheme.textSecondary)
                }

                Spacer()

                Image(systemName: "chevron.right")
                    .foregroundColor(CoachiTheme.primary)
            }
            .padding(16)
            .background(CoachiTheme.surface)
            .clipShape(RoundedRectangle(cornerRadius: 14, style: .continuous))
            .overlay(
                RoundedRectangle(cornerRadius: 14, style: .continuous)
                    .stroke(Color.white.opacity(0.06), lineWidth: 1)
            )
        }
        .buttonStyle(.plain)
    }
}
