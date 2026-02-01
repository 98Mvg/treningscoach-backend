//
//  AppTheme.swift
//  TreningsCoach
//
//  Dark purple/blue theme system
//  All colors and shared styles live here
//

import SwiftUI

// MARK: - Color Extension (Hex Support)

extension Color {
    init(hex: String) {
        let hex = hex.trimmingCharacters(in: CharacterSet.alphanumerics.inverted)
        var int: UInt64 = 0
        Scanner(string: hex).scanHexInt64(&int)
        let r = Double((int >> 16) & 0xFF) / 255.0
        let g = Double((int >> 8) & 0xFF) / 255.0
        let b = Double(int & 0xFF) / 255.0
        self.init(red: r, green: g, blue: b)
    }
}

// MARK: - Theme

struct AppTheme {
    // Background
    static let background = Color(hex: "1A1A2E")
    static let backgroundDeep = Color(hex: "0F0F1A")
    static let cardSurface = Color(hex: "16213E")

    // Accents
    static let primaryAccent = Color(hex: "7C3AED")   // Purple
    static let secondaryAccent = Color(hex: "22D3EE")  // Cyan
    static let success = Color(hex: "10B981")           // Green
    static let danger = Color(hex: "EF4444")            // Red
    static let warning = Color(hex: "F59E0B")           // Orange

    // Text
    static let textPrimary = Color(hex: "F8FAFC")
    static let textSecondary = Color(hex: "94A3B8")

    // Gradients
    static let backgroundGradient = LinearGradient(
        colors: [background, backgroundDeep],
        startPoint: .top,
        endPoint: .bottom
    )

    static let purpleGradient = LinearGradient(
        colors: [Color(hex: "7C3AED"), Color(hex: "6D28D9")],
        startPoint: .topLeading,
        endPoint: .bottomTrailing
    )

    static let greenGradient = LinearGradient(
        colors: [Color(hex: "10B981"), Color(hex: "059669")],
        startPoint: .topLeading,
        endPoint: .bottomTrailing
    )

    static let redGradient = LinearGradient(
        colors: [Color(hex: "EF4444"), Color(hex: "DC2626")],
        startPoint: .topLeading,
        endPoint: .bottomTrailing
    )
}

// MARK: - Card Style Modifier

struct CardStyle: ViewModifier {
    func body(content: Content) -> some View {
        content
            .background(AppTheme.cardSurface)
            .clipShape(RoundedRectangle(cornerRadius: 16))
            .overlay(
                RoundedRectangle(cornerRadius: 16)
                    .stroke(Color.white.opacity(0.08), lineWidth: 1)
            )
    }
}

extension View {
    func cardStyle() -> some View {
        modifier(CardStyle())
    }
}
