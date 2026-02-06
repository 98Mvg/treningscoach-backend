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
    static var appName: String { "Treningscoach" }

    // MARK: - Greetings
    static var goodMorning: String { current == .no ? "God morgen" : "Good morning" }
    static var goodAfternoon: String { current == .no ? "God ettermiddag" : "Good afternoon" }
    static var goodEvening: String { current == .no ? "God kveld" : "Good evening" }
    static var goodNight: String { current == .no ? "God natt" : "Good night" }

    // MARK: - Home
    static var startWorkout: String { current == .no ? "Start trening" : "Start Workout" }
    static var audioCoachingStarts: String { current == .no ? "Lydcoaching starter umiddelbart" : "Audio coaching starts immediately" }
    static var thisWeek: String { current == .no ? "Denne uken" : "This week" }
    static var workoutsCompleted: String { current == .no ? "treninger fullfort" : "workouts completed" }
    static var recentWorkouts: String { current == .no ? "Siste treninger" : "Recent Workouts" }
    static var noWorkoutsYet: String { current == .no ? "Ingen treninger ennaa" : "No workouts yet" }
    static var tapStartWorkout: String { current == .no ? "Trykk Start trening for aa begynne" : "Tap Start Workout to begin your first session" }
    static var of: String { current == .no ? "av" : "of" }

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
    static var settings: String { current == .no ? "Innstillinger" : "Settings" }
    static var workouts: String { current == .no ? "Treninger" : "Workouts" }
    static var minutes: String { current == .no ? "Minutter" : "Minutes" }
    static var streak: String { current == .no ? "Rekke" : "Streak" }
    static var experienceLevel: String { current == .no ? "Treningsnivaa" : "Experience Level" }
    static var coachVoice: String { current == .no ? "Coach-stemme" : "Coach Voice" }
    static var language: String { current == .no ? "Spraak" : "Language" }
    static var signOut: String { current == .no ? "Logg ut" : "Sign Out" }
    static var athlete: String { current == .no ? "Utover" : "Athlete" }

    // MARK: - Onboarding
    static var chooseLanguage: String { current == .no ? "Velg spraak" : "Choose Language" }
    static var languageSubtitle: String { current == .no ? "Dette styrer bade appen og coachen" : "This controls both the app and the coach" }
    static var signIn: String { current == .no ? "Logg inn" : "Sign In" }
    static var signInSubtitle: String { current == .no ? "Opprett kontoen din for aa komme i gang" : "Create your account to get started" }
    static var signInWithGoogle: String { current == .no ? "Logg inn med Google" : "Sign in with Google" }
    static var signInWithFacebook: String { current == .no ? "Logg inn med Facebook" : "Sign in with Facebook" }
    static var signInWithVipps: String { current == .no ? "Logg inn med Vipps" : "Sign in with Vipps" }
    static var trainingLevel: String { current == .no ? "Treningsnivaa" : "Training Level" }
    static var trainingLevelSubtitle: String { current == .no ? "Dette paavirker coachens tone og intensitet" : "This influences the coach's tone and intensity" }
    static var continueButton: String { current == .no ? "Fortsett" : "Continue" }
    static var getStarted: String { current == .no ? "Kom i gang" : "Get Started" }
    static var skip: String { current == .no ? "Hopp over" : "Skip" }
    static var continueWithoutAccount: String { current == .no ? "Fortsett uten konto" : "Continue without account" }

    // MARK: - Intensity
    static var calm: String { current == .no ? "Rolig" : "Calm" }
    static var moderate: String { current == .no ? "Moderat" : "Moderate" }
    static var intenseLvl: String { current == .no ? "Intens" : "Intense" }
    static var critical: String { current == .no ? "Kritisk" : "Critical" }

    // MARK: - Wake Word
    static var sayCoachToSpeak: String { current == .no ? "Si \"Trener\" for aa snakke" : "Say \"Coach\" to speak" }
    static var listeningForYou: String { current == .no ? "Lytter..." : "Listening..." }
    static var coachHeard: String { current == .no ? "Hoert!" : "Heard!" }

    // MARK: - Workout Player
    static var paused: String { current == .no ? "Pauset" : "Paused" }
    static var recording: String { current == .no ? "Opptaker" : "Recording" }

    // MARK: - Errors
    static var error: String { current == .no ? "Feil" : "Error" }
    static var ok: String { "OK" }
    static var cancel: String { current == .no ? "Avbryt" : "Cancel" }
}
