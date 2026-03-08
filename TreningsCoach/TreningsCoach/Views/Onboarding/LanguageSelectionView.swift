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
        GeometryReader { geo in
            ScrollView(showsIndicators: false) {
                VStack(spacing: 0) {
                    Spacer(minLength: max(20, geo.size.height * 0.1))

                    Image(systemName: "globe")
                        .font(.largeTitle.weight(.light))
                        .foregroundStyle(CoachiTheme.primaryGradient)
                        .opacity(appeared ? 1 : 0)

                    Text(L10n.chooseLanguage)
                        .font(.title.weight(.bold))
                        .foregroundColor(CoachiTheme.textPrimary)
                        .multilineTextAlignment(.center)
                        .padding(.top, 20)
                        .opacity(appeared ? 1 : 0)

                    Text(L10n.languageSubtitle)
                        .font(.body)
                        .foregroundColor(CoachiTheme.textSecondary)
                        .multilineTextAlignment(.center)
                        .fixedSize(horizontal: false, vertical: true)
                        .padding(.top, 8)
                        .opacity(appeared ? 1 : 0)

                    VStack(spacing: 14) {
                        languageCard(language: .en)
                        languageCard(language: .no)
                    }
                    .padding(.top, 30)
                    .opacity(appeared ? 1 : 0)
                    .offset(y: appeared ? 0 : 20)

                    Text(L10n.current == .no ? "Du kan endre dette senere i profilen." : "You can change this later in Profile.")
                        .font(.footnote.weight(.semibold))
                        .foregroundColor(CoachiTheme.textSecondary)
                        .multilineTextAlignment(.center)
                        .padding(.top, 18)
                        .opacity(appeared ? 1 : 0)

                    Spacer(minLength: max(20, geo.size.height * 0.12))
                }
                .frame(minHeight: geo.size.height)
                .padding(.horizontal, geo.size.width < 390 ? 20 : 24)
                .padding(.top, max(20, geo.safeAreaInsets.top + 4))
                .padding(.bottom, max(24, geo.safeAreaInsets.bottom + 8))
            }
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
                    .font(.largeTitle)

                VStack(alignment: .leading, spacing: 4) {
                    Text(language.displayName)
                        .font(.headline.weight(.semibold))
                        .foregroundColor(CoachiTheme.textPrimary)

                    Text(language == .en ? "English language & coach" : "Norsk språk & coach")
                        .font(.footnote)
                        .foregroundColor(CoachiTheme.textSecondary)
                        .fixedSize(horizontal: false, vertical: true)
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
