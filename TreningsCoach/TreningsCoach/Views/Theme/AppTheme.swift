//
//  AppTheme.swift
//  TreningsCoach
//
//  "Midnight Ember" design system — Coachi theme
//  All colors, gradients, and shared view modifiers live here
//

import SwiftUI

// MARK: - Color Extension (Hex Support with Alpha)

extension Color {
    init(hex: String) {
        let hex = hex.trimmingCharacters(in: CharacterSet.alphanumerics.inverted)
        var int: UInt64 = 0
        Scanner(string: hex).scanHexInt64(&int)
        let a, r, g, b: UInt64
        switch hex.count {
        case 6:
            (a, r, g, b) = (255, int >> 16, int >> 8 & 0xFF, int & 0xFF)
        case 8:
            (a, r, g, b) = (int >> 24, int >> 16 & 0xFF, int >> 8 & 0xFF, int & 0xFF)
        default:
            (a, r, g, b) = (255, 0, 0, 0)
        }
        self.init(
            .sRGB,
            red: Double(r) / 255,
            green: Double(g) / 255,
            blue: Double(b) / 255,
            opacity: Double(a) / 255
        )
    }
}

// MARK: - Coachi Theme

enum CoachiTheme {
    // Backgrounds
    static let bgDeep           = Color(hex: "0A0A0F")
    static let bg               = Color(hex: "111118")
    static let surface          = Color(hex: "1A1A24")
    static let surfaceElevated  = Color(hex: "222230")

    // Primary
    static let primary          = Color(hex: "FF6B35")
    static let primaryLight     = Color(hex: "FF8F5E")

    // Secondary
    static let secondary        = Color(hex: "4ECDC4")

    // Accent
    static let accent           = Color(hex: "FFD93D")

    // Text
    static let textPrimary      = Color(hex: "F5F5F7")
    static let textSecondary    = Color(hex: "8E8E9A")
    static let textTertiary     = Color(hex: "55556A")

    // Warmup Dial
    static let dialPurple       = Color(hex: "7B2FBE")
    static let dialMagenta      = Color(hex: "D946EF")

    // Semantic
    static let danger           = Color(hex: "FF4757")
    static let success          = Color(hex: "2ED573")

    // Gradients
    static let primaryGradient    = LinearGradient(colors: [primary, Color(hex: "FF4757")], startPoint: .topLeading, endPoint: .bottomTrailing)
    static let backgroundGradient = LinearGradient(colors: [bg, bgDeep], startPoint: .top, endPoint: .bottom)
    static let surfaceGradient    = LinearGradient(colors: [surface, Color(hex: "151520")], startPoint: .top, endPoint: .bottom)
    static let activeGradient     = LinearGradient(colors: [primary, accent], startPoint: .topLeading, endPoint: .bottomTrailing)
    static let coolGradient       = LinearGradient(colors: [secondary, success], startPoint: .topLeading, endPoint: .bottomTrailing)
    static let emberGradient      = LinearGradient(colors: [primary, primaryLight], startPoint: .top, endPoint: .bottom)
    static let tealGradient       = LinearGradient(colors: [secondary, success], startPoint: .top, endPoint: .bottom)
    static let goldGradient       = LinearGradient(colors: [accent, primary], startPoint: .top, endPoint: .bottom)
    static let grayGradient       = LinearGradient(colors: [textTertiary, textSecondary], startPoint: .top, endPoint: .bottom)
}

// MARK: - Backward-compat: AppTheme → CoachiTheme

typealias AppTheme = CoachiTheme

extension CoachiTheme {
    // Old names → new names
    static var background: Color { bg }
    static var backgroundDeep: Color { bgDeep }
    static var cardSurface: Color { surface }
    static var primaryAccent: Color { primary }
    static var secondaryAccent: Color { secondary }
    static var warning: Color { accent }
}

// MARK: - Card Style Modifier

struct CardStyle: ViewModifier {
    func body(content: Content) -> some View {
        content
            .background(CoachiTheme.surface)
            .clipShape(RoundedRectangle(cornerRadius: 16, style: .continuous))
            .overlay(
                RoundedRectangle(cornerRadius: 16, style: .continuous)
                    .stroke(Color.white.opacity(0.06), lineWidth: 1)
            )
    }
}

// MARK: - Glass Card Modifier

struct GlassCard: ViewModifier {
    func body(content: Content) -> some View {
        content
            .background(.ultraThinMaterial.opacity(0.3))
            .background(CoachiTheme.surface.opacity(0.6))
            .clipShape(RoundedRectangle(cornerRadius: 20, style: .continuous))
            .overlay(
                RoundedRectangle(cornerRadius: 20, style: .continuous)
                    .stroke(
                        LinearGradient(
                            colors: [Color.white.opacity(0.15), Color.white.opacity(0.03)],
                            startPoint: .topLeading,
                            endPoint: .bottomTrailing
                        ),
                        lineWidth: 1
                    )
            )
            .shadow(color: Color.black.opacity(0.3), radius: 20, y: 10)
    }
}

// MARK: - Glow Modifier

struct GlowModifier: ViewModifier {
    let color: Color
    let radius: CGFloat
    func body(content: Content) -> some View {
        content
            .shadow(color: color.opacity(0.4), radius: radius, y: 0)
            .shadow(color: color.opacity(0.2), radius: radius * 1.5, y: 0)
    }
}

// MARK: - View Extensions

extension View {
    func cardStyle() -> some View { modifier(CardStyle()) }
    func glassCard() -> some View { modifier(GlassCard()) }
    func glow(color: Color, radius: CGFloat = 15) -> some View { modifier(GlowModifier(color: color, radius: radius)) }
}
