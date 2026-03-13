//
//  AuthView.swift
//  TreningsCoach
//
//  Required account onboarding step.
//  Keeps the existing Apple + passwordless email auth model while matching the
//  refreshed register-first onboarding layout.
//

import SwiftUI
import UIKit

struct AuthView: View {
    @EnvironmentObject var authManager: AuthManager
    let onContinue: () -> Void
    let onContinueWithoutAccount: () -> Void

    @FocusState private var focusedField: Field?

    @State private var appeared = false
    @State private var emailAddress = ""
    @State private var verificationCode = ""
    @State private var emailCodeRequested = false
    @State private var acceptedTerms = false
    @State private var showTermsValidationError = false
    @State private var showTermsSheet = false
    @State private var showPrivacySheet = false

    private enum Field: Hashable {
        case email
        case code
    }

    private var hasEnabledProviders: Bool {
        AppConfig.Auth.appleSignInEnabled || AppConfig.Auth.emailSignInEnabled
    }

    private var normalizedEmail: String {
        emailAddress.trimmingCharacters(in: .whitespacesAndNewlines).lowercased()
    }

    private var canRequestEmailCode: Bool {
        AppConfig.Auth.emailSignInEnabled
            && acceptedTerms
            && normalizedEmail.contains("@")
            && normalizedEmail.contains(".")
            && !authManager.isLoading
    }

    private var canVerifyEmailCode: Bool {
        emailCodeRequested
            && acceptedTerms
            && verificationCode.trimmingCharacters(in: .whitespacesAndNewlines).count == 6
            && !authManager.isLoading
    }

    private var canContinueWithoutAccount: Bool {
        acceptedTerms && !authManager.isLoading
    }

    var body: some View {
        GeometryReader { geo in
            let renderWidth = geo.size.width
            let renderHeight = geo.size.height
            let deviceWidth = UIScreen.main.bounds.width
            let layoutWidth = min(min(renderWidth, deviceWidth), 500)
            let sidePadding = layoutWidth < 390 ? 16.0 : 20.0
            let contentWidth = max(0.0, layoutWidth - (sidePadding * 2))
            let bottomInset = min(42.0, max(24.0, geo.safeAreaInsets.bottom + 10.0))

            ScrollView(.vertical, showsIndicators: false) {
                VStack(spacing: 0) {
                    Spacer().frame(height: max(renderHeight * 0.12, geo.safeAreaInsets.top + 18.0))

                    header(contentWidth: contentWidth)

                    VStack(spacing: 14) {
                        appleButton
                        googleButton
                    }
                    .frame(width: contentWidth, alignment: .center)
                    .padding(.top, 26)
                    .opacity(appeared ? 1 : 0)
                    .offset(y: appeared ? 0 : 14)

                    divider(contentWidth: contentWidth)
                        .padding(.top, 20)
                        .opacity(appeared ? 1 : 0)

                    if AppConfig.Auth.emailSignInEnabled {
                        emailCard(contentWidth: contentWidth)
                            .padding(.top, 18)
                            .opacity(appeared ? 1 : 0)
                            .offset(y: appeared ? 0 : 18)
                    }

                    if let errorMessage = authManager.errorMessage, !errorMessage.isEmpty {
                        Text(errorMessage)
                            .font(.footnote.weight(.medium))
                            .foregroundColor(CoachiTheme.primary)
                            .multilineTextAlignment(.center)
                            .frame(width: contentWidth, alignment: .center)
                            .padding(.top, 14)
                    }

                    if !hasEnabledProviders {
                        Text(L10n.emailDeliveryUnavailable)
                            .font(.footnote.weight(.medium))
                            .foregroundColor(CoachiTheme.primary)
                            .multilineTextAlignment(.center)
                            .frame(width: contentWidth, alignment: .center)
                            .padding(.top, 14)
                    }

                    Spacer().frame(height: bottomInset)
                }
                .frame(width: layoutWidth, alignment: .top)
                .frame(maxWidth: .infinity, alignment: .top)
            }
            .scrollBounceBehavior(.basedOnSize, axes: .vertical)
            .scrollDismissesKeyboard(.interactively)
            .frame(width: layoutWidth, height: renderHeight, alignment: .top)
            .frame(maxWidth: .infinity, maxHeight: .infinity, alignment: .top)
            .clipped()
            .background {
                ZStack(alignment: .topTrailing) {
                    CoachiTheme.bg
                        .ignoresSafeArea()

                    Circle()
                        .fill(CoachiTheme.secondary.opacity(0.7))
                        .frame(width: 220, height: 220)
                        .blur(radius: 4)
                        .offset(x: 92, y: 120)
                }
            }
        }
        .simultaneousGesture(
            TapGesture().onEnded {
                hideKeyboard()
            }
        )
        .onAppear {
            withAnimation(.easeOut(duration: 0.6).delay(0.1)) { appeared = true }
        }
        .onChange(of: normalizedEmail) { _, _ in
            verificationCode = ""
            emailCodeRequested = false
        }
        .onChange(of: acceptedTerms) { _, isAccepted in
            if isAccepted {
                showTermsValidationError = false
            }
        }
        .sheet(isPresented: $showTermsSheet) {
            NavigationStack {
                TermsOfUseView()
            }
        }
        .sheet(isPresented: $showPrivacySheet) {
            NavigationStack {
                PrivacyPolicyView()
            }
        }
    }

    private func header(contentWidth: CGFloat) -> some View {
        VStack(spacing: 14) {
            Text(L10n.current == .no ? "Velkommen" : "Welcome")
                .font(.largeTitle.weight(.bold))
                .foregroundColor(CoachiTheme.textPrimary)
                .frame(width: contentWidth, alignment: .center)

            Text(
                L10n.current == .no
                    ? "Logg inn med Apple eller e-post for å lagre fremgangen din og låse opp Premium"
                    : "Sign in with Apple or email to save your progress and unlock Premium"
            )
            .font(.body.weight(.medium))
            .foregroundColor(CoachiTheme.textSecondary)
            .multilineTextAlignment(.center)
            .frame(width: contentWidth, alignment: .center)
            .fixedSize(horizontal: false, vertical: true)

            Text(L10n.accountRequiredHint)
                .font(.footnote.weight(.semibold))
                .foregroundColor(CoachiTheme.primary)
                .multilineTextAlignment(.center)
                .frame(width: contentWidth, alignment: .center)

            VStack(alignment: .leading, spacing: 12) {
                authBenefitRow(icon: "chart.line.uptrend.xyaxis", text: L10n.authBenefitSaveHistory)
                authBenefitRow(icon: "person.crop.circle.badge.checkmark", text: L10n.authBenefitSyncProfile)
                authBenefitRow(icon: "envelope.badge", text: L10n.authBenefitAppleOrEmail)
            }
            .padding(18)
            .background(CoachiTheme.surface.opacity(0.96))
            .clipShape(RoundedRectangle(cornerRadius: 20, style: .continuous))
            .overlay(
                RoundedRectangle(cornerRadius: 20, style: .continuous)
                    .stroke(CoachiTheme.borderSubtle.opacity(0.36), lineWidth: 1)
            )
            .frame(width: contentWidth, alignment: .center)
        }
    }

    private var appleButton: some View {
        socialButton(
            title: L10n.registerWithApple,
            icon: .system("applelogo"),
            disabled: authManager.isLoading
        ) {
            guard acceptedTerms else {
                withAnimation(.easeInOut(duration: 0.2)) {
                    showTermsValidationError = true
                }
                return
            }
            Task {
                let signedIn = await authManager.signInWithApple()
                if signedIn {
                    onContinue()
                }
            }
        }
    }

    private var googleButton: some View {
        Group {
            if AppConfig.Auth.googleSignInEnabled {
                socialButton(
                    title: L10n.registerWithGoogle,
                    icon: .text("G"),
                    disabled: authManager.isLoading
                ) {
                    Task { await authManager.signInWithGoogle() }
                }
            } else {
                socialButton(
                    title: L10n.registerWithGoogle,
                    icon: .text("G"),
                    disabled: true,
                    badge: L10n.current == .no ? "Kommer snart" : "Coming soon"
                ) {}
            }
        }
    }

    private func divider(contentWidth: CGFloat) -> some View {
        HStack(spacing: 12) {
            Rectangle()
                .fill(CoachiTheme.textTertiary.opacity(0.35))
                .frame(height: 1)

            Text(L10n.or)
                .font(.subheadline.weight(.semibold))
                .foregroundColor(CoachiTheme.textSecondary)

            Rectangle()
                .fill(CoachiTheme.textTertiary.opacity(0.35))
                .frame(height: 1)
        }
        .frame(width: contentWidth, alignment: .center)
    }

    private func emailCard(contentWidth: CGFloat) -> some View {
        VStack(alignment: .leading, spacing: 16) {
            Text(
                emailCodeRequested
                    ? (L10n.current == .no ? "Bekreft koden fra e-posten din" : "Verify the code from your email")
                    : (L10n.current == .no ? "Registrer deg med e-postadressen din" : "Register with your email address")
            )
            .font(.title3.weight(.bold))
            .foregroundColor(CoachiTheme.textPrimary)

            if emailCodeRequested {
                inputField(
                    title: L10n.emailCodeLabel,
                    text: $verificationCode,
                    keyboard: .numberPad,
                    textContentType: .oneTimeCode,
                    focused: .code
                )

                Text(L10n.emailCodeSentHint)
                    .font(.footnote.weight(.medium))
                    .foregroundColor(CoachiTheme.textSecondary)
                    .fixedSize(horizontal: false, vertical: true)
            } else {
                inputField(
                    title: L10n.emailAddress,
                    text: $emailAddress,
                    keyboard: .emailAddress,
                    textContentType: .emailAddress,
                    focused: .email
                )
            }

            termsSection

            primaryActionButton(
                title: emailCodeRequested
                    ? (L10n.current == .no ? "Bekreft kode" : "Verify code")
                    : L10n.register,
                disabled: emailCodeRequested ? !canVerifyEmailCode : !canRequestEmailCode
            ) {
                Task {
                    if emailCodeRequested {
                        let signedIn = await authManager.signInWithEmail(
                            email: normalizedEmail,
                            code: verificationCode
                        )
                        if signedIn {
                            onContinue()
                        }
                    } else {
                        let requested = await authManager.requestEmailSignInCode(email: normalizedEmail)
                        if requested {
                            emailCodeRequested = true
                            focusedField = .code
                        }
                    }
                }
            }

            secondaryActionButton(
                title: L10n.continueWithoutAccount,
                disabled: !canContinueWithoutAccount
            ) {
                guard acceptedTerms else {
                    withAnimation(.easeInOut(duration: 0.2)) {
                        showTermsValidationError = true
                    }
                    return
                }
                hideKeyboard()
                onContinueWithoutAccount()
            }

            Text(L10n.signInLaterHint)
                .font(.footnote.weight(.medium))
                .foregroundColor(CoachiTheme.textSecondary)
                .fixedSize(horizontal: false, vertical: true)
        }
        .padding(22)
        .frame(width: contentWidth, alignment: .leading)
        .background(CoachiTheme.surface.opacity(0.96))
        .clipShape(RoundedRectangle(cornerRadius: 24, style: .continuous))
        .overlay(
            RoundedRectangle(cornerRadius: 24, style: .continuous)
                .stroke(CoachiTheme.borderSubtle.opacity(0.36), lineWidth: 1)
        )
    }

    private var termsSection: some View {
        VStack(alignment: .leading, spacing: 10) {
            Button {
                acceptedTerms.toggle()
            } label: {
                HStack(alignment: .top, spacing: 12) {
                    Image(systemName: acceptedTerms ? "checkmark.square.fill" : "square")
                        .font(.title3.weight(.semibold))
                        .foregroundColor(acceptedTerms ? CoachiTheme.primary : CoachiTheme.textSecondary)
                        .padding(.top, 1)

                    Text(
                        L10n.current == .no
                            ? "Ved aa hake av i denne boksen godtar du Coachi sin personvernerklaering og vilkar for bruk."
                            : "By checking this box you accept Coachi's privacy policy and terms of use."
                    )
                    .font(.footnote.weight(.medium))
                    .foregroundColor(CoachiTheme.textPrimary)
                    .multilineTextAlignment(.leading)
                }
            }
            .buttonStyle(.plain)

            HStack(spacing: 14) {
                Button(L10n.privacyPolicy) {
                    showPrivacySheet = true
                }
                .font(.footnote.weight(.bold))
                .foregroundColor(CoachiTheme.primary)

                Button(L10n.termsOfUse) {
                    showTermsSheet = true
                }
                .font(.footnote.weight(.bold))
                .foregroundColor(CoachiTheme.primary)
            }

            if showTermsValidationError {
                Text(
                    L10n.current == .no
                        ? "Du maa godta vilkaarene foer du kan fortsette."
                        : "You must accept the terms before you can continue."
                )
                .font(.footnote.weight(.semibold))
                .foregroundColor(CoachiTheme.primary)
                .fixedSize(horizontal: false, vertical: true)
            }
        }
    }

    private enum SocialIcon {
        case system(String)
        case text(String)
    }

    private func socialButton(
        title: String,
        icon: SocialIcon,
        disabled: Bool,
        badge: String? = nil,
        action: @escaping () -> Void
    ) -> some View {
        Button(action: action) {
            HStack(spacing: 12) {
                Group {
                    switch icon {
                    case let .system(systemName):
                        Image(systemName: systemName)
                    case let .text(label):
                        Text(label)
                    }
                }
                .font(.title3.weight(.semibold))
                .foregroundColor(CoachiTheme.textPrimary)
                .frame(width: 22)

                Text(title)
                    .font(.body.weight(.bold))
                    .foregroundColor(CoachiTheme.textPrimary)

                Spacer()

                if let badge {
                    Text(badge)
                        .font(.caption.weight(.bold))
                        .foregroundColor(CoachiTheme.primary)
                        .padding(.horizontal, 10)
                        .padding(.vertical, 6)
                        .background(CoachiTheme.primary.opacity(0.1))
                        .clipShape(Capsule())
                } else if authManager.isLoading && !disabled {
                    ProgressView()
                        .tint(CoachiTheme.primary)
                }
            }
            .padding(.horizontal, 18)
            .frame(height: 58)
            .background(CoachiTheme.surface)
            .clipShape(RoundedRectangle(cornerRadius: 18, style: .continuous))
            .overlay(
                RoundedRectangle(cornerRadius: 18, style: .continuous)
                    .stroke(CoachiTheme.borderSubtle.opacity(0.45), lineWidth: 1)
            )
            .opacity(disabled ? 0.62 : 1)
        }
        .disabled(disabled)
    }

    private func primaryActionButton(title: String, disabled: Bool, action: @escaping () -> Void) -> some View {
        Button(action: action) {
            HStack {
                Spacer()
                if authManager.isLoading {
                    ProgressView()
                        .tint(.white)
                } else {
                    Text(title)
                        .font(.headline.weight(.bold))
                        .foregroundColor(.white)
                }
                Spacer()
            }
            .frame(height: 54)
        }
        .background {
            RoundedRectangle(cornerRadius: 18, style: .continuous)
                .fill(disabled ? AnyShapeStyle(CoachiTheme.textTertiary.opacity(0.55)) : AnyShapeStyle(CoachiTheme.primaryGradient))
        }
        .disabled(disabled)
    }

    private func secondaryActionButton(title: String, disabled: Bool, action: @escaping () -> Void) -> some View {
        Button(action: action) {
            HStack {
                Spacer()
                Text(title)
                    .font(.headline.weight(.bold))
                    .foregroundColor(disabled ? CoachiTheme.textSecondary : CoachiTheme.textPrimary)
                Spacer()
            }
            .frame(height: 54)
            .background(CoachiTheme.surfaceElevated.opacity(disabled ? 0.7 : 1))
            .clipShape(RoundedRectangle(cornerRadius: 18, style: .continuous))
            .overlay(
                RoundedRectangle(cornerRadius: 18, style: .continuous)
                    .stroke(CoachiTheme.borderSubtle.opacity(0.36), lineWidth: 1)
            )
        }
        .disabled(disabled)
    }

    private func inputField(
        title: String,
        text: Binding<String>,
        keyboard: UIKeyboardType,
        textContentType: UITextContentType?,
        focused: Field
    ) -> some View {
        TextField(title, text: text)
            .font(.body.weight(.semibold))
            .foregroundColor(CoachiTheme.textPrimary)
            .tint(CoachiTheme.textPrimary)
            .textInputAutocapitalization(.never)
            .autocorrectionDisabled()
            .keyboardType(keyboard)
            .textContentType(textContentType)
            .submitLabel(focused == .email && !emailCodeRequested ? .go : .done)
            .focused($focusedField, equals: focused)
            .onSubmit {
                if focused == .email {
                    if canRequestEmailCode {
                        hideKeyboard()
                    }
                } else {
                    hideKeyboard()
                }
            }
            .padding(.horizontal, 16)
            .frame(height: 54)
            .background(CoachiTheme.surfaceElevated)
            .clipShape(RoundedRectangle(cornerRadius: 16, style: .continuous))
            .overlay(
                RoundedRectangle(cornerRadius: 16, style: .continuous)
                    .stroke(CoachiTheme.borderSubtle.opacity(0.36), lineWidth: 1)
            )
    }

    private func authBenefitRow(icon: String, text: String) -> some View {
        HStack(alignment: .top, spacing: 12) {
            Image(systemName: icon)
                .font(.subheadline.weight(.semibold))
                .foregroundColor(CoachiTheme.primary)
                .frame(width: 20)

            Text(text)
                .font(.subheadline.weight(.semibold))
                .foregroundColor(CoachiTheme.textPrimary)
                .fixedSize(horizontal: false, vertical: true)

            Spacer(minLength: 0)
        }
    }

    private func hideKeyboard() {
        focusedField = nil
        UIApplication.shared.sendAction(#selector(UIResponder.resignFirstResponder), to: nil, from: nil, for: nil)
    }
}
