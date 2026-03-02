import SwiftUI

struct ProfileView: View {
    @EnvironmentObject var appViewModel: AppViewModel
    @StateObject private var viewModel = ProfileViewModel()
    @State private var showSettings = false
    @State private var appeared = false

    var body: some View {
        NavigationStack {
            ScrollView(showsIndicators: false) {
                VStack(spacing: 0) {
                    // Avatar + Name
                    VStack(spacing: 12) {
                        Image(systemName: "person.circle.fill")
                            .font(.system(size: 72, weight: .light))
                            .foregroundStyle(CoachiTheme.primaryGradient)

                        Text(appViewModel.userProfile.name)
                            .font(.system(size: 24, weight: .bold))
                            .foregroundColor(CoachiTheme.textPrimary)

                        // Training level badge
                        HStack(spacing: 6) {
                            Image(systemName: appViewModel.trainingLevel.icon)
                                .font(.system(size: 12, weight: .semibold))
                            Text(appViewModel.trainingLevel.displayName)
                                .font(.system(size: 13, weight: .semibold))
                        }
                        .foregroundColor(CoachiTheme.primary)
                        .padding(.horizontal, 14)
                        .padding(.vertical, 6)
                        .background(
                            Capsule().fill(CoachiTheme.primary.opacity(0.15))
                        )
                    }
                    .padding(.top, 24)
                    .opacity(appeared ? 1 : 0)

                    // Stats
                    HStack(spacing: 12) {
                        StatCardView(icon: "flame.fill", value: "\(viewModel.stats.totalWorkouts)", label: "Workouts")
                        StatCardView(icon: "clock.fill", value: "\(viewModel.stats.totalMinutes)", label: "Minutes", color: CoachiTheme.secondary)
                        StatCardView(icon: "bolt.fill", value: "\(viewModel.stats.currentStreak)", label: "Streak", color: CoachiTheme.accent)
                    }
                    .padding(.horizontal, 20)
                    .padding(.top, 28)
                    .opacity(appeared ? 1 : 0)
                    .offset(y: appeared ? 0 : 15)

                    // Settings button
                    Button {
                        showSettings = true
                    } label: {
                        HStack {
                            Image(systemName: "gearshape.fill")
                                .font(.system(size: 16))
                                .foregroundColor(CoachiTheme.textSecondary)
                            Text("Settings")
                                .font(.system(size: 16, weight: .semibold))
                                .foregroundColor(CoachiTheme.textPrimary)
                            Spacer()
                            Image(systemName: "chevron.right")
                                .font(.system(size: 13, weight: .semibold))
                                .foregroundColor(CoachiTheme.textTertiary)
                        }
                        .padding(16)
                        .cardStyle()
                    }
                    .padding(.horizontal, 20)
                    .padding(.top, 28)
                    .opacity(appeared ? 1 : 0)

                    Spacer()
                        .frame(height: 100)
                }
            }
            .background(CoachiTheme.backgroundGradient.ignoresSafeArea())
            .navigationDestination(isPresented: $showSettings) {
                SettingsView()
                    .environmentObject(appViewModel)
            }
        }
        .onAppear {
            withAnimation(.easeOut(duration: 0.5).delay(0.1)) {
                appeared = true
            }
        }
    }
}

#Preview {
    ProfileView()
        .environmentObject(AppViewModel())
}
