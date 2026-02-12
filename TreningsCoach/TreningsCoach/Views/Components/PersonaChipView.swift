//
//  PersonaChipView.swift
//  TreningsCoach
//
//  Persona selection chip for coach picker
//

import SwiftUI

struct PersonaChipView: View {
    let persona: CoachPersonality
    let isSelected: Bool
    let action: () -> Void

    var body: some View {
        Button(action: action) {
            HStack(spacing: 8) {
                Image(systemName: persona.icon).font(.system(size: 14, weight: .semibold))
                Text(persona.displayName).font(.system(size: 14, weight: .semibold))
            }
            .foregroundColor(isSelected ? .white : CoachiTheme.textSecondary)
            .padding(.horizontal, 16).padding(.vertical, 10)
            .background(
                Group {
                    if isSelected {
                        RoundedRectangle(cornerRadius: 20, style: .continuous).fill(CoachiTheme.primaryGradient)
                    } else {
                        RoundedRectangle(cornerRadius: 20, style: .continuous).fill(CoachiTheme.surface)
                            .overlay(RoundedRectangle(cornerRadius: 20, style: .continuous).stroke(CoachiTheme.textTertiary.opacity(0.3), lineWidth: 1))
                    }
                }
            )
        }
        .buttonStyle(.plain)
    }
}
