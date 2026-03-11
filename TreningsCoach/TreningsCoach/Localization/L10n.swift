//
//  L10n.swift
//  TreningsCoach
//
//  Bilingual string catalog (English + Norwegian)
//  Driven by UserDefaults("app_language")
//

import Foundation

struct L10n {
    static var current: AppLanguage {
        let raw = UserDefaults.standard.string(forKey: "app_language") ?? "en"
        return AppLanguage(rawValue: raw) ?? .en
    }

    static func set(_ language: AppLanguage) {
        UserDefaults.standard.set(language.rawValue, forKey: "app_language")
    }

    // MARK: - General
    static var appName: String { "Coachi" }

    // MARK: - Greetings
    static var goodMorning: String { current == .no ? "God morgen" : "Good morning" }
    static var goodAfternoon: String { current == .no ? "God ettermiddag" : "Good afternoon" }
    static var goodEvening: String { current == .no ? "God kveld" : "Good evening" }
    static var goodNight: String { current == .no ? "God natt" : "Good night" }

    // MARK: - Home
    static var startWorkout: String { current == .no ? "Start trening" : "Start Workout" }
    static var audioCoachingStarts: String { current == .no ? "Lydcoaching starter umiddelbart" : "Audio coaching starts immediately" }
    static var connectHeartRateMonitorTitle: String { current == .no ? "Koble til pulsmåleren din" : "Connect your heart rate monitor" }
    static var connectHeartRateMonitorBody: String {
        current == .no
            ? "For live coaching, bruk Apple Watch eller Bluetooth-sensor."
            : "For live coaching, use Apple Watch or a Bluetooth HR sensor."
    }
    static var goToManageMonitors: String {
        current == .no ? "Gå til pulsmålere" : "Go to heart-rate monitors"
    }
    static var connected: String { current == .no ? "Tilkoblet" : "Connected" }
    static var notConnected: String { current == .no ? "Ikke tilkoblet" : "Not connected" }
    static var liveCapability: String { current == .no ? "Live" : "Live" }
    static var historyCapability: String { current == .no ? "Historikk" : "History" }
    static var liveCoachingSourceHint: String {
        current == .no
            ? "For live coaching, bruk Apple Watch eller en Bluetooth HR-sensor (stropp/klokke med broadcast)."
            : "For live coaching, use Apple Watch or a Bluetooth HR sensor (strap/watch broadcast)."
    }
    static var historySyncOnlyHint: String {
        current == .no
            ? "Fitbit/Withings synker historikk etter økten. Dette er ikke live puls."
            : "Fitbit/Withings connect for history only. This is not live HR."
    }
    static var historyViaBroadcastHint: String {
        current == .no
            ? "Live kun ved Bluetooth-broadcast"
            : "Live only if broadcasting Bluetooth HR"
    }
    static var thisWeek: String { current == .no ? "Denne uken" : "This week" }
    static var workoutsCompleted: String { current == .no ? "treninger fullfort" : "workouts completed" }
    static var recentWorkouts: String { current == .no ? "Siste treninger" : "Recent Workouts" }
    static var noWorkoutsYet: String { current == .no ? "Ingen treninger ennaa" : "No workouts yet" }
    static var tapStartWorkout: String { current == .no ? "Trykk Start trening for aa begynne" : "Tap Start Workout to begin your first session" }
    static var of: String { current == .no ? "av" : "of" }
    static var today: String { current == .no ? "I dag" : "Today" }
    static var coachScore: String { current == .no ? "Coach score" : "Coach score" }

    // MARK: - Workout
    static var warmup: String { current == .no ? "Oppvarming" : "Warm-up" }
    static var intense: String { current == .no ? "Intens" : "Intense" }
    static var cooldown: String { current == .no ? "Nedkjoeling" : "Cool-down" }
    static var tapToStart: String { current == .no ? "Trykk for aa starte trening" : "Tap to start workout" }
    static var stopWorkout: String { current == .no ? "Stopp trening" : "Stop Workout" }
    static var skipToWorkout: String { current == .no ? "Hopp til trening" : "Skip to Workout" }
    static var selectCoach: String { current == .no ? "Velg coach" : "Select Coach" }

    // MARK: - Profile
    static var myStatistics: String { current == .no ? "Min statistikk" : "My Statistics" }
    static var personalProfile: String { current == .no ? "Personlig profil" : "Personal profile" }
    static var healthProfile: String { current == .no ? "Helseprofil" : "Health profile" }
    static var manageHeartRateMonitors: String { current == .no ? "Puls og sensorer" : "Heart rate & sensors" }
    static var settings: String { current == .no ? "Innstillinger" : "Settings" }
    static var account: String { current == .no ? "Konto" : "Account" }
    static var accountStatus: String { current == .no ? "Kontostatus" : "Account status" }
    static var signedInAs: String { current == .no ? "Logget inn som" : "Signed in as" }
    static var usingWithoutAccount: String { current == .no ? "Bruker Coachi uten konto" : "Using Coachi without account" }
    static var connectAccountLaterHint: String {
        current == .no
            ? "Du kan koble til konto senere for historikk og synk."
            : "You can connect an account later for history and sync."
    }
    static var coaching: String { current == .no ? "Coaching" : "Coaching" }
    static var helpAndLegal: String { current == .no ? "Hjelp og juridisk" : "Help & legal" }
    static var audioAndVoices: String { current == .no ? "Lyd og stemmer" : "Audio & voices" }
    static var historyAndData: String { current == .no ? "Historikk og data" : "History & data" }
    static var howCoachiWorks: String { current == .no ? "Hvordan Coachi fungerer" : "How Coachi works" }
    static var ifHeartRateMissing: String { current == .no ? "Hvis puls mangler" : "If heart rate is missing" }
    static var trainingHistory: String { current == .no ? "Treningshistorikk" : "Training history" }
    static var dataAndPrivacy: String { current == .no ? "Data og personvern" : "Data & privacy" }
    static var voicePackStatus: String { current == .no ? "Status for lydpakke" : "Voice pack status" }
    static var activeVoice: String { current == .no ? "Aktiv stemme" : "Active voice" }
    static var accountSettings: String { current == .no ? "Brukerkontoinnstillinger" : "Account settings" }
    static var notifications: String { current == .no ? "Varsler" : "Notifications" }
    static var privacySettings: String { current == .no ? "Personverninnstillinger" : "Privacy settings" }
    static var sharingSettings: String { current == .no ? "Delingsinnstillinger" : "Sharing settings" }
    static var manageSubscription: String { current == .no ? "Administrer abonnement" : "Manage subscription" }
    static var helpAndSupport: String { current == .no ? "Hjelp og brukerstøtte" : "Help and support" }
    static var faqTitle: String { current == .no ? "Hvordan bruke Coachi (FAQ)" : "How to use Coachi (FAQ)" }
    static var contactSupport: String { current == .no ? "Kontakt brukerstøtte" : "Contact support" }
    static var legal: String { current == .no ? "Juridisk" : "Legal" }
    static var termsOfUse: String { current == .no ? "Brukervilkår" : "Terms of use" }
    static var privacyPolicy: String { current == .no ? "Personvernerklæring" : "Privacy policy" }
    static var appVersionLabel: String { current == .no ? "App-versjon" : "App version" }
    static var comingSoon: String { current == .no ? "Kommer snart" : "Coming soon" }
    static var workouts: String { current == .no ? "Treninger" : "Workouts" }
    static var minutes: String { current == .no ? "Minutter" : "Minutes" }
    static var streak: String { current == .no ? "Rekke" : "Streak" }
    static var experienceLevel: String { current == .no ? "Treningsnivaa" : "Experience Level" }
    static var dateOfBirth: String { current == .no ? "Fødselsdato" : "Date of birth" }
    static var coachVoice: String { current == .no ? "Coach-stemme" : "Coach Voice" }
    static var language: String { current == .no ? "Språk" : "Language" }
    static var signOut: String { current == .no ? "Logg ut" : "Sign Out" }
    static var athlete: String { current == .no ? "Utover" : "Athlete" }

    // MARK: - Onboarding
    static var chooseLanguage: String { current == .no ? "Velg språk" : "Choose language" }
    static var languageSubtitle: String {
        current == .no
            ? "Dette styrer appen og coachen. Du kan endre det senere."
            : "This controls the app and the coach. You can change it later."
    }
    static var signIn: String { current == .no ? "Logg inn for å fortsette" : "Sign in to continue" }
    static var signInSubtitle: String {
        current == .no
            ? "Bruk Apple eller e-post for å fortsette oppsettet og lagre framgangen din."
            : "Use Apple or email to continue setup and save your progress."
    }
    static var registerWithApple: String { current == .no ? "Registrer deg med Apple" : "Register with Apple" }
    static var continueWithEmail: String { current == .no ? "Fortsett med e-post" : "Continue with email" }
    static var sendEmailCode: String { current == .no ? "Send kode" : "Send code" }
    static var verifyEmailCode: String { current == .no ? "Bekreft kode" : "Verify code" }
    static var emailCodeLabel: String { current == .no ? "Engangskode" : "One-time code" }
    static var emailCodeSentHint: String {
        current == .no
            ? "Skriv inn koden vi sendte til e-posten din for å fortsette."
            : "Enter the code we sent to your email to continue."
    }
    static var accountRequiredHint: String {
        current == .no
            ? "Du trenger en konto for å fortsette i onboarding."
            : "You need an account to continue onboarding."
    }
    static var emailAddressInvalid: String {
        current == .no ? "Skriv inn en gyldig e-postadresse." : "Enter a valid email address."
    }
    static var emailCodeInvalid: String {
        current == .no ? "Skriv inn den seks-sifrede koden fra e-posten." : "Enter the six-digit code from your email."
    }
    static var emailCodeRequestFailed: String {
        current == .no ? "Kunne ikke sende kode. Prøv igjen." : "Could not send code. Please try again."
    }
    static var emailCodeVerifyFailed: String {
        current == .no ? "Kunne ikke bekrefte koden. Prøv igjen." : "Could not verify the code. Please try again."
    }
    static var emailDeliveryUnavailable: String {
        current == .no ? "E-postinnlogging er ikke tilgjengelig akkurat nå." : "Email sign-in is unavailable right now."
    }
    static var emailCodeExpired: String {
        current == .no ? "Koden er utløpt. Be om en ny kode." : "The code expired. Request a new code."
    }
    static var emailCodeMismatch: String {
        current == .no ? "Koden stemmer ikke. Prøv igjen." : "That code does not match. Try again."
    }
    static var registerWithGoogle: String { current == .no ? "Registrer deg med Google" : "Register with Google" }
    static var or: String { current == .no ? "Eller" : "Or" }
    static var emailAddress: String { current == .no ? "E-postadresse" : "Email address" }
    static var passwordLabel: String { current == .no ? "Passord" : "Password" }
    static var repeatPasswordLabel: String { current == .no ? "Gjenta passordet" : "Repeat password" }
    static var acceptTerms: String {
        current == .no
            ? "Ved aa hake av godtar du vilkar for bruk og personvern."
            : "By checking this box, you accept terms and privacy policy."
    }
    static var register: String { current == .no ? "Registrer deg" : "Register" }
    static var alreadyHaveUser: String { current == .no ? "Jeg har allerede en bruker" : "I already have an account" }
    static var signInWithGoogle: String { current == .no ? "Logg inn med Google" : "Sign in with Google" }
    static var signInWithFacebook: String { current == .no ? "Logg inn med Facebook" : "Sign in with Facebook" }
    static var signInWithVipps: String { current == .no ? "Logg inn med Vipps" : "Sign in with Vipps" }
    static var appleSignInFailedTryAgain: String {
        current == .no ? "Apple-innlogging feilet. Prøv igjen." : "Apple sign-in failed. Please try again."
    }
    static var appleIdentityVerifyFailed: String {
        current == .no ? "Kunne ikke verifisere Apple-identitet." : "Unable to verify Apple identity."
    }
    static var appleTokenExpired: String {
        current == .no ? "Apple-innloggingen utløp. Prøv igjen." : "Apple sign-in token expired. Please try again."
    }
    static var trainingLevel: String { current == .no ? "Treningsnivaa" : "Training Level" }
    static var trainingLevelSubtitle: String { current == .no ? "Dette paavirker coachens tone og intensitet" : "This influences the coach's tone and intensity" }
    static var continueButton: String { current == .no ? "Fortsett" : "Continue" }
    static var getStarted: String { current == .no ? "Kom i gang" : "Get Started" }
    static var skip: String { current == .no ? "Hopp over" : "Skip" }
    static var continueWithoutAccount: String { current == .no ? "Fortsett uten konto" : "Continue without account" }
    static var signInLaterHint: String {
        current == .no
            ? "Du kan starte gratis nå og koble til konto senere."
            : "You can start free now and connect an account later."
    }
    static var startFreeBadge: String { current == .no ? "Start gratis" : "Start free" }
    static var accountRequiredBadge: String { current == .no ? "Konto kreves" : "Account required" }
    static var watchOptionalBadge: String { current == .no ? "Klokke er valgfritt" : "Watch optional" }
    static var authBenefitSaveHistory: String {
        current == .no ? "Lagre økter og CoachScore" : "Save workouts and CoachScore"
    }
    static var authBenefitSyncProfile: String {
        current == .no ? "Synk profil og språk" : "Sync profile and language"
    }
    static var authBenefitAppleOrEmail: String {
        current == .no ? "Fortsett med Apple eller e-post" : "Continue with Apple or email"
    }

    // MARK: - Intensity
    static var calm: String { current == .no ? "Rolig" : "Calm" }
    static var moderate: String { current == .no ? "Moderat" : "Moderate" }
    static var intenseLvl: String { current == .no ? "Intens" : "Intense" }
    static var critical: String { current == .no ? "Kritisk" : "Critical" }

    // MARK: - Wake Word & Coach Interaction
    static var sayCoachToSpeak: String { current == .no ? "Si \"Coachi\" eller \"PT\"" : "Say \"Coach\" to speak" }
    static var listeningForYou: String { current == .no ? "Lytter..." : "Listening..." }
    static var coachHeard: String { current == .no ? "Hoert!" : "Heard!" }
    static var talkToCoachButton: String { current == .no ? "Snakk med coach" : "Talk to Coach" }
    static var coachSpeaking: String { current == .no ? "Coach svarer..." : "Coach speaking..." }

    // MARK: - Workout Player
    static var paused: String { current == .no ? "Pauset" : "Paused" }
    static var recording: String { current == .no ? "Opptaker" : "Recording" }
    static var console: String { current == .no ? "Konsoll" : "Console" }
    static var stopStartWorkout: String { current == .no ? "Stopp/start trening" : "Stop/start workout" }

    // MARK: - Onboarding (Coachi flow)
    static var aboutYou: String { current == .no ? "Om deg" : "About You" }
    static var firstNameLabel: String { current == .no ? "Hva er fornavnet ditt?" : "What is your first name?" }
    static var firstNamePlaceholder: String { current == .no ? "Fornavn" : "First name" }
    static var lastNameLabel: String { current == .no ? "Hva er etternavnet ditt?" : "What is your last name?" }
    static var lastNamePlaceholder: String { current == .no ? "Etternavn" : "Last name" }
    static var beginnerAutoLevelLine: String {
        current == .no
            ? "Du starter som Nybegynner og bygger deg opp med gode oekter."
            : "You start as Beginner and level up with good-quality workouts."
    }
    static var coachScoreIntroHeadline: String {
        current == .no ? "Ett tall som viser formen din" : "One score that shows your form"
    }
    static var coachScoreIntroSubline: String {
        current == .no
            ? "Bra, %@. Etter hver oekt faar du CoachScore som viser hvor godt du holdt riktig puls."
            : "Great, %@. After each workout you get a CoachScore that shows how well you stayed in the right HR zone."
    }
    static var coachScoreLabel: String { "CoachScore" }
    static var coachScoreSolidLabel: String { current == .no ? "Solid oekt" : "Solid workout" }
    static var coachScoreReasonZone: String {
        current == .no ? "Tid i riktig sone" : "Time in target zone"
    }
    static var coachScoreReasonConsistency: String {
        current == .no ? "Jevn innsats i oekten" : "Steady effort through the workout"
    }
    static var coachScoreReasonRecovery: String {
        current == .no ? "God kontroll i recovery" : "Good recovery control"
    }
    static var sensorConnectTitle: String {
        current == .no ? "Koble til pulsklokke" : "Connect your watch"
    }
    static var sensorConnectBody: String {
        current == .no
            ? "Med klokke blir pulscoaching mer presis. Uten klokke coacher vi fortsatt på struktur og tid."
            : "With a watch, heart-rate coaching becomes more precise. Without one, Coachi still guides by structure and timing."
    }
    static var sensorConnectPrimary: String {
        current == .no ? "Koble til na" : "Connect now"
    }
    static var sensorConnectSecondary: String {
        current == .no ? "Fortsett uten klokke" : "Continue without watch"
    }
    static var setupProfile: String { current == .no ? "Sett opp profilen din" : "Set up your profile" }
    static var whatToCallYou: String { current == .no ? "Hva skal vi kalle deg?" : "What should we call you?" }
    static var startTraining: String { current == .no ? "Start trening" : "Start Training" }
    static var realTimeCoaching: String { current == .no ? "Sanntids coaching" : "Real-Time Coaching" }
    static var trackProgress: String { current == .no ? "Folg fremgang" : "Track Progress" }
    static var personalTouch: String { current == .no ? "Personlig preg" : "Personal Touch" }
    static var chooseYourCoach: String { current == .no ? "Velg din coach" : "Choose Your Coach" }

    // MARK: - Workout Setup
    static var warmupTime: String { current == .no ? "Oppvarmingstid" : "Warm-up Time" }
    static var inputSources: String { current == .no ? "Datakilder" : "Input sources" }
    static var workoutIntensityTitle: String { current == .no ? "Treningsintensitet" : "Workout intensity" }
    static var workoutIntensityDescription: String {
        current == .no
            ? "Du velger pulssonen og Coachen hjelper deg å holde riktig sone."
            : "You choose the target zone and Coachi helps you stay in it."
    }
    static var breathAnalysisTitle: String { current == .no ? "Pusteanalyse" : "Breath analysis" }
    static var breathAnalysisSubtitle: String {
        current == .no
            ? "Bruker mikrofonen til å analysere pust under trening."
            : "Uses microphone to analyze breathing during workouts."
    }
    static var go: String { current == .no ? "KJØR" : "GO" }
    static var min: String { current == .no ? "min" : "min" }
    static var minutesUpper: String { current == .no ? "MINUTTER" : "MINUTES" }
    static var noWarmup: String { current == .no ? "Ingen" : "None" }
    static var skipWarmup: String { current == .no ? "HOPP OVER" : "SKIP" }
    static var intensityEasy: String { current == .no ? "Lett" : "Easy" }
    static var intensityMedium: String { current == .no ? "Middels" : "Medium" }
    static var intensityHard: String { current == .no ? "Hard" : "Hard" }
    static var warmupEasyBPMCue: String {
        current == .no
            ? "Oppvarming kjøres alltid i lett intensitet."
            : "Warm-up always runs at easy intensity."
    }

    // MARK: - Workout Complete
    static var greatWorkout: String { current == .no ? "Bra trening!" : "Great Workout!" }
    static var duration: String { current == .no ? "Varighet" : "Duration" }
    static var done: String { current == .no ? "Ferdig" : "Done" }
    static var share: String { current == .no ? "Del" : "Share" }

    // MARK: - Settings / About
    static var about: String { current == .no ? "Om" : "About" }
    static var aboutCoachi: String { current == .no ? "Om Coachi" : "About Coachi" }
    static var advancedSettings: String { current == .no ? "Avansert" : "Advanced" }
    static var audioMaintenance: String {
        current == .no
            ? "Språk, mørk modus og vedlikehold av lydpakken"
            : "Language, dark mode, and audio-pack maintenance"
    }
    static var version: String { current == .no ? "Versjon" : "Version" }
    static var themeColor: String { current == .no ? "Temafarge" : "Theme color" }
    static var chooseThemeColor: String { current == .no ? "Velg temafarge" : "Choose theme color" }
    static var darkMode: String { current == .no ? "Mørk modus" : "Dark mode" }
    static var darkModeSubtitle: String {
        current == .no
            ? "Bytt mellom svart og hvit app-visning."
            : "Switch between black and white app appearance."
    }

    // MARK: - Voice Pack
    static var voicePackTitle: String { current == .no ? "Stemmepakke" : "Voice Pack" }
    static var resetVoicePack: String { current == .no ? "Tilbakestill stemmepakke" : "Reset Voice Pack" }
    static var purgeStaleFiles: String { current == .no ? "Rydd opp filer" : "Purge Stale Files" }

    // MARK: - Tab Bar
    static var home: String { current == .no ? "Hjem" : "Home" }
    static var workout: String { current == .no ? "Trening" : "Workout" }
    static var profile: String { current == .no ? "Profil" : "Profile" }
    static var profileTab: String { current == .no ? "Din profil" : "Your profile" }

    // MARK: - Errors
    static var error: String { current == .no ? "Feil" : "Error" }
    static var ok: String { "OK" }
    static var cancel: String { current == .no ? "Avbryt" : "Cancel" }
}
