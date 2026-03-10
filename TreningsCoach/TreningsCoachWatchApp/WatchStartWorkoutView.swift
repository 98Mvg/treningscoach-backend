import SwiftUI

struct WatchStartWorkoutView: View {
    @ObservedObject var wcManager: WatchWCManager
    @ObservedObject var workoutManager: WatchWorkoutManager

    private var isWaitingForPhoneRequestDetails: Bool {
        let requestId = wcManager.pendingRequestId?.trimmingCharacters(in: .whitespacesAndNewlines) ?? ""
        return requestId.isEmpty
    }

    var body: some View {
        Group {
            if workoutManager.isRunning {
                TimelineView(.periodic(from: .now, by: 1)) { context in
                    runningDashboard(at: context.date)
                }
            } else {
                startPrompt
            }
        }
        .padding(.horizontal, 12)
        .padding(.vertical, 10)
    }

    private var startPrompt: some View {
        VStack(spacing: 12) {
            Text(isWaitingForPhoneRequestDetails ? "Syncing with iPhone..." : "Start workout?")
                .font(.headline)

            Text("Requested: \(wcManager.pendingWorkoutType ?? WCKeys.WorkoutType.easyRun)")
                .font(.footnote)
                .foregroundStyle(.secondary)

            Text("\(workoutManager.dashboardBPMText) bpm")
                .font(.title2.weight(.semibold))
                .monospacedDigit()

            Button("Start") {
                Task {
                    let requestTs = wcManager.pendingRequestTimestamp ?? Date().timeIntervalSince1970
                    let requestID = wcManager.pendingRequestId ?? UUID().uuidString
                    let requestedType = wcManager.pendingWorkoutType ?? WCKeys.WorkoutType.easyRun
                    await workoutManager.startWorkout(
                        workoutType: requestedType,
                        requestTimestamp: requestTs,
                        requestID: requestID,
                        sessionPlan: wcManager.pendingSessionPlan
                    )
                }
            }
            .buttonStyle(.borderedProminent)
            .disabled(isWaitingForPhoneRequestDetails)
        }
        .frame(maxWidth: .infinity, maxHeight: .infinity, alignment: .center)
    }

    private func runningDashboard(at date: Date) -> some View {
        VStack(spacing: 10) {
            VStack(spacing: 6) {
                Text("BPM")
                    .font(.system(size: 13, weight: .semibold, design: .rounded))
                    .foregroundStyle(Color.white.opacity(0.72))

                Text(workoutManager.dashboardBPMText)
                    .font(.system(size: 40, weight: .bold, design: .rounded))
                    .monospacedDigit()
                    .foregroundStyle(
                        LinearGradient(
                            colors: [Color(red: 1.0, green: 0.56, blue: 0.43), Color(red: 1.0, green: 0.36, blue: 0.38)],
                            startPoint: .top,
                            endPoint: .bottom
                        )
                    )

                Image(systemName: "heart.fill")
                    .font(.system(size: 14, weight: .bold))
                    .foregroundStyle(Color(red: 1.0, green: 0.36, blue: 0.38))

                Text("Live Heart Rate")
                    .font(.system(size: 12, weight: .semibold, design: .rounded))
                    .foregroundStyle(Color(red: 0.31, green: 0.89, blue: 0.83))
            }

            Divider()
                .overlay(Color.white.opacity(0.12))

            VStack(spacing: 4) {
                Text(workoutManager.dashboardTimeLabel(at: date))
                    .font(.system(size: 11, weight: .medium, design: .rounded))
                    .foregroundStyle(Color.white.opacity(0.68))

                Text(workoutManager.dashboardTimeValue(at: date))
                    .font(.system(size: 20, weight: .semibold, design: .monospaced))
                    .foregroundStyle(Color.white.opacity(0.94))
                    .monospacedDigit()
            }

            Button("Stop") {
                workoutManager.stopWorkout()
            }
            .buttonStyle(.borderedProminent)
            .tint(Color(red: 0.98, green: 0.30, blue: 0.38))
            .padding(.top, 2)
        }
        .padding(.horizontal, 14)
        .padding(.vertical, 16)
        .frame(maxWidth: .infinity, maxHeight: .infinity, alignment: .center)
        .background(
            RoundedRectangle(cornerRadius: 24, style: .continuous)
                .fill(
                    LinearGradient(
                        colors: [Color.black.opacity(0.88), Color(red: 0.08, green: 0.08, blue: 0.14).opacity(0.96)],
                        startPoint: .topLeading,
                        endPoint: .bottomTrailing
                    )
                )
                .overlay(
                    RoundedRectangle(cornerRadius: 24, style: .continuous)
                        .stroke(Color.white.opacity(0.08), lineWidth: 1)
                )
        )
    }
}
