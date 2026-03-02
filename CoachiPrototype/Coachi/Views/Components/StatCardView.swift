import SwiftUI

struct StatCardView: View {
    let icon: String
    let value: String
    let label: String
    var color: Color = CoachiTheme.primary

    var body: some View {
        VStack(spacing: 8) {
            Image(systemName: icon)
                .font(.system(size: 20))
                .foregroundColor(color)

            Text(value)
                .font(.system(size: 24, weight: .bold, design: .rounded))
                .foregroundColor(CoachiTheme.textPrimary)

            Text(label)
                .font(.system(size: 12, weight: .medium))
                .foregroundColor(CoachiTheme.textSecondary)
        }
        .frame(maxWidth: .infinity)
        .padding(.vertical, 16)
        .cardStyle()
    }
}

#Preview {
    ZStack {
        CoachiTheme.bg.ignoresSafeArea()
        HStack(spacing: 12) {
            StatCardView(icon: "flame.fill", value: "12", label: "Workouts")
            StatCardView(icon: "clock.fill", value: "340", label: "Minutes", color: CoachiTheme.secondary)
            StatCardView(icon: "bolt.fill", value: "5", label: "Streak", color: CoachiTheme.accent)
        }
        .padding()
    }
}
