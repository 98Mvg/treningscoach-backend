//
//  OnboardingContainerView.swift
//  TreningsCoach
//
//  Full onboarding flow:
//  Welcome -> Language -> Features -> Auth -> Profile -> HR setup -> Habits -> Summary -> Result
//  -> Sensor connect/no sensor -> Notifications -> Main app
//

import SwiftUI
import UIKit
import UserNotifications

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
    case notificationPermission = 16
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
                ? "Jeg blir ikke nevneverdig andpusten og svett."
                : "I can keep this pace for a long time."
        case .moderate:
            return L10n.current == .no
                ? "Jeg puster raskt, men kan holde intensiteten en stund."
                : "I breathe harder but can sustain the effort."
        case .high:
            return L10n.current == .no
                ? "Jeg tar meg nesten helt ut og holder ikke lenge."
                : "I push close to max and cannot hold it for long."
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

    @State private var currentStep: OnboardingStep = .welcome
    @State private var formState = OnboardingFormState()
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
                        onPrimary: { move(to: .auth) },
                        primaryTitle: L10n.register,
                        onSecondary: { move(to: .auth) },
                        secondaryTitle: L10n.current == .no ? "Jeg har allerede en bruker" : "I already have an account"
                    )
                    .transition(stepTransition)

                case .language:
                    LanguageSelectionView { language in
                        selectedLanguage = language
                        L10n.set(language)
                        move(to: .auth)
                    }
                    .transition(stepTransition)

                case .features:
                    FeaturesPageView(
                        mode: .postAuthExplainer(displayName: formState.displayName),
                        onPrimary: { move(to: .birthAndGender) },
                        primaryTitle: L10n.continueButton,
                        onSecondary: { move(to: .dataPurpose) },
                        secondaryTitle: L10n.current == .no ? "Tilbake" : "Back"
                    )
                    .transition(stepTransition)

                case .auth:
                    AuthView {
                        move(to: .identity)
                    }
                    .transition(stepTransition)

                case .identity:
                    IdentityStepView(
                        firstName: $formState.firstName,
                        lastName: $formState.lastName,
                        onBack: { move(to: .auth) },
                        onContinue: { move(to: .dataPurpose) }
                    )
                    .transition(stepTransition)

                case .dataPurpose:
                    DataPurposeStepView(
                        firstName: formState.firstName,
                        onBack: { move(to: .identity) },
                        onContinue: { move(to: .features) }
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
                        onContinue: { move(to: .frequencyAndDuration) }
                    )
                    .transition(stepTransition)

                case .frequencyAndDuration:
                    FrequencyDurationStepView(
                        moderateFrequency: $formState.moderateFrequency,
                        moderateDuration: $formState.moderateDuration,
                        onBack: { move(to: .enduranceHabits) },
                        onContinue: { move(to: .summary) }
                    )
                    .transition(stepTransition)

                case .summary:
                    SummaryStepView(
                        state: formState,
                        onBack: { move(to: .frequencyAndDuration) },
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
                        onBack: { move(to: .summary) },
                        onConnectNow: {
                            if let url = URL(string: UIApplication.openSettingsURLString) {
                                UIApplication.shared.open(url)
                            }
                            notificationBackStep = .sensorConnect
                            move(to: .notificationPermission)
                        },
                        onContinueWithoutSensor: {
                            notificationBackStep = .sensorConnect
                            move(to: .notificationPermission)
                        }
                    )
                    .transition(stepTransition)

                case .noSensorFallback:
                    NoSensorFallbackStepView(
                        onBack: { move(to: .sensorConnect) },
                        onContinue: {
                            notificationBackStep = .noSensorFallback
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
        [
            .identity,
            .dataPurpose,
            .features,
            .birthAndGender,
            .bodyMetrics,
            .maxHeartRate,
            .restingHeartRate,
            .enduranceHabits,
            .frequencyAndDuration,
            .summary,
            .sensorConnect,
            .notificationPermission,
        ]
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

    private func requestNotificationsAndFinish() {
        guard !finishingOnboarding else { return }
        finishingOnboarding = true

        Task {
            let granted = (try? await UNUserNotificationCenter.current().requestAuthorization(options: [.alert, .badge, .sound])) ?? false
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

private struct OnboardingAtmosphereView: View {
    let step: OnboardingStep
    @Environment(\.colorScheme) private var colorScheme

    private var imageName: String {
        switch step {
        case .welcome, .language, .features, .auth, .identity, .dataPurpose:
            return "OnboardingBgOutdoor"
        case .birthAndGender, .bodyMetrics, .maxHeartRate, .restingHeartRate, .enduranceHabits, .frequencyAndDuration, .summary, .result:
            return "OnboardingBgRun"
        case .sensorConnect, .noSensorFallback, .notificationPermission:
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
            onPrimary: onContinue
        ) {
            VStack(spacing: 16) {
                identityInputField(
                    label: L10n.firstNameLabel,
                    placeholder: L10n.firstNamePlaceholder,
                    text: $firstName,
                    focused: .firstName,
                    contentType: .givenName,
                    submitLabel: .next
                ) {
                    focusedField = .lastName
                }

                identityInputField(
                    label: L10n.lastNameLabel,
                    placeholder: L10n.lastNamePlaceholder,
                    text: $lastName,
                    focused: .lastName,
                    contentType: .familyName,
                    submitLabel: .done
                ) {
                    if canContinue {
                        onContinue()
                    }
                }
            }
        }
        .onAppear {
            focusedField = .firstName
        }
    }

    private func identityInputField(
        label: String,
        placeholder: String,
        text: Binding<String>,
        focused: Field,
        contentType: UITextContentType?,
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
                .textContentType(contentType)
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
}

private struct DataPurposeStepView: View {
    let firstName: String
    let onBack: () -> Void
    let onContinue: () -> Void

    var body: some View {
        GeometryReader { geo in
            let renderWidth = geo.size.width
            let deviceWidth = UIScreen.main.bounds.width
            let layoutWidth = min(min(renderWidth, deviceWidth), 500)
            let sidePadding = layoutWidth < 390 ? 18.0 : 24.0
            let contentWidth = max(0.0, layoutWidth - (sidePadding * 2))
            let topInset = max(geo.size.height * 0.18, geo.safeAreaInsets.top + 42.0)

            VStack(alignment: .leading, spacing: 0) {
                Spacer()
                    .frame(height: topInset)

                VStack(alignment: .leading, spacing: 18) {
                    Text(greetingTitle)
                        .font(.system(size: 36, weight: .bold, design: .rounded))
                        .foregroundColor(CoachiTheme.textPrimary)
                        .fixedSize(horizontal: false, vertical: true)

                    Text(greetingBody)
                        .font(.title3.weight(.semibold))
                        .foregroundColor(CoachiTheme.textSecondary)
                        .fixedSize(horizontal: false, vertical: true)
                        .frame(maxWidth: 320, alignment: .leading)

                    VStack(alignment: .leading, spacing: 10) {
                        helloBullet(
                            text: L10n.current == .no
                                ? "Tilpasse intensitet, oppsummering og coaching til deg."
                                : "Tailor intensity, summaries, and coaching to you."
                        )
                        helloBullet(
                            text: L10n.current == .no
                                ? "Gjore deg klar for fire korte steg om hvordan Coachi hjelper."
                                : "Get you ready for four short steps on how Coachi helps."
                        )
                    }
                    .padding(.top, 6)
                }
                .frame(width: contentWidth, alignment: .leading)
                .padding(.horizontal, sidePadding)

                Spacer(minLength: 0)
            }
            .frame(width: layoutWidth, height: geo.size.height, alignment: .topLeading)
            .frame(maxWidth: .infinity, maxHeight: .infinity, alignment: .top)
            .safeAreaInset(edge: .bottom, spacing: 0) {
                HStack(spacing: 16) {
                    Button(action: onBack) {
                        Image(systemName: "chevron.left")
                            .font(.title3.weight(.bold))
                            .foregroundColor(CoachiTheme.textPrimary)
                            .frame(width: 54, height: 54)
                            .background(CoachiTheme.surface.opacity(0.96))
                            .clipShape(Circle())
                            .overlay(
                                Circle()
                                    .stroke(CoachiTheme.borderSubtle.opacity(0.45), lineWidth: 1)
                            )
                    }

                    Spacer()

                    Button(action: onContinue) {
                        Text(L10n.continueButton)
                            .font(.headline.weight(.bold))
                            .foregroundColor(.white)
                            .padding(.horizontal, 30)
                            .frame(height: 56)
                            .background(CoachiTheme.primaryGradient)
                            .clipShape(RoundedRectangle(cornerRadius: 20, style: .continuous))
                    }
                }
                .padding(.horizontal, sidePadding)
                .padding(.top, 12)
                .padding(.bottom, max(18.0, geo.safeAreaInsets.bottom + 8.0))
            }
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

    private func helloBullet(text: String) -> some View {
        HStack(alignment: .top, spacing: 10) {
            Circle()
                .fill(CoachiTheme.primary)
                .frame(width: 7, height: 7)
                .padding(.top, 7)
            Text(text)
                .font(.body.weight(.medium))
                .foregroundColor(CoachiTheme.textSecondary)
            Spacer()
        }
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
                ? "Maks puls starter fra alder, men du kan justere hvis du vet riktig tall."
                : "Max HR starts from age, but you can adjust if you know your true value.",
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
                ? "Legg inn hvilepuls. Du kan endre dette senere i appen."
                : "Enter your resting HR. You can update this later in settings.",
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
                        ? "Tips: mål hvilepuls når du sitter rolig, helst etter noen minutter hvile."
                        : "Tip: measure resting HR while seated and relaxed for a few minutes."
                )
                .font(.footnote.weight(.medium))
                .foregroundColor(CoachiTheme.textSecondary)
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

                if doesEnduranceTraining {
                    VStack(alignment: .leading, spacing: 10) {
                        Text(
                            L10n.current == .no
                                ? "Hvor intensiv er den hardeste utholdenhetsøkta di?"
                                : "How intense is your hardest endurance session?"
                        )
                        .font(.body.weight(.semibold))
                        .foregroundColor(CoachiTheme.textPrimary)

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
    @Binding var moderateFrequency: ModerateFrequencyOption
    @Binding var moderateDuration: ModerateDurationOption
    let onBack: () -> Void
    let onContinue: () -> Void

    var body: some View {
        OnboardingScaffold(
            title: L10n.aboutYou,
            subtitle: L10n.current == .no
                ? "Hvor ofte og hvor lenge trener du med moderat intensitet?"
                : "How often and how long do you train at moderate intensity?",
            onBack: onBack,
            primaryTitle: L10n.continueButton,
            canContinue: true,
            onPrimary: onContinue
        ) {
            VStack(spacing: 16) {
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
                        ? "Du kan endre alt senere. Nå sjekker vi bare at grunnlaget stemmer."
                        : "You can change everything later. This is just a quick final check."
                )
                .font(.body.weight(.semibold))
                .foregroundColor(CoachiTheme.textSecondary)

                Divider()
                    .overlay(CoachiTheme.borderSubtle.opacity(0.55))

                summaryRow(label: L10n.firstNamePlaceholder, value: state.firstName)
                summaryRow(label: L10n.lastNamePlaceholder, value: state.lastName)
                summaryRow(label: L10n.current == .no ? "Alder" : "Age", value: "\(state.age)")
                summaryRow(label: L10n.current == .no ? "Kjønn" : "Gender", value: state.gender.title)
                summaryRow(label: L10n.current == .no ? "Høyde" : "Height", value: "\(state.heightCm) cm")
                summaryRow(label: L10n.current == .no ? "Vekt" : "Weight", value: "\(state.weightKg) kg")
                summaryRow(label: L10n.current == .no ? "Makspuls" : "Max HR", value: "\(state.hrMax) bpm")
                summaryRow(label: L10n.current == .no ? "Hvilepuls" : "Resting HR", value: "\(state.restingHR) bpm")
                summaryRow(label: L10n.current == .no ? "Moderat frekvens" : "Moderate frequency", value: state.moderateFrequency.title)
                summaryRow(label: L10n.current == .no ? "Varighet" : "Duration", value: state.moderateDuration.title)
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

    private func summaryRow(label: String, value: String) -> some View {
        HStack {
            Text(label)
                .font(.body.weight(.medium))
                .foregroundColor(CoachiTheme.textSecondary)
            Spacer()
            Text(value.isEmpty ? "-" : value)
                .font(.headline.weight(.semibold))
                .foregroundColor(CoachiTheme.textPrimary)
                .multilineTextAlignment(.trailing)
        }
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
    let onBack: () -> Void
    let onConnectNow: () -> Void
    let onContinueWithoutSensor: () -> Void

    var body: some View {
        OnboardingScaffold(
            title: L10n.sensorConnectTitle,
            subtitle: L10n.sensorConnectBody,
            onBack: onBack,
            primaryTitle: L10n.sensorConnectPrimary,
            canContinue: true,
            onPrimary: onConnectNow,
            secondaryTitle: L10n.sensorConnectSecondary,
            onSecondary: onContinueWithoutSensor
        ) {
            VStack(spacing: 14) {
                Image(systemName: "applewatch.radiowaves.left.and.right")
                    .font(.largeTitle.weight(.medium))
                    .foregroundStyle(CoachiTheme.tealGradient)
                    .frame(maxWidth: .infinity, alignment: .center)

                Text(
                    L10n.current == .no
                        ? "Klokke er best for live puls. Uten klokke får du fortsatt tydelig coaching."
                        : "A watch is best for live heart rate. Without one, you still get clear coaching."
                )
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
                    .stroke(CoachiTheme.borderSubtle.opacity(0.36), lineWidth: 1)
            )
        }
    }
}

private struct NoSensorFallbackStepView: View {
    let onBack: () -> Void
    let onContinue: () -> Void

    var body: some View {
        OnboardingScaffold(
            title: L10n.current == .no ? "Ingen pulsklokke?" : "No watch?",
            subtitle: L10n.current == .no
                ? "Ingen fare. Du kan starte i dag, og vi coacher fortsatt tydelig på struktur og tid."
                : "No problem. You can start today, and Coachi will still guide clearly by structure and timing.",
            onBack: onBack,
            primaryTitle: L10n.current == .no ? "Fortsett til appen" : "Continue to app",
            canContinue: true,
            onPrimary: onContinue
        ) {
            VStack(alignment: .leading, spacing: 10) {
                bullet(
                    text: L10n.current == .no
                        ? "Du kan koble klokke senere fra Profil."
                        : "You can connect a watch later from Profile."
                )
                bullet(
                    text: L10n.current == .no
                        ? "Med klokke blir pulscoaching mer presis."
                        : "With a watch, heart-rate coaching becomes more precise."
                )
                bullet(
                    text: L10n.current == .no
                        ? "Uten klokke holder coachen språket kort og tydelig."
                        : "Without a watch, the coach still stays short and clear."
                )
            }
            .padding(18)
            .frame(maxWidth: .infinity, alignment: .leading)
            .background(CoachiTheme.surface)
            .clipShape(RoundedRectangle(cornerRadius: 16, style: .continuous))
            .overlay(
                RoundedRectangle(cornerRadius: 16, style: .continuous)
                    .stroke(CoachiTheme.borderSubtle.opacity(0.36), lineWidth: 1)
            )
        }
    }

    private func bullet(text: String) -> some View {
        HStack(alignment: .top, spacing: 10) {
            Circle()
                .fill(CoachiTheme.primary)
                .frame(width: 7, height: 7)
                .padding(.top, 6)
            Text(text)
                .font(.subheadline.weight(.medium))
                .foregroundColor(CoachiTheme.textSecondary)
            Spacer()
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
            let bottomInset = min(42.0, max(20.0, geo.safeAreaInsets.bottom + 8.0))
            let contentTopInset = max(renderHeight * 0.08, 24.0)

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
