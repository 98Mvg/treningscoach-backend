//
//  PulseButtonView.swift
//  TreningsCoach
//
//  Pulsing CTA button for workout start
//

import SwiftUI

enum PulseButtonLayout {
    case orb
    case card
}

struct PulseButtonView: View {
    let title: String
    let icon: String
    var size: CGFloat = 160
    var useNanoBananaLogo: Bool = false
    var layout: PulseButtonLayout = .orb
    let action: () -> Void

    @State private var isPulsing = false
    @State private var isPressed = false

    var body: some View {
        Group {
            switch layout {
            case .orb:
                orbButton
            case .card:
                cardButton
            }
        }
        .onAppear {
            withAnimation(.easeInOut(duration: AppConfig.Anim.orbIdlePulse).repeatForever(autoreverses: true)) { isPulsing = true }
        }
    }

    private var orbButton: some View {
        Button(action: action) {
            ZStack {
                Circle().fill(CoachiTheme.primary.opacity(0.06)).frame(width: size * 1.5, height: size * 1.5).scaleEffect(isPulsing ? 1.08 : 1.0)
                Circle().fill(CoachiTheme.primary.opacity(0.12)).frame(width: size * 1.25, height: size * 1.25).scaleEffect(isPulsing ? 1.05 : 0.98)
                Circle().fill(CoachiTheme.primaryGradient).frame(width: size, height: size).shadow(color: CoachiTheme.primary.opacity(0.4), radius: 20, y: 5)
                VStack(spacing: 8) {
                    logo(size: size * 0.36)
                    Text(title).font(.system(size: size * 0.1, weight: .bold))
                }
                .foregroundColor(.white)
            }
            .scaleEffect(isPressed ? 0.92 : 1.0)
        }
        .buttonStyle(.plain)
        .simultaneousGesture(pressGesture)
    }

    private var cardButton: some View {
        Button(action: action) {
            HStack(spacing: 10) {
                Text(title)
                    .font(.system(size: 24, weight: .bold))
                    .foregroundColor(.white)

                Spacer(minLength: 0)

                Image(systemName: "chevron.right")
                    .font(.system(size: 15, weight: .bold))
                    .foregroundColor(.white.opacity(0.92))
            }
            .padding(.horizontal, 22)
            .frame(height: 76)
            .background(
                RoundedRectangle(cornerRadius: 26, style: .continuous)
                    .fill(CoachiTheme.primaryGradient)
            )
            .overlay(
                RoundedRectangle(cornerRadius: 26, style: .continuous)
                    .stroke(Color.white.opacity(0.18), lineWidth: 1)
            )
            .shadow(color: CoachiTheme.primary.opacity(isPulsing ? 0.45 : 0.30), radius: isPulsing ? 22 : 14, y: 6)
            .scaleEffect(isPressed ? 0.97 : 1.0)
        }
        .buttonStyle(.plain)
        .simultaneousGesture(pressGesture)
    }

    private var pressGesture: some Gesture {
        DragGesture(minimumDistance: 0)
            .onChanged { _ in withAnimation(.spring(response: 0.2)) { isPressed = true } }
            .onEnded { _ in withAnimation(.spring(response: 0.3, dampingFraction: 0.6)) { isPressed = false } }
    }

    @ViewBuilder
    private func logo(size: CGFloat) -> some View {
        if useNanoBananaLogo {
            StartWorkoutNanoBananaLogo(size: size)
        } else {
            Image(systemName: icon)
                .font(.system(size: size, weight: .semibold))
        }
    }
}

private struct StartWorkoutNanoBananaLogo: View {
    let size: CGFloat

    var body: some View {
        ZStack {
            Circle()
                .stroke(Color.white.opacity(0.28), lineWidth: size * 0.15)

            Circle()
                .trim(from: 0.08, to: 0.68)
                .stroke(
                    LinearGradient(
                        colors: [Color(red: 0.18, green: 0.93, blue: 0.86), Color(red: 0.15, green: 0.75, blue: 0.96)],
                        startPoint: .topLeading,
                        endPoint: .bottomTrailing
                    ),
                    style: StrokeStyle(lineWidth: size * 0.15, lineCap: .round)
                )
                .rotationEffect(.degrees(-90))
                .shadow(color: Color(red: 0.18, green: 0.93, blue: 0.86).opacity(0.55), radius: 8)

            Circle()
                .trim(from: 0.68, to: 0.92)
                .stroke(
                    LinearGradient(
                        colors: [Color(red: 1.0, green: 0.6, blue: 0.26), Color(red: 1.0, green: 0.44, blue: 0.34)],
                        startPoint: .topLeading,
                        endPoint: .bottomTrailing
                    ),
                    style: StrokeStyle(lineWidth: size * 0.15, lineCap: .round)
                )
                .rotationEffect(.degrees(-90))
                .shadow(color: Color(red: 1.0, green: 0.55, blue: 0.28).opacity(0.45), radius: 6)

        }
        .frame(width: size, height: size)
    }
}
