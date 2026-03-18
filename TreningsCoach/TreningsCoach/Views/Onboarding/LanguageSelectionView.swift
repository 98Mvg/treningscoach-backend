//
//  LanguageSelectionView.swift
//  TreningsCoach
//
//  Onboarding step 2: Choose English or Norwegian
//  Controls both UI text and coach voice language
//

import SwiftUI
import UIKit

struct LanguageSelectionView: View {
    let onLanguageSelected: (AppLanguage) -> Void
    @State private var appeared = false

    var body: some View {
        GeometryReader { geo in
            let renderWidth = geo.size.width
            let renderHeight = geo.size.height
            let deviceWidth = UIScreen.main.bounds.width
            let layoutWidth = min(min(renderWidth, deviceWidth), 500)
            let horizontalSafeInset = max(geo.safeAreaInsets.leading, geo.safeAreaInsets.trailing)
            let sidePadding = (layoutWidth < 390 ? 18.0 : 22.0) + horizontalSafeInset
            let contentWidth = max(0.0, layoutWidth - (sidePadding * 2))
            let topSpacing = max(renderHeight * 0.16, geo.safeAreaInsets.top + 28.0)
            let bottomInset = min(42.0, max(24.0, geo.safeAreaInsets.bottom + 10.0))

            ScrollView(.vertical, showsIndicators: false) {
                VStack(spacing: 0) {
                    Spacer().frame(height: topSpacing)

                    Image(systemName: "globe")
                        .font(.largeTitle.weight(.light))
                        .foregroundStyle(CoachiTheme.primaryGradient)
                        .opacity(appeared ? 1 : 0)

                    Text(L10n.chooseLanguage)
                        .font(.title.weight(.bold))
                        .foregroundColor(CoachiTheme.textPrimary)
                        .multilineTextAlignment(.center)
                        .lineLimit(nil)
                        .fixedSize(horizontal: false, vertical: true)
                        .frame(width: contentWidth, alignment: .center)
                        .padding(.top, 20)
                        .opacity(appeared ? 1 : 0)

                    Text(L10n.languageSubtitle)
                        .font(.body)
                        .foregroundColor(CoachiTheme.textSecondary)
                        .multilineTextAlignment(.center)
                        .lineLimit(nil)
                        .fixedSize(horizontal: false, vertical: true)
                        .frame(width: contentWidth, alignment: .center)
                        .padding(.top, 8)
                        .opacity(appeared ? 1 : 0)

                    VStack(spacing: 14) {
                        languageCard(language: .en)
                        languageCard(language: .no)
                    }
                    .frame(width: contentWidth, alignment: .center)
                    .padding(.top, 30)
                    .opacity(appeared ? 1 : 0)
                    .offset(y: appeared ? 0 : 20)

                    Text(L10n.current == .no ? "Du kan endre dette senere i profilen." : "You can change this later in Profile.")
                        .font(.footnote.weight(.semibold))
                        .foregroundColor(CoachiTheme.textSecondary)
                        .multilineTextAlignment(.center)
                        .fixedSize(horizontal: false, vertical: true)
                        .frame(width: contentWidth, alignment: .center)
                        .padding(.top, 18)
                        .opacity(appeared ? 1 : 0)

                    Spacer().frame(height: bottomInset)
                }
                .frame(width: layoutWidth, alignment: .top)
                .frame(maxWidth: .infinity, alignment: .top)
            }
            .scrollBounceBehavior(.basedOnSize, axes: .vertical)
            .frame(width: layoutWidth, height: renderHeight, alignment: .top)
            .frame(maxWidth: .infinity, maxHeight: .infinity, alignment: .top)
            .clipped()
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
                        .lineLimit(1)

                    Text(language == .en ? "English language & coach" : "Norsk språk & coach")
                        .font(.footnote)
                        .foregroundColor(CoachiTheme.textSecondary)
                        .lineLimit(nil)
                        .fixedSize(horizontal: false, vertical: true)
                }
                .frame(maxWidth: .infinity, alignment: .leading)

                Spacer()

                Image(systemName: "chevron.right")
                    .foregroundColor(CoachiTheme.primary)
            }
            .padding(16)
            .frame(maxWidth: .infinity, alignment: .leading)
            .background(CoachiTheme.surface)
            .clipShape(RoundedRectangle(cornerRadius: 14, style: .continuous))
            .overlay(
                RoundedRectangle(cornerRadius: 14, style: .continuous)
                    .stroke(CoachiTheme.borderSubtle.opacity(0.36), lineWidth: 1)
            )
        }
        .buttonStyle(.plain)
    }
}
