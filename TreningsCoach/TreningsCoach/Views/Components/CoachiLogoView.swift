//
//  CoachiLogoView.swift
//  TreningsCoach
//
//  SF Symbol-based logo with optional animation
//

import SwiftUI

struct CoachiLogoView: View {
    let size: CGFloat
    var animated: Bool = false

    @State private var ringProgress: CGFloat = 0
    @State private var figureOpacity: Double = 0
    @State private var waveformScale: CGFloat = 0
    @State private var rotationAngle: Double = 0

    private var safeSize: CGFloat {
        guard size.isFinite, size > 0 else { return 120 }
        return size
    }

    private var safeRingProgress: CGFloat {
        let raw = animated ? ringProgress : 1
        guard raw.isFinite else { return 0 }
        return max(0, min(1, raw))
    }

    private var safeRotationAngle: Double {
        guard rotationAngle.isFinite else { return 0 }
        return rotationAngle
    }

    private var safeWaveformScale: CGFloat {
        let raw = animated ? waveformScale : 1
        guard raw.isFinite else { return 1 }
        return max(0.01, raw)
    }

    private var safeFigureOpacity: Double {
        let raw = animated ? figureOpacity : 1
        guard raw.isFinite else { return 1 }
        return max(0, min(1, raw))
    }

    var body: some View {
        ZStack {
            Circle()
                .trim(from: 0, to: safeRingProgress)
                .stroke(CoachiTheme.primaryGradient, style: StrokeStyle(lineWidth: safeSize * 0.05, lineCap: .round))
                .frame(width: safeSize, height: safeSize)
                .rotationEffect(.degrees(-90))
                .rotationEffect(.degrees(animated ? 0 : safeRotationAngle))

            Image(systemName: "figure.run")
                .font(.system(size: safeSize * 0.38, weight: .medium))
                .foregroundStyle(CoachiTheme.primaryGradient)
                .opacity(safeFigureOpacity)

            Image(systemName: "waveform")
                .font(.system(size: safeSize * 0.14, weight: .bold))
                .foregroundStyle(CoachiTheme.secondary)
                .offset(x: safeSize * 0.34, y: -safeSize * 0.34)
                .scaleEffect(safeWaveformScale)
        }
        .onAppear {
            guard animated else { return }
            withAnimation(.easeOut(duration: 0.8)) { ringProgress = 1 }
            withAnimation(.easeOut(duration: 0.5).delay(0.4)) { figureOpacity = 1 }
            withAnimation(.spring(response: 0.5, dampingFraction: 0.6).delay(0.7)) { waveformScale = 1 }
        }
    }
}
