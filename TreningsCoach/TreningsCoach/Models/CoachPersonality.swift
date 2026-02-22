//
//  CoachPersonality.swift
//  TreningsCoach
//
//  Coach personality enum for persona selection during workouts
//  2 personas: Personal Trainer (default), Performance Mode
//

import SwiftUI

enum CoachPersonality: String, CaseIterable, Identifiable, Codable {
    case personalTrainer = "personal_trainer"
    case toxicMode = "toxic_mode"

    var id: String { rawValue }

    var displayName: String {
        if L10n.current == .no {
            switch self {
            case .personalTrainer: return "Personlig Trener"
            case .toxicMode: return "Performance Mode"
            }
        }
        switch self {
        case .personalTrainer: return "Personal Trainer"
        case .toxicMode: return "Performance Mode"
        }
    }

    var description: String {
        if L10n.current == .no {
            switch self {
            case .personalTrainer: return "Rolig, disiplinert og direkte"
            case .toxicMode: return "Mer trykk, tydelig fokus og høy energi."
            }
        }
        switch self {
        case .personalTrainer: return "Calm, disciplined, and direct"
        case .toxicMode: return "Higher energy with sharper performance focus."
        }
    }

    var icon: String {
        switch self {
        case .personalTrainer: return "figure.run"
        case .toxicMode: return "bolt.heart.fill"
        }
    }

    var accentColor: Color {
        switch self {
        case .personalTrainer: return CoachiTheme.primary
        case .toxicMode: return CoachiTheme.danger
        }
    }
}
