import SwiftUI

struct SettingsView: View {
    @EnvironmentObject var appViewModel: AppViewModel
    @Environment(\.dismiss) private var dismiss

    var body: some View {
        ScrollView(showsIndicators: false) {
            VStack(spacing: 16) {
                // Language
                SettingsRow(icon: "globe", title: "Language", value: "English")

                // Training Level
                SettingsRow(icon: "figure.run", title: "Training Level", value: appViewModel.trainingLevel.displayName)

                // Coach Voice
                SettingsRow(icon: "speaker.wave.2.fill", title: "Coach Voice", value: "Default")

                // Divider
                Rectangle()
                    .fill(CoachiTheme.textTertiary.opacity(0.2))
                    .frame(height: 1)
                    .padding(.vertical, 8)

                // About
                SettingsRow(icon: "info.circle.fill", title: "About", value: "v\(AppConfig.appVersion)")

                Spacer()
                    .frame(height: 20)

                // Sign out
                Button {
                    appViewModel.resetOnboarding()
                    dismiss()
                } label: {
                    HStack {
                        Image(systemName: "rectangle.portrait.and.arrow.right")
                            .font(.system(size: 16))
                        Text("Sign Out")
                            .font(.system(size: 16, weight: .semibold))
                    }
                    .foregroundColor(CoachiTheme.danger)
                    .frame(maxWidth: .infinity)
                    .padding(.vertical, 16)
                    .background(CoachiTheme.danger.opacity(0.1))
                    .clipShape(RoundedRectangle(cornerRadius: 14, style: .continuous))
                }
            }
            .padding(.horizontal, 20)
            .padding(.top, 20)
        }
        .background(CoachiTheme.backgroundGradient.ignoresSafeArea())
        .navigationTitle("Settings")
        .navigationBarTitleDisplayMode(.large)
        .toolbarColorScheme(.dark, for: .navigationBar)
    }
}

struct SettingsRow: View {
    let icon: String
    let title: String
    let value: String

    var body: some View {
        HStack {
            Image(systemName: icon)
                .font(.system(size: 16))
                .foregroundColor(CoachiTheme.primary)
                .frame(width: 28)

            Text(title)
                .font(.system(size: 16, weight: .medium))
                .foregroundColor(CoachiTheme.textPrimary)

            Spacer()

            Text(value)
                .font(.system(size: 14, weight: .medium))
                .foregroundColor(CoachiTheme.textSecondary)

            Image(systemName: "chevron.right")
                .font(.system(size: 12, weight: .semibold))
                .foregroundColor(CoachiTheme.textTertiary)
        }
        .padding(16)
        .cardStyle()
    }
}

#Preview {
    NavigationStack {
        SettingsView()
            .environmentObject(AppViewModel())
    }
}
