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

enum CoachiAccentPreset: String, CaseIterable, Identifiable {
    case sunset
    case mint
    case ocean
    case violet

    static let storageKey = "theme_accent_preset"
    static let defaultPreset: CoachiAccentPreset = .sunset

    var id: String { rawValue }

    var primaryHex: String {
        switch self {
        case .sunset: return "FF6B35"
        case .mint: return "22C55E"
        case .ocean: return "3B82F6"
        case .violet: return "8B5CF6"
        }
    }

    var primaryLightHex: String {
        switch self {
        case .sunset: return "FF8F5E"
        case .mint: return "4ADE80"
        case .ocean: return "60A5FA"
        case .violet: return "A78BFA"
        }
    }

    var gradientTailHex: String {
        switch self {
        case .sunset: return "FF4757"
        case .mint: return "3ED4D5"
        case .ocean: return "22D3EE"
        case .violet: return "EC4899"
        }
    }
}

// MARK: - Coachi Theme

enum CoachiTheme {
    private static func adaptive(light: String, dark: String) -> Color {
        Color(uiColor: UIColor { traits in
            UIColor(hex: traits.userInterfaceStyle == .dark ? dark : light)
        })
    }

    private static var accentPreset: CoachiAccentPreset {
        let stored = UserDefaults.standard.string(forKey: CoachiAccentPreset.storageKey)
        return CoachiAccentPreset(rawValue: stored ?? "") ?? CoachiAccentPreset.defaultPreset
    }

    // Backgrounds
    static let bgDeep           = adaptive(light: "DEE7FF", dark: "0A0A0F")
    static let bg               = adaptive(light: "EEF3FF", dark: "111118")
    static let surface          = adaptive(light: "FFFFFF", dark: "1A1A24")
    static let surfaceElevated  = adaptive(light: "F3F6FF", dark: "222230")

    // Primary
    static var primary: Color { Color(hex: accentPreset.primaryHex) }
    static var primaryLight: Color { Color(hex: accentPreset.primaryLightHex) }

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
    static var primaryGradient: LinearGradient {
        LinearGradient(colors: [primary, Color(hex: accentPreset.gradientTailHex)], startPoint: .topLeading, endPoint: .bottomTrailing)
    }
    static let backgroundGradient = LinearGradient(colors: [bg, bgDeep], startPoint: .top, endPoint: .bottom)
    static let surfaceGradient    = LinearGradient(colors: [surface, Color(hex: "151520")], startPoint: .top, endPoint: .bottom)
    static var activeGradient: LinearGradient {
        LinearGradient(colors: [primary, accent], startPoint: .topLeading, endPoint: .bottomTrailing)
    }
    static let coolGradient       = LinearGradient(colors: [secondary, success], startPoint: .topLeading, endPoint: .bottomTrailing)
    static var emberGradient: LinearGradient {
        LinearGradient(colors: [primary, primaryLight], startPoint: .top, endPoint: .bottom)
    }
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
    var fullSweepBeforeSettling: Bool = false
    var animationDuration: Double = 2.1
    var trackColor: Color = Color(hex: "DCE3F8")
    var gradientColors: [Color] = [Color(hex: "3ED4D5"), Color(hex: "2ED573")]
    var valueColor: Color = CoachiTheme.textPrimary
    var labelColor: Color = CoachiTheme.textSecondary
    var levelColor: Color? = nil
    var levelLabel: String? = nil
    var xpProgress: Double? = nil
    var showsOuterXPRing: Bool = false
    var animateXPAward: Bool = false
    var xpAnimationFrom: Double? = nil
    var xpAnimationTo: Double? = nil

    @State private var displayedScore: Int = 0
    @State private var displayedProgress: CGFloat = 0.0
    @State private var displayedXPProgress: CGFloat = 0.0
    @State private var displayedLevelLabel: String?

    private var clampedScore: Int {
        max(0, min(100, score))
    }

    private var targetProgress: CGFloat {
        CGFloat(clampedScore) / 100.0
    }

    private var clampedXPProgress: CGFloat {
        CGFloat(max(0, min(1, xpProgress ?? 0)))
    }

    private var outerLineWidth: CGFloat {
        max(6, lineWidth * 0.55)
    }

    private var outerRingSize: CGFloat {
        size + (showsOuterXPRing ? max(22, outerLineWidth * 3.8) : 0)
    }

    private var animationKey: String {
        [
            "\(clampedScore)",
            levelLabel ?? "nil",
            "\(xpProgress ?? -1)",
            "\(animateXPAward)",
            "\(xpAnimationFrom ?? -1)",
            "\(xpAnimationTo ?? -1)",
            "\(fullSweepBeforeSettling)",
        ].joined(separator: "|")
    }

    var body: some View {
        VStack(spacing: showsOuterXPRing ? max(8, size * 0.05) : 0) {
            if showsOuterXPRing, let displayedLevelLabel {
                Text(displayedLevelLabel)
                    .font(.system(size: size * 0.16, weight: .bold))
                    .foregroundColor(levelColor ?? labelColor)
                    .monospacedDigit()
            }

            ZStack {
                if showsOuterXPRing {
                    Circle()
                        .stroke(trackColor.opacity(0.32), lineWidth: outerLineWidth)
                        .frame(width: outerRingSize, height: outerRingSize)

                    Circle()
                        .trim(from: 0, to: displayedXPProgress)
                        .stroke(
                            LinearGradient(
                                colors: [Color(hex: "FDE68A"), Color(hex: "F59E0B")],
                                startPoint: .leading,
                                endPoint: .trailing
                            ),
                            style: StrokeStyle(lineWidth: outerLineWidth, lineCap: .round)
                        )
                        .frame(width: outerRingSize, height: outerRingSize)
                        .rotationEffect(.degrees(-90))
                }

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
            .frame(width: outerRingSize, height: outerRingSize)
        }
        .frame(width: outerRingSize)
        .task(id: animationKey) {
            await animateVisuals()
        }
    }

    private func animateVisuals() async {
        let finalLevelLabel = levelLabel
        let finalLevelNumber = parsedLevelNumber(from: finalLevelLabel)
        let startXP = CGFloat(max(0, min(1, xpAnimationFrom ?? xpProgress ?? 0)))

        if showsOuterXPRing {
            displayedXPProgress = animateXPAward ? startXP : clampedXPProgress
            displayedLevelLabel = initialDisplayedLevelLabel(
                finalLabel: finalLevelLabel,
                finalLevelNumber: finalLevelNumber
            )
        } else {
            displayedLevelLabel = finalLevelLabel
        }

        await animateScore()

        guard showsOuterXPRing else { return }
        await animateXP(
            finalLabel: finalLevelLabel,
            finalLevelNumber: finalLevelNumber
        )
    }

    private func animateScore() async {
        if !animateFromOne {
            displayedScore = clampedScore
            displayedProgress = targetProgress
            return
        }

        if fullSweepBeforeSettling {
            await animateFullSweepThenSettle()
            return
        }

        let startScore = clampedScore > 0 ? 1 : 0
        displayedScore = startScore
        displayedProgress = CGFloat(startScore) / 100.0

        withAnimation(.easeOut(duration: animationDuration)) {
            displayedProgress = targetProgress
        }

        let remainingSteps = clampedScore - startScore
        guard remainingSteps > 0 else { return }

        let stepNanos = UInt64((animationDuration / Double(remainingSteps)) * 1_000_000_000)
        let safeStepNanos = max(UInt64(8_000_000), stepNanos)

        for step in (startScore + 1)...clampedScore {
            try? await Task.sleep(nanoseconds: safeStepNanos)
            if Task.isCancelled { return }
            displayedScore = step
        }
    }

    private func animateFullSweepThenSettle() async {
        let sweepStart = 1
        displayedScore = sweepStart
        displayedProgress = CGFloat(sweepStart) / 100.0

        let sweepSteps = 100 - sweepStart
        let sweepStepNanos = UInt64((animationDuration / Double(max(1, sweepSteps))) * 1_000_000_000)
        let safeSweepStepNanos = max(UInt64(8_000_000), sweepStepNanos)

        for step in (sweepStart + 1)...100 {
            try? await Task.sleep(nanoseconds: safeSweepStepNanos)
            if Task.isCancelled { return }
            displayedScore = step
            displayedProgress = CGFloat(step) / 100.0
        }

        let settleTarget = clampedScore
        guard settleTarget != 100 else { return }

        let settleSteps = abs(100 - settleTarget)
        let settleDuration = max(0.45, animationDuration * 0.38)
        let settleStepNanos = UInt64((settleDuration / Double(max(1, settleSteps))) * 1_000_000_000)
        let safeSettleStepNanos = max(UInt64(8_000_000), settleStepNanos)

        if settleTarget < 100 {
            for step in stride(from: 99, through: settleTarget, by: -1) {
                try? await Task.sleep(nanoseconds: safeSettleStepNanos)
                if Task.isCancelled { return }
                displayedScore = step
                displayedProgress = CGFloat(step) / 100.0
            }
        } else {
            for step in 101...settleTarget {
                try? await Task.sleep(nanoseconds: safeSettleStepNanos)
                if Task.isCancelled { return }
                displayedScore = step
                displayedProgress = CGFloat(step) / 100.0
            }
        }
    }

    private func animateXP(finalLabel: String?, finalLevelNumber: Int) async {
        if !animateXPAward {
            displayedLevelLabel = finalLabel
            displayedXPProgress = clampedXPProgress
            return
        }

        let start = CGFloat(max(0, min(1, xpAnimationFrom ?? xpProgress ?? 0)))
        let end = CGFloat(max(0, min(1, xpAnimationTo ?? xpProgress ?? 0)))
        let wrapsLevel = start > end && finalLevelNumber > CoachiProgressState.startingLevel

        if wrapsLevel {
            withAnimation(.easeOut(duration: 0.38)) {
                displayedXPProgress = 1.0
            }
            try? await Task.sleep(nanoseconds: 420_000_000)
            if Task.isCancelled { return }
            displayedLevelLabel = finalLabel
            displayedXPProgress = 0.0
            withAnimation(.easeOut(duration: 0.46)) {
                displayedXPProgress = end
            }
            return
        }

        displayedLevelLabel = finalLabel
        withAnimation(.easeOut(duration: 0.5)) {
            displayedXPProgress = end
        }
    }

    private func initialDisplayedLevelLabel(finalLabel: String?, finalLevelNumber: Int) -> String? {
        guard animateXPAward else { return finalLabel }
        let start = max(0, min(1, xpAnimationFrom ?? xpProgress ?? 0))
        let end = max(0, min(1, xpAnimationTo ?? xpProgress ?? 0))
        guard start > end, finalLevelNumber > CoachiProgressState.startingLevel else {
            return finalLabel
        }
        return formattedLevelLabel(for: finalLevelNumber - 1, template: finalLabel)
    }

    private func parsedLevelNumber(from label: String?) -> Int {
        let digits = (label ?? "").filter(\.isNumber)
        return Int(digits) ?? CoachiProgressState.startingLevel
    }

    private func formattedLevelLabel(for level: Int, template: String?) -> String {
        let safeLevel = max(CoachiProgressState.startingLevel, level)
        let normalized = (template ?? "").lowercased()
        if normalized.contains("nivå") {
            return "Nivå \(safeLevel)"
        }
        if normalized.contains("level") {
            return "Level \(safeLevel)"
        }
        return "Lv.\(safeLevel)"
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
