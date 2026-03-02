import SwiftUI

struct GlassCardView<Content: View>: View {
    @ViewBuilder let content: Content

    var body: some View {
        content
            .padding(20)
            .glassCard()
    }
}

#Preview {
    ZStack {
        CoachiTheme.bg.ignoresSafeArea()
        GlassCardView {
            VStack(spacing: 12) {
                Text("Workout Complete")
                    .font(.title2.bold())
                    .foregroundColor(CoachiTheme.textPrimary)
                Text("32:15")
                    .font(.system(size: 48, weight: .light, design: .monospaced))
                    .foregroundColor(CoachiTheme.primary)
            }
        }
        .padding()
    }
}
