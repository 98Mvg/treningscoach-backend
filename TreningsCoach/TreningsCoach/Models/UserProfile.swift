//
//  UserProfile.swift
//  TreningsCoach
//
//  User profile, language, and training level models
//

import Foundation

// MARK: - App Language

enum AppLanguage: String, Codable, CaseIterable, Identifiable {
    case en = "en"
    case no = "no"

    var id: String { rawValue }

    var displayName: String {
        switch self {
        case .en: return "English"
        case .no: return "Norsk"
        }
    }

    var flagEmoji: String {
        switch self {
        case .en: return "\u{1F1EC}\u{1F1E7}"  // GB flag
        case .no: return "\u{1F1F3}\u{1F1F4}"  // NO flag
        }
    }
}

// MARK: - Training Level

enum TrainingLevel: String, Codable, CaseIterable, Identifiable {
    case beginner = "beginner"
    case intermediate = "intermediate"
    case advanced = "advanced"

    var id: String { rawValue }

    var displayName: String {
        switch self {
        case .beginner: return L10n.current == .no ? "Nybegynner" : "Beginner"
        case .intermediate: return L10n.current == .no ? "Middels" : "Intermediate"
        case .advanced: return L10n.current == .no ? "Avansert" : "Advanced"
        }
    }

    var description: String {
        switch self {
        case .beginner: return L10n.current == .no ? "Jeg er ny med trening" : "I'm new to working out"
        case .intermediate: return L10n.current == .no ? "Jeg trener jevnlig" : "I work out regularly"
        case .advanced: return L10n.current == .no ? "Jeg er en erfaren utover" : "I'm an experienced athlete"
        }
    }

    var iconName: String {
        switch self {
        case .beginner: return "figure.walk"
        case .intermediate: return "figure.run"
        case .advanced: return "figure.highintensity.intervaltraining"
        }
    }
}

// MARK: - User Profile

struct UserProfile: Codable {
    let id: String
    let email: String
    var displayName: String?
    var avatarURL: String?
    var language: AppLanguage
    var trainingLevel: TrainingLevel
    var preferredPersona: String?

    enum CodingKeys: String, CodingKey {
        case id, email
        case displayName = "display_name"
        case avatarURL = "avatar_url"
        case language
        case trainingLevel = "training_level"
        case preferredPersona = "preferred_persona"
    }

    init(from decoder: Decoder) throws {
        let container = try decoder.container(keyedBy: CodingKeys.self)
        id = try container.decode(String.self, forKey: .id)
        email = try container.decode(String.self, forKey: .email)
        displayName = try container.decodeIfPresent(String.self, forKey: .displayName)
        avatarURL = try container.decodeIfPresent(String.self, forKey: .avatarURL)

        let langString = try container.decodeIfPresent(String.self, forKey: .language) ?? "en"
        language = AppLanguage(rawValue: langString) ?? .en

        let levelString = try container.decodeIfPresent(String.self, forKey: .trainingLevel) ?? "intermediate"
        trainingLevel = TrainingLevel(rawValue: levelString) ?? .intermediate

        preferredPersona = try container.decodeIfPresent(String.self, forKey: .preferredPersona)
    }
}

// MARK: - Auth Response

struct AuthResponse: Codable {
    let token: String
    let user: UserProfile
}

struct ProfileResponse: Codable {
    let user: UserProfile
}
