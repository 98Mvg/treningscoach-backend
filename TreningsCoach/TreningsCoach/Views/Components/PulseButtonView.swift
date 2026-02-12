//
//  PulseButtonView.swift
//  TreningsCoach
//
//  Pulsing CTA button for workout start
//

import SwiftUI

struct PulseButtonView: View {
    let title: String
    let icon: String
    var size: CGFloat = 160
    let action: () -> Void

    @State private var isPulsing = false
    @State private var isPressed = false

    var body: some View {
        Button(action: action) {
            ZStack {
                Circle().fill(CoachiTheme.primary.opacity(0.06)).frame(width: size * 1.5, height: size * 1.5).scaleEffect(isPulsing ? 1.08 : 1.0)
                Circle().fill(CoachiTheme.primary.opacity(0.12)).frame(width: size * 1.25, height: size * 1.25).scaleEffect(isPulsing ? 1.05 : 0.98)
                Circle().fill(CoachiTheme.primaryGradient).frame(width: size, height: size).shadow(color: CoachiTheme.primary.opacity(0.4), radius: 20, y: 5)
                VStack(spacing: 8) {
                    Image(systemName: icon).font(.system(size: size * 0.2, weight: .semibold))
                    Text(title).font(.system(size: size * 0.1, weight: .bold))
                }
                .foregroundColor(.white)
            }
            .scaleEffect(isPressed ? 0.92 : 1.0)
        }
        .buttonStyle(.plain)
        .simultaneousGesture(
            DragGesture(minimumDistance: 0)
                .onChanged { _ in withAnimation(.spring(response: 0.2)) { isPressed = true } }
                .onEnded { _ in withAnimation(.spring(response: 0.3, dampingFraction: 0.6)) { isPressed = false } }
        )
        .onAppear {
            withAnimation(.easeInOut(duration: AppConfig.Anim.orbIdlePulse).repeatForever(autoreverses: true)) { isPulsing = true }
        }
    }
}
