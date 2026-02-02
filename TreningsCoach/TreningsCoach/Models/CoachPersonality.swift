//
//  CoachPersonality.swift
//  TreningsCoach
//
//  Coach personality enum for persona selection during workouts
//

import SwiftUI

enum CoachPersonality: String, CaseIterable, Identifiable, Codable {
    case fitnessCoach = "fitness_coach"
    case calmCoach = "calm_coach"
    case drillSergeant = "drill_sergeant"
    case personalTrainer = "personal_trainer"
    case toxicMode = "toxic_mode"

    var id: String { rawValue }

    var displayName: String {
        if L10n.current == .no {
            switch self {
            case .fitnessCoach: return "Treningscoach"
            case .calmCoach: return "Rolig Coach"
            case .drillSergeant: return "Drillsersjant"
            case .personalTrainer: return "Personlig Trener"
            case .toxicMode: return "Toxic Mode"
            }
        }
        switch self {
        case .fitnessCoach: return "Fitness Coach"
        case .calmCoach: return "Calm Coach"
        case .drillSergeant: return "Drill Sergeant"
        case .personalTrainer: return "Personal Trainer"
        case .toxicMode: return "Toxic Mode"
        }
    }

    var description: String {
        if L10n.current == .no {
            switch self {
            case .fitnessCoach: return "Energisk og motiverende"
            case .calmCoach: return "Rolig og oppmerksom"
            case .drillSergeant: return "Toff og krevende"
            case .personalTrainer: return "Profesjonell og kunnskapsrik"
            case .toxicMode: return "Brutal humor. Ingen naade."
            }
        }
        switch self {
        case .fitnessCoach: return "Energetic and motivating"
        case .calmCoach: return "Gentle and mindful"
        case .drillSergeant: return "Tough and demanding"
        case .personalTrainer: return "Professional and knowledgeable"
        case .toxicMode: return "Dark humor. Zero mercy."
        }
    }

    var icon: String {
        switch self {
        case .fitnessCoach: return "flame.fill"
        case .calmCoach: return "leaf.fill"
        case .drillSergeant: return "shield.fill"
        case .personalTrainer: return "brain.head.profile"
        case .toxicMode: return "bolt.heart.fill"
        }
    }

    var accentColor: Color {
        switch self {
        case .fitnessCoach: return AppTheme.primaryAccent
        case .calmCoach: return AppTheme.success
        case .drillSergeant: return AppTheme.warning
        case .personalTrainer: return AppTheme.secondaryAccent
        case .toxicMode: return AppTheme.danger
        }
    }
}
