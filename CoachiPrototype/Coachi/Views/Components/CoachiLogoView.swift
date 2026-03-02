import SwiftUI

struct CoachiLogoView: View {
    let size: CGFloat
    var animated: Bool = false

    @State private var ringProgress: CGFloat = 0
    @State private var figureOpacity: Double = 0
    @State private var waveformScale: CGFloat = 0
    @State private var rotationAngle: Double = 0

    var body: some View {
        ZStack {
            // Outer ring
            Circle()
                .trim(from: 0, to: animated ? ringProgress : 1)
                .stroke(
                    CoachiTheme.primaryGradient,
                    style: StrokeStyle(lineWidth: size * 0.05, lineCap: .round)
                )
                .frame(width: size, height: size)
                .rotationEffect(.degrees(-90))
                .rotationEffect(.degrees(animated ? 0 : rotationAngle))

            // Runner figure
            Image(systemName: "figure.run")
                .font(.system(size: size * 0.38, weight: .medium))
                .foregroundStyle(CoachiTheme.primaryGradient)
                .opacity(animated ? figureOpacity : 1)

            // Waveform badge
            Image(systemName: "waveform")
                .font(.system(size: size * 0.14, weight: .bold))
                .foregroundStyle(CoachiTheme.secondary)
                .offset(x: size * 0.34, y: -size * 0.34)
                .scaleEffect(animated ? waveformScale : 1)
        }
        .onAppear {
            guard animated else { return }
            withAnimation(.easeOut(duration: 0.8)) {
                ringProgress = 1
            }
            withAnimation(.easeOut(duration: 0.5).delay(0.4)) {
                figureOpacity = 1
            }
            withAnimation(.spring(response: 0.5, dampingFraction: 0.6).delay(0.7)) {
                waveformScale = 1
            }
        }
    }
}

#Preview {
    ZStack {
        CoachiTheme.bg.ignoresSafeArea()
        VStack(spacing: 40) {
            CoachiLogoView(size: 120, animated: true)
            CoachiLogoView(size: 60)
            CoachiLogoView(size: 32)
        }
    }
}
