//
//  HomeView.swift
//  TreningsCoach
//
//  Coachi home screen with greeting, monitor CTA, coach score, and workout launch
//

import SwiftUI

struct HomeView: View {
    @EnvironmentObject var appViewModel: AppViewModel
    @EnvironmentObject var workoutViewModel: WorkoutViewModel
    @StateObject private var viewModel = HomeViewModel()
    @State private var appeared = false
    @State private var showManageMonitors = false
    let onStartWorkout: () -> Void

    private var homeHorizontalPadding: CGFloat { 16 }

    var body: some View {
        NavigationStack {
            GeometryReader { geo in
                ScrollView(.vertical, showsIndicators: false) {
                    VStack(spacing: 0) {
                        VStack(spacing: 0) {
                            headerSection
                                .padding(.top, 16)
                                .opacity(appeared ? 1 : 0)

                            monitorButton
                                .padding(.top, 18)
                                .opacity(appeared ? 1 : 0)

                            PulseButtonView(
                                title: L10n.startWorkout,
                                icon: "play.fill",
                                size: 140,
                                useNanoBananaLogo: true,
                                layout: .card
                            ) {
                                onStartWorkout()
                            }
                            .frame(maxWidth: .infinity)
                            .padding(.top, 24)
                            .opacity(appeared ? 1 : 0)

                            CoachScoreSection(
                                scoreHistory: workoutViewModel.coachScoreHistory,
                                coachScore: workoutViewModel.homeCoachScore,
                                xpProgress: appViewModel.coachiXPProgressFraction,
                                xpLine: appViewModel.coachiXPLine
                            )
                            .frame(maxWidth: .infinity)
                            .padding(.top, 22)
                            .opacity(appeared ? 1 : 0)
                            .offset(y: appeared ? 0 : 10)
                        }
                        .frame(maxWidth: 560)
                        .frame(maxWidth: .infinity)
                    }
                    .padding(.horizontal, homeHorizontalPadding)
                    .padding(.bottom, max(geo.safeAreaInsets.bottom + 84, 96))
                    .frame(maxWidth: .infinity)
                }
            }
            .background(CoachiTheme.backgroundGradient.ignoresSafeArea())
            .navigationDestination(isPresented: $showManageMonitors) {
                HeartRateMonitorsView()
            }
        }
        .task {
            await viewModel.loadData()
            withAnimation(.easeOut(duration: 0.6).delay(0.1)) { appeared = true }
        }
    }

    private var headerSection: some View {
        HStack(alignment: .top) {
            VStack(alignment: .leading, spacing: 4) {
                Text(viewModel.greeting + ",")
                    .font(.system(size: 16, weight: .medium))
                    .foregroundColor(CoachiTheme.textSecondary)

                HStack(alignment: .firstTextBaseline, spacing: 10) {
                    Text(appViewModel.userProfile.name)
                        .font(.system(size: 28, weight: .bold))
                        .foregroundColor(CoachiTheme.textPrimary)
                        .lineLimit(1)
                        .minimumScaleFactor(0.82)

                    homeLevelBadge
                }
            }
            Spacer()
        }
        .frame(maxWidth: .infinity, alignment: .leading)
    }

    private var homeLevelBadge: some View {
        Text(L10n.current == .no ? "Nivå \(appViewModel.coachiProgressState.level)" : "Level \(appViewModel.coachiProgressState.level)")
            .font(.system(size: 16, weight: .heavy))
            .foregroundColor(CoachiTheme.success)
            .padding(.horizontal, 11)
            .padding(.vertical, 5)
            .background(
                Capsule(style: .continuous)
                    .fill(CoachiTheme.success.opacity(0.12))
            )
            .overlay(
                Capsule(style: .continuous)
                    .stroke(CoachiTheme.success.opacity(0.45), lineWidth: 1)
            )
    }

    private var monitorButton: some View {
        Button {
            showManageMonitors = true
        } label: {
            HStack(spacing: 12) {
                Image(systemName: "applewatch")
                    .font(.system(size: 18, weight: .semibold))
                    .foregroundColor(CoachiTheme.primary)

                VStack(alignment: .leading, spacing: 4) {
                    Text(
                        workoutViewModel.hrSource == .wc || workoutViewModel.hrSource == .ble
                            ? (L10n.current == .no ? "Live puls klar" : "Live heart-rate ready")
                            : L10n.connectHeartRateMonitorTitle
                    )
                    .font(.system(size: 15, weight: .semibold))
                    .foregroundColor(CoachiTheme.textPrimary)

                    if workoutViewModel.hrSource == .wc || workoutViewModel.hrSource == .ble,
                       let hr = workoutViewModel.heartRate {
                        Text("HR \(hr)")
                            .font(.system(size: 12, weight: .bold, design: .monospaced))
                            .foregroundColor(CoachiTheme.textSecondary)
                    } else {
                        Text(L10n.connectHeartRateMonitorBody)
                            .font(.system(size: 12, weight: .medium))
                            .foregroundColor(CoachiTheme.textSecondary)
                    }
                }

                Spacer()

                Image(systemName: "chevron.right")
                    .font(.system(size: 12, weight: .bold))
                    .foregroundColor(CoachiTheme.textTertiary)
            }
            .padding(14)
            .cardStyle()
        }
        .buttonStyle(.plain)
        .frame(maxWidth: .infinity)
    }
}

private struct CoachScoreSection: View {
    let scoreHistory: [CoachScoreRecord]
    let coachScore: Int
    let xpProgress: Double
    let xpLine: String

    private var streakDays: Int {
        scoreHistory.currentWorkoutStreak()
    }

    var body: some View {
        VStack(spacing: 12) {
            Text(L10n.coachScore)
                .font(.system(size: 24, weight: .bold))
                .foregroundColor(CoachiTheme.textPrimary)
                .frame(maxWidth: .infinity, alignment: .leading)

            VStack(spacing: 16) {
                HStack(spacing: 10) {
                    progressPill(
                        icon: "flame.fill",
                        title: L10n.streak,
                        value: "\(streakDays)"
                    )
                    progressPill(
                        icon: "sparkles",
                        title: "XP",
                        value: xpLine
                    )
                }
                .frame(maxWidth: .infinity, alignment: .leading)

                HStack(spacing: 8) {
                    ForEach(weekSlots) { slot in
                        VStack(spacing: 4) {
                            Text(slot.label)
                                .font(.system(size: 12, weight: .bold))
                                .foregroundColor(slot.isToday ? CoachiTheme.textPrimary : CoachiTheme.textSecondary)

                            Text(slot.dateNumber)
                                .font(.system(size: 11, weight: .semibold))
                                .foregroundColor(slot.isToday ? CoachiTheme.textPrimary : CoachiTheme.textSecondary)

                            ZStack {
                                Circle()
                                    .stroke(
                                        slot.isToday ? CoachiTheme.primary : CoachiTheme.borderSubtle,
                                        lineWidth: 2
                                    )
                                    .frame(width: 44, height: 44)
                                    .background(slot.isToday ? CoachiTheme.primary : Color.clear)
                                    .clipShape(Circle())

                                Text("\(slot.value)")
                                    .font(.system(size: 22, weight: .bold))
                                    .foregroundColor(slot.isToday ? .white : CoachiTheme.textPrimary)
                            }
                        }
                        .frame(maxWidth: .infinity)
                    }
                }

                GamifiedCoachScoreRingView(
                    score: coachScore,
                    label: L10n.current == .no ? "Score" : "Score",
                    size: 216,
                    lineWidth: 12,
                    fullSweepBeforeSettling: true,
                    xpProgress: xpProgress,
                    showsOuterXPRing: true
                )
                .padding(.vertical, 4)
            }
            .padding(.horizontal, 14)
            .padding(.top, 14)
            .padding(.bottom, 18)
            .background(CoachiTheme.surface)
            .clipShape(RoundedRectangle(cornerRadius: 22, style: .continuous))
        }
        .frame(maxWidth: .infinity)
    }

    private func progressPill(icon: String, title: String, value: String) -> some View {
        HStack(spacing: 8) {
            Image(systemName: icon)
                .font(.system(size: 12, weight: .bold))
                .foregroundColor(CoachiTheme.primary)

            VStack(alignment: .leading, spacing: 2) {
                Text(title)
                    .font(.system(size: 11, weight: .bold))
                    .foregroundColor(CoachiTheme.textSecondary)
                Text(value)
                    .font(.system(size: 13, weight: .semibold))
                    .foregroundColor(CoachiTheme.textPrimary)
                    .lineLimit(1)
                    .minimumScaleFactor(0.8)
            }
        }
        .padding(.horizontal, 12)
        .padding(.vertical, 10)
        .background(CoachiTheme.surfaceElevated)
        .clipShape(Capsule(style: .continuous))
    }

    private var weekSlots: [CoachScoreWeekSlot] {
        let calendar = Calendar.autoupdatingCurrent
        let today = calendar.startOfDay(for: Date())
        var latestScoreByDay: [Date: Int] = [:]

        for record in scoreHistory.sorted(by: { $0.date > $1.date }) {
            let day = calendar.startOfDay(for: record.date)
            if latestScoreByDay[day] == nil {
                latestScoreByDay[day] = record.score
            }
        }

        return (0..<7).map { index in
            let offset = 6 - index
            let date = calendar.date(byAdding: .day, value: -offset, to: today) ?? today
            let isToday = offset == 0
            let label = isToday ? L10n.today : weekDayLabel(for: date)
            let dateNumber = String(calendar.component(.day, from: date))
            return CoachScoreWeekSlot(label: label, dateNumber: dateNumber, value: latestScoreByDay[date] ?? 0, isToday: isToday)
        }
    }

    private func weekDayLabel(for date: Date) -> String {
        let formatter = DateFormatter()
        formatter.locale = Locale.autoupdatingCurrent
        formatter.dateFormat = "EEEEE"
        return formatter.string(from: date).uppercased()
    }
}

private struct CoachScoreWeekSlot: Identifiable {
    let id = UUID()
    let label: String
    let dateNumber: String
    let value: Int
    let isToday: Bool
}
