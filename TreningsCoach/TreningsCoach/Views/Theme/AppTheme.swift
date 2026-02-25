//
//  AppTheme.swift
//  TreningsCoach
//
//  "Midnight Ember" design system — Coachi theme
//  All colors, gradients, and shared view modifiers live here
//

import SwiftUI
import UIKit

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

extension UIColor {
    convenience init(hex: String) {
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
            red: CGFloat(r) / 255,
            green: CGFloat(g) / 255,
            blue: CGFloat(b) / 255,
            alpha: CGFloat(a) / 255
        )
    }
}

// MARK: - Coachi Theme

enum CoachiTheme {
    private static func adaptive(light: String, dark: String) -> Color {
        Color(uiColor: UIColor { traits in
            UIColor(hex: traits.userInterfaceStyle == .dark ? dark : light)
        })
    }

    // Backgrounds
    static let bgDeep           = adaptive(light: "DEE7FF", dark: "0A0A0F")
    static let bg               = adaptive(light: "EEF3FF", dark: "111118")
    static let surface          = adaptive(light: "FFFFFF", dark: "1A1A24")
    static let surfaceElevated  = adaptive(light: "F3F6FF", dark: "222230")

    // Primary
    static let primary          = Color(hex: "FF6B35")
    static let primaryLight     = Color(hex: "FF8F5E")

    // Secondary
    static let secondary        = Color(hex: "4ECDC4")

    // Accent
    static let accent           = Color(hex: "FFD93D")

    // Text
    static let textPrimary      = adaptive(light: "1F2850", dark: "F5F5F7")
    static let textSecondary    = adaptive(light: "5E678E", dark: "8E8E9A")
    static let textTertiary     = adaptive(light: "8B96BE", dark: "55556A")

    // Warmup Dial
    static let dialPurple       = Color(hex: "7B2FBE")
    static let dialMagenta      = Color(hex: "D946EF")

    // Semantic
    static let danger           = Color(hex: "FF4757")
    static let success          = Color(hex: "2ED573")
    static let borderSubtle     = adaptive(light: "D3DCF7", dark: "3A3A4E")

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

// MARK: - Shared Coach Score Ring

struct GamifiedCoachScoreRingView: View {
    let score: Int
    var label: String = "Score"
    var size: CGFloat = 180
    var lineWidth: CGFloat = 14
    var animateFromOne: Bool = true
    var animationDuration: Double = 2.1
    var trackColor: Color = Color(hex: "DCE3F8")
    var gradientColors: [Color] = [Color(hex: "3ED4D5"), Color(hex: "2ED573")]
    var valueColor: Color = CoachiTheme.textPrimary
    var labelColor: Color = CoachiTheme.textSecondary

    @State private var displayedScore: Int = 0
    @State private var displayedProgress: CGFloat = 0.0

    private var clampedScore: Int {
        max(0, min(100, score))
    }

    private var targetProgress: CGFloat {
        CGFloat(clampedScore) / 100.0
    }

    var body: some View {
        ZStack {
            Circle()
                .stroke(trackColor, lineWidth: lineWidth)

            Circle()
                .trim(from: 0, to: displayedProgress)
                .stroke(
                    LinearGradient(
                        colors: gradientColors,
                        startPoint: .leading,
                        endPoint: .trailing
                    ),
                    style: StrokeStyle(lineWidth: lineWidth, lineCap: .round)
                )
                .rotationEffect(.degrees(-90))

            VStack(spacing: 2) {
                Text("\(displayedScore)")
                    .font(.system(size: size * 0.30, weight: .bold))
                    .foregroundColor(valueColor)
                    .monospacedDigit()

                Text(label)
                    .font(.system(size: size * 0.14, weight: .semibold))
                    .foregroundColor(labelColor)
            }
        }
        .frame(width: size, height: size)
        .task(id: clampedScore) {
            await animateScore()
        }
    }

    private func animateScore() async {
        if !animateFromOne {
            displayedScore = clampedScore
            displayedProgress = targetProgress
            return
        }

        displayedScore = 0
        displayedProgress = 0.0

        withAnimation(.easeOut(duration: animationDuration)) {
            displayedProgress = targetProgress
        }

        let steps = clampedScore
        guard steps > 0 else { return }

        let stepNanos = UInt64((animationDuration / Double(steps)) * 1_000_000_000)
        let safeStepNanos = max(UInt64(8_000_000), stepNanos)

        for step in 1...steps {
            try? await Task.sleep(nanoseconds: safeStepNanos)
            if Task.isCancelled { return }
            displayedScore = min(clampedScore, step)
        }
    }
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
