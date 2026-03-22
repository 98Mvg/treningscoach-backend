//
//  OnboardingContainerView.swift
//  TreningsCoach
//
//  Full onboarding flow:
//  Welcome -> Auth -> Profile -> explainer -> HR setup -> Habits -> Summary -> Result
//  -> Sensor connect/no sensor -> Premium bridge -> Notifications -> Main app
//

import StoreKit
import SwiftUI
import UIKit

enum OnboardingStep: Int {
    case welcome = 0
    case language = 1
    case features = 2
    case auth = 3
    case dataPurpose = 4
    case identity = 5
    case birthAndGender = 6
    case bodyMetrics = 7
    case maxHeartRate = 8
    case restingHeartRate = 9
    case enduranceHabits = 10
    case frequencyAndDuration = 11
    case summary = 12
    case result = 13
    case sensorConnect = 14
    case noSensorFallback = 15
    case premiumOffer = 16
    case notificationPermission = 17
}

private enum OnboardingGender: String, CaseIterable, Identifiable {
    case male
    case female

    var id: String { rawValue }

    var title: String {
        switch self {
        case .male:
            return L10n.current == .no ? "Mann" : "Male"
        case .female:
            return L10n.current == .no ? "Kvinne" : "Female"
        }
    }

    var icon: String {
        switch self {
        case .male:
            return "figure.stand"
        case .female:
            return "figure.stand.dress"
        }
    }
}

private enum HardestIntensityOption: String, CaseIterable, Identifiable {
    case low
    case moderate
    case high

    var id: String { rawValue }

    var title: String {
        switch self {
        case .low:
            return L10n.current == .no ? "Lav intensitet" : "Low intensity"
        case .moderate:
            return L10n.current == .no ? "Moderat intensitet" : "Moderate intensity"
        case .high:
            return L10n.current == .no ? "Høy intensitet" : "High intensity"
        }
    }

    var subtitle: String {
        switch self {
        case .low:
            return L10n.current == .no
                ? "Du blir bare lett andpusten og kan holde samme tempo lenge uten problemer."
                : "You only get lightly out of breath and can keep this pace for a long time."
        case .moderate:
            return L10n.current == .no
                ? "Du puster raskere og kjenner at du jobber, men du har fortsatt kontroll og kan holde på en god stund."
                : "You breathe harder and feel the effort, but still have control and can keep going for a while."
        case .high:
            return L10n.current == .no
                ? "Du blir tydelig andpusten, må jobbe hardt og klarer bare å holde intensiteten i korte drag."
                : "You get clearly out of breath, have to work hard, and can only hold the intensity for short bursts."
        }
    }

    var followUpQuestion: String {
        switch self {
        case .low:
            return L10n.current == .no
                ? "Hvor ofte og hvor lenge trener du vanligvis med lav intensitet?"
                : "How often and how long do you usually train at low intensity?"
        case .moderate:
            return L10n.current == .no
                ? "Hvor ofte og hvor lenge trener du vanligvis med moderat intensitet?"
                : "How often and how long do you usually train at moderate intensity?"
        case .high:
            return L10n.current == .no
                ? "Hvor ofte og hvor lenge trener du vanligvis med høy intensitet?"
                : "How often and how long do you usually train at high intensity?"
        }
    }

    var followUpExplanationTitle: String {
        switch self {
        case .low:
            return L10n.current == .no ? "Hva mener vi med lav intensitet?" : "What do we mean by low intensity?"
        case .moderate:
            return L10n.current == .no ? "Hva mener vi med moderat intensitet?" : "What do we mean by moderate intensity?"
        case .high:
            return L10n.current == .no ? "Hva mener vi med høy intensitet?" : "What do we mean by high intensity?"
        }
    }

    var followUpExplanationMessage: String {
        switch self {
        case .low:
            return L10n.current == .no
                ? "Lav intensitet er tempoet der du holder det rolig, puster kontrollert og kan fortsette lenge uten å bli veldig sliten."
                : "Low intensity is the pace where you keep it easy, breathe comfortably, and can continue for a long time without getting very tired."
        case .moderate:
            return L10n.current == .no
                ? "Moderat intensitet er tempoet der du puster raskere og kjenner at du jobber, men fortsatt kan holde det gående en stund."
                : "Moderate intensity is the pace where you breathe harder and feel the effort, but can still keep going for a while."
        case .high:
            return L10n.current == .no
                ? "Høy intensitet er tempoet der du blir tydelig andpusten, må jobbe hardt og bare kan holde det i korte drag."
                : "High intensity is the pace where you get clearly out of breath, have to work hard, and can only hold it for short bursts."
        }
    }
}

private enum ModerateFrequencyOption: String, CaseIterable, Identifiable {
    case never
    case lessThanWeekly
    case oncePerWeek
    case twoToThreePerWeek
    case fourOrMorePerWeek

    var id: String { rawValue }

    var title: String {
        switch self {
        case .never:
            return L10n.current == .no ? "Aldri" : "Never"
        case .lessThanWeekly:
            return L10n.current == .no ? "Sjeldnere enn en gang i uka" : "Less than once a week"
        case .oncePerWeek:
            return L10n.current == .no ? "En gang i uka" : "Once per week"
        case .twoToThreePerWeek:
            return L10n.current == .no ? "To til tre ganger i uka" : "Two to three times per week"
        case .fourOrMorePerWeek:
            return L10n.current == .no ? "Fire ganger eller mer i uka" : "Four or more times per week"
        }
    }
}

private enum ModerateDurationOption: String, CaseIterable, Identifiable {
    case lessThan30
    case between30And60
    case moreThan60

    var id: String { rawValue }

    var title: String {
        switch self {
        case .lessThan30:
            return L10n.current == .no ? "Mindre enn 30 minutter" : "Less than 30 minutes"
        case .between30And60:
            return L10n.current == .no ? "30-60 minutter" : "30-60 minutes"
        case .moreThan60:
            return L10n.current == .no ? "Mer enn 60 minutter" : "More than 60 minutes"
        }
    }
}

private enum OnboardingSummaryField {
    case identity
    case birthAndGender
    case bodyMetrics
    case maxHeartRate
    case restingHeartRate
    case enduranceHabits
    case frequencyAndDuration

    func targetStep(doesEnduranceTraining: Bool) -> OnboardingStep {
        switch self {
        case .identity:
            return .identity
        case .birthAndGender:
            return .birthAndGender
        case .bodyMetrics:
            return .bodyMetrics
        case .maxHeartRate:
            return .maxHeartRate
        case .restingHeartRate:
            return .restingHeartRate
        case .enduranceHabits:
            return .enduranceHabits
        case .frequencyAndDuration:
            return doesEnduranceTraining ? .frequencyAndDuration : .enduranceHabits
        }
    }
}

private struct OnboardingFormState {
    var firstName: String = ""
    var lastName: String = ""
    var birthDate: Date = Calendar.current.date(byAdding: .year, value: -28, to: Date()) ?? Date()
    var gender: OnboardingGender = .male
    var heightCm: Int = 178
    var weightKg: Int = 75
    var hrMax: Int = 192
    var restingHR: Int = 60
    var doesEnduranceTraining: Bool = true
    var hardestIntensity: HardestIntensityOption = .moderate
    var moderateFrequency: ModerateFrequencyOption = .twoToThreePerWeek
    var moderateDuration: ModerateDurationOption = .between30And60

    var displayName: String {
        let first = firstName.trimmingCharacters(in: .whitespacesAndNewlines)
        let last = lastName.trimmingCharacters(in: .whitespacesAndNewlines)
        let joined = [first, last].filter { !$0.isEmpty }.joined(separator: " ")
        return joined.isEmpty ? L10n.athlete : joined
    }

    var age: Int {
        let years = Calendar.current.dateComponents([.year], from: birthDate, to: Date()).year ?? 0
        return max(14, min(95, years))
    }

    var calculatedHRMaxFromAge: Int {
        max(150, min(220, 220 - age))
    }

    func toDraft(languageCode: String, notificationsOptIn: Bool) -> AppViewModel.OnboardingProfileDraft {
        AppViewModel.OnboardingProfileDraft(
            firstName: firstName.trimmingCharacters(in: .whitespacesAndNewlines),
            lastName: lastName.trimmingCharacters(in: .whitespacesAndNewlines),
            birthDate: birthDate,
            gender: gender.rawValue,
            heightCm: heightCm,
            weightKg: weightKg,
            hrMax: hrMax,
            restingHR: restingHR,
            doesEnduranceTraining: doesEnduranceTraining,
            hardestIntensity: hardestIntensity.rawValue,
            moderateSessionsPerWeek: moderateFrequency.rawValue,
            moderateDuration: moderateDuration.rawValue,
            notificationsOptIn: notificationsOptIn,
            languageCode: languageCode,
            trainingLevel: "beginner"
        )
    }
}

struct OnboardingContainerView: View {
    @EnvironmentObject var appViewModel: AppViewModel
    @EnvironmentObject private var authManager: AuthManager
    @EnvironmentObject private var subscriptionManager: SubscriptionManager

    @State private var currentStep: OnboardingStep = .welcome
    @State private var formState = OnboardingFormState()
    @State private var skipAccountStepAfterLanguage = false
    @State private var selectedLanguage: AppLanguage = L10n.current
    @State private var notificationBackStep: OnboardingStep = .sensorConnect
    @State private var finishingOnboarding = false

    var body: some View {
        ZStack {
            OnboardingAtmosphereView(step: currentStep)

            Group {
                switch currentStep {
                case .welcome:
                    FeaturesPageView(
                        mode: .intro,
                        onPrimary: {
                            skipAccountStepAfterLanguage = false
                            move(to: .language)
                        },
                        primaryTitle: L10n.continueButton,
                        onSecondary: {
                            skipAccountStepAfterLanguage = true
                            move(to: .language)
                        },
                        secondaryTitle: L10n.continueWithoutAccount
                    )
                    .transition(stepTransition)

                case .language:
                    LanguageSelectionView { language in
                        selectedLanguage = language
                        L10n.set(language)
                        move(to: skipAccountStepAfterLanguage ? .identity : .auth)
                    }
                    .transition(stepTransition)

                case .features, .dataPurpose:
                    FeaturesPageView(
                        mode: .postAuthExplainer(displayName: formState.displayName),
                        onPrimary: { move(to: .birthAndGender) },
                        primaryTitle: L10n.continueButton,
                        onSecondary: { move(to: .identity) },
                        secondaryTitle: L10n.current == .no ? "Tilbake" : "Back"
                    )
                    .transition(stepTransition)

                case .auth:
                    AuthView(mode: .register) {
                        if let currentUser = authManager.currentUser,
                           authManager.lastAuthCreatedNewUser == false,
                           currentUser.hasCompletedProfileSetup {
                            let displayName = authManager.currentUser?.resolvedDisplayName ?? ""
                            appViewModel.completeOnboardingForReturningUser(
                                displayName: displayName,
                                languageCode: L10n.current.rawValue
                            )
                        } else {
                            move(to: .identity)
                        }
                    } onContinueWithoutAccount: {
                        move(to: .identity)
                    }
                    .transition(stepTransition)

                case .identity:
                    IdentityStepView(
                        firstName: $formState.firstName,
                        lastName: $formState.lastName,
                        onBack: { move(to: skipAccountStepAfterLanguage ? .language : .auth) },
                        onContinue: { dismissKeyboardAndMove(to: .features) }
                    )
                    .transition(stepTransition)

                case .birthAndGender:
                    BirthGenderStepView(
                        birthDate: $formState.birthDate,
                        gender: $formState.gender,
                        onBack: { move(to: .features) },
                        onContinue: {
                            if formState.hrMax == 192 {
                                formState.hrMax = formState.calculatedHRMaxFromAge
                            }
                            move(to: .bodyMetrics)
                        }
                    )
                    .transition(stepTransition)

                case .bodyMetrics:
                    BodyMetricsStepView(
                        heightCm: $formState.heightCm,
                        weightKg: $formState.weightKg,
                        onBack: { move(to: .birthAndGender) },
                        onContinue: { move(to: .maxHeartRate) }
                    )
                    .transition(stepTransition)

                case .maxHeartRate:
                    MaxHeartRateStepView(
                        age: formState.age,
                        hrMax: $formState.hrMax,
                        onBack: { move(to: .bodyMetrics) },
                        onRecalculate: {
                            formState.hrMax = formState.calculatedHRMaxFromAge
                        },
                        onContinue: { move(to: .restingHeartRate) }
                    )
                    .transition(stepTransition)

                case .restingHeartRate:
                    RestingHeartRateStepView(
                        restingHR: $formState.restingHR,
                        onBack: { move(to: .maxHeartRate) },
                        onContinue: { move(to: .enduranceHabits) }
                    )
                    .transition(stepTransition)

                case .enduranceHabits:
                    EnduranceHabitStepView(
                        doesEnduranceTraining: $formState.doesEnduranceTraining,
                        hardestIntensity: $formState.hardestIntensity,
                        onBack: { move(to: .restingHeartRate) },
                        onContinue: { move(to: nextStepAfterEnduranceHabits) }
                    )
                    .transition(stepTransition)

                case .frequencyAndDuration:
                    FrequencyDurationStepView(
                        hardestIntensity: $formState.hardestIntensity,
                        moderateFrequency: $formState.moderateFrequency,
                        moderateDuration: $formState.moderateDuration,
                        onBack: { move(to: .enduranceHabits) },
                        onContinue: { move(to: .summary) }
                    )
                    .transition(stepTransition)

                case .summary:
                    SummaryStepView(
                        state: formState,
                        onBack: { move(to: summaryBackStep) },
                        onEditField: { field in
                            move(to: field.targetStep(doesEnduranceTraining: formState.doesEnduranceTraining))
                        },
                        onContinue: { move(to: .sensorConnect) }
                    )
                    .transition(stepTransition)

                case .result:
                    OnboardingResultStepView(
                        name: formState.displayName,
                        score: readinessScore,
                        age: formState.age,
                        onBack: { move(to: .summary) },
                        onContinue: { move(to: .sensorConnect) }
                    )
                    .transition(stepTransition)

                case .sensorConnect:
                    SensorConnectOnboardingView(
                        watchManager: PhoneWCManager.shared,
                        onBack: { move(to: .summary) },
                        onContinue: { watchConnected in
                            if !subscriptionManager.hasPremiumAccess {
                                notificationBackStep = .premiumOffer
                                move(to: .premiumOffer)
                            } else {
                                notificationBackStep = .sensorConnect
                                move(to: .notificationPermission)
                            }
                        }
                    )
                    .transition(stepTransition)

                case .noSensorFallback:
                    // Unreachable — kept for enum exhaustiveness.
                    // Sensor fallback content is now inline in SensorConnectOnboardingView.
                    SensorConnectOnboardingView(
                        watchManager: PhoneWCManager.shared,
                        onBack: { move(to: .sensorConnect) },
                        onContinue: { _ in
                            notificationBackStep = .noSensorFallback
                            move(to: .notificationPermission)
                        }
                    )
                    .transition(stepTransition)

                case .premiumOffer:
                    WatchConnectedPremiumOfferStepView(
                        watchManager: PhoneWCManager.shared,
                        onBack: { move(to: .sensorConnect) },
                        onContinue: {
                            notificationBackStep = .premiumOffer
                            move(to: .notificationPermission)
                        }
                    )
                    .transition(stepTransition)

                case .notificationPermission:
                    NotificationPermissionStepView(
                        isLoading: finishingOnboarding,
                        onBack: { move(to: notificationBackStep) },
                        onEnable: { requestNotificationsAndFinish() },
                        onSkip: { finishOnboarding(notificationsGranted: false) }
                    )
                    .transition(stepTransition)
                }
            }

            if showsGuidedProgress {
                VStack {
                    OnboardingFlowProgressView(
                        progress: onboardingProgress,
                        label: onboardingProgressLabel
                    )
                    .padding(.horizontal, 22)
                    .padding(.top, 6)
                    Spacer()
                }
                .allowsHitTesting(false)
                .transition(.opacity)
            }
        }
        .frame(maxWidth: .infinity, maxHeight: .infinity)
        .animation(AppConfig.Anim.transitionSpring, value: currentStep.rawValue)
        .statusBar(hidden: hidesStatusBar)
    }

    private var stepTransition: AnyTransition {
        .asymmetric(insertion: .move(edge: .trailing), removal: .move(edge: .leading))
    }

    private var readinessScore: Int {
        var score = 60
        switch formState.moderateFrequency {
        case .never:
            score += 0
        case .lessThanWeekly:
            score += 5
        case .oncePerWeek:
            score += 10
        case .twoToThreePerWeek:
            score += 18
        case .fourOrMorePerWeek:
            score += 25
        }

        switch formState.moderateDuration {
        case .lessThan30:
            score += 4
        case .between30And60:
            score += 8
        case .moreThan60:
            score += 12
        }

        if formState.doesEnduranceTraining {
            score += 8
        }

        return max(45, min(95, score))
    }

    private var guidedOnboardingSteps: [OnboardingStep] {
        var steps: [OnboardingStep] = [
            .birthAndGender,
            .bodyMetrics,
            .maxHeartRate,
            .restingHeartRate,
            .enduranceHabits,
            .summary,
            .sensorConnect,
            .notificationPermission,
        ]
        if formState.doesEnduranceTraining {
            steps.insert(.frequencyAndDuration, at: 5)
        }
        // premiumOffer excluded — no progress bar on plan selection
        return steps
    }

    private var nextStepAfterEnduranceHabits: OnboardingStep {
        formState.doesEnduranceTraining ? .frequencyAndDuration : .summary
    }

    private var summaryBackStep: OnboardingStep {
        formState.doesEnduranceTraining ? .frequencyAndDuration : .enduranceHabits
    }

    private var showsGuidedProgress: Bool {
        guidedOnboardingSteps.contains(currentStep)
    }

    private var onboardingProgress: CGFloat {
        guard let index = guidedOnboardingSteps.firstIndex(of: currentStep) else { return 0 }
        let numerator = Double(index + 1)
        let denominator = Double(guidedOnboardingSteps.count)
        return CGFloat(max(0.0, min(1.0, numerator / denominator)))
    }

    private var onboardingProgressLabel: String {
        guard let index = guidedOnboardingSteps.firstIndex(of: currentStep) else { return "" }
        let current = index + 1
        let total = guidedOnboardingSteps.count
        if L10n.current == .no {
            return "Steg \(current) av \(total)"
        }
        return "Step \(current) of \(total)"
    }

    private var hidesStatusBar: Bool {
        true
    }

    private func move(to step: OnboardingStep) {
        withAnimation(AppConfig.Anim.transitionSpring) {
            currentStep = step
        }
    }

    private func dismissKeyboardAndMove(to step: OnboardingStep) {
        UIApplication.shared.sendAction(#selector(UIResponder.resignFirstResponder), to: nil, from: nil, for: nil)
        DispatchQueue.main.asyncAfter(deadline: .now() + 0.08) {
            move(to: step)
        }
    }

    private func requestNotificationsAndFinish() {
        guard !finishingOnboarding else { return }
        finishingOnboarding = true

        Task {
            let granted = await appViewModel.pushNotificationManager.requestAuthorizationAndRegister()
            await MainActor.run {
                finishOnboarding(notificationsGranted: granted)
            }
        }
    }

    private func finishOnboarding(notificationsGranted: Bool) {
        guard !appViewModel.hasCompletedOnboarding else { return }
        let profileDraft = formState.toDraft(languageCode: selectedLanguage.rawValue, notificationsOptIn: notificationsGranted)
        appViewModel.completeOnboarding(profile: profileDraft)
    }
}

private struct OnboardingFlowProgressView: View {
    let progress: CGFloat
    let label: String

    var body: some View {
        VStack(alignment: .leading, spacing: 6) {
            Text(label)
                .font(.caption.weight(.semibold))
                .foregroundColor(CoachiTheme.textSecondary)

            GeometryReader { geometry in
                let width = max(0, geometry.size.width * progress)
                ZStack(alignment: .leading) {
                    Capsule()
                        .fill(CoachiTheme.surface.opacity(0.9))
                        .frame(height: 6)
                    Capsule()
                        .fill(CoachiTheme.primaryGradient)
                        .frame(width: width, height: 6)
                }
            }
            .frame(height: 6)
        }
        .padding(12)
        .background(CoachiTheme.surface.opacity(0.78))
        .overlay(
            RoundedRectangle(cornerRadius: 12, style: .continuous)
                .stroke(CoachiTheme.borderSubtle.opacity(0.45), lineWidth: 1)
        )
        .clipShape(RoundedRectangle(cornerRadius: 12, style: .continuous))
    }
}

struct OnboardingAtmosphereView: View {
    let step: OnboardingStep
    @Environment(\.colorScheme) private var colorScheme

    private var imageName: String {
        switch step {
        case .welcome, .language, .features, .auth, .identity, .dataPurpose:
            return "OnboardingBgOutdoor"
        case .birthAndGender, .bodyMetrics, .maxHeartRate, .restingHeartRate, .enduranceHabits, .frequencyAndDuration, .summary, .result:
            return "OnboardingBgRun"
        case .sensorConnect, .noSensorFallback, .premiumOffer, .notificationPermission:
            return "OnboardingBgCalm"
        }
    }

    var body: some View {
        ZStack {
            CoachiTheme.backgroundGradient.ignoresSafeArea()

            Image(imageName)
                .resizable()
                .scaledToFill()
                .ignoresSafeArea()
                .blur(radius: colorScheme == .dark ? 12 : 9)
                .opacity(colorScheme == .dark ? 0.28 : 0.42)

            LinearGradient(
                colors: colorScheme == .dark
                    ? [Color.black.opacity(0.54), Color.black.opacity(0.14), Color.black.opacity(0.56)]
                    : [Color.white.opacity(0.28), Color(hex: "EEF4FF").opacity(0.24), Color(hex: "D6E3FF").opacity(0.52)],
                startPoint: .top,
                endPoint: .bottom
            )
            .ignoresSafeArea()

            RadialGradient(
                colors: colorScheme == .dark
                    ? [CoachiTheme.primary.opacity(0.16), .clear]
                    : [Color(hex: "8FA5FF").opacity(0.24), .clear],
                center: .topLeading,
                startRadius: 70,
                endRadius: 460
            )
            .ignoresSafeArea()

            LinearGradient(
                colors: [
                    Color(hex: "8AA8FF").opacity(colorScheme == .dark ? 0.05 : 0.14),
                    Color.clear,
                    Color(hex: "B7C7FF").opacity(colorScheme == .dark ? 0.02 : 0.09),
                ],
                startPoint: .topLeading,
                endPoint: .bottomTrailing
            )
            .ignoresSafeArea()
        }
    }
}

private struct IdentityStepView: View {
    private enum Field: Hashable {
        case firstName
        case lastName
    }

    @Binding var firstName: String
    @Binding var lastName: String
    let onBack: () -> Void
    let onContinue: () -> Void

    @FocusState private var focusedField: Field?

    private var canContinue: Bool {
        !firstName.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty
            && !lastName.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty
    }

    var body: some View {
        OnboardingScaffold(
            title: L10n.firstNameLabel,
            subtitle: L10n.current == .no
                ? "Hva er etternavnet ditt?"
                : "What is your last name?",
            onBack: onBack,
            primaryTitle: L10n.continueButton,
            canContinue: canContinue,
            onPrimary: {
                continueAfterKeyboardDismiss()
            }
        ) {
            VStack(spacing: 16) {
                identityInputField(
                    label: L10n.firstNameLabel,
                    placeholder: L10n.firstNamePlaceholder,
                    text: $firstName,
                    focused: .firstName,
                    submitLabel: .next
                ) {
                    focusedField = .lastName
                }

                identityInputField(
                    label: L10n.lastNameLabel,
                    placeholder: L10n.lastNamePlaceholder,
                    text: $lastName,
                    focused: .lastName,
                    submitLabel: .done
                ) {
                    if canContinue {
                        continueAfterKeyboardDismiss()
                    }
                }
            }
        }
        .onAppear {
            Task { @MainActor in
                await Task.yield()
                focusedField = .firstName
            }
        }
    }

    private func identityInputField(
        label: String,
        placeholder: String,
        text: Binding<String>,
        focused: Field,
        submitLabel: SubmitLabel,
        onSubmit: @escaping () -> Void
    ) -> some View {
        VStack(alignment: .leading, spacing: 8) {
            Text(label)
                .font(.subheadline.weight(.semibold))
                .foregroundColor(CoachiTheme.textPrimary)

            TextField("", text: text, prompt: Text(placeholder).foregroundColor(CoachiTheme.textTertiary))
                .font(.body.weight(.medium))
                .foregroundColor(CoachiTheme.textPrimary)
                .textInputAutocapitalization(.words)
                .autocorrectionDisabled()
                .submitLabel(submitLabel)
                .focused($focusedField, equals: focused)
                .onSubmit(onSubmit)
                .padding(.horizontal, 14)
                .frame(height: 50)
                .background(CoachiTheme.surface)
                .clipShape(RoundedRectangle(cornerRadius: 12, style: .continuous))
                .overlay(
                    RoundedRectangle(cornerRadius: 12, style: .continuous)
                        .stroke(CoachiTheme.borderSubtle.opacity(0.45), lineWidth: 1)
                )
        }
    }

    private func continueAfterKeyboardDismiss() {
        focusedField = nil
        UIApplication.shared.sendAction(#selector(UIResponder.resignFirstResponder), to: nil, from: nil, for: nil)
        Task { @MainActor in
            await Task.yield()
            onContinue()
        }
    }
}

private struct DataPurposeStepView: View {
    let firstName: String
    let onBack: () -> Void
    let onContinue: () -> Void

    var body: some View {
        GeometryReader { geo in
            let renderWidth = geo.size.width
            let renderHeight = geo.size.height
            let deviceWidth = UIScreen.main.bounds.width
            let layoutWidth = min(min(renderWidth, deviceWidth), 500)
            let sidePadding = layoutWidth < 390 ? 18.0 : 24.0
            let contentWidth = max(0.0, layoutWidth - (sidePadding * 2))
            let textWidth = max(0.0, min(contentWidth, layoutWidth < 390 ? 288.0 : 328.0))
            let topInset = max(renderHeight * 0.18, geo.safeAreaInsets.top + 42.0)
            let bottomInset = max(20.0, geo.safeAreaInsets.bottom + 10.0)
            let controlsHeight = 74.0 + bottomInset + 24.0

            ZStack {
                Image("OnboardingBgOutdoor")
                    .resizable()
                    .scaledToFill()
                    .frame(width: layoutWidth, height: renderHeight)
                    .clipped()
                    .overlay(
                        LinearGradient(
                            colors: [Color.black.opacity(0.34), CoachiTheme.primary.opacity(0.14), Color.black.opacity(0.56)],
                            startPoint: .top,
                            endPoint: .bottom
                        )
                    )

                VStack(alignment: .leading, spacing: 0) {
                    Spacer()
                        .frame(height: topInset)

                    VStack(alignment: .leading, spacing: 16) {
                        Text(greetingTitle)
                            .font(.system(size: 38, weight: .semibold, design: .rounded))
                            .foregroundColor(.white)
                            .multilineTextAlignment(.leading)
                            .fixedSize(horizontal: false, vertical: true)
                            .frame(width: textWidth, alignment: .leading)

                        Text(greetingBody)
                            .font(.system(size: 34, weight: .semibold, design: .rounded))
                            .foregroundColor(.white.opacity(0.96))
                            .lineSpacing(3)
                            .multilineTextAlignment(.leading)
                            .fixedSize(horizontal: false, vertical: true)
                            .frame(width: textWidth, alignment: .leading)
                    }
                    .frame(width: contentWidth, alignment: .leading)
                    .padding(.horizontal, sidePadding)
                    .padding(.bottom, controlsHeight)

                    Spacer(minLength: 0)
                }

                VStack {
                    Spacer(minLength: 0)

                    HStack(spacing: 16) {
                        Button(action: onBack) {
                            Image(systemName: "chevron.left")
                                .font(.title2.weight(.bold))
                                .foregroundColor(CoachiTheme.primary)
                                .frame(width: 74, height: 74)
                                .background(Color.white.opacity(0.97))
                                .clipShape(Circle())
                                .overlay(
                                    Circle()
                                        .stroke(CoachiTheme.primary.opacity(0.85), lineWidth: 2)
                                )
                        }
                        .buttonStyle(.plain)

                        Spacer()

                        Button(action: onContinue) {
                            HStack(spacing: 14) {
                                Text(L10n.current == .no ? "Neste" : "Next")
                                Image(systemName: "chevron.right")
                                    .font(.title3.weight(.bold))
                            }
                                .font(.title3.weight(.bold))
                                .foregroundColor(.white)
                                .padding(.horizontal, 32)
                                .frame(height: 74)
                                .background(CoachiTheme.primaryGradient.opacity(0.96))
                                .clipShape(RoundedRectangle(cornerRadius: 28, style: .continuous))
                        }
                        .buttonStyle(.plain)
                    }
                    .padding(.horizontal, sidePadding)
                    .padding(.bottom, bottomInset)
                }
            }
            .frame(width: layoutWidth, height: renderHeight, alignment: .topLeading)
            .frame(maxWidth: .infinity, maxHeight: .infinity, alignment: .top)
        }
        .onTapGesture {
            hideKeyboard()
        }
    }

    private var greetingTitle: String {
        let sanitized = firstName.trimmingCharacters(in: .whitespacesAndNewlines)
        let fallback = L10n.current == .no ? "der" : "there"
        let displayName = sanitized.isEmpty ? fallback : sanitized

        return "Hello! \(displayName)"
    }

    private var greetingBody: String {
        "Let me first explain what we can do for you."
    }

    private func hideKeyboard() {
        UIApplication.shared.sendAction(#selector(UIResponder.resignFirstResponder), to: nil, from: nil, for: nil)
    }
}

private struct BirthGenderStepView: View {
    @Binding var birthDate: Date
    @Binding var gender: OnboardingGender
    let onBack: () -> Void
    let onContinue: () -> Void

    private var maxDate: Date { Date() }
    private var minDate: Date { Calendar.current.date(byAdding: .year, value: -95, to: Date()) ?? Date() }

    var body: some View {
        OnboardingScaffold(
            title: L10n.aboutYou,
            subtitle: L10n.current == .no
                ? "Når ble du født, og hvordan vil du beskrive kjønn?"
                : "When were you born, and how would you describe your gender?",
            onBack: onBack,
            primaryTitle: L10n.continueButton,
            canContinue: true,
            onPrimary: onContinue
        ) {
            VStack(alignment: .leading, spacing: 18) {
                Text(L10n.current == .no ? "Fødselsdato" : "Date of birth")
                    .font(.body.weight(.semibold))
                    .foregroundColor(CoachiTheme.textPrimary)

                DatePicker(
                    "",
                    selection: $birthDate,
                    in: minDate...maxDate,
                    displayedComponents: .date
                )
                .datePickerStyle(.wheel)
                .labelsHidden()
                .tint(CoachiTheme.primary)
                .padding(.horizontal, 8)
                .padding(.vertical, 10)
                .frame(height: 172)
                .frame(maxWidth: .infinity, alignment: .leading)
                .background(CoachiTheme.surface)
                .clipShape(RoundedRectangle(cornerRadius: 14, style: .continuous))
                .overlay(
                    RoundedRectangle(cornerRadius: 14, style: .continuous)
                        .stroke(CoachiTheme.borderSubtle.opacity(0.45), lineWidth: 1)
                )

                Text(L10n.current == .no ? "Kjønn" : "Gender")
                    .font(.body.weight(.semibold))
                    .foregroundColor(CoachiTheme.textPrimary)
                    .padding(.top, 4)

                HStack(spacing: 12) {
                    ForEach(OnboardingGender.allCases) { option in
                        Button {
                            gender = option
                        } label: {
                            VStack(spacing: 10) {
                                Image(systemName: option.icon)
                                    .font(.title2.weight(.medium))
                                Text(option.title)
                                    .font(.body.weight(.semibold))
                            }
                            .foregroundColor(gender == option ? .white : CoachiTheme.textPrimary)
                            .frame(maxWidth: .infinity)
                            .frame(height: 96)
                            .background(gender == option ? CoachiTheme.primary : CoachiTheme.surface)
                            .clipShape(RoundedRectangle(cornerRadius: 16, style: .continuous))
                            .overlay(
                                RoundedRectangle(cornerRadius: 16, style: .continuous)
                                    .stroke(gender == option ? Color.clear : CoachiTheme.borderSubtle.opacity(0.45), lineWidth: 1)
                            )
                        }
                        .buttonStyle(.plain)
                    }
                }
            }
        }
    }
}

private struct BodyMetricsStepView: View {
    @Binding var heightCm: Int
    @Binding var weightKg: Int
    let onBack: () -> Void
    let onContinue: () -> Void

    @State private var heightText = ""
    @State private var weightText = ""

    private var parsedHeight: Int? {
        guard let value = Int(heightText), (130...230).contains(value) else { return nil }
        return value
    }

    private var parsedWeight: Int? {
        guard let value = Int(weightText), (35...220).contains(value) else { return nil }
        return value
    }

    private var canContinue: Bool {
        parsedHeight != nil && parsedWeight != nil
    }

    var body: some View {
        OnboardingScaffold(
            title: L10n.aboutYou,
            subtitle: L10n.current == .no ? "Høyde og vekt hjelper oss med bedre HR-rammer." : "Height and weight help us set better HR targets.",
            onBack: onBack,
            primaryTitle: L10n.continueButton,
            canContinue: canContinue,
            onPrimary: {
                if let parsedHeight {
                    heightCm = parsedHeight
                }
                if let parsedWeight {
                    weightKg = parsedWeight
                }
                onContinue()
            }
        ) {
            VStack(spacing: 16) {
                OnboardingNumericField(
                    label: L10n.current == .no ? "Hvor høy er du?" : "How tall are you?",
                    placeholder: "178",
                    unit: "cm",
                    text: $heightText
                )

                OnboardingNumericField(
                    label: L10n.current == .no ? "Hva veier du?" : "What is your weight?",
                    placeholder: "75",
                    unit: "kg",
                    text: $weightText
                )
            }
            .onAppear {
                if heightText.isEmpty {
                    heightText = String(heightCm)
                }
                if weightText.isEmpty {
                    weightText = String(weightKg)
                }
            }
        }
    }
}

private struct MaxHeartRateStepView: View {
    let age: Int
    @Binding var hrMax: Int
    let onBack: () -> Void
    let onRecalculate: () -> Void
    let onContinue: () -> Void

    @State private var hrMaxText = ""

    private var parsedHRMax: Int? {
        guard let value = Int(hrMaxText), (130...230).contains(value) else { return nil }
        return value
    }

    var body: some View {
        OnboardingScaffold(
            title: L10n.aboutYou,
            subtitle: L10n.current == .no
                ? "Makspuls er det høyeste antallet hjerteslag per minutt du kan nå under hard trening."
                : "Max HR is the highest number of heart beats per minute your heart can reach during intense exercise.",
            onBack: onBack,
            primaryTitle: L10n.continueButton,
            canContinue: parsedHRMax != nil,
            onPrimary: {
                if let parsedHRMax {
                    hrMax = parsedHRMax
                    onContinue()
                }
            }
        ) {
            VStack(alignment: .leading, spacing: 14) {
                Text(L10n.current == .no ? "Maks puls (slag/min)" : "Max heart rate (bpm)")
                    .font(.body.weight(.semibold))
                    .foregroundColor(CoachiTheme.textPrimary)

                HStack(spacing: 10) {
                    TextField("190", text: $hrMaxText)
                        .keyboardType(.numberPad)
                        .font(.title3.weight(.semibold))
                        .foregroundColor(CoachiTheme.textPrimary)
                        .padding(.horizontal, 14)
                        .frame(height: 52)
                        .background(CoachiTheme.surface)
                        .clipShape(RoundedRectangle(cornerRadius: 12, style: .continuous))
                        .overlay(
                            RoundedRectangle(cornerRadius: 12, style: .continuous)
                                .stroke(CoachiTheme.borderSubtle.opacity(0.45), lineWidth: 1)
                        )

                    Button(action: {
                        onRecalculate()
                        hrMaxText = String(hrMax)
                    }) {
                        Text(L10n.current == .no ? "Beregn" : "Recalc")
                            .font(.subheadline.weight(.bold))
                            .foregroundColor(CoachiTheme.primary)
                            .padding(.horizontal, 12)
                            .frame(height: 52)
                            .background(CoachiTheme.surface)
                            .clipShape(RoundedRectangle(cornerRadius: 12, style: .continuous))
                    }
                }

                Text(
                    L10n.current == .no
                        ? "Alder: \(age) år. Standardberegning er 220 - alder."
                        : "Age: \(age). Standard estimate is 220 - age."
                )
                .font(.footnote.weight(.medium))
                .foregroundColor(CoachiTheme.textSecondary)

                OnboardingExplanationCard(
                    title: L10n.current == .no ? "Hva betyr makspuls?" : "What does Max Heart Rate mean?",
                    message: L10n.current == .no
                        ? "Makspuls er det høyeste antallet hjerteslag per minutt hjertet ditt kan nå under hard trening."
                        : "Max HR is the highest number of heart beats per minute your heart can reach during intense exercise."
                )
            }
            .onAppear {
                if hrMaxText.isEmpty {
                    hrMaxText = String(hrMax)
                }
            }
        }
    }
}

private struct RestingHeartRateStepView: View {
    @Binding var restingHR: Int
    let onBack: () -> Void
    let onContinue: () -> Void

    @State private var restingText = ""

    private var parsedResting: Int? {
        guard let value = Int(restingText), (35...110).contains(value) else { return nil }
        return value
    }

    var body: some View {
        OnboardingScaffold(
            title: L10n.aboutYou,
            subtitle: L10n.current == .no
                ? "Hvilepuls er hvor mange ganger hjertet ditt slår per minutt når du er avslappet og ikke trener."
                : "Resting HR is how many times your heart beats per minute when you are relaxed and not exercising.",
            onBack: onBack,
            primaryTitle: L10n.continueButton,
            canContinue: parsedResting != nil,
            onPrimary: {
                if let parsedResting {
                    restingHR = parsedResting
                    onContinue()
                }
            }
        ) {
            VStack(alignment: .leading, spacing: 14) {
                OnboardingNumericField(
                    label: L10n.current == .no ? "Hvilepuls (slag/min)" : "Resting HR (bpm)",
                    placeholder: "60",
                    unit: L10n.current == .no ? "slag/min" : "bpm",
                    text: $restingText
                )

                Text(
                    L10n.current == .no
                        ? "Mål gjerne når du er avslappet og kroppen føles rolig. Du kan alltids oppdatere tallet senere."
                        : "Measure it when you feel calm and settled. You can always update the number later."
                )
                .font(.footnote.weight(.medium))
                .foregroundColor(CoachiTheme.textSecondary)

                OnboardingExplanationCard(
                    title: L10n.current == .no ? "Hva er hvilepuls?" : "What is Resting HR?",
                    message: L10n.current == .no
                        ? "Hvilepuls er hvor mange ganger hjertet ditt slår per minutt når du er avslappet og ikke trener."
                        : "Resting HR is how many times your heart beats per minute when you are relaxed and not exercising."
                )
            }
            .onAppear {
                if restingText.isEmpty {
                    restingText = String(restingHR)
                }
            }
        }
    }
}

private struct EnduranceHabitStepView: View {
    @Binding var doesEnduranceTraining: Bool
    @Binding var hardestIntensity: HardestIntensityOption
    let onBack: () -> Void
    let onContinue: () -> Void

    var body: some View {
        OnboardingScaffold(
            title: L10n.aboutYou,
            subtitle: L10n.current == .no
                ? "Trener du utholdenhet i en vanlig uke?"
                : "Do you train endurance in a normal week?",
            onBack: onBack,
            primaryTitle: L10n.continueButton,
            canContinue: true,
            onPrimary: onContinue
        ) {
            VStack(spacing: 14) {
                HStack(spacing: 12) {
                    yesNoButton(
                        title: L10n.current == .no ? "Ja" : "Yes",
                        selected: doesEnduranceTraining,
                        action: { doesEnduranceTraining = true }
                    )

                    yesNoButton(
                        title: L10n.current == .no ? "Nei" : "No",
                        selected: !doesEnduranceTraining,
                        action: { doesEnduranceTraining = false }
                    )
                }

                OnboardingExplanationCard(
                    title: L10n.current == .no ? "Hva er utholdenhetstrening?" : "What counts as endurance training?",
                    message: L10n.current == .no
                        ? "Vi mener aktivitet som holder pulsen oppe over tid og trener hjertet og pusten."
                        : "We mean activity that keeps your heart rate up over time and trains your heart and breathing."
                ) {
                    VStack(alignment: .leading, spacing: 10) {
                        OnboardingExampleGroup(
                            title: L10n.current == .no ? "Dette teller som utholdenhet" : "This counts as endurance",
                            tint: CoachiTheme.primary,
                            items: L10n.current == .no
                                ? ["✅ 🏃 Løping", "✅ 🚶 Gåturer", "✅ 🚴 Sykling", "✅ 🏊 Svømming", "✅ 💃 Dansing", "✅ 🤸 Aerobic"]
                                : ["✅ 🏃 Running", "✅ 🚶 Walking", "✅ 🚴 Cycling", "✅ 🏊 Swimming", "✅ 💃 Dancing", "✅ 🤸 Aerobics"]
                        )

                        OnboardingExampleGroup(
                            title: L10n.current == .no ? "Dette teller vanligvis ikke alene" : "This usually does not count on its own",
                            tint: Color.orange,
                            items: L10n.current == .no
                                ? ["❌ 🧘 Yoga", "❌ 🏋️ Styrketrening", "❌ 🙆 Pilates"]
                                : ["❌ 🧘 Yoga", "❌ 🏋️ Strength training", "❌ 🙆 Pilates"]
                        )
                    }
                }

                if doesEnduranceTraining {
                    VStack(alignment: .leading, spacing: 10) {
                        Text(
                            L10n.current == .no
                                ? "Hvor intensiv er den hardeste utholdenhetsaktiviteten du vanligvis gjør i løpet av en uke?"
                                : "How intense is the hardest endurance activity you usually do in a normal week?"
                        )
                        .font(.body.weight(.semibold))
                        .foregroundColor(CoachiTheme.textPrimary)

                        Text(
                            L10n.current == .no
                                ? "Tenk på økta der du må jobbe mest. Velg det alternativet som ligner best på hvordan kroppen din føles."
                                : "Think about the session where you have to work the hardest. Pick the option that best matches how your body feels."
                        )
                        .font(.footnote.weight(.medium))
                        .foregroundColor(CoachiTheme.textSecondary)

                        ForEach(HardestIntensityOption.allCases) { option in
                            Button {
                                hardestIntensity = option
                            } label: {
                                VStack(alignment: .leading, spacing: 6) {
                                    Text(option.title)
                                        .font(.body.weight(.semibold))
                                        .foregroundColor(CoachiTheme.textPrimary)
                                    Text(option.subtitle)
                                        .font(.footnote.weight(.medium))
                                        .foregroundColor(CoachiTheme.textSecondary)
                                }
                                .padding(14)
                                .frame(maxWidth: .infinity, alignment: .leading)
                                .background(hardestIntensity == option ? CoachiTheme.primary.opacity(0.2) : CoachiTheme.surface)
                                .clipShape(RoundedRectangle(cornerRadius: 12, style: .continuous))
                                .overlay(
                                    RoundedRectangle(cornerRadius: 12, style: .continuous)
                                        .stroke(hardestIntensity == option ? CoachiTheme.primary.opacity(0.7) : CoachiTheme.borderSubtle.opacity(0.36), lineWidth: 1)
                                )
                            }
                            .buttonStyle(.plain)
                        }
                    }
                }
            }
        }
    }

    private func yesNoButton(title: String, selected: Bool, action: @escaping () -> Void) -> some View {
        Button(action: action) {
            Text(title)
                .font(.body.weight(.bold))
                .foregroundColor(selected ? .white : CoachiTheme.textPrimary)
                .frame(maxWidth: .infinity)
                .frame(height: 52)
                .background(selected ? CoachiTheme.primary : CoachiTheme.surface)
                .clipShape(RoundedRectangle(cornerRadius: 12, style: .continuous))
                .overlay(
                    RoundedRectangle(cornerRadius: 12, style: .continuous)
                        .stroke(selected ? Color.clear : CoachiTheme.borderSubtle.opacity(0.36), lineWidth: 1)
                )
        }
        .buttonStyle(.plain)
    }
}

private struct FrequencyDurationStepView: View {
    @Binding var hardestIntensity: HardestIntensityOption
    @Binding var moderateFrequency: ModerateFrequencyOption
    @Binding var moderateDuration: ModerateDurationOption
    let onBack: () -> Void
    let onContinue: () -> Void

    var body: some View {
        OnboardingScaffold(
            title: L10n.aboutYou,
            subtitle: hardestIntensity.followUpQuestion,
            onBack: onBack,
            primaryTitle: L10n.continueButton,
            canContinue: true,
            onPrimary: onContinue
        ) {
            VStack(spacing: 16) {
                OnboardingExplanationCard(
                    title: hardestIntensity.followUpExplanationTitle,
                    message: hardestIntensity.followUpExplanationMessage
                )

                VStack(alignment: .leading, spacing: 8) {
                    Text(L10n.current == .no ? "Frekvens per uke" : "Frequency per week")
                        .font(.subheadline.weight(.semibold))
                        .foregroundColor(CoachiTheme.textPrimary)

                    Picker("", selection: $moderateFrequency) {
                        ForEach(ModerateFrequencyOption.allCases) { option in
                            Text(option.title).tag(option)
                        }
                    }
                    .pickerStyle(.menu)
                    .tint(CoachiTheme.textPrimary)
                    .frame(maxWidth: .infinity, alignment: .leading)
                    .padding(.horizontal, 14)
                    .frame(height: 52)
                    .background(CoachiTheme.surface)
                    .clipShape(RoundedRectangle(cornerRadius: 12, style: .continuous))
                    .overlay(
                        RoundedRectangle(cornerRadius: 12, style: .continuous)
                            .stroke(CoachiTheme.borderSubtle.opacity(0.45), lineWidth: 1)
                    )
                }

                VStack(alignment: .leading, spacing: 8) {
                    Text(L10n.current == .no ? "Varighet per økt" : "Duration per session")
                        .font(.subheadline.weight(.semibold))
                        .foregroundColor(CoachiTheme.textPrimary)

                    Picker("", selection: $moderateDuration) {
                        ForEach(ModerateDurationOption.allCases) { option in
                            Text(option.title).tag(option)
                        }
                    }
                    .pickerStyle(.menu)
                    .tint(CoachiTheme.textPrimary)
                    .frame(maxWidth: .infinity, alignment: .leading)
                    .padding(.horizontal, 14)
                    .frame(height: 52)
                    .background(CoachiTheme.surface)
                    .clipShape(RoundedRectangle(cornerRadius: 12, style: .continuous))
                    .overlay(
                        RoundedRectangle(cornerRadius: 12, style: .continuous)
                            .stroke(CoachiTheme.borderSubtle.opacity(0.45), lineWidth: 1)
                    )
                }
            }
        }
    }
}

private struct SummaryStepView: View {
    let state: OnboardingFormState
    let onBack: () -> Void
    let onEditField: (OnboardingSummaryField) -> Void
    let onContinue: () -> Void

    var body: some View {
        OnboardingScaffold(
            title: L10n.current == .no ? "Klar til å starte?" : "Ready to start?",
            subtitle: L10n.current == .no
                ? "Se over profilen før vi lager startoppsettet ditt."
                : "Review your profile before we build your starting setup.",
            onBack: onBack,
            primaryTitle: L10n.continueButton,
            canContinue: true,
            onPrimary: onContinue
        ) {
            VStack(alignment: .leading, spacing: 14) {
                Text(L10n.current == .no ? "Dette bruker vi for å starte riktig." : "This is what we use to start in the right place.")
                    .font(.title2.weight(.bold))
                    .foregroundColor(CoachiTheme.textPrimary)

                Text(
                    L10n.current == .no
                        ? "Trykk på en verdi hvis du vil oppdatere den før du fortsetter."
                        : "Tap any value if you want to update it before continuing."
                )
                .font(.body.weight(.semibold))
                .foregroundColor(CoachiTheme.textSecondary)

                Divider()
                    .overlay(CoachiTheme.borderSubtle.opacity(0.55))

                summaryRow(label: L10n.firstNamePlaceholder, value: state.firstName, field: .identity)
                summaryRow(label: L10n.lastNamePlaceholder, value: state.lastName, field: .identity)
                summaryRow(label: L10n.current == .no ? "Alder" : "Age", value: "\(state.age)", field: .birthAndGender)
                summaryRow(label: L10n.current == .no ? "Kjønn" : "Gender", value: state.gender.title, field: .birthAndGender)
                summaryRow(label: L10n.current == .no ? "Høyde" : "Height", value: "\(state.heightCm) cm", field: .bodyMetrics)
                summaryRow(label: L10n.current == .no ? "Vekt" : "Weight", value: "\(state.weightKg) kg", field: .bodyMetrics)
                summaryRow(label: L10n.current == .no ? "Makspuls" : "Max HR", value: "\(state.hrMax) bpm", field: .maxHeartRate)
                summaryRow(label: L10n.current == .no ? "Hvilepuls" : "Resting HR", value: "\(state.restingHR) bpm", field: .restingHeartRate)
                summaryRow(
                    label: L10n.current == .no ? "Utholdenhetstrening" : "Endurance training",
                    value: state.doesEnduranceTraining
                        ? (L10n.current == .no ? "Ja" : "Yes")
                        : (L10n.current == .no ? "Nei" : "No"),
                    field: .enduranceHabits
                )
                if state.doesEnduranceTraining {
                    summaryRow(
                        label: L10n.current == .no ? "Hardeste intensitet" : "Hardest intensity",
                        value: state.hardestIntensity.title,
                        field: .enduranceHabits
                    )
                    summaryRow(
                        label: L10n.current == .no ? "Moderat frekvens" : "Moderate frequency",
                        value: state.moderateFrequency.title,
                        field: .frequencyAndDuration
                    )
                    summaryRow(
                        label: L10n.current == .no ? "Varighet" : "Duration",
                        value: state.moderateDuration.title,
                        field: .frequencyAndDuration
                    )
                }
            }
            .padding(16)
            .background(CoachiTheme.surface)
            .clipShape(RoundedRectangle(cornerRadius: 16, style: .continuous))
            .overlay(
                RoundedRectangle(cornerRadius: 16, style: .continuous)
                    .stroke(CoachiTheme.borderSubtle.opacity(0.36), lineWidth: 1)
            )
        }
    }

    private func summaryRow(label: String, value: String, field: OnboardingSummaryField) -> some View {
        Button {
            onEditField(field)
        } label: {
            HStack(spacing: 12) {
                Text(label)
                    .font(.body.weight(.medium))
                    .foregroundColor(CoachiTheme.textSecondary)
                Spacer()
                Text(value.isEmpty ? "-" : value)
                    .font(.headline.weight(.semibold))
                    .foregroundColor(CoachiTheme.textPrimary)
                    .multilineTextAlignment(.trailing)
                Image(systemName: "chevron.right")
                    .font(.footnote.weight(.bold))
                    .foregroundColor(CoachiTheme.textTertiary)
            }
        }
        .buttonStyle(.plain)
    }
}

private struct OnboardingResultStepView: View {
    let name: String
    let score: Int
    let age: Int
    let onBack: () -> Void
    let onContinue: () -> Void

    var body: some View {
        OnboardingScaffold(
            title: L10n.current == .no ? "Dette er startpunktet ditt" : "This is your starting point",
            subtitle: L10n.current == .no
                ? "Bra, \(name). Vi starter kontrollert og justerer etter øktene dine."
                : "Good, \(name). We will start controlled and adjust as you train.",
            onBack: onBack,
            primaryTitle: L10n.current == .no ? "Fortsett" : "Continue",
            canContinue: true,
            onPrimary: onContinue
        ) {
            VStack(spacing: 18) {
                GamifiedCoachScoreRingView(
                    score: score,
                    label: L10n.current == .no ? "Startscore" : "Start score",
                    size: 236,
                    lineWidth: 16
                )
                .padding(.top, 2)

                VStack(spacing: 8) {
                    Text(L10n.current == .no
                        ? "Du er klar for første økt."
                        : "You are ready for your first workout.")
                        .font(.body.weight(.bold))
                        .foregroundColor(CoachiTheme.textPrimary)

                    Text(L10n.current == .no
                        ? "Coachi bygger seg smartere etter hvert som du trener."
                        : "Coachi gets smarter as you keep training.")
                        .font(.subheadline.weight(.semibold))
                        .foregroundColor(CoachiTheme.textSecondary)

                    Text(L10n.current == .no
                        ? "Alder registrert: \(age) år"
                        : "Age registered: \(age)")
                        .font(.footnote.weight(.medium))
                        .foregroundColor(CoachiTheme.textTertiary)
                }
            }
            .padding(20)
            .frame(maxWidth: .infinity)
            .background(CoachiTheme.surface)
            .clipShape(RoundedRectangle(cornerRadius: 20, style: .continuous))
            .overlay(
                RoundedRectangle(cornerRadius: 20, style: .continuous)
                    .stroke(CoachiTheme.borderSubtle.opacity(0.36), lineWidth: 1)
            )
        }
    }
}

struct SensorConnectOnboardingView: View {
    @ObservedObject var watchManager: PhoneWCManager
    let onBack: () -> Void
    let onContinue: (Bool) -> Void
    var contentTopInsetOverride: CGFloat? = nil
    var bottomActionClearance: CGFloat = 0

    private var state: PhoneWCManager.WatchCapabilityState {
        watchManager.watchCapabilityState
    }

    private var isConnected: Bool { state == .watchReady }

    private var stateIcon: String {
        switch state {
        case .watchReady: return "applewatch.radiowaves.left.and.right"
        case .watchInstalledNotReachable: return "applewatch"
        case .watchNotInstalled: return "applewatch.slash"
        case .noWatchSupport: return "applewatch.slash"
        }
    }

    private var stateColor: Color {
        switch state {
        case .watchReady: return CoachiTheme.success
        case .watchInstalledNotReachable, .watchNotInstalled: return CoachiTheme.warning
        case .noWatchSupport: return CoachiTheme.textTertiary
        }
    }

    private var stateTitle: String {
        switch state {
        case .watchReady: return L10n.watchConnected
        case .watchInstalledNotReachable: return L10n.watchNotReachable
        case .watchNotInstalled: return L10n.watchAppNotInstalled
        case .noWatchSupport: return L10n.watchNotDetected
        }
    }

    private var stateDetail: String {
        switch state {
        case .watchReady: return L10n.watchConnectedDetail
        case .watchInstalledNotReachable: return L10n.watchNotReachableDetail
        case .watchNotInstalled: return L10n.watchNotInstalledDetail
        case .noWatchSupport: return L10n.watchNotDetectedDetail
        }
    }

    private var secondaryButtonTitle: String? {
        if isConnected { return nil }
        if state == .watchNotInstalled { return L10n.watchOpenWatchApp }
        return L10n.watchCheckAgain
    }

    private func secondaryAction() {
        if state == .watchNotInstalled {
            // Open the Watch app on iPhone — closest we can get to triggering install.
            // Apple provides no API to programmatically install a watch app.
            let schemes = ["itms-watchs://", "App-prefs:WATCH"]
            for scheme in schemes {
                if let url = URL(string: scheme), UIApplication.shared.canOpenURL(url) {
                    UIApplication.shared.open(url)
                    break
                }
            }
        }
        watchManager.refreshStateManually()
    }

    var body: some View {
        OnboardingScaffold(
            title: L10n.sensorConnectTitle,
            onBack: onBack,
            primaryTitle: isConnected ? L10n.watchContinue : L10n.watchContinueWithout,
            canContinue: true,
            onPrimary: { onContinue(isConnected) },
            secondaryTitle: secondaryButtonTitle,
            onSecondary: isConnected ? nil : { secondaryAction() },
            contentTopInsetOverride: contentTopInsetOverride,
            additionalBottomSafeArea: bottomActionClearance
        ) {
            VStack(spacing: 16) {
                // State icon with color ring
                ZStack {
                    Circle()
                        .fill(stateColor.opacity(0.12))
                        .frame(width: 72, height: 72)
                    Image(systemName: stateIcon)
                        .font(.system(size: 30, weight: .medium))
                        .foregroundColor(stateColor)
                }
                .frame(maxWidth: .infinity, alignment: .center)

                // State label
                HStack(spacing: 8) {
                    Circle()
                        .fill(stateColor)
                        .frame(width: 8, height: 8)
                    Text(stateTitle)
                        .font(.headline.weight(.semibold))
                        .foregroundColor(CoachiTheme.textPrimary)
                }

                // Detail text
                Text(stateDetail)
                    .font(.subheadline.weight(.medium))
                    .foregroundColor(CoachiTheme.textSecondary)
                    .multilineTextAlignment(.center)
            }
            .padding(20)
            .frame(maxWidth: .infinity)
            .background(CoachiTheme.surface)
            .clipShape(RoundedRectangle(cornerRadius: 18, style: .continuous))
            .overlay(
                RoundedRectangle(cornerRadius: 18, style: .continuous)
                    .stroke(stateColor.opacity(0.3), lineWidth: 1)
            )
            .animation(.easeInOut(duration: 0.3), value: state.rawValue)
        }
        .onAppear {
            watchManager.activate()
        }
    }
}

// NoSensorFallbackStepView removed — content merged into SensorConnectOnboardingView

struct ManageSubscriptionFeatureRowData: Identifiable {
    let id: String
    let title: String
    let freeValue: String
    let premiumValue: String
}

enum SubscriptionComparisonCatalog {
    static func featureRows(isNorwegian: Bool) -> [ManageSubscriptionFeatureRowData] {
        [
            ManageSubscriptionFeatureRowData(
                id: "guided_workouts",
                title: isNorwegian ? "Guidede økter" : "Guided workouts",
                freeValue: "✓",
                premiumValue: "✓"
            ),
            ManageSubscriptionFeatureRowData(
                id: "coach_score",
                title: isNorwegian ? "Coachi Score" : "Coachi Score",
                freeValue: "✓",
                premiumValue: "✓"
            ),
            ManageSubscriptionFeatureRowData(
                id: "hr_zone_coaching",
                title: isNorwegian ? "Coaching ved å analysere puls" : "Coaching by analysing puls",
                freeValue: "✓",
                premiumValue: "✓"
            ),
            ManageSubscriptionFeatureRowData(
                id: "talk_to_coach_live",
                title: isNorwegian ? "Talk to Coach Live" : "Talk to Coach Live",
                freeValue: isNorwegian ? "1/dag" : "1/day",
                premiumValue: isNorwegian ? "3/dag" : "3/day"
            ),
            ManageSubscriptionFeatureRowData(
                id: "workout_history",
                title: isNorwegian ? "Økthistorikk" : "Workout history",
                freeValue: isNorwegian ? "5 dagers økthistorikk" : "5 days workout history",
                premiumValue: isNorwegian ? "Full økthistorikk" : "Full workout history"
            ),
            ManageSubscriptionFeatureRowData(
                id: "single_session_feedback",
                title: isNorwegian ? "Tilbakemelding etter hver økt" : "Single session feedback",
                freeValue: "✓",
                premiumValue: "—"
            ),
            ManageSubscriptionFeatureRowData(
                id: "deep_workout_insights",
                title: isNorwegian ? "Dype øktoppsummeringer" : "Deep workout insights",
                freeValue: "—",
                premiumValue: "✓"
            ),
            ManageSubscriptionFeatureRowData(
                id: "remembers_past_workouts",
                title: isNorwegian ? "Husker tidligere økter" : "Remembers past workouts",
                freeValue: "—",
                premiumValue: "✓"
            ),
            ManageSubscriptionFeatureRowData(
                id: "coach_voice_coming_soon",
                title: isNorwegian ? "Velg coach-stemme (kommer snart)" : "Choose coach voice (coming soon)",
                freeValue: "—",
                premiumValue: "✓"
            ),
        ]
    }
}

struct WatchConnectedPremiumOfferStepView: View {
    @EnvironmentObject private var authManager: AuthManager
    @EnvironmentObject private var subscriptionManager: SubscriptionManager
    @Environment(\.colorScheme) private var colorScheme
    @ObservedObject var watchManager: PhoneWCManager
    @State private var selectedPlan: PlanSelection = .free
    @State private var selectedTrialPlan: PaywallPlanSelectionOption = .yearly
    @State private var autoAdvanceTask: Task<Void, Never>?
    @State private var isPagerInteracting = false
    @State private var isAdvancingAutomatically = false
    @State private var purchaseSuccessState: PremiumAccessSuccessState?
    @State private var showPurchaseAuthSheet = false
    @State private var pendingPurchaseOption: PaywallPlanSelectionOption?

    let onBack: () -> Void
    let onContinue: () -> Void
    let presentationMode: PresentationMode

    enum PresentationMode {
        case onboardingStep
        case manageSubscriptionInline
    }

    private enum PlanSelection: Int, CaseIterable {
        case free
        case premium
        case trial
    }

    private enum PremiumAccessSuccessState: String, Identifiable {
        case premium
        case trial

        var id: String { rawValue }
    }

    private var isNorwegian: Bool { L10n.current == .no }
    private var hasPremiumAccess: Bool { subscriptionManager.hasPremiumAccess }
    private var watchReady: Bool { watchManager.watchCapabilityState == .watchReady }

    private var featureRows: [ManageSubscriptionFeatureRowData] {
        SubscriptionComparisonCatalog.featureRows(isNorwegian: isNorwegian)
    }

    private var monthlyPriceText: String {
        subscriptionManager.formattedPrice(for: .monthly, isNorwegian: isNorwegian)
    }

    private var yearlyPriceText: String {
        subscriptionManager.formattedPrice(for: .yearly, isNorwegian: isNorwegian)
    }

    private var trialDays: Int {
        AppConfig.Subscription.trialDurationDays
    }

    private var hasIntroOffer: Bool {
        !trialEligibleOptions.isEmpty
    }

    private var trialEligibleOptions: [PaywallPlanSelectionOption] {
        var options: [PaywallPlanSelectionOption] = []
        if subscriptionManager.monthlyHasIntroOffer {
            options.append(.monthly)
        }
        if subscriptionManager.yearlyHasIntroOffer {
            options.append(.yearly)
        }
        return options
    }

    private var showsOnboardingChrome: Bool { presentationMode == .onboardingStep }
    private var selectsPremiumOnAppear: Bool { presentationMode == .onboardingStep }
    private var showsCurrentPlanState: Bool { presentationMode == .manageSubscriptionInline }
    private var isInlineManageSubscription: Bool { presentationMode == .manageSubscriptionInline }
    private var autoAdvanceIntervalSeconds: UInt64? {
        nil
    }

    private var resolvedCurrentPlan: PlanSelection {
        switch subscriptionManager.status {
        case .trial:
            return .trial
        case .premium:
            return .premium
        case .free, .expired:
            return .free
        case .unknown:
            if let resolvedLabelPlan = resolvedPlanSelection(from: subscriptionManager.resolvedPlanLabel) {
                return resolvedLabelPlan
            }
            return hasPremiumAccess ? .premium : .free
        }
    }

    private var titleText: String {
        isNorwegian ? "Velg plan" : "Choose plan"
    }

    private var subtitleText: String {
        if watchReady {
            return isNorwegian
                ? "Klokken er koblet til. Velg om du vil fortsette med Gratis eller åpne Premium før du går videre."
                : "Your watch is connected. Choose whether to continue with Free or open Premium before you move on."
        }

        return isNorwegian
            ? "Velg om du vil starte med Gratis eller se hva Premium legger til. Du kan alltid oppgradere senere i appen."
            : "Choose whether to start with Free or see what Premium adds. You can always upgrade later in the app."
    }

    init(
        watchManager: PhoneWCManager,
        onBack: @escaping () -> Void,
        onContinue: @escaping () -> Void,
        presentationMode: PresentationMode = .onboardingStep
    ) {
        self.watchManager = watchManager
        self.onBack = onBack
        self.onContinue = onContinue
        self.presentationMode = presentationMode
    }

    var body: some View {
        Group {
            if isInlineManageSubscription {
                inlineManageSubscriptionBody
            } else {
                onboardingOfferBody
            }
        }
        .onAppear {
            if !subscriptionManager.hasLoadedProducts {
                Task { await subscriptionManager.loadProducts() }
            }
            syncSelectedTrialPlanToEligibility()
            syncSelectionForCurrentContext(animated: false)
            restartAutoAdvanceIfNeeded()
        }
        .onDisappear {
            autoAdvanceTask?.cancel()
            autoAdvanceTask = nil
            isPagerInteracting = false
        }
        .onChange(of: selectedPlan) { _, _ in
            guard autoAdvanceIntervalSeconds != nil else { return }
            guard !isPagerInteracting, !isAdvancingAutomatically else { return }
            restartAutoAdvanceIfNeeded()
        }
        .onChange(of: subscriptionManager.status) { _, _ in
            syncSelectionForCurrentContext(animated: true)
        }
        .onChange(of: subscriptionManager.hasPremiumAccess) { _, _ in
            syncSelectionForCurrentContext(animated: true)
        }
        .onChange(of: subscriptionManager.hasLoadedProducts) { _, _ in
            syncSelectedTrialPlanToEligibility()
        }
        .onChange(of: purchaseSuccessState) { _, newValue in
            if newValue != nil {
                autoAdvanceTask?.cancel()
                autoAdvanceTask = nil
                isPagerInteracting = false
            } else {
                restartAutoAdvanceIfNeeded()
            }
        }
        .fullScreenCover(item: $purchaseSuccessState) { state in
            premiumSuccessScreen(for: state)
                .interactiveDismissDisabled()
        }
        .sheet(isPresented: $showPurchaseAuthSheet) {
            AuthView(
                mode: .login,
                onContinue: {
                    showPurchaseAuthSheet = false
                    resumePendingPurchaseIfNeeded()
                },
                onContinueWithoutAccount: {
                    showPurchaseAuthSheet = false
                    pendingPurchaseOption = nil
                }
            )
            .environmentObject(authManager)
        }
    }

    private var onboardingOfferBody: some View {
        GeometryReader { geo in
            let renderWidth = geo.size.width
            let renderHeight = geo.size.height
            let deviceWidth = UIScreen.main.bounds.width
            let layoutWidth = min(min(renderWidth, deviceWidth), 500)
            let safeTop = geo.safeAreaInsets.top
            let safeBottom = max(geo.safeAreaInsets.bottom, 18)
            let horizontalSafeInset = max(geo.safeAreaInsets.leading, geo.safeAreaInsets.trailing)
            let contentSideInset: CGFloat = (layoutWidth < 390 ? 18 : 24) + horizontalSafeInset
            let contentWidth = max(0.0, layoutWidth - (contentSideInset * 2))
            let compactLayout = layoutWidth < 390 || renderHeight < 780
            // Page indicator dots only — no title row
            let chromeHeight: CGFloat = (watchReady ? 60.0 : 0.0) + 28.0
            let availablePagerHeight = max(380.0, renderHeight - safeTop - safeBottom - chromeHeight)

            ZStack {
                planBackground(for: selectedPlan)
                    .ignoresSafeArea()

                VStack(spacing: 0) {
                    if watchReady {
                        watchReadyBadge
                            .frame(width: contentWidth, alignment: .leading)
                            .padding(.top, safeTop + 6)
                    }

                    planPager(
                        cardWidth: contentWidth,
                        pageHeight: availablePagerHeight,
                        compactLayout: compactLayout,
                        topInset: 0,
                        bottomInset: 0
                    )
                    .frame(width: contentWidth, height: availablePagerHeight)
                    .padding(.top, watchReady ? 6 : safeTop + 4)

                    pageIndicator
                    .padding(.top, 6)
                    .padding(.bottom, safeBottom)
                }
                .frame(width: layoutWidth, height: renderHeight, alignment: .top)
                .frame(maxWidth: .infinity, maxHeight: .infinity, alignment: .top)
            }
        }
    }

    private var inlineManageSubscriptionBody: some View {
        GeometryReader { geo in
            let renderWidth = geo.size.width
            let renderHeight = geo.size.height
            let compactLayout = renderWidth < 390 || renderHeight < 620
            let pagerHeight = max(0.0, renderHeight - 36)

            VStack(spacing: 16) {
                planPager(
                    cardWidth: renderWidth,
                    pageHeight: pagerHeight,
                    compactLayout: compactLayout,
                    topInset: 0,
                    bottomInset: 0
                )
                .frame(width: renderWidth, height: pagerHeight)

                pageIndicator
            }
            .frame(width: renderWidth, height: renderHeight, alignment: .top)
        }
    }

    private var backButton: some View {
        Button(action: onBack) {
            Image(systemName: "chevron.left")
                .font(.title3.weight(.bold))
                .foregroundColor(highContrastForeground(for: selectedPlan))
                .frame(width: 42, height: 42)
                .background(
                    Circle()
                        .fill(CoachiTheme.surface.opacity(colorScheme == .dark ? 0.32 : 0.72))
                )
                .overlay(
                    Circle()
                        .stroke(highContrastForeground(for: selectedPlan).opacity(0.16), lineWidth: 1)
                )
        }
        .buttonStyle(.plain)
    }

    private var watchReadyBadge: some View {
        HStack(spacing: 8) {
            Image(systemName: "applewatch.radiowaves.left.and.right")
                .font(.system(size: 14, weight: .semibold))

            Text(isNorwegian ? "Apple Watch koblet til" : "Apple Watch connected")
                .font(.subheadline.weight(.semibold))
        }
        .foregroundColor(CoachiTheme.success)
        .padding(.horizontal, 14)
        .padding(.vertical, 10)
        .background(CoachiTheme.success.opacity(0.10))
        .clipShape(Capsule(style: .continuous))
        .overlay(
            Capsule(style: .continuous)
                .stroke(CoachiTheme.success.opacity(0.28), lineWidth: 1)
        )
        .frame(maxWidth: .infinity, alignment: .leading)
    }

    private func planPager(cardWidth: CGFloat, pageHeight: CGFloat, compactLayout: Bool, topInset: CGFloat, bottomInset: CGFloat) -> some View {
        TabView(selection: $selectedPlan) {
            ForEach(PlanSelection.allCases, id: \.rawValue) { plan in
                planCard(
                    for: plan,
                    availableHeight: pageHeight,
                    compactLayout: compactLayout,
                    topInset: topInset,
                    bottomInset: bottomInset
                )
                .frame(width: cardWidth, height: pageHeight)
                .tag(plan)
            }
        }
        .tabViewStyle(.page(indexDisplayMode: .never))
        .frame(width: cardWidth, height: pageHeight, alignment: .leading)
        .clipped()
        .simultaneousGesture(pagerInteractionGesture)
    }

    private var pageIndicator: some View {
        HStack(spacing: 10) {
            ForEach(PlanSelection.allCases, id: \.rawValue) { plan in
                Capsule(style: .continuous)
                    .fill(selectedPlan == plan ? highContrastForeground(for: selectedPlan) : highContrastForeground(for: selectedPlan).opacity(0.34))
                    .frame(width: selectedPlan == plan ? 24 : 8, height: 8)
                    .animation(.spring(response: 0.3, dampingFraction: 0.8), value: selectedPlan)
                    .onTapGesture {
                        withAnimation(.spring(response: 0.35, dampingFraction: 0.82)) {
                            selectedPlan = plan
                        }
                    }
            }
        }
        .frame(maxWidth: .infinity, alignment: .center)
    }

    private func planCard(for plan: PlanSelection, availableHeight: CGFloat, compactLayout: Bool, topInset: CGFloat, bottomInset: CGFloat) -> some View {
        let accent = accentColor(for: plan)
        let badgeText = badgeText(for: plan)
        let premiumPriceSuffix = isNorwegian ? "/mnd" : "/mo"
        let isTrialPlan = plan == .trial
        let isCurrentPlan = showsCurrentPlanState && plan == resolvedCurrentPlan
        let isActionDisabled = isPlanActionDisabled(for: plan)
        let denseLayout = compactLayout || isInlineManageSubscription
        let cardPadding: CGFloat = compactLayout ? 20 : 24
        let titleSize: CGFloat = denseLayout ? 24 : 30
        let priceSize: CGFloat = denseLayout ? 34 : 42
        let featureSize: CGFloat = denseLayout ? 16 : 18
        let buttonVerticalPadding: CGFloat = denseLayout ? 14 : 16
        let cornerRadius: CGFloat = 28
        let contentSpacing: CGFloat = denseLayout ? 12 : 18
        let featureSpacing: CGFloat = denseLayout ? 10 : 14
        let footerSpacing: CGFloat = denseLayout ? 6 : 10
        let headerHeight: CGFloat = {
            switch plan {
            case .free:
                return 8
            case .premium:
                return 44
            case .trial:
                return denseLayout ? 64 : 76
            }
        }()

        return VStack(spacing: 0) {
            planCardHeader(for: plan, accent: accent, isCurrentPlan: isCurrentPlan, height: headerHeight)

            VStack(alignment: .leading, spacing: contentSpacing) {
                HStack(alignment: .top) {
                    VStack(alignment: .leading, spacing: denseLayout ? 6 : 8) {
                        Text(planTitle(for: plan))
                            .font(.system(size: titleSize, weight: .heavy))
                            .foregroundColor(accent)
                            .lineLimit(nil)
                            .fixedSize(horizontal: false, vertical: true)

                        HStack(alignment: .firstTextBaseline, spacing: 6) {
                            Text(priceHeadline(for: plan))
                                .font(.system(size: priceSize, weight: .heavy))
                                .foregroundColor(accent)
                                .minimumScaleFactor(0.7)
                                .lineLimit(1)

                            if plan == .premium {
                                Text(premiumPriceSuffix)
                                    .font(.title3.weight(.semibold))
                                    .foregroundColor(accent.opacity(0.76))
                            }
                        }
                    }

                    Spacer(minLength: 12)

                    if let badgeText {
                        Text(badgeText)
                            .font(.system(size: 14, weight: .bold))
                            .foregroundColor(badgeForegroundColor(for: plan, accent: accent, isCurrentPlan: isCurrentPlan))
                            .multilineTextAlignment(.center)
                            .padding(.horizontal, 14)
                            .padding(.vertical, 10)
                            .background(
                                Capsule(style: .continuous)
                                    .fill(badgeBackgroundColor(for: plan, accent: accent, isCurrentPlan: isCurrentPlan))
                            )
                    }
                }

                Divider()
                    .overlay(CoachiTheme.borderSubtle.opacity(0.6))

                if isTrialPlan {
                    trialFeaturesSection(accent: accent, compactLayout: denseLayout, featureSize: featureSize)
                } else {
                    VStack(alignment: .leading, spacing: featureSpacing) {
                        ForEach(planFeatures(for: plan), id: \.self) { feature in
                            HStack(alignment: .top, spacing: 12) {
                                Image(systemName: "checkmark")
                                    .font(.system(size: 16, weight: .bold))
                                    .foregroundColor(accent)
                                    .frame(width: 18, alignment: .center)

                                Text(feature)
                                    .font(.system(size: featureSize, weight: .semibold))
                                    .foregroundColor(CoachiTheme.textPrimary)
                                    .fixedSize(horizontal: false, vertical: true)
                            }
                        }
                    }
                }

                Spacer(minLength: 4)

                Button {
                    handlePlanAction(for: plan)
                } label: {
                    Text(buttonTitle(for: plan))
                        .font(.headline.weight(.bold))
                        .multilineTextAlignment(.center)
                        .foregroundColor(primaryButtonForegroundColor(for: plan, accent: accent, isCurrentPlan: isCurrentPlan))
                        .frame(maxWidth: .infinity)
                        .padding(.vertical, buttonVerticalPadding)
                        .background {
                            primaryButtonBackground(for: plan, accent: accent, isCurrentPlan: isCurrentPlan)
                        }
                        .clipShape(Capsule(style: .continuous))
                        .overlay(
                            Capsule(style: .continuous)
                                .stroke(primaryButtonBorderColor(for: plan, accent: accent, isCurrentPlan: isCurrentPlan), lineWidth: 2)
                        )
                }
                .buttonStyle(.plain)
                .disabled(isActionDisabled)
                .opacity(isActionDisabled ? 0.94 : 1)
            }
            .frame(maxWidth: .infinity, maxHeight: .infinity, alignment: .topLeading)
            .padding(cardPadding)
            .padding(.top, topInset)
            .padding(.bottom, bottomInset)
        }
        .frame(height: availableHeight, alignment: .topLeading)
        .background(cardBackground(for: plan))
        .clipShape(RoundedRectangle(cornerRadius: cornerRadius, style: .continuous))
        .overlay(
            RoundedRectangle(cornerRadius: cornerRadius, style: .continuous)
                .stroke(planBorderColor(for: plan, accent: accent, isCurrentPlan: isCurrentPlan), lineWidth: planBorderWidth(for: plan, isCurrentPlan: isCurrentPlan))
        )
        .shadow(color: accent.opacity(planShadowOpacity(for: plan, isCurrentPlan: isCurrentPlan)), radius: selectedPlan == plan ? 18 : 12, x: 0, y: 12)
    }

    private func planCardHeader(for plan: PlanSelection, accent: Color, isCurrentPlan: Bool, height: CGFloat) -> some View {
        Rectangle()
            .fill(.clear)
            .frame(height: height)
            .background {
                headerBackground(for: plan, accent: accent)
            }
            .clipped()
            .overlay(alignment: .bottom) {
                if plan == .trial {
                    Rectangle()
                        .fill(Color.black.opacity(colorScheme == .dark ? 0.34 : 0.16))
                        .frame(height: 4)
                }
            }
            .overlay {
                if plan == .premium && !hasPremiumAccess && !isCurrentPlan {
                    Text(isNorwegian ? "ANBEFALT" : "RECOMMENDED")
                        .font(.system(size: 13, weight: .bold))
                        .foregroundColor(.white.opacity(0.96))
                }
            }
    }

    @ViewBuilder
    private func headerBackground(for plan: PlanSelection, accent: Color) -> some View {
        switch plan {
        case .trial:
            LinearGradient(
                colors: [
                    Color(hex: "132F8A"),
                    Color(hex: "2C7CFF"),
                    Color(hex: "1E3FAF"),
                ],
                startPoint: .leading,
                endPoint: .trailing
            )
            .overlay(
                LinearGradient(
                    colors: [
                        Color.white.opacity(colorScheme == .dark ? 0.14 : 0.20),
                        Color.clear,
                        Color.white.opacity(colorScheme == .dark ? 0.08 : 0.12),
                    ],
                    startPoint: .topLeading,
                    endPoint: .bottomTrailing
                )
            )
        default:
            accent
        }
    }

    private func planFeatures(for plan: PlanSelection) -> [String] {
        featureRows.compactMap { row in
            if row.id == "talk_to_coach_live" {
                if plan == .free {
                    return isNorwegian
                        ? "Begrensede samtaler med coach"
                        : "Limited conversations with coach"
                }

                return isNorwegian
                    ? "Fullverdige samtaler med coach"
                    : "Full conversations with coach"
            }

            if row.id == "workout_history" {
                return plan == .free ? row.freeValue : row.premiumValue
            }

            let value = plan == .free ? row.freeValue : row.premiumValue
            guard value != "—" else { return nil }
            if value == "✓" {
                return row.title
            }
            return "\(row.title) · \(value)"
        }
    }

    private func planTitle(for plan: PlanSelection) -> String {
        switch plan {
        case .free:
            return isNorwegian ? "Gratis" : "Free"
        case .premium:
            return "Premium"
        case .trial:
            return isNorwegian ? "\(trialDays) dager gratis" : "\(trialDays)-day free trial"
        }
    }

    private func priceHeadline(for plan: PlanSelection) -> String {
        switch plan {
        case .free:
            return subscriptionManager.formattedFreePrice(isNorwegian: isNorwegian)
        case .premium:
            return monthlyPriceText
        case .trial:
            return isNorwegian ? "Prøv nå" : "Try now"
        }
    }

    private func accentColor(for plan: PlanSelection) -> Color {
        switch plan {
        case .free:
            return Color(hex: "F97316")
        case .premium:
            return Color(hex: "22C55E")
        case .trial:
            return Color(hex: "2F7BFF")
        }
    }

    private func cardBackground(for plan: PlanSelection) -> LinearGradient {
        let accent = accentColor(for: plan)
        switch plan {
        case .free:
            return LinearGradient(
                colors: [CoachiTheme.surface, accent.opacity(colorScheme == .dark ? 0.18 : 0.10), CoachiTheme.surfaceElevated],
                startPoint: .topLeading,
                endPoint: .bottomTrailing
            )
        case .premium:
            return LinearGradient(
                colors: [CoachiTheme.surface, accent.opacity(colorScheme == .dark ? 0.18 : 0.10), CoachiTheme.surfaceElevated],
                startPoint: .topLeading,
                endPoint: .bottomTrailing
            )
        case .trial:
            return LinearGradient(
                colors: [
                    Color(hex: colorScheme == .dark ? "141C28" : "15253B"),
                    Color(hex: colorScheme == .dark ? "18293A" : "1E314D"),
                    Color(hex: colorScheme == .dark ? "101723" : "1A2940"),
                ],
                startPoint: .topLeading,
                endPoint: .bottomTrailing
            )
        }
    }

    private func badgeText(for plan: PlanSelection) -> String? {
        if showsCurrentPlanState {
            if plan == resolvedCurrentPlan {
                return isNorwegian ? "Din plan" : "Current plan"
            }

            switch plan {
            case .free:
                return isNorwegian ? "Gratis" : "Free"
            case .premium:
                return "Premium"
            case .trial:
                return nil
            }
        }

        if hasPremiumAccess {
            return plan == selectedPlan ? (isNorwegian ? "Aktiv" : "Active") : nil
        }

        if plan == .free {
            return isNorwegian ? "Din plan" : "Current plan"
        }
        if plan == .premium {
            return "Premium"
        }
        return nil
    }

    private func detailText(for plan: PlanSelection) -> String {
        if showsCurrentPlanState, plan == resolvedCurrentPlan {
            switch plan {
            case .free:
                return isNorwegian
                    ? "Dette er den aktive gratisplanen din akkurat nå."
                    : "This is your active free plan right now."
            case .premium:
                return isNorwegian
                    ? "Dette er den aktive Premium-planen din. Administrering skjer i App Store."
                    : "This is your active Premium plan. Management stays in the App Store."
            case .trial:
                return isNorwegian
                    ? "Dette er den aktive gratis prøveperioden din akkurat nå."
                    : "This is your active free trial right now."
            }
        }

        switch plan {
        case .free:
            return isNorwegian
                ? "Du kan oppgradere når som helst i appen."
                : "You can upgrade any time in the app."
        case .premium:
            if hasIntroOffer {
                return isNorwegian
                    ? "\(trialDays) dager gratis tilgjengelig i App Store med måneds- eller årsvalg."
                    : "\(trialDays)-day free trial available in the App Store with monthly or yearly plans."
            }

            return isNorwegian
                ? "Tilgjengelig i App Store. Årlig plan fra \(yearlyPriceText)."
                : "Available in the App Store. Yearly plan from \(yearlyPriceText)."
        case .trial:
            if subscriptionManager.hasLoadedProducts && trialEligibleOptions.isEmpty {
                return isNorwegian
                    ? "Gratis prøveperiode er ikke tilgjengelig akkurat nå."
                    : "Free trial is not available right now."
            }
            return isNorwegian
                ? "Alle Coachi-funksjoner er inkludert i prøveperioden. Kjøpet fullføres i App Store."
                : "All Coachi features are included during the trial. The purchase still completes in the App Store."
        }
    }

    private func planSummary(for plan: PlanSelection) -> String {
        switch plan {
        case .free:
            return isNorwegian
                ? "Start med Coachi-kjernene og oppgrader når du vil."
                : "Start with the Coachi essentials and upgrade whenever you want."
        case .premium:
            return isNorwegian
                ? "Lås opp hele Coachi-opplevelsen med mer innsikt, historikk og live coaching."
                : "Unlock the full Coachi experience with deeper insights, history, and live coaching."
        case .trial:
            return isNorwegian
                ? "Prøv hele Coachi gratis i 14 dager med samme enkle oversikt som de andre planene."
                : "Try the full Coachi experience free for 14 days with the same simple setup as the other plans."
        }
    }

    private func buttonTitle(for plan: PlanSelection) -> String {
        if showsCurrentPlanState, plan == resolvedCurrentPlan {
            return isNorwegian ? "Din plan" : "Current plan"
        }

        if showsCurrentPlanState {
            switch plan {
            case .free:
                return isNorwegian ? "Gratis plan" : "Free plan"
            case .premium:
                return isNorwegian ? "Få Premium" : "Get Premium"
            case .trial:
                return isNorwegian ? "Start \(trialDays) dagers gratis prøveperiode nå" : "Start \(trialDays) days free trail now"
            }
        }

        if hasPremiumAccess {
            return isNorwegian ? "Fortsett" : "Continue"
        }

        switch plan {
        case .free:
            return isNorwegian ? "Fortsett med Gratis" : "Continue with Free"
        case .premium:
            return isNorwegian ? "Få Premium" : "Get Premium"
        case .trial:
            return isNorwegian ? "Start \(trialDays) dagers gratis prøveperiode nå" : "Start \(trialDays) days free trail now"
        }
    }

    private var successHeadlineText: String {
        isNorwegian ? "Gratulerer!" : "Congratulations!"
    }

    private func successSubtitle(for state: PremiumAccessSuccessState) -> String {
        switch state {
        case .premium:
            return isNorwegian
                ? "Du er nå et Coachi PREMIUM-medlem!"
                : "You are now a Coachi PREMIUM member!"
        case .trial:
            return isNorwegian
                ? "Din \(trialDays) dagers Coachi PREMIUM-prøveperiode er nå aktiv!"
                : "Your \(trialDays)-day Coachi PREMIUM trial is now active!"
        }
    }

    private func successBodyText(for state: PremiumAccessSuccessState) -> String {
        switch state {
        case .premium:
            return isNorwegian
                ? "Gratulerer! Du har nå full tilgang til alle appfunksjoner."
                : "Congratulations! You now have full access to all app features."
        case .trial:
            return isNorwegian
                ? "Gratulerer! Du har nå full tilgang til alle appfunksjoner i prøveperioden."
                : "Congratulations! You now have full access to all app features during your trial."
        }
    }

    private var successContinueTitle: String {
        return isNorwegian ? "Fortsett" : "Continue"
    }

    private var successFeatureItems: [String] {
        [
            isNorwegian ? "Coachi Score" : "Coachi Score",
            isNorwegian ? "Coaching ved å analysere puls" : "Coaching by analyzing pulse",
            isNorwegian ? "Fullverdige samtaler med en coach" : "Full conversations with a coach",
            isNorwegian ? "Full økthistorikk" : "Full workout history",
            isNorwegian ? "Dyp treningsinnsikt" : "Deep workout insights",
        ]
    }

    private func handlePlanAction(for plan: PlanSelection) {
        guard !isPlanActionDisabled(for: plan) else { return }

        if showsCurrentPlanState {
            switch plan {
            case .free:
                return
            case .premium:
                Task { await purchaseSelection(.monthly) }
            case .trial:
                Task { await purchaseSelection(selectedTrialPlan) }
            }
            return
        }

        if hasPremiumAccess {
            onContinue()
            return
        }

        switch plan {
        case .free:
            onContinue()
        case .premium:
            Task { await purchaseSelection(.monthly) }
        case .trial:
            Task { await purchaseSelection(selectedTrialPlan) }
        }
    }

    private func trialFeaturesSection(accent: Color, compactLayout: Bool, featureSize: CGFloat) -> some View {
        VStack(alignment: .leading, spacing: compactLayout ? 12 : 16) {
            VStack(alignment: .leading, spacing: compactLayout ? 8 : 12) {
                ForEach(planFeatures(for: .premium), id: \.self) { feature in
                    HStack(alignment: .top, spacing: 12) {
                        Image(systemName: "checkmark")
                            .font(.system(size: 16, weight: .bold))
                            .foregroundColor(accent)
                            .frame(width: 18, alignment: .center)

                        Text(feature)
                            .font(.system(size: featureSize, weight: .semibold))
                            .foregroundColor(CoachiTheme.textPrimary)
                            .fixedSize(horizontal: false, vertical: true)
                    }
                }
            }

            VStack(alignment: .leading, spacing: compactLayout ? 8 : 12) {
                if !subscriptionManager.hasLoadedProducts {
                    HStack(spacing: 12) {
                        ProgressView()
                            .tint(accent)

                        Text(isNorwegian ? "Laster prøvealternativer..." : "Loading trial options...")
                            .font(.system(size: compactLayout ? 14 : 15, weight: .semibold))
                            .foregroundColor(CoachiTheme.textSecondary)
                    }
                    .frame(maxWidth: .infinity, alignment: .leading)
                } else if trialEligibleOptions.isEmpty {
                    Text(isNorwegian ? "Gratis prøveperiode er ikke tilgjengelig akkurat nå." : "Free trial is not available right now.")
                        .font(.system(size: compactLayout ? 14 : 15, weight: .semibold))
                        .foregroundColor(CoachiTheme.textSecondary)
                        .fixedSize(horizontal: false, vertical: true)
                } else {
                    HStack(spacing: 12) {
                        ForEach(trialEligibleOptions, id: \.self) { option in
                            trialPricingOption(
                                title: option == .monthly ? (isNorwegian ? "Månedlig" : "Monthly") : (isNorwegian ? "Årlig" : "Yearly"),
                                price: option == .monthly ? monthlyPriceText : yearlyPriceText,
                                suffix: option == .monthly ? (isNorwegian ? "/mnd" : "/mo") : (isNorwegian ? "/år" : "/yr"),
                                option: option,
                                accent: accent,
                                compactLayout: compactLayout
                            )
                        }
                    }
                }

                if !isInlineManageSubscription, trialEligibleOptions.contains(.yearly), let savingsText = yearlySavingsText {
                    HStack {
                        Spacer()
                        Text(savingsText)
                            .font(.system(size: 12, weight: .bold))
                            .foregroundColor(.white)
                            .padding(.horizontal, 12)
                            .padding(.vertical, 8)
                            .background(
                                RoundedRectangle(cornerRadius: 16, style: .continuous)
                                    .fill(accent)
                            )
                    }
                }
            }
        }
    }

    private func trialPricingOption(
        title: String,
        price: String,
        suffix: String,
        option: PaywallPlanSelectionOption,
        accent: Color,
        compactLayout: Bool
    ) -> some View {
        let isSelected = selectedTrialPlan == option
        let optionPadding: CGFloat = compactLayout ? 14 : 16

        return Button {
            selectedTrialPlan = option
        } label: {
            VStack(alignment: .leading, spacing: 8) {
                HStack {
                    Spacer()
                    Circle()
                        .stroke(accent.opacity(0.6), lineWidth: 1.5)
                        .frame(width: 22, height: 22)
                        .overlay {
                            if isSelected {
                                Circle()
                                    .fill(accent)
                                    .frame(width: 12, height: 12)
                            }
                        }
                }

                Text(title)
                    .font(.system(size: compactLayout ? 16 : 17, weight: .semibold))
                    .foregroundColor(CoachiTheme.textPrimary)
                    .lineLimit(1)

                HStack(alignment: .firstTextBaseline, spacing: 4) {
                    Text(price)
                        .font(.system(size: compactLayout ? 22 : 24, weight: .heavy))
                        .foregroundColor(CoachiTheme.textPrimary)
                        .minimumScaleFactor(0.7)

                    Text(suffix)
                        .font(.subheadline.weight(.semibold))
                        .foregroundColor(CoachiTheme.textSecondary)
                }
            }
            .padding(optionPadding)
            .frame(maxWidth: .infinity, alignment: .leading)
            .background(
                RoundedRectangle(cornerRadius: 18, style: .continuous)
                    .fill(
                        LinearGradient(
                            colors: [
                                Color(hex: colorScheme == .dark ? "162334" : "1C2B43"),
                                Color(hex: colorScheme == .dark ? "1A2637" : "22344D"),
                            ],
                            startPoint: .topLeading,
                            endPoint: .bottomTrailing
                        )
                    )
            )
            .overlay(
                RoundedRectangle(cornerRadius: 18, style: .continuous)
                    .stroke(isSelected ? accent : accent.opacity(0.28), lineWidth: isSelected ? 2.5 : 1.2)
            )
            .shadow(color: isSelected ? accent.opacity(0.30) : .clear, radius: 14, x: 0, y: 8)
        }
        .buttonStyle(.plain)
    }

    private var yearlySavingsText: String? {
        let monthly = subscriptionManager.monthlyProduct?.price
            ?? (isNorwegian ? AppConfig.Subscription.fallbackMonthlyPriceNOK : AppConfig.Subscription.fallbackMonthlyPriceUSD)
        let yearly = subscriptionManager.yearlyProduct?.price
            ?? (isNorwegian ? AppConfig.Subscription.fallbackYearlyPriceNOK : AppConfig.Subscription.fallbackYearlyPriceUSD)

        let monthlyDouble = NSDecimalNumber(decimal: monthly).doubleValue
        let yearlyDouble = NSDecimalNumber(decimal: yearly).doubleValue
        guard monthlyDouble > 0, yearlyDouble > 0 else { return nil }

        let yearlyIfMonthly = monthlyDouble * 12
        let savings = max(0, Int(round((1 - (yearlyDouble / yearlyIfMonthly)) * 100)))
        guard savings > 0 else { return nil }

        return isNorwegian
            ? "Spar \(savings)% med år"
            : "Save \(savings)% yearly"
    }

    private func planBackground(for plan: PlanSelection) -> LinearGradient {
        let accent = accentColor(for: plan)
        return LinearGradient(
            colors: colorScheme == .dark
                ? [Color.black.opacity(0.82), accent.opacity(0.40), CoachiTheme.bgDeep]
                : [accent.opacity(0.22), CoachiTheme.bg, CoachiTheme.bgDeep.opacity(0.72)],
            startPoint: .topLeading,
            endPoint: .bottomTrailing
        )
    }

    private func highContrastForeground(for plan: PlanSelection) -> Color {
        _ = plan
        return colorScheme == .dark ? .white : CoachiTheme.textPrimary
    }

    private func planBorderColor(for plan: PlanSelection, accent: Color, isCurrentPlan: Bool) -> Color {
        if isCurrentPlan {
            return accent.opacity(0.95)
        }
        if selectedPlan == plan {
            return accent.opacity(0.78)
        }
        return CoachiTheme.borderSubtle.opacity(0.35)
    }

    private func planBorderWidth(for plan: PlanSelection, isCurrentPlan: Bool) -> CGFloat {
        if isCurrentPlan {
            return 3
        }
        return selectedPlan == plan ? 2 : 1
    }

    private func planShadowOpacity(for plan: PlanSelection, isCurrentPlan: Bool) -> Double {
        if isCurrentPlan {
            return 0.24
        }
        return selectedPlan == plan ? 0.14 : 0.06
    }

    private func badgeForegroundColor(for plan: PlanSelection, accent: Color, isCurrentPlan: Bool) -> Color {
        if isCurrentPlan {
            return .white
        }
        return plan == .premium && !hasPremiumAccess ? .white : accent
    }

    private func badgeBackgroundColor(for plan: PlanSelection, accent: Color, isCurrentPlan: Bool) -> Color {
        if isCurrentPlan {
            return accent
        }
        return plan == .premium && !hasPremiumAccess ? accent : accent.opacity(0.14)
    }

    private func primaryButtonForegroundColor(for plan: PlanSelection, accent: Color, isCurrentPlan: Bool) -> Color {
        if isCurrentPlan {
            return accent
        }
        return plan == .free && !hasPremiumAccess ? accent : .white
    }

    @ViewBuilder
    private func primaryButtonBackground(for plan: PlanSelection, accent: Color, isCurrentPlan: Bool) -> some View {
        if isCurrentPlan {
            CoachiTheme.surface
        } else if plan == .trial {
            LinearGradient(
                colors: [
                    Color(hex: "1E4DDE"),
                    Color(hex: "3294FF"),
                    Color(hex: "213DCC"),
                ],
                startPoint: .leading,
                endPoint: .trailing
            )
        } else if plan == .free && !hasPremiumAccess {
            CoachiTheme.surface
        } else {
            accent
        }
    }

    private func primaryButtonBorderColor(for plan: PlanSelection, accent: Color, isCurrentPlan: Bool) -> Color {
        if isCurrentPlan {
            return accent.opacity(0.9)
        }
        return accent.opacity(plan == .free && !hasPremiumAccess ? 0.9 : 0.0)
    }

    private func isPlanActionDisabled(for plan: PlanSelection) -> Bool {
        if subscriptionManager.isLoading {
            return true
        }
        if plan == .trial, (!subscriptionManager.hasLoadedProducts || trialEligibleOptions.isEmpty) {
            return true
        }
        if showsCurrentPlanState, plan == resolvedCurrentPlan {
            return true
        }
        return showsCurrentPlanState && plan == .free
    }

    private func purchaseSelection(_ option: PaywallPlanSelectionOption) async {
        guard authManager.isAuthenticated else {
            pendingPurchaseOption = option
            showPurchaseAuthSheet = true
            return
        }
        await performPurchaseSelection(option)
    }

    private func performPurchaseSelection(_ option: PaywallPlanSelectionOption) async {
        if selectedProduct(for: option) == nil {
            await subscriptionManager.loadProducts()
            syncSelectedTrialPlanToEligibility()
        }

        guard let product = selectedProduct(for: option) else { return }
        let purchaseOutcome = await subscriptionManager.purchase(product)
        guard case let .success(status) = purchaseOutcome else { return }
        guard let successState = successState(for: status) else { return }
        purchaseSuccessState = successState
    }

    private func resumePendingPurchaseIfNeeded() {
        guard authManager.isAuthenticated, let option = pendingPurchaseOption else { return }
        pendingPurchaseOption = nil
        Task {
            await performPurchaseSelection(option)
        }
    }

    private func selectedProduct(for option: PaywallPlanSelectionOption) -> Product? {
        switch option {
        case .monthly:
            return subscriptionManager.monthlyProduct
        case .yearly:
            return subscriptionManager.yearlyProduct
        }
    }

    private func syncSelectedTrialPlanToEligibility() {
        guard !trialEligibleOptions.isEmpty else { return }
        if !trialEligibleOptions.contains(selectedTrialPlan), let firstEligible = trialEligibleOptions.first {
            selectedTrialPlan = firstEligible
        }
    }

    private func successState(for status: SubscriptionStatus) -> PremiumAccessSuccessState? {
        switch status {
        case .trial:
            return .trial
        case .premium:
            return .premium
        default:
            return nil
        }
    }

    @ViewBuilder
    private func premiumSuccessScreen(for state: PremiumAccessSuccessState) -> some View {
        ZStack {
            CoachiTheme.bgDeep
                .ignoresSafeArea()

            LinearGradient(
                colors: [
                    Color(hex: "050B1A"),
                    Color(hex: "0B1730"),
                    Color(hex: "111827"),
                ],
                startPoint: .top,
                endPoint: .bottom
            )
            .ignoresSafeArea()

            VStack(spacing: 0) {
                ZStack(alignment: .top) {
                    VStack(spacing: 18) {
                        Text(successHeadlineText)
                            .font(.system(size: 42, weight: .heavy))
                            .foregroundStyle(.white)
                            .shadow(color: Color(hex: "4FA3FF").opacity(0.65), radius: 18, x: 0, y: 0)
                            .multilineTextAlignment(.center)

                        Text(successSubtitle(for: state))
                            .font(.system(size: 19, weight: .bold))
                            .foregroundStyle(.white.opacity(0.96))
                            .multilineTextAlignment(.center)
                            .fixedSize(horizontal: false, vertical: true)

                        premiumSuccessBadge
                    }
                    .padding(.top, 84)
                    .padding(.horizontal, 32)

                    premiumSuccessHeader
                }

                VStack(alignment: .leading, spacing: 22) {
                    Text(successBodyText(for: state))
                        .font(.system(size: 17, weight: .medium))
                        .foregroundStyle(.white.opacity(0.92))
                        .multilineTextAlignment(.leading)
                        .frame(maxWidth: .infinity, alignment: .leading)
                        .padding(.top, 24)

                    Divider()
                        .overlay(Color.white.opacity(0.12))

                    VStack(alignment: .leading, spacing: 18) {
                        ForEach(Array(successFeatureItems.enumerated()), id: \.offset) { _, item in
                            HStack(alignment: .top, spacing: 14) {
                                Image(systemName: "checkmark")
                                    .font(.system(size: 18, weight: .bold))
                                    .foregroundStyle(Color(hex: "2F7BFF"))
                                    .frame(width: 18)
                                Text(item)
                                    .font(.system(size: 15, weight: .medium))
                                    .foregroundStyle(.white)
                                    .fixedSize(horizontal: false, vertical: true)
                            }
                        }
                    }

                    Spacer(minLength: 24)

                    Button {
                        let shouldContinueOnboarding = presentationMode == .onboardingStep
                        purchaseSuccessState = nil
                        if shouldContinueOnboarding {
                            onContinue()
                        }
                    } label: {
                        Text(successContinueTitle)
                            .font(.system(size: 18, weight: .heavy))
                            .foregroundStyle(.white)
                            .frame(maxWidth: .infinity)
                            .padding(.vertical, 18)
                            .background(
                                LinearGradient(
                                    colors: [
                                        Color(hex: "213DCC"),
                                        Color(hex: "2F7BFF"),
                                        Color(hex: "1E4DDE"),
                                    ],
                                    startPoint: .leading,
                                    endPoint: .trailing
                                )
                            )
                            .clipShape(Capsule(style: .continuous))
                            .overlay(
                                Capsule(style: .continuous)
                                    .stroke(Color(hex: "5DB0FF").opacity(0.85), lineWidth: 2)
                            )
                            .shadow(color: Color(hex: "2F7BFF").opacity(0.42), radius: 18, x: 0, y: 10)
                    }
                    .buttonStyle(.plain)
                }
                .padding(.horizontal, 30)
                .padding(.bottom, 42)
                .frame(maxWidth: .infinity, maxHeight: .infinity, alignment: .top)
                .background(Color(hex: "171C24"))
                .clipShape(RoundedRectangle(cornerRadius: 34, style: .continuous))
                .overlay(
                    RoundedRectangle(cornerRadius: 34, style: .continuous)
                        .stroke(Color.white.opacity(0.06), lineWidth: 1)
                )
                .padding(.horizontal, 20)
                .padding(.bottom, 30)
                .offset(y: -20)
            }
        }
    }

    private var premiumSuccessHeader: some View {
        ZStack(alignment: .top) {
            Ellipse()
                .fill(
                    RadialGradient(
                        colors: [
                            Color(hex: "2F7BFF").opacity(0.72),
                            Color(hex: "1D4ED8").opacity(0.42),
                            Color.clear,
                        ],
                        center: .top,
                        startRadius: 24,
                        endRadius: 340
                    )
                )
                .frame(height: 340)
                .offset(y: -126)

            Circle()
                .fill(Color.white.opacity(0.18))
                .frame(width: 4, height: 4)
                .offset(x: -138, y: 92)

            Circle()
                .fill(Color.white.opacity(0.22))
                .frame(width: 3, height: 3)
                .offset(x: 148, y: 116)

            Circle()
                .fill(Color.white.opacity(0.14))
                .frame(width: 5, height: 5)
                .offset(x: -42, y: 64)
        }
        .frame(height: 260)
    }

    private var premiumSuccessBadge: some View {
        ZStack {
            Capsule(style: .continuous)
                .fill(Color(hex: "9C6B1A"))
                .frame(width: 18, height: 86)
                .rotationEffect(.degrees(22))
                .offset(x: -24, y: 38)

            Capsule(style: .continuous)
                .fill(Color(hex: "5D87D9"))
                .frame(width: 18, height: 86)
                .rotationEffect(.degrees(-22))
                .offset(x: 24, y: 38)

            Circle()
                .fill(
                    RadialGradient(
                        colors: [
                            Color(hex: "2F7BFF"),
                            Color(hex: "1737C8"),
                        ],
                        center: .center,
                        startRadius: 12,
                        endRadius: 72
                    )
                )
                .frame(width: 118, height: 118)
                .shadow(color: Color(hex: "2F7BFF").opacity(0.55), radius: 22, x: 0, y: 0)

            Circle()
                .stroke(Color(hex: "F6D47A"), lineWidth: 7)
                .frame(width: 106, height: 106)

            Circle()
                .stroke(Color.white.opacity(0.20), lineWidth: 3)
                .frame(width: 90, height: 90)

            Image(systemName: "star.fill")
                .font(.system(size: 38, weight: .black))
                .foregroundStyle(Color(hex: "F5C356"))
                .shadow(color: Color.black.opacity(0.22), radius: 6, x: 0, y: 4)
        }
        .frame(height: 170)
        .padding(.top, 6)
    }

    private func resolvedPlanSelection(from label: String) -> PlanSelection? {
        switch label {
        case "Free Trial":
            return .trial
        case "Premium":
            return .premium
        case "Free", "Expired", "Checking":
            return .free
        default:
            return nil
        }
    }

    private var pagerInteractionGesture: some Gesture {
        DragGesture(minimumDistance: 10)
            .onChanged { _ in
                guard autoAdvanceIntervalSeconds != nil else { return }
                if !isPagerInteracting {
                    isPagerInteracting = true
                    autoAdvanceTask?.cancel()
                    autoAdvanceTask = nil
                }
            }
            .onEnded { _ in
                guard autoAdvanceIntervalSeconds != nil else { return }
                isPagerInteracting = false
                restartAutoAdvanceIfNeeded()
            }
    }

    private func syncSelectionForCurrentContext(animated: Bool) {
        let targetPlan: PlanSelection
        if isInlineManageSubscription {
            targetPlan = resolvedCurrentPlan
        } else if selectsPremiumOnAppear && hasPremiumAccess {
            targetPlan = resolvedCurrentPlan
        } else {
            targetPlan = .free
        }

        guard selectedPlan != targetPlan else { return }
        if animated {
            withAnimation(.spring(response: 0.35, dampingFraction: 0.82)) {
                selectedPlan = targetPlan
            }
        } else {
            selectedPlan = targetPlan
        }
    }

    private func restartAutoAdvanceIfNeeded() {
        autoAdvanceTask?.cancel()
        autoAdvanceTask = nil

        guard let intervalSeconds = autoAdvanceIntervalSeconds else { return }

        autoAdvanceTask = Task {
            try? await Task.sleep(nanoseconds: intervalSeconds * 1_000_000_000)
            guard !Task.isCancelled else { return }
            await MainActor.run {
                guard !isPagerInteracting else {
                    restartAutoAdvanceIfNeeded()
                    return
                }
                isAdvancingAutomatically = true
                withAnimation(.easeInOut(duration: 0.32)) {
                    let nextIndex = (selectedPlan.rawValue + 1) % max(PlanSelection.allCases.count, 1)
                    selectedPlan = PlanSelection(rawValue: nextIndex) ?? .free
                }
                isAdvancingAutomatically = false
                restartAutoAdvanceIfNeeded()
            }
        }
    }
}

private struct NotificationPermissionStepView: View {
    let isLoading: Bool
    let onBack: () -> Void
    let onEnable: () -> Void
    let onSkip: () -> Void

    var body: some View {
        OnboardingScaffold(
            title: L10n.current == .no ? "Varsler" : "Notifications",
            subtitle: L10n.current == .no
                ? "Vil du ha varsler om framgang, resultater og viktige oppdateringer?"
                : "Do you want notifications about progress, results, and important updates?",
            onBack: onBack,
            primaryTitle: isLoading
                ? (L10n.current == .no ? "Laster..." : "Loading...")
                : (L10n.current == .no ? "Ja, aktiver" : "Yes, enable"),
            canContinue: !isLoading,
            onPrimary: onEnable,
            secondaryTitle: L10n.current == .no ? "Kanskje senere" : "Maybe later",
            onSecondary: onSkip
        ) {
            VStack(spacing: 14) {
                Image(systemName: "bell.badge")
                    .font(.largeTitle.weight(.medium))
                    .foregroundStyle(CoachiTheme.primaryGradient)

                Text(
                    L10n.current == .no
                        ? "Du kan alltid endre varslene senere i innstillinger."
                        : "You can always change notification settings later."
                )
                .font(.subheadline.weight(.medium))
                .foregroundColor(CoachiTheme.textSecondary)
                .multilineTextAlignment(.center)
            }
            .padding(.vertical, 8)
            .frame(maxWidth: .infinity)
        }
    }
}

private struct OnboardingScaffold<Content: View>: View {
    let title: String
    let subtitle: String?
    let onBack: () -> Void
    let primaryTitle: String
    let canContinue: Bool
    let onPrimary: () -> Void
    let secondaryTitle: String?
    let onSecondary: (() -> Void)?
    let contentTopInsetOverride: CGFloat?
    let additionalBottomSafeArea: CGFloat
    let showsBottomActions: Bool
    let content: Content

    init(
        title: String,
        subtitle: String? = nil,
        onBack: @escaping () -> Void,
        primaryTitle: String,
        canContinue: Bool,
        onPrimary: @escaping () -> Void,
        secondaryTitle: String? = nil,
        onSecondary: (() -> Void)? = nil,
        contentTopInsetOverride: CGFloat? = nil,
        additionalBottomSafeArea: CGFloat = 0,
        showsBottomActions: Bool = true,
        @ViewBuilder content: () -> Content
    ) {
        self.title = title
        self.subtitle = subtitle
        self.onBack = onBack
        self.primaryTitle = primaryTitle
        self.canContinue = canContinue
        self.onPrimary = onPrimary
        self.secondaryTitle = secondaryTitle
        self.onSecondary = onSecondary
        self.contentTopInsetOverride = contentTopInsetOverride
        self.additionalBottomSafeArea = additionalBottomSafeArea
        self.showsBottomActions = showsBottomActions
        self.content = content()
    }

    var body: some View {
        GeometryReader { geo in
            let renderWidth = geo.size.width
            let renderHeight = geo.size.height
            let deviceWidth = UIScreen.main.bounds.width
            let layoutWidth = min(min(renderWidth, deviceWidth), 500)
            let sidePadding = layoutWidth < 390 ? 16.0 : 22.0
            let contentWidth = max(0.0, layoutWidth - (sidePadding * 2))
            let bottomInset = min(42.0, max(20.0, geo.safeAreaInsets.bottom + 8.0)) + additionalBottomSafeArea
            let contentTopInset = contentTopInsetOverride ?? max(renderHeight * 0.08, 24.0)

            ScrollView(.vertical, showsIndicators: false) {
                VStack(spacing: 0) {
                    HStack {
                        Button(action: onBack) {
                            Image(systemName: "chevron.left")
                                .font(.title3.weight(.bold))
                                .foregroundColor(CoachiTheme.textPrimary)
                                .frame(width: 40, height: 40)
                                .background(CoachiTheme.surface)
                                .clipShape(Circle())
                                .overlay(
                                    Circle()
                                        .stroke(CoachiTheme.borderSubtle.opacity(0.45), lineWidth: 1)
                                )
                        }

                        Spacer()
                    }
                    .frame(width: contentWidth, alignment: .leading)
                    .frame(width: layoutWidth, alignment: .center)
                    .padding(.top, max(12.0, geo.safeAreaInsets.top + 6.0))

                    VStack(alignment: .leading, spacing: 18) {
                        Text(title)
                            .font(.largeTitle.weight(.bold))
                            .foregroundColor(CoachiTheme.textPrimary)
                            .fixedSize(horizontal: false, vertical: true)

                        if let subtitle {
                            Text(subtitle)
                                .font(.body.weight(.medium))
                                .foregroundColor(CoachiTheme.textSecondary)
                                .fixedSize(horizontal: false, vertical: true)
                        }

                        content
                    }
                    .frame(width: contentWidth, alignment: .leading)
                    .padding(.top, contentTopInset)
                    .padding(.bottom, 18)
                    .frame(width: layoutWidth, alignment: .center)
                }
                .frame(width: layoutWidth, alignment: .center)
            }
            .safeAreaInset(edge: .bottom, spacing: 0) {
                if showsBottomActions {
                    VStack(spacing: 10) {
                        Button(action: onPrimary) {
                            Text(primaryTitle)
                                .font(.headline.weight(.bold))
                                .foregroundColor(canContinue ? .white : CoachiTheme.textSecondary)
                                .frame(maxWidth: .infinity)
                                .frame(minHeight: 56)
                                .background(
                                    canContinue
                                        ? AnyView(CoachiTheme.primaryGradient)
                                        : AnyView(CoachiTheme.surfaceElevated.opacity(0.85))
                                )
                                .clipShape(RoundedRectangle(cornerRadius: 16, style: .continuous))
                        }
                        .disabled(!canContinue)
                        .frame(width: contentWidth, alignment: .center)

                        if let secondaryTitle, let onSecondary {
                            Button(action: onSecondary) {
                                Text(secondaryTitle)
                                    .font(.body.weight(.semibold))
                                    .foregroundColor(CoachiTheme.textPrimary)
                                    .frame(maxWidth: .infinity)
                                    .frame(minHeight: 50)
                                    .background(CoachiTheme.surface)
                                    .clipShape(RoundedRectangle(cornerRadius: 14, style: .continuous))
                                    .overlay(
                                        RoundedRectangle(cornerRadius: 14, style: .continuous)
                                            .stroke(CoachiTheme.borderSubtle.opacity(0.45), lineWidth: 1)
                                    )
                            }
                            .frame(width: contentWidth, alignment: .center)
                        }
                    }
                    .padding(.top, 10)
                    .padding(.bottom, bottomInset)
                    .frame(width: layoutWidth, alignment: .center)
                    .background(.ultraThinMaterial)
                }
            }
            .scrollBounceBehavior(.basedOnSize, axes: .vertical)
            .scrollDismissesKeyboard(.interactively)
            .frame(width: layoutWidth, height: renderHeight, alignment: .top)
            .frame(maxWidth: .infinity, maxHeight: .infinity, alignment: .top)
            .clipped()
        }
        .onTapGesture {
            hideKeyboard()
        }
    }

    private func hideKeyboard() {
        UIApplication.shared.sendAction(#selector(UIResponder.resignFirstResponder), to: nil, from: nil, for: nil)
    }
}

private struct OnboardingInputField: View {
    let label: String
    let placeholder: String
    @Binding var text: String
    let contentType: UITextContentType?
    let keyboardType: UIKeyboardType

    var body: some View {
        VStack(alignment: .leading, spacing: 8) {
            Text(label)
                .font(.subheadline.weight(.semibold))
                .foregroundColor(CoachiTheme.textPrimary)

            TextField("", text: $text, prompt: Text(placeholder).foregroundColor(CoachiTheme.textTertiary))
                .font(.body.weight(.medium))
                .foregroundColor(CoachiTheme.textPrimary)
                .textInputAutocapitalization(.words)
                .autocorrectionDisabled()
                .textContentType(contentType)
                .keyboardType(keyboardType)
                .padding(.horizontal, 14)
                .frame(height: 50)
                .background(CoachiTheme.surface)
                .clipShape(RoundedRectangle(cornerRadius: 12, style: .continuous))
                .overlay(
                    RoundedRectangle(cornerRadius: 12, style: .continuous)
                        .stroke(CoachiTheme.borderSubtle.opacity(0.45), lineWidth: 1)
                )
        }
    }
}

private struct OnboardingNumericField: View {
    let label: String
    let placeholder: String
    let unit: String
    @Binding var text: String

    var body: some View {
        VStack(alignment: .leading, spacing: 8) {
            Text(label)
                .font(.subheadline.weight(.semibold))
                .foregroundColor(CoachiTheme.textPrimary)

            HStack(spacing: 8) {
                TextField(placeholder, text: $text)
                    .keyboardType(.numberPad)
                    .font(.headline.weight(.semibold))
                    .foregroundColor(CoachiTheme.textPrimary)
                    .padding(.horizontal, 14)
                    .frame(height: 50)
                    .background(CoachiTheme.surface)
                    .clipShape(RoundedRectangle(cornerRadius: 12, style: .continuous))
                    .overlay(
                        RoundedRectangle(cornerRadius: 12, style: .continuous)
                            .stroke(CoachiTheme.borderSubtle.opacity(0.45), lineWidth: 1)
                    )

                Text(unit)
                    .font(.subheadline.weight(.bold))
                    .foregroundColor(CoachiTheme.textSecondary)
                    .padding(.horizontal, 10)
                    .frame(height: 40)
                    .background(CoachiTheme.surface)
                    .clipShape(RoundedRectangle(cornerRadius: 10, style: .continuous))
            }
        }
    }
}

private struct OnboardingExplanationCard<Content: View>: View {
    let title: String
    let message: String
    let content: Content

    init(
        title: String,
        message: String,
        @ViewBuilder content: () -> Content
    ) {
        self.title = title
        self.message = message
        self.content = content()
    }

    var body: some View {
        VStack(alignment: .leading, spacing: 10) {
            Text(title)
                .font(.subheadline.weight(.bold))
                .foregroundColor(CoachiTheme.textPrimary)

            Text(message)
                .font(.footnote.weight(.medium))
                .foregroundColor(CoachiTheme.textSecondary)
                .fixedSize(horizontal: false, vertical: true)

            content
        }
        .padding(14)
        .frame(maxWidth: .infinity, alignment: .leading)
        .background(CoachiTheme.surface.opacity(0.94))
        .clipShape(RoundedRectangle(cornerRadius: 14, style: .continuous))
        .overlay(
            RoundedRectangle(cornerRadius: 14, style: .continuous)
                .stroke(CoachiTheme.borderSubtle.opacity(0.4), lineWidth: 1)
        )
    }
}

private extension OnboardingExplanationCard where Content == EmptyView {
    init(title: String, message: String) {
        self.init(title: title, message: message) {
            EmptyView()
        }
    }
}

private struct OnboardingExampleGroup: View {
    let title: String
    let tint: Color
    let items: [String]

    var body: some View {
        VStack(alignment: .leading, spacing: 8) {
            Text(title)
                .font(.footnote.weight(.bold))
                .foregroundColor(tint)

            LazyVGrid(columns: [GridItem(.flexible()), GridItem(.flexible())], alignment: .leading, spacing: 8) {
                ForEach(items, id: \.self) { item in
                    Text(item)
                        .font(.footnote.weight(.medium))
                        .foregroundColor(CoachiTheme.textPrimary)
                        .frame(maxWidth: .infinity, alignment: .leading)
                        .padding(.horizontal, 10)
                        .padding(.vertical, 8)
                        .background(CoachiTheme.surfaceElevated)
                        .clipShape(RoundedRectangle(cornerRadius: 10, style: .continuous))
                }
            }
        }
    }
}
