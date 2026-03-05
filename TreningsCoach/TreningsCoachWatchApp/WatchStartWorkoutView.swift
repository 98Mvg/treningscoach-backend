import SwiftUI

struct WatchStartWorkoutView: View {
    @ObservedObject var wcManager: WatchWCManager
    @ObservedObject var workoutManager: WatchWorkoutManager

    var body: some View {
        VStack(spacing: 12) {
            Text("Start workout?")
                .font(.headline)

            Text("Requested: \(wcManager.pendingWorkoutType ?? WCKeys.WorkoutType.easyRun)")
                .font(.footnote)
                .foregroundStyle(.secondary)

            if let hr = workoutManager.currentHR {
                Text("\(Int(hr)) bpm")
                    .font(.title2)
            } else {
                Text("-- bpm")
                    .font(.title2)
            }

            if workoutManager.isRunning {
                Button("Stop") {
                    workoutManager.stopWorkout()
                }
            } else {
                Button("Start") {
                    Task {
                        let requestTs = wcManager.pendingRequestTimestamp ?? Date().timeIntervalSince1970
                        let requestID = wcManager.pendingRequestId ?? UUID().uuidString
                        let requestedType = wcManager.pendingWorkoutType ?? WCKeys.WorkoutType.easyRun
                        await workoutManager.startWorkout(
                            workoutType: requestedType,
                            requestTimestamp: requestTs,
                            requestID: requestID
                        )
                    }
                }
            }
        }
        .padding()
    }
}
